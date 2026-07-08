#!/usr/bin/env python3
"""Deterministic SQL ground-truth generator for the OPTIMIZATION TRAIN SET — Phase 6 (issue #29, EPIC E #5).

Sibling of ``eval/ground_truth.py``: it computes the canonical expected answer for every question in
``eval/optimization_trainset.jsonl`` by running its committed ``sql`` over the SAME four synthetic CSVs in
``data/`` with DuckDB, through the SAME oracle primitives (``_connect`` / ``_resolve`` / ``_data_fingerprint``)
imported from ``ground_truth.py``. This leaves ``ground_truth.py`` and the held-out ``ground_truth.json``
**byte-identical** (single-variable integrity, Constitution Art. I / issue #29): the optimizer trains on a
DISJOINT question set over the UNCHANGED data, never on the 24-Q held-out eval.

Writes ``eval/optimization_ground_truth.json`` (committed). Idempotent; ``--check`` fails if the committed file
is stale. Also asserts the trainset is **disjoint** (no shared question text) from ``eval/dataset.jsonl`` and
that the four tables carry the Phase-4 verified row counts (20 / 50 / 200 / 80) so every answer is computed
over the real committed tables.

Usage:
  python eval/trainset_ground_truth.py            # (re)generate eval/optimization_ground_truth.json
  python eval/trainset_ground_truth.py --check    # verify the committed file is up to date (CI-style)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import ground_truth as gt  # noqa: E402 — reuse the EXACT held-out oracle; do not modify it.

_ROOT = _HERE.parent
_TRAINSET = _ROOT / "eval" / "optimization_trainset.jsonl"
_EVAL = _ROOT / "eval" / "dataset.jsonl"
_OUT = _ROOT / "eval" / "optimization_ground_truth.json"

# Phase-4 verified committed row counts (byte-identical CSV<->Delta). Guards against silent data drift.
_EXPECTED_COUNTS = {
    "sites": 20,
    "algae_species": 50,
    "water_quality_measurements": 200,
    "treatment_records": 80,
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _assert_counts(con: "gt.duckdb.DuckDBPyConnection") -> None:
    for table, expected in _EXPECTED_COUNTS.items():
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if n != expected:
            raise SystemExit(
                f"data drift: table {table} has {n} rows, expected {expected} (Phase-4 verified). "
                "The trainset must query the EXISTING committed data only — no rows may be added or mutated."
            )


def _assert_disjoint(trainset: list[dict[str, Any]]) -> None:
    eval_qs = {r["question"].strip().lower() for r in _read_jsonl(_EVAL)}
    overlap = sorted(r["id"] for r in trainset if r["question"].strip().lower() in eval_qs)
    if overlap:
        raise SystemExit(
            f"trainset is NOT disjoint from the held-out eval: {overlap} share a question with "
            "eval/dataset.jsonl. Disjoint means different questions over the same data."
        )


def build() -> dict[str, Any]:
    con = gt._connect()
    _assert_counts(con)
    records = _read_jsonl(_TRAINSET)
    _assert_disjoint(records)

    truth: dict[str, Any] = {}
    split_counts: dict[str, int] = {}
    for rec in records:
        resolved = gt._resolve(con, rec)
        resolved.update(
            {
                "category": rec["category"],
                "split": rec.get("split"),
                "question": rec["question"],
                "expected_traversal": rec.get("expected_traversal", []),
                "sql": rec.get("sql"),
            }
        )
        truth[rec["id"]] = resolved
        split_counts[rec.get("split", "unspecified")] = split_counts.get(rec.get("split", "unspecified"), 0) + 1

    return {
        "_meta": {
            "source": "eval/optimization_trainset.jsonl over data/*.csv via DuckDB (same oracle as ground_truth.py)",
            "data_fingerprint_sha256": gt._data_fingerprint(),
            "n_questions": len(records),
            "split_counts": split_counts,
            "disjoint_from": "eval/dataset.jsonl (verified: no shared question text)",
            "note": "TRAIN/DEV split for the Phase-6 optimizer; the 24-Q eval stays the pure held-out test.",
        },
        "ground_truth": truth,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate/verify the optimization-trainset ground truth.")
    parser.add_argument("--check", action="store_true",
                        help="fail if committed optimization_ground_truth.json is stale")
    args = parser.parse_args()

    payload = build()
    serialized = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)

    if args.check:
        current = _OUT.read_text(encoding="utf-8") if _OUT.exists() else ""
        if current.strip() != serialized.strip():
            raise SystemExit("optimization_ground_truth.json is stale — re-run `python eval/trainset_ground_truth.py`.")
        print("optimization_ground_truth.json is up to date.")
        return

    _OUT.write_text(serialized + "\n", encoding="utf-8")
    m = payload["_meta"]
    print(f"Wrote {_OUT.relative_to(_ROOT)} ({m['n_questions']} questions; split {m['split_counts']}).")


if __name__ == "__main__":
    main()
