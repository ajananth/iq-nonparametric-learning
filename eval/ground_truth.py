#!/usr/bin/env python3
"""Deterministic SQL ground-truth generator — Phase 5 (issue #24, EPIC D #4).

Computes the canonical expected answer for every question in ``eval/dataset.jsonl`` by running its
committed ``sql`` over the four synthetic CSVs in ``data/`` with DuckDB. Because those CSVs are vendored
verbatim and loaded FLAT (one managed Delta table each) into the live Lakehouse (Phase 4), the local
result is byte-identical to what the ontology is bound to — so ground truth is fully reproducible offline
by any third party (Art. V) and owes nothing to the model under test (Art. I: SQL is the primary oracle).

Writes ``eval/ground_truth.json`` (committed). Re-running is idempotent; ``--check`` fails if the committed
file is stale, which guards against silent drift.

Usage:
  python eval/ground_truth.py            # (re)generate eval/ground_truth.json
  python eval/ground_truth.py --check    # verify the committed file is up to date (CI-style)
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import duckdb

_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _ROOT / "data"
_DATASET = _ROOT / "eval" / "dataset.jsonl"
_OUT = _ROOT / "eval" / "ground_truth.json"
_TABLES = ["sites", "algae_species", "water_quality_measurements", "treatment_records"]


def _connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    for t in _TABLES:
        csv = (_DATA_DIR / f"{t}.csv").as_posix()
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_csv_auto('{csv}', header=true)")
    return con


def _canonical_scalar(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 2)
    if isinstance(value, bool):
        return value
    return value


def _resolve(con: duckdb.DuckDBPyConnection, rec: dict[str, Any]) -> dict[str, Any]:
    answer_type = rec["answer_type"]
    if answer_type == "refusal":
        return {"answer_type": "refusal", "answerable": False}

    rows = con.execute(rec["sql"]).fetchall()
    if answer_type == "scalar":
        value = _canonical_scalar(rows[0][0]) if rows and rows[0] else None
        return {"answer_type": "scalar", "value": value}
    if answer_type == "set":
        values = sorted(str(r[0]) for r in rows if r[0] is not None)
        return {"answer_type": "set", "values": values, "count": len(values)}
    raise ValueError(f"unknown answer_type: {answer_type}")


def _data_fingerprint() -> str:
    h = hashlib.sha256()
    for t in _TABLES:
        h.update((_DATA_DIR / f"{t}.csv").read_bytes())
    return h.hexdigest()


def build() -> dict[str, Any]:
    con = _connect()
    records = [json.loads(line) for line in _DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
    truth: dict[str, Any] = {}
    for rec in records:
        resolved = _resolve(con, rec)
        resolved.update(
            {
                "category": rec["category"],
                "question": rec["question"],
                "expected_traversal": rec.get("expected_traversal", []),
                "sql": rec.get("sql"),
            }
        )
        truth[rec["id"]] = resolved
    return {
        "_meta": {
            "source": "eval/dataset.jsonl over data/*.csv via DuckDB",
            "data_fingerprint_sha256": _data_fingerprint(),
            "n_questions": len(records),
        },
        "ground_truth": truth,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate/verify deterministic SQL ground truth.")
    parser.add_argument("--check", action="store_true", help="fail if committed ground_truth.json is stale")
    args = parser.parse_args()

    payload = build()
    serialized = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)

    if args.check:
        current = _OUT.read_text(encoding="utf-8") if _OUT.exists() else ""
        if current.strip() != serialized.strip():
            raise SystemExit("ground_truth.json is stale — re-run `python eval/ground_truth.py`.")
        print("ground_truth.json is up to date.")
        return

    _OUT.write_text(serialized + "\n", encoding="utf-8")
    n = payload["_meta"]["n_questions"]
    print(f"Wrote {_OUT.relative_to(_ROOT)} ({n} questions).")


if __name__ == "__main__":
    main()
