#!/usr/bin/env python3
"""Create a new empty Fabric IQ **Ontology (preview)** item via the Fabric REST API.

Phase 4 deliverable (issue #22, EPIC C #3). Closes the tooling gap where
``deploy_ontology.py`` could only *update* an existing ontology item — this helper
creates the item first, then prints its GUID to feed into the deploy step.

What it does:
  1. ``POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/items`` with
     body ``{"displayName": "iqnpl_ontology", "type": "Ontology"}``.
  2. Handles the create as a Fabric **long-running operation (LRO)**: a ``201`` returns
     the item inline; a ``202`` returns a ``Location`` operation URL which we poll until
     ``Succeeded``, then GET its ``/result`` for the created item.
  3. Prints the new ontology **item GUID** (set it as ``FABRIC_ONTOLOGY_ITEM_ID``).

Verified against primary sources (Constitution Art. I, accessed 2026-07-06):
  - **Item Management overview** (Microsoft Learn, ``updated_at`` 2026-06-18) lists, under
    **Fabric IQ**, the item type **``Ontology``** as supporting *Create (without definition)*.
  - **Items - Create Item** REST API (``updated_at`` 2026-06-17): ``POST /workspaces/{id}/items``
    with ``displayName`` + ``type`` (an ``ItemType``); ``201`` inline or ``202`` + ``Location`` LRO.
  https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/item-management-overview
  https://learn.microsoft.com/en-us/rest/api/fabric/core/items/create-item
  https://learn.microsoft.com/en-us/rest/api/fabric/articles/long-running-operation

**Fallback:** if the REST create is unavailable in your tenant, create ``iqnpl_ontology``
in the Fabric portal (New item -> Ontology (preview)) and copy its item GUID from the URL.

Configuration (env or CLI; **never** hardcode secrets — Constitution Art. VI):
  FABRIC_WORKSPACE_ID   (required)  target workspace GUID

Usage (Phase 4):
  python scripts/create_ontology_item.py \
      --workspace-id <ws-guid> [--display-name iqnpl_ontology]
"""
from __future__ import annotations

import argparse
import os
import time

_FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
_FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"

_ONTOLOGY_ITEM_TYPE = "Ontology"
_DEFAULT_ONTOLOGY_NAME = "iqnpl_ontology"


def _poll_create_operation(operation_url: str, headers: dict, timeout_s: int = 300) -> str | None:
    """Poll a Fabric create LRO until it succeeds; return the created item id if exposed."""
    import requests

    deadline = time.time() + timeout_s
    wait = 2
    while time.time() < deadline:
        resp = requests.get(operation_url, headers=headers, timeout=30)
        body = resp.json() if resp.content else {}
        status = body.get("status")
        if status in ("Succeeded", "Completed"):
            # The created resource is returned from the operation's result endpoint.
            result = requests.get(operation_url.rstrip("/") + "/result", headers=headers, timeout=30)
            if result.status_code == 200 and result.content:
                return result.json().get("id")
            return None
        if status == "Failed":
            raise RuntimeError(f"Ontology item creation failed: {resp.text[:300]}")
        time.sleep(wait)
        wait = min(wait * 2, 15)
    raise TimeoutError("Ontology item creation did not complete in time")


def create_ontology_item(workspace_id: str, display_name: str, token: str) -> str:
    """Create the ontology item; return its GUID. Raises on failure."""
    import requests

    url = f"{_FABRIC_API_BASE}/workspaces/{workspace_id}/items"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "displayName": display_name,
        "type": _ONTOLOGY_ITEM_TYPE,
        "description": "Fabric IQ ontology for the water-utilities / algal-bloom demo (Phase 4).",
    }
    resp = requests.post(url, headers=headers, json=body, timeout=120)

    if resp.status_code in (200, 201):
        item_id = resp.json().get("id")
        if not item_id:
            raise RuntimeError(f"Item created but response missing 'id': {resp.text[:300]}")
        return item_id

    if resp.status_code == 202 and "Location" in resp.headers:
        item_id = _poll_create_operation(resp.headers["Location"], headers)
        if not item_id:
            raise RuntimeError(
                "Ontology item created (LRO succeeded) but the item GUID was not returned; "
                "find it via the List items API or the portal URL."
            )
        return item_id

    raise RuntimeError(
        f"Failed to create ontology item: HTTP {resp.status_code} — {resp.text[:300]}\n"
        "If the REST create surface is unavailable for Ontology items in your tenant, create "
        f"'{display_name}' in the Fabric portal (New -> Ontology (preview)) and use its item GUID."
    )


def main() -> None:
    from azure.identity import DefaultAzureCredential
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-id", default=os.environ.get("FABRIC_WORKSPACE_ID"))
    parser.add_argument("--display-name", default=_DEFAULT_ONTOLOGY_NAME)
    args = parser.parse_args()

    if not args.workspace_id:
        parser.error("workspace id required (pass --workspace-id or set FABRIC_WORKSPACE_ID)")

    token = DefaultAzureCredential().get_token(_FABRIC_SCOPE).token
    item_id = create_ontology_item(args.workspace_id, args.display_name, token)

    print(f"Ontology item created: {item_id}")
    print(f"Set FABRIC_ONTOLOGY_ITEM_ID={item_id} for scripts/deploy_ontology.py.")


if __name__ == "__main__":
    main()
