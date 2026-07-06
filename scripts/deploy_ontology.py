#!/usr/bin/env python3
"""Deploy the ontology/ parts to a Fabric IQ ontology item via updateDefinition.

Phase 3 deliverable (issue #20, EPIC C #3). **AUTHORING ONLY — do not run against
live Fabric until Phase 4** (Constitution Art. VIII human-in-the-loop gate).

What it does (pattern adapted from `ajananth/research-iq` `scripts/setup_ontology.py`
— **pattern only**; none of that repo's tenant/workspace/item GUIDs are copied):
  1. Walk the source-controlled ``ontology/`` tree (see ``ontology/README.md``).
  2. Substitute the ``${FABRIC_WORKSPACE_ID}`` / ``${FABRIC_LAKEHOUSE_ID}`` placeholders
     in the data-binding + contextualization parts from the environment (Art. VI — no
     GUIDs or secrets are committed).
  3. Base64-encode each part and POST them as one ``parts`` array to
     ``items/{ontology_item_id}/updateDefinition?beta=true``, then poll the async op.

Configuration (env or CLI):
  FABRIC_WORKSPACE_ID     (required)  workspace GUID hosting the ontology + Lakehouse
  FABRIC_LAKEHOUSE_ID     (required)  managed-Delta Lakehouse the bindings target
  FABRIC_ONTOLOGY_ITEM_ID (required)  the ontology (preview) item GUID to update

Usage (Phase 4):
  python scripts/deploy_ontology.py \
      --workspace-id <ws> --lakehouse-id <lh> --ontology-item-id <ont> [--dry-run]

``--dry-run`` validates + assembles the parts and prints a summary **without** calling
Fabric — safe to use for local checks.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import time
from pathlib import Path

_FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
_FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"

_ONTOLOGY_DIR = Path(__file__).resolve().parent.parent / "ontology"


def _iter_part_files(root: Path):
    """Yield (relative_posix_path, raw_text) for every .json part under ontology/."""
    for path in sorted(root.rglob("*.json")):
        rel = path.relative_to(root).as_posix()
        yield rel, path.read_text(encoding="utf-8")


def build_parts(root: Path, workspace_id: str, lakehouse_id: str) -> list[dict]:
    """Assemble the updateDefinition parts array from the ontology/ tree."""
    subs = {"${FABRIC_WORKSPACE_ID}": workspace_id, "${FABRIC_LAKEHOUSE_ID}": lakehouse_id}
    parts = []
    for rel, text in _iter_part_files(root):
        for placeholder, value in subs.items():
            text = text.replace(placeholder, value)
        # Validate JSON and re-serialise compactly before encoding.
        obj = json.loads(text)
        payload = base64.b64encode(
            json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).decode("ascii")
        parts.append({"path": rel, "payload": payload, "payloadType": "InlineBase64"})
    if not any(p["path"] == "definition.json" for p in parts):
        raise RuntimeError("ontology/definition.json (root part) is missing")
    return parts


def _poll_operation(operation_url: str, headers: dict, timeout_s: int = 300) -> None:
    import requests

    deadline = time.time() + timeout_s
    wait = 2
    while time.time() < deadline:
        resp = requests.get(operation_url, headers=headers, timeout=30)
        status = resp.json().get("status") if resp.content else None
        if status in ("Succeeded", "Completed"):
            return
        if status == "Failed":
            raise RuntimeError(f"updateDefinition operation failed: {resp.text[:300]}")
        time.sleep(wait)
        wait = min(wait * 2, 15)
    raise TimeoutError("updateDefinition operation did not complete in time")


def deploy(parts: list[dict], workspace_id: str, ontology_item_id: str, token: str) -> None:
    import requests

    url = (
        f"{_FABRIC_API_BASE}/workspaces/{workspace_id}"
        f"/items/{ontology_item_id}/updateDefinition?beta=true"
    )
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"definition": {"parts": parts}}
    resp = requests.post(url, headers=headers, json=body, timeout=120)
    if resp.status_code == 202 and "Location" in resp.headers:
        _poll_operation(resp.headers["Location"], headers)
    elif resp.status_code not in (200, 201):
        raise RuntimeError(f"updateDefinition failed: HTTP {resp.status_code} — {resp.text[:300]}")
    print(f"Ontology definition applied to item {ontology_item_id}.")


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-id", default=os.environ.get("FABRIC_WORKSPACE_ID"))
    parser.add_argument("--lakehouse-id", default=os.environ.get("FABRIC_LAKEHOUSE_ID"))
    parser.add_argument("--ontology-item-id", default=os.environ.get("FABRIC_ONTOLOGY_ITEM_ID"))
    parser.add_argument("--ontology-dir", default=str(_ONTOLOGY_DIR))
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Assemble + validate parts and print a summary without calling Fabric.",
    )
    args = parser.parse_args()

    root = Path(args.ontology_dir)
    ws = args.workspace_id or "${FABRIC_WORKSPACE_ID}"
    lh = args.lakehouse_id or "${FABRIC_LAKEHOUSE_ID}"

    parts = build_parts(root, ws, lh)
    print(f"Assembled {len(parts)} parts from {root}:")
    for p in parts:
        print(f"  - {p['path']}")

    if args.dry_run:
        unresolved = [p["path"] for p in parts if "${FABRIC_" in base64.b64decode(p["payload"]).decode("utf-8")]
        if unresolved:
            print(f"NOTE: placeholders still unresolved in: {unresolved} (pass real IDs to deploy).")
        print("Dry run only — nothing sent to Fabric.")
        return

    missing = [
        n for n, v in (
            ("--workspace-id/FABRIC_WORKSPACE_ID", args.workspace_id),
            ("--lakehouse-id/FABRIC_LAKEHOUSE_ID", args.lakehouse_id),
            ("--ontology-item-id/FABRIC_ONTOLOGY_ITEM_ID", args.ontology_item_id),
        ) if not v
    ]
    if missing:
        parser.error("missing required config for deploy: " + ", ".join(missing))

    from azure.identity import DefaultAzureCredential

    token = DefaultAzureCredential().get_token(_FABRIC_SCOPE).token
    deploy(parts, args.workspace_id, args.ontology_item_id, token)


if __name__ == "__main__":
    main()
