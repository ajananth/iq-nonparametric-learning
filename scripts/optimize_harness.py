#!/usr/bin/env python3
"""SkillOpt-style CUSTOM optimization loop — Phase 6 (issue #29, EPIC E #5).

Optimizes the frozen-weights **text surface** of the Fabric-IQ-grounded agent on a FIXED model
(``gpt-5.4``) and proves a lift vs the Phase-5 grounded baseline (91.7% @ $0.175, 22/24). This is a
CUSTOM loop over OUR ``agent/harness.py`` (retrieve+inject, ``rerankerThreshold:0``, dual-auth) and OUR
``eval/scorer.py`` primitives — NOT ``azd ai agent optimize`` — because the native optimizer cannot run our
retrieve+inject preprocessing and would confound the lift (docs/verified-capabilities.md §2c/§3). The
mechanism is attributed to **Microsoft Research SkillOpt** (docs/verified-capabilities.md §4; Art. VII.2):

    seed = baseline config
    ROLLOUT   score the current config on the TRAIN split
    REFLECT   an optimizer model (gpt-5.4) proposes ONE bounded text edit, clipped by a textual
              "learning rate", with a rejected-edit buffer supplied as NEGATIVE context
    VALIDATE  if promising on TRAIN, re-score on the HELD-OUT DEV split
    ADOPT     keep the candidate ONLY if it is STRICTLY better on DEV (and never regresses the
              negative/safe-refusal guardrail) → keep best-version; else buffer the rejected edit

Governance:
  * Art. II  — weights are FROZEN. Only text/config is tuned; the model is a deployment-name string.
  * Art. III — the grounding MECHANISM is held constant baseline→optimized (single variable = the text
               config). ``--model`` is fixed to gpt-5.4 here (the model swap is Phase 7).
  * Art. I   — TRAIN/DEV come from ``eval/optimization_trainset.jsonl`` (DISJOINT from the 24-Q held-out
               ``eval/dataset.jsonl``). The held-out eval / scorer / ground-truth stay BYTE-IDENTICAL; this
               loop only IMPORTS scorer primitives, it never edits them.
  * Art. VIII — every live rollout issues real, billable model + Fabric IQ calls. Requires ``--confirm-cost``
               (or run offline with ``--dry-run``). Produce a cost estimate and get approval before a full run.

Optimization surface (all frozen-weights TEXT, issue #29):
  instructions.md · skills/SKILL.md · tools.json KB ``description`` · row-injection format (injection.json)
  · KB retrieval/answer instructions + ``retrievalReasoningEffort`` (re-provisioned via
  scripts/provision_knowledge_base.py when ``--allow-kb-reprovision`` is set).

Usage:
  # Offline mechanics check (no live calls, no cost) — confirms candidates+scores+diffs materialize:
  python scripts/optimize_harness.py --dry-run --max-steps 3

  # Tiny LIVE de-risk iteration (a handful of calls):
  python scripts/optimize_harness.py --confirm-cost --max-steps 1 --train-limit 2 --dev-limit 1

  # Full live run (after cost approval):
  python scripts/optimize_harness.py --confirm-cost --max-steps 12 --allow-kb-reprovision
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import random
import shutil
import sys
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "agent"))
sys.path.insert(0, str(_ROOT / "eval"))
sys.path.insert(0, str(_ROOT / "scripts"))

_BASELINE_DIR = _ROOT / "agent" / ".agent_configs" / "baseline"
_OPTIMIZED_DIR = _ROOT / "agent" / ".agent_configs" / "optimized"
_TRAINSET = _ROOT / "eval" / "optimization_trainset.jsonl"
_TRUTH = _ROOT / "eval" / "optimization_ground_truth.json"
_PRICING = _ROOT / "eval" / "pricing.json"
_WORKSPACE = _ROOT / ".optimize_workspace"          # gitignored candidate scratch
_RUNS_DIR = _ROOT / "eval" / "optimization_runs"     # committed logs / ranking / diff

# Baseline KB params (mirror scripts/provision_knowledge_base.py defaults). A candidate that leaves these
# unchanged never triggers a re-provision (the KB stays in its Phase-5 baseline state).
_BASELINE_KB_PARAMS: dict[str, Any] = {
    "reasoning": "medium",
    "retrieval_instructions": None,
    "answer_instructions": None,
}
_INJECTION_DEFAULTS: dict[str, Any] = {
    "include_synthesized_answer": True,
    "max_rows": None,
    "drop_columns": [],
    "max_row_chars": None,
}


# --------------------------------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------------------------------
def _load_split(train_limit: int | None, dev_limit: int | None) -> tuple[list, list, dict]:
    records = [json.loads(l) for l in _TRAINSET.read_text(encoding="utf-8").splitlines() if l.strip()]
    truth = json.loads(_TRUTH.read_text(encoding="utf-8"))["ground_truth"]
    train = [r for r in records if r.get("split") == "train"]
    dev = [r for r in records if r.get("split") == "dev"]
    if train_limit is not None:
        train = train[:train_limit]
    if dev_limit is not None:
        dev = dev[:dev_limit]
    return train, dev, truth


# --------------------------------------------------------------------------------------------------
# Candidate config
# --------------------------------------------------------------------------------------------------
@dataclass
class Candidate:
    cid: str
    instructions: str
    tools: dict[str, Any]           # parsed tools.json (env ${TOKENS} preserved as literal strings)
    skill: str                      # single SKILL.md body (baseline ships one skill)
    injection: dict[str, Any]       # row-injection format overrides
    kb_params: dict[str, Any]       # {reasoning, retrieval_instructions, answer_instructions}
    parent: str | None = None
    edit: dict[str, Any] | None = None

    @property
    def description(self) -> str:
        return self.tools["grounding"]["description"]

    def with_description(self, desc: str) -> "Candidate":
        tools = json.loads(json.dumps(self.tools))
        tools["grounding"]["description"] = desc
        return replace(self, tools=tools)


def _baseline_candidate() -> Candidate:
    instructions = (_BASELINE_DIR / "instructions.md").read_text(encoding="utf-8")
    tools = json.loads((_BASELINE_DIR / "tools.json").read_text(encoding="utf-8"))
    skill = (_BASELINE_DIR / "skills" / "SKILL.md").read_text(encoding="utf-8")
    return Candidate(
        cid="seed", instructions=instructions, tools=tools, skill=skill,
        injection=dict(_INJECTION_DEFAULTS), kb_params=dict(_BASELINE_KB_PARAMS),
    )


def _materialize(cand: Candidate) -> Path:
    """Write a candidate to a config dir the harness can load. injection.json is written ONLY when the
    injection differs from the byte-identical defaults, so a text-only candidate is grounded identically
    to the baseline."""
    d = _WORKSPACE / cand.cid
    if d.exists():
        shutil.rmtree(d)
    (d / "skills").mkdir(parents=True, exist_ok=True)
    (d / "instructions.md").write_text(cand.instructions, encoding="utf-8")
    (d / "tools.json").write_text(json.dumps(cand.tools, indent=2, ensure_ascii=False), encoding="utf-8")
    (d / "skills" / "SKILL.md").write_text(cand.skill, encoding="utf-8")
    if cand.injection != _INJECTION_DEFAULTS:
        (d / "injection.json").write_text(json.dumps(cand.injection, indent=2), encoding="utf-8")
    (d / "kb_params.json").write_text(json.dumps(cand.kb_params, indent=2), encoding="utf-8")
    return d


# --------------------------------------------------------------------------------------------------
# Metrics / objective / guardrail
# --------------------------------------------------------------------------------------------------
def _summarize(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(tasks)
    correct = sum(1 for t in tasks if t["correct"])
    neg = [t for t in tasks if t["category"] == "negative"]
    tokens = sum(t["input_tokens"] + t["output_tokens"] for t in tasks)
    return {
        "n": n,
        "correct": correct,
        "accuracy_pct": round(100.0 * correct / n, 2) if n else 0.0,
        "tokens": tokens,
        "neg_n": len(neg),
        "neg_correct": sum(1 for t in neg if t["correct"]),
    }


def _objective(summary: dict[str, Any]) -> tuple[float, int]:
    """Lexicographic objective: MAXIMISE accuracy, then MINIMISE total tokens (the H1 cost axis)."""
    return (summary["accuracy_pct"], -summary["tokens"])


# --------------------------------------------------------------------------------------------------
# Rollout (live + mock)
# --------------------------------------------------------------------------------------------------
def _mock_invoke(model: str, rec: dict[str, Any], gt: dict[str, Any], injection: dict[str, Any]):
    from harness import InvokeResult
    at = gt["answer_type"]
    if at == "scalar":
        ans = f"The answer is {gt['value']}."
    elif at == "set":
        ans = "Results: " + "; ".join(gt["values"]) + "."
    else:
        ans = "That information is not available in the ontology, so I cannot answer."
    # Token proxy sensitive to the injection knobs so the token objective is exercised offline.
    base = 1500
    if not injection.get("include_synthesized_answer", True):
        base -= 120
    base -= 70 * len(injection.get("drop_columns") or [])
    if injection.get("max_rows"):
        base -= 250
    base = max(300, base)
    return InvokeResult(model=model, prompt=rec["question"], answer=ans,
                        tool_calls=[{"type": "fabric_kb_retrieve", "name": "kb"}],
                        input_tokens=base, output_tokens=120, latency_ms=1000, config_hash="mock")


def _rollout(cand: Candidate, records: list, truth: dict, rates: dict, model: str,
             judge_model: str, mock: bool) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    import scorer
    cand_dir = _materialize(cand)
    tasks: list[dict[str, Any]] = []
    if mock:
        for rec in records:
            gt = truth[rec["id"]]
            res = _mock_invoke(model, rec, gt, cand.injection)
            tasks.append(scorer.score_task(rec, gt, res, None, rates))
    else:
        from harness import AgentHarness
        with AgentHarness(config_dir=cand_dir) as hz:
            judge = scorer.Judge(hz._openai, judge_model)
            for i, rec in enumerate(records, 1):
                gt = truth[rec["id"]]
                print(f"    [{i}/{len(records)}] {rec['id']} ({cand.cid}) ...", flush=True)
                res = hz.invoke(rec["question"], model=model)
                tasks.append(scorer.score_task(rec, gt, res, judge, rates))
                time.sleep(0.2)
    return _summarize(tasks), tasks


# --------------------------------------------------------------------------------------------------
# KB re-provision (only when a candidate changes KB params and it is allowed)
# --------------------------------------------------------------------------------------------------
def _ensure_kb(target: dict[str, Any], current: dict[str, Any], model: str,
               allow: bool, mock: bool) -> dict[str, Any]:
    if mock or target == current:
        return current
    if not allow:
        raise SystemExit(
            f"candidate needs a KB re-provision ({target}) but --allow-kb-reprovision was not set.")
    import provision_knowledge_base as pkb
    print(f"    re-provisioning KB: {target}", flush=True)
    pkb.provision_kb(model, reasoning=target["reasoning"],
                     retrieval_instructions=target["retrieval_instructions"],
                     answer_instructions=target["answer_instructions"])
    time.sleep(2)
    return dict(target)


# --------------------------------------------------------------------------------------------------
# Reflection
# --------------------------------------------------------------------------------------------------
_REFLECT_SYSTEM = (
    "You are optimizing the TEXT configuration of a water-quality analyst agent whose model WEIGHTS ARE "
    "FROZEN (non-parametric learning). You may only edit text/config; you may not change the model or the "
    "grounding mechanism. The agent is grounded: every question arrives with verbatim ontology rows "
    "retrieved from a Fabric IQ knowledge base, and the agent must answer ONLY from those rows and refuse "
    "safely when the data is absent. Your job is to propose ONE small, bounded edit (a textual 'learning "
    "rate' — change at most a few sentences, or a couple of injection/KB knobs) that improves accuracy on "
    "the failing questions and/or REDUCES token usage WITHOUT causing fabrication on unanswerable questions. "
    "Never encode table/column names, SQL, or specific data values into the text (semantics live in the "
    "ontology). Respond as STRICT JSON with keys: "
    '{"target": one of ["instructions","skill","description","injection","kb_params"], '
    '"rationale": "<why this helps>", "new_content": "<full replacement text; for instructions|skill|'
    'description only>", "injection": {<full injection dict; for target=injection>}, '
    '"kb_params": {"reasoning":"low|medium","retrieval_instructions":str|null,"answer_instructions":str|null}}. '
    "Provide ONLY the key matching the chosen target (plus target + rationale)."
)

_INJECTION_HELP = (
    "injection knobs: include_synthesized_answer(bool), max_rows(int|null cap of injected row blocks), "
    "drop_columns(list of CSV column names to omit, e.g. long free-text 'notes'), max_row_chars(int|null). "
    "Dropping the free-text 'notes' column and/or capping rows cuts tokens; keep enough evidence to stay correct."
)


def _reflect_prompt(cand: Candidate, train_tasks: list[dict[str, Any]], buffer: list[dict[str, Any]]) -> str:
    fails = [t for t in train_tasks if not t["correct"]]
    costly = sorted(train_tasks, key=lambda t: t["input_tokens"] + t["output_tokens"], reverse=True)[:3]
    lines = ["## Current agent instructions", cand.instructions,
             "\n## Current skill body", cand.skill,
             "\n## Current KB grounding description", cand.description,
             "\n## Current row-injection format", json.dumps(cand.injection),
             "\n## Current KB params", json.dumps(cand.kb_params),
             "\n## " + _INJECTION_HELP,
             "\n## Failing TRAIN questions (fix these without breaking refusals)"]
    for t in fails:
        lines.append(f"- {t['id']} [{t['category']}]: {t['question']}\n   expected={t['expected']}  "
                     f"got={(t['answer'] or '')[:160]!r}  detail={t['sql_detail']}")
    if not fails:
        lines.append("- (none — all TRAIN questions correct; focus on REDUCING tokens while staying correct)")
    lines.append("\n## Most token-expensive TRAIN questions (trim these)")
    for t in costly:
        lines.append(f"- {t['id']}: {t['input_tokens']}+{t['output_tokens']} tokens")
    if buffer:
        lines.append("\n## Previously REJECTED edits (did NOT improve — do NOT repeat)")
        for b in buffer[-6:]:
            lines.append(f"- target={b.get('target')}: {b.get('rationale','')[:160]}")
    lines.append("\nPropose ONE bounded edit as STRICT JSON.")
    return "\n".join(lines)


def _apply_edit(cand: Candidate, edit: dict[str, Any], cid: str) -> Candidate | None:
    target = edit.get("target")
    try:
        if target == "instructions" and edit.get("new_content"):
            return replace(cand, cid=cid, instructions=edit["new_content"], parent=cand.cid, edit=edit)
        if target == "skill" and edit.get("new_content"):
            return replace(cand, cid=cid, skill=edit["new_content"], parent=cand.cid, edit=edit)
        if target == "description" and edit.get("new_content"):
            updated = cand.with_description(edit["new_content"])
            return replace(updated, cid=cid, parent=cand.cid, edit=edit)
        if target == "injection" and isinstance(edit.get("injection"), dict):
            inj = dict(_INJECTION_DEFAULTS)
            inj.update({k: v for k, v in edit["injection"].items() if k in _INJECTION_DEFAULTS})
            return replace(cand, cid=cid, injection=inj, parent=cand.cid, edit=edit)
        if target == "kb_params" and isinstance(edit.get("kb_params"), dict):
            kp = dict(cand.kb_params)
            kp.update({k: v for k, v in edit["kb_params"].items() if k in kp})
            return replace(cand, cid=cid, kb_params=kp, parent=cand.cid, edit=edit)
    except Exception as exc:  # noqa: BLE001
        print(f"    edit apply failed: {exc}", flush=True)
    return None


def _reflect_live(openai_client: Any, reflect_model: str, cand: Candidate,
                  train_tasks: list[dict[str, Any]], buffer: list[dict[str, Any]]) -> dict[str, Any] | None:
    try:
        resp = openai_client.chat.completions.create(
            model=reflect_model,
            messages=[{"role": "system", "content": _REFLECT_SYSTEM},
                      {"role": "user", "content": _reflect_prompt(cand, train_tasks, buffer)}],
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as exc:  # noqa: BLE001
        print(f"    reflection error: {type(exc).__name__}: {exc}", flush=True)
        return None


# Deterministic stub edits for --dry-run: exercise injection + text targets so candidates/scores/diffs
# materialize with ZERO cost and no reflection LLM call.
_STUB_EDITS = [
    {"target": "injection", "rationale": "Drop the long free-text 'notes' column to cut tokens.",
     "injection": {"drop_columns": ["notes"]}},
    {"target": "instructions", "rationale": "Add an explicit filter-application instruction (S01-style).",
     "new_content": None},  # filled at runtime (append a sentence to current instructions)
    {"target": "injection", "rationale": "Also omit the synthesized summary to cut tokens further.",
     "injection": {"drop_columns": ["notes"], "include_synthesized_answer": False}},
]


def _reflect_stub(cand: Candidate, step: int) -> dict[str, Any]:
    edit = json.loads(json.dumps(_STUB_EDITS[step % len(_STUB_EDITS)]))
    if edit["target"] == "instructions":
        edit["new_content"] = cand.instructions.rstrip() + (
            "\n\n- When a question asks for a count or list under a condition (e.g. active sites, a named "
            "water body, a toxicity level), apply that condition to the provided rows before answering.")
    return edit


# --------------------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------------------
def _write_optimized(cand: Candidate) -> None:
    if _OPTIMIZED_DIR.exists():
        shutil.rmtree(_OPTIMIZED_DIR)
    (_OPTIMIZED_DIR / "skills").mkdir(parents=True, exist_ok=True)
    (_OPTIMIZED_DIR / "instructions.md").write_text(cand.instructions, encoding="utf-8")
    (_OPTIMIZED_DIR / "tools.json").write_text(
        json.dumps(cand.tools, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (_OPTIMIZED_DIR / "skills" / "SKILL.md").write_text(cand.skill, encoding="utf-8")
    if cand.injection != _INJECTION_DEFAULTS:
        (_OPTIMIZED_DIR / "injection.json").write_text(
            json.dumps(cand.injection, indent=2) + "\n", encoding="utf-8")
    (_OPTIMIZED_DIR / "kb_params.json").write_text(
        json.dumps(cand.kb_params, indent=2) + "\n", encoding="utf-8")


def _text_diff(winner: Candidate) -> str:
    base = _baseline_candidate()
    parts: list[str] = []

    def diff(name: str, a: str, b: str) -> None:
        d = list(difflib.unified_diff(a.splitlines(), b.splitlines(),
                                      fromfile=f"baseline/{name}", tofile=f"optimized/{name}", lineterm=""))
        parts.append("\n".join(d) if d else f"# {name}: (unchanged)")

    diff("instructions.md", base.instructions, winner.instructions)
    diff("skills/SKILL.md", base.skill, winner.skill)
    diff("tools.json:grounding.description", base.description, winner.description)
    parts.append(f"# injection.json\n- baseline: {json.dumps(base.injection)}\n+ optimized: {json.dumps(winner.injection)}")
    parts.append(f"# kb_params\n- baseline: {json.dumps(base.kb_params)}\n+ optimized: {json.dumps(winner.kb_params)}")
    return "\n\n".join(parts) + "\n"


def _write_run(run_dir: Path, log: list[dict[str, Any]], winner_cid: str, cfg: dict[str, Any],
               winner: Candidate) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "candidates_log.json").write_text(
        json.dumps({"config": cfg, "candidates": log}, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "optimized_vs_baseline.diff").write_text(_text_diff(winner), encoding="utf-8")

    ranked = sorted([e for e in log if e.get("dev")], key=lambda e: tuple(e["dev_objective"]), reverse=True)
    lines = [
        "# Phase-6 optimization run — candidate ranking",
        "",
        f"_Generated {datetime.now(timezone.utc).isoformat()} · model `{cfg['model']}` (FROZEN) · "
        f"reflection `{cfg['reflect_model']}` · seed {cfg['seed']} · mode "
        f"{'DRY-RUN (mock)' if cfg['mock'] else 'LIVE'}._",
        "",
        f"**Winner: `{winner_cid}`.** Objective = lexicographic (accuracy ↑, then tokens ↓). "
        "Adopt only if STRICTLY better on the held-out DEV split and the negative safe-refusal guardrail "
        "never regresses.",
        "",
        "| cand | target | parent | TRAIN acc% | TRAIN tok | promising | DEV acc% | DEV tok | adopted |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for e in log:
        tr, dv = e.get("train", {}), e.get("dev")
        lines.append(
            f"| {e['cid']} | {e.get('target','seed')} | {e.get('parent','-')} | "
            f"{tr.get('accuracy_pct','-')} | {tr.get('tokens','-')} | {e.get('promising','-')} | "
            f"{dv['accuracy_pct'] if dv else '-'} | {dv['tokens'] if dv else '-'} | {e.get('adopted','-')} |")
    lines += ["", "## Ranking by DEV objective (validated candidates)", ""]
    for i, e in enumerate(ranked, 1):
        lines.append(f"{i}. `{e['cid']}` ({e.get('target')}) — DEV acc {e['dev']['accuracy_pct']}%, "
                     f"{e['dev']['tokens']} tok — {e.get('rationale','')[:100]}")
    (run_dir / "ranking.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------------------------------
# The loop
# --------------------------------------------------------------------------------------------------
def optimize(args: argparse.Namespace) -> None:
    import scorer
    random.seed(args.seed)
    _WORKSPACE.mkdir(parents=True, exist_ok=True)

    train, dev, truth = _load_split(args.train_limit, args.dev_limit)
    rates = scorer._load_pricing(args.model)
    print(f"TRAIN={len(train)}  DEV={len(dev)}  model={args.model}  mode={'DRY' if args.mock else 'LIVE'}")

    reflect_client = None
    if not args.mock:
        from harness import AgentHarness
        # A lightweight project client just for reflection (rollouts open their own per-candidate harness).
        _rc = AgentHarness().__enter__()
        reflect_client = _rc._openai

    current_kb = dict(_BASELINE_KB_PARAMS)
    seed = _baseline_candidate()
    current_kb = _ensure_kb(seed.kb_params, current_kb, args.model, args.allow_kb_reprovision, args.mock)

    print("== seed rollout ==")
    seed_train, seed_train_tasks = _rollout(seed, train, truth, rates, args.model, args.judge_model, args.mock)
    seed_dev, _ = _rollout(seed, dev, truth, rates, args.model, args.judge_model, args.mock)
    best, best_train, best_dev, best_train_tasks = seed, seed_train, seed_dev, seed_train_tasks
    seed_neg = seed_dev["neg_correct"]

    log: list[dict[str, Any]] = [{
        "cid": "seed", "target": "seed", "parent": None, "rationale": "Phase-5 baseline config.",
        "train": seed_train, "dev": seed_dev, "dev_objective": list(_objective(seed_dev)),
        "promising": True, "adopted": True,
    }]
    buffer: list[dict[str, Any]] = []

    for step in range(args.max_steps):
        cid = f"c{step+1:02d}"
        print(f"\n== step {step+1}/{args.max_steps} ({cid}) ==")
        edit = _reflect_stub(best, step) if args.mock else \
            _reflect_live(reflect_client, args.reflect_model, best, best_train_tasks, buffer)
        if not edit:
            print("    no edit proposed; skipping.")
            continue
        cand = _apply_edit(best, edit, cid)
        if cand is None:
            print(f"    unusable edit for target={edit.get('target')}; buffering.")
            buffer.append(edit)
            continue
        print(f"    edit target={edit.get('target')} :: {edit.get('rationale','')[:100]}")

        current_kb = _ensure_kb(cand.kb_params, current_kb, args.model, args.allow_kb_reprovision, args.mock)
        ct, ct_tasks = _rollout(cand, train, truth, rates, args.model, args.judge_model, args.mock)
        promising = _objective(ct) > _objective(best_train)
        guardrail = ct["neg_correct"] >= best_train["neg_correct"]
        entry: dict[str, Any] = {
            "cid": cid, "target": edit.get("target"), "parent": best.cid,
            "rationale": edit.get("rationale", ""), "edit": edit,
            "train": ct, "promising": promising and guardrail,
        }
        if promising and guardrail:
            cd, _ = _rollout(cand, dev, truth, rates, args.model, args.judge_model, args.mock)
            strictly_better = (_objective(cd) > _objective(best_dev)
                               and cd["accuracy_pct"] >= seed_dev["accuracy_pct"]
                               and cd["neg_correct"] >= seed_neg)
            entry["dev"] = cd
            entry["dev_objective"] = list(_objective(cd))
            entry["adopted"] = strictly_better
            if strictly_better:
                print(f"    ADOPTED (DEV acc {cd['accuracy_pct']}%, {cd['tokens']} tok).")
                best, best_train, best_dev, best_train_tasks = cand, ct, cd, ct_tasks
            else:
                print(f"    rejected on DEV (acc {cd['accuracy_pct']}%, {cd['tokens']} tok).")
                buffer.append(edit)
                current_kb = _ensure_kb(best.kb_params, current_kb, args.model, args.allow_kb_reprovision, args.mock)
        else:
            print(f"    not promising on TRAIN (acc {ct['accuracy_pct']}%, {ct['tokens']} tok, "
                  f"guardrail={guardrail}); buffering.")
            entry["adopted"] = False
            buffer.append(edit)
            current_kb = _ensure_kb(best.kb_params, current_kb, args.model, args.allow_kb_reprovision, args.mock)
        log.append(entry)

    # Leave the KB in the WINNER's state and ship the winning config.
    _ensure_kb(best.kb_params, current_kb, args.model, args.allow_kb_reprovision, args.mock)
    _write_optimized(best)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = _RUNS_DIR / ("dryrun_" + ts if args.mock else ts)
    cfg = {"model": args.model, "reflect_model": args.reflect_model, "judge_model": args.judge_model,
           "seed": args.seed, "max_steps": args.max_steps, "mock": args.mock,
           "train_n": len(train), "dev_n": len(dev),
           "objective": "lexicographic(accuracy desc, tokens asc); DEV strict-better gate; neg guardrail"}
    _write_run(run_dir, log, best.cid, cfg, best)

    if reflect_client is not None:
        try:
            _rc.__exit__(None, None, None)
        except Exception:
            pass

    print(f"\nWinner: {best.cid}")
    print(f"  seed  DEV: acc {seed_dev['accuracy_pct']}%  tokens {seed_dev['tokens']}")
    print(f"  best  DEV: acc {best_dev['accuracy_pct']}%  tokens {best_dev['tokens']}")
    print(f"Optimized config -> {_OPTIMIZED_DIR}")
    print(f"Run log/ranking/diff -> {run_dir}")


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    ap = argparse.ArgumentParser(description="SkillOpt-style custom optimization loop (Phase 6).")
    ap.add_argument("--model", default=os.environ.get("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-5.4"),
                    help="FIXED target/synthesis model deployment (frozen weights). Default gpt-5.4.")
    ap.add_argument("--reflect-model", default="gpt-5.4", help="optimizer/reflection model deployment.")
    ap.add_argument("--judge-model", default="gpt-5.4", help="LLM-as-judge deployment (scorer).")
    ap.add_argument("--max-steps", type=int, default=8, help="number of reflect→validate iterations.")
    ap.add_argument("--seed", type=int, default=1234, help="RNG seed (reproducibility).")
    ap.add_argument("--train-limit", type=int, default=None, help="use only the first N TRAIN questions.")
    ap.add_argument("--dev-limit", type=int, default=None, help="use only the first N DEV questions.")
    ap.add_argument("--allow-kb-reprovision", action="store_true",
                    help="permit candidates that re-provision the KB (retrievalReasoningEffort / KB instructions).")
    ap.add_argument("--dry-run", dest="mock", action="store_true",
                    help="offline: mock rollouts + stub reflection; no live calls, no cost.")
    ap.add_argument("--confirm-cost", action="store_true",
                    help="acknowledge that live rollouts issue real, billable model + Fabric IQ calls (Art. VIII).")
    args = ap.parse_args()

    if not args.mock and not args.confirm_cost:
        raise SystemExit(
            "Cost gate (Art. VIII): live rollouts issue real model + Fabric IQ calls. "
            "Re-run with --confirm-cost once approved, or use --dry-run offline.")
    optimize(args)


if __name__ == "__main__":
    main()
