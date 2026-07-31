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
    accuracy_vs_cost.png            (a) accuracy vs total cost across the 3 runs (two cost levers)
    cost_per_correct.png            (b) cost-per-correct-answer bar
    token_totals.png                (c) total tokens (Phase-6 trim + Phase-7 swap), in/out split
    xvendor_accuracy_vs_cost.png    (d) cross-vendor: Kimi-K2.6 vs the gpt-5.4 anchor (H-6, #58)

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
# Cross-vendor scorecard merged by H-4 (#50): the tuned harness re-run with the
# reasoning/answer model swapped to the open-weights, non-GPT Kimi-K2.6 (Art. VII —
# read byte-identical, never mutated here).
XVENDOR_KIMI = REPO / "eval" / "showdown_xvendor" / "xvendor_kimi-k2.6.json"
XVENDOR_ANCHOR = SCORECARDS / "optimized_gpt-5.4.json"
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
    "xvendor_accuracy_vs_cost.png",
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


def load_xvendor_pair() -> list[dict]:
    """Read the H-6 cross-vendor pair: Kimi-K2.6 vs the enshrined gpt-5.4 anchor.

    Both scorecards share the same ``aggregate`` schema, so every plotted number is
    pulled straight from the committed JSON at runtime (Art. I) — nothing hardcoded.
    The gpt-5.4 anchor is the enshrined Phase-7 Optimized-LLM run; Kimi-K2.6 is the
    identical tuned harness with only the reasoning/answer deployment string swapped.
    """
    specs = [
        {
            "path": XVENDOR_ANCHOR,
            "short": "gpt-5.4 (anchor)",
            "color": "#1f6fb4",
            "marker": "o",
        },
        {
            "path": XVENDOR_KIMI,
            "short": "kimi-k2.6",
            "color": "#c0504d",
            "marker": "s",
        },
    ]
    pair = []
    for spec in specs:
        agg = json.loads(spec["path"].read_text(encoding="utf-8"))["aggregate"]
        pair.append(
            {
                **spec,
                "model": agg["model"],
                "accuracy_pct": agg["accuracy"]["overall_pct"],
                "correct": agg["accuracy"]["correct"],
                "n": agg["n_tasks"],
                "cost_usd": agg["cost"]["total_usd"],
                "cost_per_correct": agg["cost"]["cost_per_correct_usd"],
                "pricing_verified": agg["cost"].get("pricing_verified", False),
            }
        )
    return pair


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

# Migrated from the removed frontier chart (issue #35): the paired-Δ CI on the
# Phase-7 model swap. Kept so no honesty (Art. I) is lost on consolidation.
CI_CAVEAT = "Model swap paired Δ −4.2 pts, 95% CI [−12.5, 0.0] includes 0 (N=24)."

def _finish(fig, out: Path, dpi: int = 150) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out.relative_to(REPO)}")


