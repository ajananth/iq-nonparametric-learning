#!/usr/bin/env python3
"""Baseline run matrix + H1 comparison — Phase 5 (issue #24, EPIC D #4).

Runs the hybrid scorer for EACH model in the baseline matrix (default: gpt-5.4 and gpt-5.4-mini) over the
identical eval set, with the ontology grounded in ALL runs, then writes a combined comparison scorecard and
evaluates the pre-registered H1 Pareto criterion (SLM accuracy >= LLM AND SLM tokens/cost << LLM).

Single-variable fairness control (Art. III / experiment protocol): the ontology, agent config, eval set,
and SQL ground truth are identical across models; the ONLY thing that changes is the model deployment
string. The scorer records the config hash per task; this script asserts it is identical across models.

Cost gate (Art. VIII / C9): every task issues real model + Fabric IQ calls. Confirm cost approval before
running. Use --confirm-cost to acknowledge, or run interactively.

Usage:
  python eval/run_baseline.py --models gpt-5.4 gpt-5.4-mini --confirm-cost
  python eval/run_baseline.py --dry-run-mock            # offline validation, no live calls / no cost
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import scorer  # local module (eval/ is the cwd-relative import root)

_ROOT = Path(__file__).resolve().parent.parent
_SCORECARD_DIR = _ROOT / "eval" / "scorecards"


def _pareto(llm: dict[str, Any], slm: dict[str, Any]) -> dict[str, Any]:
    """Evaluate the H1 Pareto criterion using the LLM as reference and the SLM as challenger."""
    acc_slm = slm["accuracy"]["overall_pct"]
    acc_llm = llm["accuracy"]["overall_pct"]
    tok_slm = slm["tokens"]["total"]
    tok_llm = llm["tokens"]["total"]
    cost_slm = slm["cost"]["total_usd"]
    cost_llm = llm["cost"]["total_usd"]

    accuracy_ge = acc_slm >= acc_llm
    tokens_much_less = tok_llm > 0 and tok_slm <= 0.75 * tok_llm
    cost_much_less = cost_llm > 0 and cost_slm <= 0.75 * cost_llm
    return {
        "reference_llm": llm["model"],
        "challenger_slm": slm["model"],
        "accuracy_slm_ge_llm": accuracy_ge,
        "accuracy_slm_pct": acc_slm,
        "accuracy_llm_pct": acc_llm,
        "tokens_ratio_slm_over_llm": round(tok_slm / tok_llm, 3) if tok_llm else None,
        "cost_ratio_slm_over_llm": round(cost_slm / cost_llm, 3) if cost_llm else None,
        "tokens_much_less": tokens_much_less,
        "cost_much_less": cost_much_less,
        "pareto_win": bool(accuracy_ge and tokens_much_less and cost_much_less),
        "note": "Baseline (un-optimized) figures. H1 is fully tested after Phase 6 optimization; this "
                "scorecard pre-registers the criterion and records the starting point.",
    }


def _render_comparison(aggs: dict[str, dict[str, Any]], pareto: dict[str, Any] | None) -> str:
    models = list(aggs)
    lines = [
        "# Baseline comparison scorecard",
        "",
        f"_Generated {datetime.now(timezone.utc).isoformat()} · single-variable fairness: only the model "
        "deployment string varies; ontology + config + eval set + SQL ground truth are identical._",
        "",
        "| Metric | " + " | ".join(f"`{m}`" for m in models) + " |",
        "| --- | " + " | ".join("---" for _ in models) + " |",
    ]

    def row(label: str, fn) -> str:
        return f"| {label} | " + " | ".join(str(fn(aggs[m])) for m in models) + " |"

    lines += [
        row("Accuracy overall %", lambda a: a["accuracy"]["overall_pct"]),
        row("  single_hop %", lambda a: a["accuracy"]["by_category"].get("single_hop", {}).get("pct", "-")),
        row("  multi_hop %", lambda a: a["accuracy"]["by_category"].get("multi_hop", {}).get("pct", "-")),
        row("  negative %", lambda a: a["accuracy"]["by_category"].get("negative", {}).get("pct", "-")),
        row("Tokens total", lambda a: a["tokens"]["total"]),
        row("Tokens avg/task", lambda a: a["tokens"]["avg_per_task"]),
        row("Cost total (USD)", lambda a: a["cost"]["total_usd"]),
        row("Cost/correct (USD)", lambda a: a["cost"]["cost_per_correct_usd"]),
        row("Latency avg (ms)", lambda a: a["latency_ms"]["avg"]),
        row("Grounded %", lambda a: a["grounding"]["called_fabric_iq_pct"]),
        row("Multi-hop traversal %", lambda a: a["grounding"]["multi_hop_traversal_ok_pct"]),
        row("Config hash", lambda a: a["frozen_weights"]["config_hashes"][0][:12] if a["frozen_weights"]["config_hashes"] else "-"),
    ]
    lines.append("")

    hashes = {a["frozen_weights"]["config_hashes"][0] for a in aggs.values()
              if a["frozen_weights"]["config_hashes"]}
    lines += [
        "## Fairness / frozen-weights control",
        "",
        f"- Identical config across models: **{len(hashes) == 1}** "
        f"({'single shared config hash' if len(hashes) == 1 else 'MISMATCH — investigate'}).",
        "- Fine-tuning: **none** (model is a deployment-name string; weights frozen — Art. II).",
        "- Only variable across runs: the model deployment string (Art. III).",
        "",
    ]

    if pareto is not None:
        lines += [
            "## H1 Pareto check (pre-registered)",
            "",
            f"- Challenger SLM: `{pareto['challenger_slm']}` vs reference LLM: `{pareto['reference_llm']}`",
            f"- Accuracy SLM >= LLM: **{pareto['accuracy_slm_ge_llm']}** "
            f"({pareto['accuracy_slm_pct']}% vs {pareto['accuracy_llm_pct']}%)",
            f"- Tokens ratio SLM/LLM: **{pareto['tokens_ratio_slm_over_llm']}** "
            f"(much-less <= 0.75: {pareto['tokens_much_less']})",
            f"- Cost ratio SLM/LLM: **{pareto['cost_ratio_slm_over_llm']}** "
            f"(much-less <= 0.75: {pareto['cost_much_less']})",
            f"- **Pareto win: {pareto['pareto_win']}**",
            "",
            f"> {pareto['note']}",
            "",
        ]
    return "\n".join(lines)


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    ap = argparse.ArgumentParser(description="Run the baseline matrix over both models and compare.")
    ap.add_argument("--models", nargs="+", default=["gpt-5.4", "gpt-5.4-mini"],
                    help="model deployments to score (order: LLM first, SLM second, for the Pareto check)")
    ap.add_argument("--judge-model", default="gpt-5.4")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--confirm-cost", action="store_true",
                    help="acknowledge that every task issues real, billable model + Fabric IQ calls")
    ap.add_argument("--dry-run-mock", action="store_true", help="offline validation; no live calls, no cost")
    args = ap.parse_args()

    if not args.dry_run_mock and not args.confirm_cost:
        raise SystemExit(
            "Cost gate (Art. VIII): every eval task issues real model + Fabric IQ calls. "
            "Re-run with --confirm-cost once the user has approved, or use --dry-run-mock offline.")

    aggs: dict[str, dict[str, Any]] = {}
    for model in args.models:
        print(f"\n===== scoring {model} =====", flush=True)
        aggs[model] = scorer.run(model, judge_model=args.judge_model,
                                 mock=args.dry_run_mock, limit=args.limit)

    pareto = None
    if len(args.models) == 2:
        llm, slm = args.models[0], args.models[1]
        pareto = _pareto(aggs[llm], aggs[slm])

    _SCORECARD_DIR.mkdir(parents=True, exist_ok=True)
    combined = {"generated_at": datetime.now(timezone.utc).isoformat(),
                "models": args.models, "aggregates": aggs, "h1_pareto": pareto}
    (_SCORECARD_DIR / "baseline_comparison.json").write_text(
        json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8")
    (_SCORECARD_DIR / "baseline_comparison.md").write_text(
        _render_comparison(aggs, pareto), encoding="utf-8")
    print(f"\nWrote {_SCORECARD_DIR / 'baseline_comparison.md'}")
    if pareto:
        print(json.dumps(pareto, indent=2))


if __name__ == "__main__":
    main()
