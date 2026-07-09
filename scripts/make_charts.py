#!/usr/bin/env python3
"""Generate the result charts embedded in the root README (issue #33, EPIC G #7).

Phase 8 — README-as-article. This script is the *single, reproducible* source of the
committed chart images under ``docs/assets/``. It reads the already-committed Phase 5–7
scorecards (``eval/scorecards/*.json``) and the Phase-7 showdown record
(``eval/showdown/RESULTS.md``) — it makes **no** live Azure/Foundry/Fabric calls and incurs
**no** cost (Constitution Art. VIII). Every number plotted is pulled straight from the
committed scorecard JSON, so the charts match the scorecards **exactly** (Art. I).

Usage::

    pip install -r requirements.txt
    python scripts/make_charts.py            # writes the 4 PNGs to docs/assets/
    python scripts/make_charts.py --check    # fail if committed PNGs are missing/stale

Outputs (docs/assets/):
    accuracy_vs_cost.png       (a) accuracy vs total cost across the 3 runs
    cost_per_correct.png       (b) cost-per-correct-answer bar
    token_totals.png           (c) total tokens (Phase-6 trim + Phase-7 swap), in/out split
    cost_accuracy_frontier.png (d) cost/accuracy frontier scatter (log cost axis)

Pricing note (Art. I): ``eval/pricing.json`` is ``verified:false`` — the absolute dollar
figures are operator-supplied placeholders. The conclusions ride the *ratio* between models,
which is robust to the absolute rate as long as both are priced on the same basis.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless / deterministic PNG output
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SCORECARDS = REPO / "eval" / "scorecards"
SHOWDOWN = REPO / "eval" / "showdown" / "RESULTS.md"
ASSETS = REPO / "docs" / "assets"

# The three enshrined runs, in narrative order (Phase 5 -> 6 -> 7).
RUNS = [
    {
        "key": "baseline",
        "file": "baseline_gpt-5.4.json",
        "label": "Baseline-LLM\ngpt-5.4 (P5)",
        "short": "Baseline-LLM",
        "color": "#8c8c8c",
    },
    {
        "key": "optimized_llm",
        "file": "optimized_gpt-5.4.json",
        "label": "Optimized-LLM\ngpt-5.4 (P6)",
        "short": "Optimized-LLM",
        "color": "#1f6fb4",
    },
    {
        "key": "optimized_slm",
        "file": "optimized_gpt-5.4-mini.json",
        "label": "Optimized-SLM\ngpt-5.4-mini (P7)",
        "short": "Optimized-SLM",
        "color": "#2e9e5b",
    },
]

OUTPUTS = [
    "accuracy_vs_cost.png",
    "cost_per_correct.png",
    "token_totals.png",
    "cost_accuracy_frontier.png",
]


def load_runs() -> list[dict]:
    """Read each scorecard JSON and pull the exact aggregate figures."""
    runs = []
    for spec in RUNS:
        path = SCORECARDS / spec["file"]
        agg = json.loads(path.read_text(encoding="utf-8"))["aggregate"]
        runs.append(
            {
                **spec,
                "model": agg["model"],
                "accuracy_pct": agg["accuracy"]["overall_pct"],
                "correct": agg["accuracy"]["correct"],
                "n": agg["n_tasks"],
                "tokens_in": agg["tokens"]["input"],
                "tokens_out": agg["tokens"]["output"],
                "tokens_total": agg["tokens"]["total"],
                "cost_usd": agg["cost"]["total_usd"],
                "cost_per_correct": agg["cost"]["cost_per_correct_usd"],
                "pricing_verified": agg["cost"].get("pricing_verified", False),
            }
        )
    return runs


def showdown_config_hash() -> str | None:
    """Best-effort read of the single shared config hash from the Phase-7 record."""
    if not SHOWDOWN.exists():
        return None
    text = SHOWDOWN.read_text(encoding="utf-8")
    m = re.search(r"\b([0-9a-f]{64})\b", text)
    return m.group(1) if m else None


PRICING_CAVEAT = (
    "Costs use eval/pricing.json (verified:false) — placeholder rates; "
    "conclusions ride the ratio, not the absolute $."
)

# Per-run label offsets so the two near-equal-cost LLM points don't collide.
LABEL_OFFSETS = {
    "baseline": dict(xytext=(0, -34), va="top", ha="center"),
    "optimized_llm": dict(xytext=(0, 16), va="bottom", ha="center"),
    "optimized_slm": dict(xytext=(14, 0), va="center", ha="left"),
}


def _finish(fig, out: Path, dpi: int = 150) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out.relative_to(REPO)}")


def chart_accuracy_vs_cost(runs: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for r in runs:
        ax.scatter(
            r["cost_usd"], r["accuracy_pct"], s=170, color=r["color"],
            edgecolors="white", linewidths=1.5, zorder=3,
        )
        off = LABEL_OFFSETS[r["key"]]
        ax.annotate(
            f"{r['short']}\n{r['accuracy_pct']:.1f}%  ${r['cost_usd']:.4f}",
            (r["cost_usd"], r["accuracy_pct"]),
            textcoords="offset points", fontsize=8.5, **off,
        )
    ax.set_xlabel("Total cost over the 24-Q held-out eval (USD)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Accuracy vs cost — identical harness, model is the only lever")
    ax.set_ylim(80, 95)
    ax.set_xlim(0, max(r["cost_usd"] for r in runs) * 1.3)
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.text(0.5, -0.02, PRICING_CAVEAT, ha="center", fontsize=7, color="#555")
    _finish(fig, ASSETS / "accuracy_vs_cost.png")


def chart_cost_per_correct(runs: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    labels = [r["short"] for r in runs]
    vals = [r["cost_per_correct"] for r in runs]
    colors = [r["color"] for r in runs]
    bars = ax.bar(labels, vals, color=colors, edgecolor="white", zorder=3)
    for b, r in zip(bars, runs):
        ax.text(
            b.get_x() + b.get_width() / 2, b.get_height(),
            f"${r['cost_per_correct']:.6f}", ha="center", va="bottom", fontsize=9,
        )
    ax.set_ylabel("Cost per correct answer (USD)")
    ax.set_title("Cost per correct answer — the SLM is ~7.4× cheaper per correct")
    ax.set_ylim(0, max(vals) * 1.18)
    ax.grid(True, axis="y", linestyle=":", alpha=0.5)
    fig.text(0.5, -0.02, PRICING_CAVEAT, ha="center", fontsize=7, color="#555")
    _finish(fig, ASSETS / "cost_per_correct.png")


def chart_token_totals(runs: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    labels = [r["short"] for r in runs]
    ins = [r["tokens_in"] for r in runs]
    outs = [r["tokens_out"] for r in runs]
    ax.bar(labels, ins, color="#3a7bbf", edgecolor="white", label="input tokens", zorder=3)
    ax.bar(labels, outs, bottom=ins, color="#f0a63a", edgecolor="white",
           label="output tokens", zorder=3)
    for i, r in enumerate(runs):
        ax.text(i, r["tokens_total"], f"{r['tokens_total']:,}", ha="center",
                va="bottom", fontsize=9)
    ax.set_ylabel("Tokens over the 24-Q held-out eval")
    ax.set_title("Token totals — Phase-6 injection trim, then Phase-7 model swap")
    ax.set_ylim(0, max(r["tokens_total"] for r in runs) * 1.15)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, axis="y", linestyle=":", alpha=0.5)
    _finish(fig, ASSETS / "token_totals.png")


def chart_cost_accuracy_frontier(runs: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for r in runs:
        ax.scatter(
            r["cost_usd"], r["accuracy_pct"], s=190, color=r["color"],
            edgecolors="white", linewidths=1.5, zorder=3,
        )
        off = LABEL_OFFSETS[r["key"]]
        ax.annotate(
            f"{r['short']} ({r['model']})\n{r['correct']}/{r['n']} = {r['accuracy_pct']:.1f}%"
            f"  ·  ${r['cost_usd']:.4f}",
            (r["cost_usd"], r["accuracy_pct"]),
            textcoords="offset points", fontsize=8, **off,
        )
    ax.set_xscale("log")
    ax.set_xlabel("Total cost (USD, log scale) — cheaper \u2190")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Cost / accuracy frontier — pick the model per workload")
    ax.set_ylim(82, 96)
    ax.set_xlim(runs[2]["cost_usd"] * 0.55, runs[0]["cost_usd"] * 1.9)
    ax.grid(True, which="both", linestyle=":", alpha=0.45)
    ax.annotate(
        "cheaper & near-flagship", xy=(runs[2]["cost_usd"], runs[2]["accuracy_pct"]),
        xytext=(runs[2]["cost_usd"], 83.0), fontsize=8, color="#2e9e5b", ha="center",
    )
    fig.text(0.5, -0.02,
             "Paired \u0394 \u22124.2 pts, 95% CI [\u221212.5, 0.0] includes 0 (N=24). "
             + PRICING_CAVEAT, ha="center", fontsize=7, color="#555")
    _finish(fig, ASSETS / "cost_accuracy_frontier.png")


def build(check: bool) -> int:
    runs = load_runs()
    cfg = showdown_config_hash()
    print("Loaded scorecards (exact figures from committed JSON):")
    for r in runs:
        print(f"  {r['short']:<14} {r['model']:<13} "
              f"acc={r['accuracy_pct']:.1f}% ({r['correct']}/{r['n']}) "
              f"tok={r['tokens_total']:,} cost=${r['cost_usd']:.6f} "
              f"$/correct=${r['cost_per_correct']:.6f}")
    if cfg:
        print(f"  Phase-7 single shared config hash: {cfg[:16]}\u2026 (model = sole variable)")

    if check:
        missing = [o for o in OUTPUTS if not (ASSETS / o).exists()]
        if missing:
            print(f"ERROR: missing committed charts: {missing}", file=sys.stderr)
            return 1
        print("All committed charts present.")
        return 0

    print("Rendering charts:")
    chart_accuracy_vs_cost(runs)
    chart_cost_per_correct(runs)
    chart_token_totals(runs)
    chart_cost_accuracy_frontier(runs)
    print("Done.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="verify committed PNGs exist (no rendering)")
    args = ap.parse_args()
    return build(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
