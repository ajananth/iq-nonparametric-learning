#!/usr/bin/env python3
"""Flat load: vendored synthetic CSVs -> managed Delta tables in a Fabric Lakehouse.

Phase 3 deliverable (issue #20, EPIC C #3). **AUTHORING ONLY — do not run against
live Fabric until Phase 4** (Constitution Art. VIII human-in-the-loop gate).

What it does (adapted from `ajananth/water-quality-assistant` data-seeder — pattern
only, no secrets/GUIDs copied):
  1. Reuse an existing Fabric Lakehouse (``--lakehouse-id`` / ``FABRIC_LAKEHOUSE_ID``)
     or create one via the Fabric REST API.
  2. For each of the 4 CSVs in ``data/``, write it **directly** as a **managed Delta
     table** under ``Tables/<name>`` using ``deltalake`` (delta-rs) + a
     ``DefaultAzureCredential`` bearer token.

Deliberately **flat**: no medallion (Bronze/Silver/Gold), no transforms — one CSV ->
one managed Delta table of the same stem name. Managed tables (no OneLake security, no
column mapping) are required so the Fabric IQ ontology can bind to them
(``docs/verified-capabilities.md`` §1a).

Configuration (env or CLI; **never** hardcode secrets — Constitution Art. VI):
  FABRIC_WORKSPACE_ID   (required)  target workspace GUID
  FABRIC_LAKEHOUSE_ID   (optional)  reuse this Lakehouse; omit to create a new one

Usage (Phase 4):
  python scripts/load_lakehouse.py \
      --workspace-id <ws-guid> [--lakehouse-id <lh-guid>] [--data-dir data]
"""
from __future__ import annotations

import argparse
import os

_ONELAKE_HOST = "onelake.dfs.fabric.microsoft.com"
_FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
_FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
_STORAGE_SCOPE = "https://storage.azure.com/.default"

# CSV stem -> managed Delta table name (identical; flat load, no renaming).
_TABLES = [
    ("sites", "sites.csv"),
    ("algae_species", "algae_species.csv"),
    ("water_quality_measurements", "water_quality_measurements.csv"),
    ("treatment_records", "treatment_records.csv"),
]

_DEFAULT_LAKEHOUSE_NAME = "WaterIQ_Lakehouse"


def create_lakehouse(workspace_id: str, token: str, display_name: str) -> str:
    """Create a Fabric Lakehouse in *workspace_id*; return its item GUID."""
    import requests

    url = f"{_FABRIC_API_BASE}/workspaces/{workspace_id}/lakehouses"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "displayName": display_name,
        "description": "Flat synthetic water-quality dataset for the Fabric IQ demo (Phase 3/4).",
    }
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Failed to create Lakehouse: HTTP {resp.status_code} — {resp.text[:300]}"
        )
    data = resp.json()
    if "id" not in data:
        raise RuntimeError(f"Lakehouse created but response missing 'id': {resp.text[:300]}")
    return data["id"]


def upload_table(workspace_id: str, lakehouse_id: str, table_name: str, df, credential) -> None:
    """Write *df* as a managed Delta table under ``Tables/<table_name>``."""
    import pyarrow as pa
    from deltalake import write_deltalake

    table = pa.Table.from_pandas(df, preserve_index=False)
    table_uri = (
        f"abfss://{workspace_id}@{_ONELAKE_HOST}"
        f"/{lakehouse_id}/Tables/{table_name}"
    )
    # delta-rs needs a raw bearer token, not a credential object.
    token = credential.get_token(_STORAGE_SCOPE).token
    storage_options = {
        "bearer_token": token,
        "account_name": "onelake",
        "use_fabric_endpoint": "true",
    }
    write_deltalake(table_uri, table, storage_options=storage_options, mode="overwrite")


def main() -> None:
    import pandas as pd
    from azure.identity import DefaultAzureCredential
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-id", default=os.environ.get("FABRIC_WORKSPACE_ID"))
    parser.add_argument("--lakehouse-id", default=os.environ.get("FABRIC_LAKEHOUSE_ID"))
    parser.add_argument("--lakehouse-name", default=_DEFAULT_LAKEHOUSE_NAME)
    parser.add_argument(
        "--data-dir",
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"),
        help="Directory holding the 4 vendored CSVs (default: repo data/).",
    )
    args = parser.parse_args()

    if not args.workspace_id:
        parser.error("workspace id required (pass --workspace-id or set FABRIC_WORKSPACE_ID)")

    credential = DefaultAzureCredential()

    lakehouse_id = args.lakehouse_id
    if lakehouse_id:
        print(f"Using existing Lakehouse: {lakehouse_id}")
    else:
        fabric_token = credential.get_token(_FABRIC_SCOPE).token
        lakehouse_id = create_lakehouse(args.workspace_id, fabric_token, args.lakehouse_name)
        print(f"Lakehouse created: {lakehouse_id}")

    for table_name, csv_file in _TABLES:
        csv_path = os.path.join(args.data_dir, csv_file)
        print(f"Uploading managed Delta table '{table_name}' from {csv_file} ...")
        df = pd.read_csv(csv_path)
        upload_table(args.workspace_id, lakehouse_id, table_name, df, credential)
        print(f"  OK {table_name} ({len(df)} rows)")

    print(
        f"Flat load complete: {len(_TABLES)} managed Delta tables in Lakehouse "
        f"{lakehouse_id}. Set FABRIC_LAKEHOUSE_ID={lakehouse_id} for the ontology deploy."
    )


if __name__ == "__main__":
    main()