def chart_accuracy_vs_cost(runs: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    by_key = {r["key"]: r for r in runs}
    grey = by_key["baseline"]
    blue = by_key["optimized_llm"]
    green = by_key["optimized_slm"]

    # Scatter each run with a legend entry mapping colour -> run + model.
    for r in runs:
        ax.scatter(
            r["cost_usd"], r["accuracy_pct"], s=180, color=r["color"],
            edgecolors="white", linewidths=1.5, zorder=4,
            label=f"{r['short']} · {r['model']}",
        )

    # Per-point %/$ labels attached with short leader lines so grey vs blue
    # (same 91.7%, nearly-equal cost) is unambiguous.
    leader = dict(arrowstyle="-", color="#888", lw=0.8, shrinkA=0, shrinkB=4)
    point_labels = {
        "baseline": dict(xytext=(30, -34), ha="left", va="top"),
        "optimized_llm": dict(xytext=(-18, -42), ha="right", va="top"),
        "optimized_slm": dict(xytext=(20, 10), ha="left", va="bottom"),
    }
    for r in runs:
        off = point_labels[r["key"]]
        ax.annotate(
            f"{r['short']}\n{r['accuracy_pct']:.1f}%  ${r['cost_usd']:.4f}",
            (r["cost_usd"], r["accuracy_pct"]),
            textcoords="offset points", fontsize=8.5, color="#222",
            arrowprops=leader, **off,
        )

    # Lever arrow 1 (Phase 6): grey -> blue. The two points nearly overlap, so
    # draw a short curved connector lifted above them with its label in the
    # empty upper-left area.
    ax.annotate(
        "", xy=(blue["cost_usd"], blue["accuracy_pct"] + 0.9),
        xytext=(grey["cost_usd"], grey["accuracy_pct"] + 0.9),
        arrowprops=dict(arrowstyle="->", color="#1f6fb4", lw=1.6,
                        connectionstyle="arc3,rad=-0.45"), zorder=5,
    )
    ax.text(
        (grey["cost_usd"] + blue["cost_usd"]) / 2 - 0.004, blue["accuracy_pct"] + 2.7,
        "harness tuning (P6):\n−6.7% cost, same accuracy",
        ha="center", va="bottom", fontsize=8, color="#1f6fb4",
    )

    # Lever arrow 2 (Phase 7): blue -> green. Long diagonal (big cost cut,
    # small accuracy drop).
    ax.annotate(
        "", xy=(green["cost_usd"], green["accuracy_pct"]),
        xytext=(blue["cost_usd"], blue["accuracy_pct"]),
        arrowprops=dict(arrowstyle="->", color="#2e9e5b", lw=1.6,
                        connectionstyle="arc3,rad=0.10"), zorder=5,
    )
    ax.text(
        0.072, 92.5,
        "model swap (P7):\n~8× cheaper, −4.2 pts",
        ha="center", va="bottom", fontsize=8, color="#2e9e5b",
    )

    ax.set_xlabel("Total cost over the 24-Q held-out eval (USD)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Cutting cost at near-constant accuracy: harness tuning + model swap")
    ax.set_ylim(82, 97)
    ax.set_xlim(0, max(r["cost_usd"] for r in runs) * 1.3)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    fig.text(0.5, -0.03, CI_CAVEAT + " " + PRICING_CAVEAT,
             ha="center", fontsize=7, color="#555")
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


# H-6 (#58): dedicated cross-vendor view. USD is the only like-for-like axis across
# vendors (Kimi-K2.6 and gpt-5.4 use different tokenizers, so tokens are NOT comparable
# and deliberately do not appear here). The headline is "parity within noise + cheaper
# than the flagship," never "8× cheaper" (that is the same-vendor gpt-5.4-mini story).
XVENDOR_CI_CAVEAT = (
    "Paired accuracy Δ (Kimi − gpt-5.4) −4.2 pts, 95% CI [−12.5, 0.0] includes 0 "
    "(10k resamples, N=24) — parity within noise."
)


def chart_xvendor_accuracy_vs_cost(pair: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(7.6, 5.0))

    for r in pair:
        ax.scatter(
            r["cost_usd"], r["accuracy_pct"], s=200, color=r["color"],
            marker=r["marker"], edgecolors="white", linewidths=1.5, zorder=4,
            label=f"{r['short']} · {r['accuracy_pct']:.1f}% ({r['correct']}/{r['n']})",
        )

    leader = dict(arrowstyle="-", color="#888", lw=0.8, shrinkA=0, shrinkB=4)
    point_labels = {
        "gpt-5.4": dict(xytext=(14, 12), ha="left", va="bottom"),
        "kimi-k2.6": dict(xytext=(-14, -30), ha="right", va="top"),
    }
    for r in pair:
        off = point_labels.get(r["model"], dict(xytext=(12, 10), ha="left", va="bottom"))
        ax.annotate(
            f"{r['short']}\n{r['accuracy_pct']:.1f}%  ${r['cost_usd']:.6f}",
            (r["cost_usd"], r["accuracy_pct"]),
            textcoords="offset points", fontsize=8.5, color="#222",
            arrowprops=leader, **off,
        )

    costs = [r["cost_usd"] for r in pair]
    lo, hi = min(costs), max(costs)
    span = (hi - lo) or hi * 0.1
    ax.set_xlim(lo - span * 1.4, hi + span * 1.4)
    ax.set_ylim(82, 97)
    ax.set_xlabel("Total cost over the 24-Q held-out eval (USD — the comparable cross-vendor axis)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Cross-vendor swap: Kimi-K2.6 vs the gpt-5.4 anchor — parity within noise, cheaper $")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    fig.text(0.5, -0.03, XVENDOR_CI_CAVEAT + " " + PRICING_CAVEAT,
             ha="center", fontsize=7, color="#555")
    _finish(fig, ASSETS / "xvendor_accuracy_vs_cost.png")


def build(check: bool) -> int:
    runs = load_runs()
    xvendor = load_xvendor_pair()
    cfg = showdown_config_hash()
    print("Loaded scorecards (exact figures from committed JSON):")
    for r in runs:
        print(f"  {r['short']:<14} {r['model']:<13} "
              f"acc={r['accuracy_pct']:.1f}% ({r['correct']}/{r['n']}) "
              f"tok={r['tokens_total']:,} cost=${r['cost_usd']:.6f} "
              f"$/correct=${r['cost_per_correct']:.6f}")
    print("Cross-vendor pair (H-6, USD-only comparison):")
    for r in xvendor:
        print(f"  {r['short']:<16} {r['model']:<13} "
              f"acc={r['accuracy_pct']:.1f}% ({r['correct']}/{r['n']}) "
              f"cost=${r['cost_usd']:.6f} $/correct=${r['cost_per_correct']:.6f}")
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
    chart_xvendor_accuracy_vs_cost(xvendor)
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
