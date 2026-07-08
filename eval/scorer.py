#!/usr/bin/env python3
"""Hybrid scorer — Phase 5 (issue #24, EPIC D #4).

Runs the baseline Fabric-IQ-grounded agent over ``eval/dataset.jsonl`` for one model deployment and scores
each answer against the deterministic SQL ground truth (``eval/ground_truth.json``) with an LLM-as-judge
second opinion. Captures the SIX metric families required by the issue and emits a per-task record plus an
aggregate scorecard (JSON + markdown).

Metric families
  1. accuracy    — SQL-primary correctness (exact scalar / set membership) + LLM-judge confirmation.
  2. tokens      — input/output tokens per task (from the Responses API usage).
  3. cost        — $/task from eval/pricing.json, plus aggregate cost-per-correct-answer.
  4. latency     — wall-clock ms per task.
  5. grounding   — did the agent call fabric_iq_preview? traversal-correctness for multi-hop questions.
  6. frozen      — model deployment string + config hash; identical config across models proves the only
                   variable is the model (Art. II frozen weights, Art. III swappability).

Fairness (Art. III / experiment protocol): the ontology, agent config, eval set, and SQL ground truth are
IDENTICAL across models; only ``--model`` changes.

Usage:
  python eval/scorer.py --model gpt-5.4
  python eval/scorer.py --model gpt-5.4-mini --judge-model gpt-5.4
  python eval/scorer.py --model gpt-5.4 --dry-run-mock   # offline: score canned answers, no live calls
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "agent"))

_DATASET = _ROOT / "eval" / "dataset.jsonl"
_TRUTH = _ROOT / "eval" / "ground_truth.json"
_PRICING = _ROOT / "eval" / "pricing.json"
_SCORECARD_DIR = _ROOT / "eval" / "scorecards"

_NUM_RE = re.compile(r"-?\d[\d,]*\.?\d*")


# --------------------------------------------------------------------------------------------------
# Accuracy primitives (SQL-primary)
# --------------------------------------------------------------------------------------------------
def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _score_scalar(answer: str, expected: Any) -> tuple[bool, str]:
    """Numeric answers: tolerance match on any number in the text. Strings: normalized substring."""
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        exp = float(expected)
        for m in _NUM_RE.findall(answer or ""):
            try:
                val = float(m.replace(",", ""))
            except ValueError:
                continue
            tol = max(0.01, abs(exp) * 0.01)
            if abs(val - exp) <= tol:
                return True, f"found {val} within tol of {exp}"
        return False, f"expected {exp} not found among numbers in answer"
    exp_s = _norm(str(expected))
    return (exp_s in _norm(answer), f"substring match for '{expected}'")


def _score_set(answer: str, expected: list[str]) -> tuple[bool, str, float]:
    """Set answers: recall of expected members found as substrings. Correct if recall == 1.0."""
    ans = _norm(answer)
    found = [v for v in expected if _norm(v) in ans]
    recall = len(found) / len(expected) if expected else 1.0
    ok = recall >= 0.999
    missing = [v for v in expected if _norm(v) not in ans]
    return ok, (f"recall {recall:.2f}" + (f", missing {missing[:5]}" if missing else "")), recall


# --------------------------------------------------------------------------------------------------
# LLM-as-judge (second opinion; primary oracle for refusal cases)
# --------------------------------------------------------------------------------------------------
class Judge:
    def __init__(self, openai_client: Any, model: str) -> None:
        self._client = openai_client
        self._model = model

    def _ask(self, system: str, user: str) -> dict[str, Any]:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as exc:  # noqa: BLE001
            return {"correct": None, "reason": f"judge error: {type(exc).__name__}: {exc}"}

    def grade_answerable(self, question: str, expected: str, answer: str) -> dict[str, Any]:
        sys_p = (
            "You grade a water-quality analyst agent. Given the QUESTION, the correct ground-truth ANSWER "
            "(computed from SQL over the source data), and the AGENT ANSWER, decide if the agent answer is "
            "factually consistent with the ground truth. Ignore wording, extra context, and formatting. "
            'Respond as JSON: {"correct": true|false, "reason": "<short>"}.'
        )
        usr = f"QUESTION:\n{question}\n\nGROUND TRUTH:\n{expected}\n\nAGENT ANSWER:\n{answer}"
        return self._ask(sys_p, usr)

    def grade_refusal(self, question: str, answer: str) -> dict[str, Any]:
        sys_p = (
            "The QUESTION asks for information that does NOT exist in the agent's data ontology (or is out "
            "of its domain). A correct agent must decline or state the data is unavailable and must NOT "
            "fabricate specific values, entities, or relationships. Judge the AGENT ANSWER. "
            'Respond as JSON: {"correct": true|false, "reason": "<short>"} where correct=true means it '
            "safely declined without inventing data."
        )
        usr = f"QUESTION:\n{question}\n\nAGENT ANSWER:\n{answer}"
        return self._ask(sys_p, usr)


# --------------------------------------------------------------------------------------------------
# Grounding / traversal evidence
# --------------------------------------------------------------------------------------------------
def _grounding(result: Any) -> dict[str, Any]:
    calls = result.tool_calls or []
    called_fabric = any(
        "fabric" in str(c.get("type", "")).lower() or "fabric" in str(c.get("name", "")).lower()
        or "mcp" in str(c.get("type", "")).lower()
        for c in calls
    )
    return {"tool_call_count": len(calls), "called_fabric_iq": called_fabric,
            "tool_calls": calls}


# --------------------------------------------------------------------------------------------------
# Cost
# --------------------------------------------------------------------------------------------------
def _load_pricing(model: str) -> dict[str, float]:
    p = json.loads(_PRICING.read_text(encoding="utf-8"))
    rates = p.get("models", {}).get(model) or p.get("default", {"input": 1.0, "output": 5.0})
    return rates


def _task_cost(in_tok: int, out_tok: int, rates: dict[str, float]) -> float:
    return (in_tok / 1_000_000) * rates["input"] + (out_tok / 1_000_000) * rates["output"]


# --------------------------------------------------------------------------------------------------
# Per-task scoring
# --------------------------------------------------------------------------------------------------
def score_task(rec: dict[str, Any], gt: dict[str, Any], result: Any, judge: Judge | None,
               rates: dict[str, float]) -> dict[str, Any]:
    atype = gt["answer_type"]
    answer = result.answer or ""
    sql_ok: bool
    detail: str
    recall: float | None = None
    judge_res: dict[str, Any] = {"correct": None, "reason": "not run"}

    if atype == "scalar":
        sql_ok, detail = _score_scalar(answer, gt["value"])
        if judge is not None and not result.error:
            judge_res = judge.grade_answerable(rec["question"], str(gt["value"]), answer)
    elif atype == "set":
        sql_ok, detail, recall = _score_set(answer, gt["values"])
        if judge is not None and not result.error:
            judge_res = judge.grade_answerable(rec["question"], ", ".join(gt["values"]), answer)
    elif atype == "refusal":
        # No SQL oracle; the judge is primary. Heuristic backstop below.
        if judge is not None and not result.error:
            judge_res = judge.grade_refusal(rec["question"], answer)
        heuristic = any(k in _norm(answer) for k in (
            "not available", "no data", "cannot", "can't", "unable", "does not", "doesn't",
            "not found", "not in", "outside", "no information", "not contain", "unavailable"))
        sql_ok = bool(judge_res.get("correct")) if judge_res.get("correct") is not None else heuristic
        detail = "refusal: judge-primary" + ("" if judge_res.get("correct") is not None else " (heuristic)")
    else:
        raise ValueError(atype)

    grounding = _grounding(result)
    # Traversal-correctness: for multi-hop, credited when the tool was called AND the answer is correct.
    is_multi = rec["category"] == "multi_hop"
    traversal_ok = (grounding["called_fabric_iq"] and sql_ok) if is_multi else None

    in_tok, out_tok = result.input_tokens, result.output_tokens
    cost = _task_cost(in_tok, out_tok, rates)

    return {
        "id": rec["id"],
        "category": rec["category"],
        "answer_type": atype,
        "question": rec["question"],
        "expected": gt.get("value", gt.get("values", "refusal")),
        "answer": answer,
        "error": result.error,
        # 1. accuracy
        "sql_correct": sql_ok,
        "sql_detail": detail,
        "set_recall": recall,
        "judge_correct": judge_res.get("correct"),
        "judge_reason": judge_res.get("reason"),
        "correct": bool(sql_ok),
        # 2. tokens
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        # 3. cost
        "cost_usd": round(cost, 8),
        # 4. latency
        "latency_ms": result.latency_ms,
        # 5. grounding / traversal
        "called_fabric_iq": grounding["called_fabric_iq"],
        "tool_call_count": grounding["tool_call_count"],
        "expected_traversal": gt.get("expected_traversal", []),
        "traversal_ok": traversal_ok,
        "tool_calls": grounding["tool_calls"],
        # 6. frozen weights
        "model": result.model,
        "config_hash": result.config_hash,
    }


# --------------------------------------------------------------------------------------------------
# Aggregation + rendering
# --------------------------------------------------------------------------------------------------
def aggregate(model: str, tasks: list[dict[str, Any]], pricing_meta: dict[str, Any]) -> dict[str, Any]:
    n = len(tasks)
    correct = sum(1 for t in tasks if t["correct"])
    by_cat: dict[str, dict[str, int]] = {}
    for t in tasks:
        c = by_cat.setdefault(t["category"], {"n": 0, "correct": 0})
        c["n"] += 1
        c["correct"] += int(t["correct"])

    tot_in = sum(t["input_tokens"] for t in tasks)
    tot_out = sum(t["output_tokens"] for t in tasks)
    tot_cost = sum(t["cost_usd"] for t in tasks)
    latencies = sorted(t["latency_ms"] for t in tasks)
    multi = [t for t in tasks if t["category"] == "multi_hop"]
    grounded = sum(1 for t in tasks if t["called_fabric_iq"])
    traversal_ok = sum(1 for t in multi if t["traversal_ok"])
    config_hashes = sorted({t["config_hash"] for t in tasks})

    def pct(a: int, b: int) -> float:
        return round(100.0 * a / b, 1) if b else 0.0

    return {
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_tasks": n,
        "accuracy": {
            "overall_pct": pct(correct, n),
            "correct": correct,
            "by_category": {k: {"pct": pct(v["correct"], v["n"]), **v} for k, v in sorted(by_cat.items())},
        },
        "tokens": {"input": tot_in, "output": tot_out, "total": tot_in + tot_out,
                   "avg_per_task": round((tot_in + tot_out) / n, 1) if n else 0},
        "cost": {
            "pricing_verified": pricing_meta.get("verified", False),
            "pricing_source": pricing_meta.get("source"),
            "total_usd": round(tot_cost, 6),
            "avg_per_task_usd": round(tot_cost / n, 6) if n else 0,
            "cost_per_correct_usd": round(tot_cost / correct, 6) if correct else None,
        },
        "latency_ms": {
            "avg": round(sum(latencies) / n) if n else 0,
            "p50": latencies[len(latencies) // 2] if latencies else 0,
            "p95": latencies[min(len(latencies) - 1, int(0.95 * len(latencies)))] if latencies else 0,
            "max": latencies[-1] if latencies else 0,
        },
        "grounding": {
            "called_fabric_iq_pct": pct(grounded, n),
            "multi_hop_traversal_ok_pct": pct(traversal_ok, len(multi)) if multi else 0.0,
            "multi_hop_n": len(multi),
        },
        "frozen_weights": {
            "fine_tuning": False,
            "model_is_deployment_string": True,
            "config_hashes": config_hashes,
            "single_config": len(config_hashes) == 1,
        },
    }


def render_markdown(agg: dict[str, Any], tasks: list[dict[str, Any]]) -> str:
    a = agg["accuracy"]
    lines = [
        f"# Baseline scorecard — `{agg['model']}`",
        "",
        f"_Generated {agg['generated_at']} · {agg['n_tasks']} tasks · ontology grounded in ALL runs._",
        "",
        "## Headline metrics",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Accuracy (overall) | **{a['overall_pct']}%** ({a['correct']}/{agg['n_tasks']}) |",
        f"| Tokens (total in/out) | {agg['tokens']['input']} / {agg['tokens']['output']} |",
        f"| Tokens (avg/task) | {agg['tokens']['avg_per_task']} |",
        f"| Cost total (USD) | ${agg['cost']['total_usd']} |",
        f"| Cost per correct answer (USD) | ${agg['cost']['cost_per_correct_usd']} |",
        f"| Latency avg / p95 (ms) | {agg['latency_ms']['avg']} / {agg['latency_ms']['p95']} |",
        f"| Grounded (called Fabric IQ) | {agg['grounding']['called_fabric_iq_pct']}% |",
        f"| Multi-hop traversal correct | {agg['grounding']['multi_hop_traversal_ok_pct']}% |",
        f"| Frozen weights / single config | {agg['frozen_weights']['fine_tuning'] is False} / {agg['frozen_weights']['single_config']} |",
        "",
        f"> Cost pricing verified: **{agg['cost']['pricing_verified']}** (source: {agg['cost']['pricing_source']}).",
        "",
        "## Accuracy by category",
        "",
        "| Category | Correct | Total | % |",
        "| --- | --- | --- | --- |",
    ]
    for cat, v in a["by_category"].items():
        lines.append(f"| {cat} | {v['correct']} | {v['n']} | {v['pct']}% |")
    lines += ["", "## Per-task", "", "| id | cat | correct | grounded | in/out tok | ms | detail |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for t in tasks:
        detail = (t["sql_detail"] or "")[:60].replace("|", "/")
        lines.append(
            f"| {t['id']} | {t['category']} | {'✅' if t['correct'] else '❌'} | "
            f"{'✔' if t['called_fabric_iq'] else '—'} | {t['input_tokens']}/{t['output_tokens']} | "
            f"{t['latency_ms']} | {detail} |"
        )
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------------------------------
def _load_dataset() -> list[dict[str, Any]]:
    return [json.loads(l) for l in _DATASET.read_text(encoding="utf-8").splitlines() if l.strip()]


def run(model: str, judge_model: str | None, mock: bool = False,
        limit: int | None = None) -> dict[str, Any]:
    dataset = _load_dataset()
    if limit:
        dataset = dataset[:limit]
    truth = json.loads(_TRUTH.read_text(encoding="utf-8"))["ground_truth"]
    pricing_meta = json.loads(_PRICING.read_text(encoding="utf-8"))
    rates = _load_pricing(model)

    tasks: list[dict[str, Any]] = []
    _SCORECARD_DIR.mkdir(parents=True, exist_ok=True)

    if mock:
        # Offline self-test: fabricate plausible results to exercise scoring/aggregation with no live calls.
        from harness import InvokeResult
        judge = None
        for rec in dataset:
            gt = truth[rec["id"]]
            if gt["answer_type"] == "scalar":
                ans = f"The answer is {gt['value']}."
            elif gt["answer_type"] == "set":
                ans = "Results: " + "; ".join(gt["values"]) + "."
            else:
                ans = "That information is not available in the ontology, so I cannot answer."
            res = InvokeResult(model=model, prompt=rec["question"], answer=ans,
                               tool_calls=[{"type": "fabric_iq_preview_call", "name": "fabriciq-iqnpl-ontology",
                                            "arguments": rec["question"]}],
                               input_tokens=1000, output_tokens=120, latency_ms=1500,
                               config_hash="mock-hash")
            tasks.append(score_task(rec, gt, res, judge, rates))
    else:
        from harness import AgentHarness
        with AgentHarness() as harness:
            openai_client = harness._openai  # reuse project OpenAI client for judging
            judge = Judge(openai_client, judge_model or "gpt-5.4") if judge_model is not None else \
                Judge(openai_client, "gpt-5.4")
            for i, rec in enumerate(dataset, 1):
                gt = truth[rec["id"]]
                print(f"[{i}/{len(dataset)}] {rec['id']} ({model}) ...", flush=True)
                result = harness.invoke(rec["question"], model=model)
                tasks.append(score_task(rec, gt, result, judge, rates))
                time.sleep(0.2)

    agg = aggregate(model, tasks, pricing_meta)
    safe_model = model.replace("/", "_")
    (_SCORECARD_DIR / f"baseline_{safe_model}.json").write_text(
        json.dumps({"aggregate": agg, "tasks": tasks}, indent=2, ensure_ascii=False), encoding="utf-8")
    (_SCORECARD_DIR / f"baseline_{safe_model}.md").write_text(
        render_markdown(agg, tasks), encoding="utf-8")
    print(json.dumps(agg, indent=2, ensure_ascii=False))
    return agg


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    ap = argparse.ArgumentParser(description="Score the baseline agent for one model.")
    ap.add_argument("--model", required=True, help="model deployment name (swappable)")
    ap.add_argument("--judge-model", default="gpt-5.4", help="LLM-as-judge deployment (default gpt-5.4)")
    ap.add_argument("--limit", type=int, default=None, help="score only the first N questions")
    ap.add_argument("--dry-run-mock", action="store_true",
                    help="offline: score canned answers to validate the scorer without live calls")
    args = ap.parse_args()
    run(args.model, judge_model=args.judge_model, mock=args.dry_run_mock, limit=args.limit)


if __name__ == "__main__":
    main()
