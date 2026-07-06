#!/usr/bin/env python3
"""Project a deployed Fabric IQ ontology into its companion **GraphModel** item.

Phase 4 deliverable (issue #22, EPIC C #3). Empirical finding during the live
deploy: calling ``updateDefinition`` on the ontology item populates entity types,
relationship types, and data bindings, but does **not** auto-build the companion
GraphModel item (its ``graphType`` / ``graphDefinition`` / ``dataSources`` stay
empty). Consequently the graph can't be refreshed (``RefreshGraph`` returns
``GraphNotRefreshable``) and NL2Ontology/GQL queries fail until the graph is built.

The Fabric portal builds this graph when you press **Save** in the graph model
editor. This script performs the same projection **programmatically** so the whole
Phase-4 pipeline needs no portal step. The projected shape mirrors a verified,
working graph model (the ``ajananth/research-iq`` ontology graph — pattern only, no
GUIDs copied): node types per entity, edge types per relationship, one Delta-table
data source per bound Lakehouse table, and node/edge table mappings.

What it does:
  1. Parse the ``ontology/`` tree (entity types, data bindings, relationship types,
     contextualizations) — the same source of truth ``deploy_ontology.py`` uses.
  2. Resolve the companion GraphModel item (``<ontology>_graph_<id>``) via List items,
     or accept ``--graph-item-id``.
  3. Build the four graph definition parts and POST them to
     ``items/{graphId}/updateDefinition`` (polls the LRO).
  4. Optionally (``--refresh``) trigger the ``RefreshGraph`` job to ingest data.

Graph property types (verified against live built graphs 2026-07-06): STRING, INT,
FLOAT, BOOLEAN. Ontology ``valueType`` maps: String->STRING, Double->FLOAT,
BigInt->INT, Boolean->BOOLEAN, DateTime->STRING (ISO text; no DATETIME token observed).

Configuration (env or CLI; **never** hardcode secrets — Constitution Art. VI):
  FABRIC_WORKSPACE_ID     (required)  workspace GUID
  FABRIC_LAKEHOUSE_ID     (required)  Lakehouse holding the bound managed Delta tables
  FABRIC_ONTOLOGY_ITEM_ID (required)  the deployed ontology (preview) item GUID

Usage (Phase 4, after deploy_ontology.py):
  python scripts/build_graph_model.py \
      --workspace-id <ws> --lakehouse-id <lh> --ontology-item-id <ont> --refresh
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import time
import uuid
from pathlib import Path

_FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
_FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
_ONELAKE_GRAPH_HOST = "onelake.pbidedicated.windows.net"

_ONTOLOGY_DIR = Path(__file__).resolve().parent.parent / "ontology"

# Ontology valueType -> graph property type (verified against live graphs 2026-07-06).
_TYPE_MAP = {"String": "STRING", "Double": "FLOAT", "BigInt": "INT",
             "Boolean": "BOOLEAN", "DateTime": "STRING"}

_GT_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/graphInstance/definition/graphType/1.0.0/schema.json"
_DS_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/graphInstance/definition/dataSources/1.0.0/schema.json"
_GD_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/graphInstance/definition/graphDefinition/1.0.0/schema.json"
_ST_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/graphInstance/definition/stylingConfiguration/1.0.0/schema.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_ontology(root: Path) -> tuple[list[dict], list[dict]]:
    """Return (entities, relationships) parsed from the ontology/ tree."""
    entities = []
    for et_def in sorted(root.glob("EntityTypes/*/definition.json")):
        d = _load_json(et_def)
        prop_by_id = {p["id"]: p for p in d["properties"]}
        key_prop = prop_by_id[d["entityIdParts"][0]]
        binding = next(iter((et_def.parent / "DataBindings").glob("*.json")), None)
        cfg = _load_json(binding)["dataBindingConfiguration"]
        entities.append({
            "et_id": d["id"],
            "name": d["name"],
            "key_col": key_prop["name"],
            "table": cfg["sourceTableProperties"]["sourceTableName"],
            "properties": [{"name": p["name"], "type": _TYPE_MAP.get(p["valueType"], "STRING")}
                           for p in d["properties"]],
        })

    relationships = []
    for rt_def in sorted(root.glob("RelationshipTypes/*/definition.json")):
        d = _load_json(rt_def)
        ctx = _load_json(next(iter((rt_def.parent / "Contextualizations").glob("*.json"))))
        relationships.append({
            "rt_id": d["id"],
            "name": d["name"],
            "source_et": d["source"]["entityTypeId"],
            "target_et": d["target"]["entityTypeId"],
            "table": ctx["dataBindingTable"]["sourceTableName"],
            "source_col": ctx["sourceKeyRefBindings"][0]["sourceColumnName"],
            "target_col": ctx["targetKeyRefBindings"][0]["sourceColumnName"],
        })
    return entities, relationships


def build_graph_parts(entities: list[dict], relationships: list[dict],
                      workspace_id: str, lakehouse_id: str,
                      table_schema: str = "") -> list[dict]:
    """Assemble the four graph definition parts as an updateDefinition array.

    ``table_schema`` is the OneLake schema folder under ``Tables/`` (e.g. ``dbo``
    for a schema-enabled Lakehouse). Leave empty for a non-schema Lakehouse where
    managed tables live directly at ``Tables/<name>`` (how ``load_lakehouse.py``
    writes them).
    """
    seg = f"{table_schema}/" if table_schema else ""

    def ds_name(table: str) -> str:
        return f"{lakehouse_id}_{table}"

    def ds_path(table: str) -> str:
        return (f"abfss://{workspace_id}@{_ONELAKE_GRAPH_HOST}"
                f"/{lakehouse_id}/Tables/{seg}{table}")

    # graphType: node types + edge types
    node_types = [{
        "primaryKeyProperties": [e["key_col"]],
        "alias": e["et_id"],
        "labels": [e["name"]],
        "properties": e["properties"],
    } for e in entities]
    edge_types = [{
        "sourceNodeType": {"alias": r["source_et"]},
        "alias": r["rt_id"],
        "destinationNodeType": {"alias": r["target_et"]},
        "labels": [r["name"]],
        "properties": [{"name": r["source_col"], "type": "STRING"},
                       {"name": r["target_col"], "type": "STRING"}],
    } for r in relationships]
    graph_type = {"$schema": _GT_SCHEMA, "nodeTypes": node_types, "edgeTypes": edge_types}

    # dataSources: one DeltaTable per distinct bound table
    tables = list(dict.fromkeys([e["table"] for e in entities]
                                + [r["table"] for r in relationships]))
    data_sources = {"$schema": _DS_SCHEMA, "dataSources": [
        {"name": ds_name(t), "type": "DeltaTable", "properties": {"path": ds_path(t)}}
        for t in tables
    ]}

    # graphDefinition: node tables + edge tables
    node_tables = [{
        "nodeTypeAlias": e["et_id"],
        "id": str(uuid.uuid4()),
        "dataSourceName": ds_name(e["table"]),
        "propertyMappings": [{"propertyName": p["name"], "sourceColumn": p["name"]}
                             for p in e["properties"]],
    } for e in entities]
    edge_tables = [{
        "edgeTypeAlias": r["rt_id"],
        "id": str(uuid.uuid4()),
        "edgeIdMapping": None,
        "dataSourceName": ds_name(r["table"]),
        "sourceNodeKeyColumns": [r["source_col"]],
        "propertyMappings": [{"propertyName": r["source_col"], "sourceColumn": r["source_col"]},
                             {"propertyName": r["target_col"], "sourceColumn": r["target_col"]}],
        "destinationNodeKeyColumns": [r["target_col"]],
    } for r in relationships]
    graph_definition = {"$schema": _GD_SCHEMA, "nodeTables": node_tables, "edgeTables": edge_tables}

    styling = {"$schema": _ST_SCHEMA,
               "modelLayout": {"positions": {}, "styles": {},
                               "pan": {"x": 0.0, "y": 0.0}, "zoomLevel": 1.0},
               "visualFormat": None, "scenario": "Ontology"}

    parts = []
    for path, obj in (("graphType.json", graph_type), ("dataSources.json", data_sources),
                      ("graphDefinition.json", graph_definition),
                      ("stylingConfiguration.json", styling)):
        payload = base64.b64encode(
            json.dumps(obj, ensure_ascii=False).encode("utf-8")).decode("ascii")
        parts.append({"path": path, "payload": payload, "payloadType": "InlineBase64"})
    return parts


def resolve_graph_item(workspace_id: str, ontology_item_id: str, token: str) -> str:
    import requests

    r = requests.get(f"{_FABRIC_API_BASE}/workspaces/{workspace_id}/items",
                     headers={"Authorization": f"Bearer {token}"}, timeout=60)
    r.raise_for_status()
    needle = ontology_item_id.replace("-", "")
    for it in r.json().get("value", []):
        if it.get("type") == "GraphModel" and needle in it.get("displayName", "").replace("-", ""):
            return it["id"]
    raise RuntimeError(
        f"Could not find the companion GraphModel for ontology {ontology_item_id}; "
        "pass --graph-item-id explicitly.")


def _poll(url: str, headers: dict, timeout_s: int = 300) -> dict:
    import requests

    deadline = time.time() + timeout_s
    wait = 3
    while time.time() < deadline:
        resp = requests.get(url, headers=headers, timeout=30)
        body = resp.json() if resp.content else {}
        status = (body.get("status") or "").lower()
        if status in ("succeeded", "completed"):
            return body
        if status in ("failed", "cancelled", "canceled", "deduped"):
            raise RuntimeError(f"operation failed: {resp.text[:400]}")
        time.sleep(wait)
        wait = min(wait * 2, 15)
    raise TimeoutError("operation did not complete in time")


def update_graph_definition(workspace_id: str, graph_id: str, parts: list[dict], token: str) -> None:
    import requests

    url = f"{_FABRIC_API_BASE}/workspaces/{workspace_id}/items/{graph_id}/updateDefinition"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json={"definition": {"parts": parts}}, timeout=120)
    if resp.status_code == 202 and "Location" in resp.headers:
        _poll(resp.headers["Location"], headers)
    elif resp.status_code not in (200, 201):
        raise RuntimeError(f"updateDefinition failed: HTTP {resp.status_code} — {resp.text[:400]}")
    print(f"Graph model definition applied to item {graph_id}.")


def refresh_graph(workspace_id: str, graph_id: str, token: str) -> None:
    import requests

    url = f"{_FABRIC_API_BASE}/workspaces/{workspace_id}/items/{graph_id}/jobs/instances?jobType=RefreshGraph"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json={}, timeout=60)
    if resp.status_code == 202 and "Location" in resp.headers:
        _poll(resp.headers["Location"], headers)
        print("Graph refresh (RefreshGraph) completed — data ingested.")
    else:
        raise RuntimeError(f"RefreshGraph failed: HTTP {resp.status_code} — {resp.text[:400]}")


def main() -> None:
    from azure.identity import DefaultAzureCredential
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-id", default=os.environ.get("FABRIC_WORKSPACE_ID"))
    parser.add_argument("--lakehouse-id", default=os.environ.get("FABRIC_LAKEHOUSE_ID"))
    parser.add_argument("--ontology-item-id", default=os.environ.get("FABRIC_ONTOLOGY_ITEM_ID"))
    parser.add_argument("--graph-item-id", default=os.environ.get("FABRIC_GRAPH_ITEM_ID"))
    parser.add_argument("--ontology-dir", default=str(_ONTOLOGY_DIR))
    parser.add_argument("--table-schema", default=os.environ.get("FABRIC_TABLE_SCHEMA", ""),
                        help="OneLake schema folder under Tables/ (e.g. 'dbo' for a "
                             "schema-enabled Lakehouse; empty for a non-schema Lakehouse).")
    parser.add_argument("--refresh", action="store_true",
                        help="Trigger a RefreshGraph job after applying the definition.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Assemble + print the graph parts without calling Fabric.")
    args = parser.parse_args()

    entities, relationships = parse_ontology(Path(args.ontology_dir))
    print(f"Parsed {len(entities)} entity types and {len(relationships)} relationship types.")

    if args.dry_run:
        ws = args.workspace_id or "${FABRIC_WORKSPACE_ID}"
        lh = args.lakehouse_id or "${FABRIC_LAKEHOUSE_ID}"
        parts = build_graph_parts(entities, relationships, ws, lh, args.table_schema)
        for p in parts:
            print(f"\n--- {p['path']} ---")
            print(base64.b64decode(p["payload"]).decode("utf-8"))
        return

    missing = [n for n, v in (("--workspace-id", args.workspace_id),
                              ("--lakehouse-id", args.lakehouse_id),
                              ("--ontology-item-id", args.ontology_item_id)) if not v]
    if missing:
        parser.error("missing required config: " + ", ".join(missing))

    token = DefaultAzureCredential().get_token(_FABRIC_SCOPE).token
    graph_id = args.graph_item_id or resolve_graph_item(args.workspace_id, args.ontology_item_id, token)
    print(f"Companion GraphModel item: {graph_id}")

    parts = build_graph_parts(entities, relationships, args.workspace_id, args.lakehouse_id,
                              args.table_schema)
    update_graph_definition(args.workspace_id, graph_id, parts, token)

    if args.refresh:
        refresh_graph(args.workspace_id, graph_id, token)
        print("Graph is built and populated — NL2Ontology/GQL queries can now run.")
    else:
        print("Definition applied. Run with --refresh (or trigger a RefreshGraph job) to ingest data.")


if __name__ == "__main__":
    main()
