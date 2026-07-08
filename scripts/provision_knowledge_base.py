#!/usr/bin/env python3
"""Provision the Foundry IQ Knowledge Base grounding path (Phase 5 re-wire, issue #24, EPIC D #4).

This is the **adopted grounding architecture** (docs/verified-capabilities.md §2b): the Azure AI Search
agentic-retrieval *Knowledge Base* over a `fabricOntology` *knowledge source*. It surfaces REAL verbatim
ontology rows to the agent, unlike the Foundry hosted-MCP *tool* paths (`fabric_iq_preview` / generic
`MCPTool`) which RAG-chunk the ontology result into an opaque stub and cause hallucination (§2a).

Idempotent: PUT creates-or-updates. Run once (or after a model swap) to (re)provision:
  * knowledge source  ``iqnpl-ontology-ks``  (kind ``fabricOntology`` -> workspace + ontology GUIDs)
  * knowledge base    ``iqnpl-ontology-kb``  (``answerSynthesis`` with a synthesis LLM deployment)

Governance:
  * Art. I  — request shapes replicate the empirically-validated Path-A' probe (2026-07-08), not a guess.
  * Art. IV — the KB binds to the ontology; no tables/columns/SQL are encoded here.
  * Art. VI — everything is infra (endpoints/GUIDs/deployment names), env-driven; NO secrets. The KB's
              synthesis LLM authenticates with the search service SYSTEM-ASSIGNED managed identity
              (``authIdentity: null``) — required because the AOAI resource has key auth disabled — so no
              key is ever placed in the definition.
  * Art. VIII — provisioning itself is negligible cost; the /retrieve calls (billable) happen in the
                harness and are gated by the baseline cost approval.

Auth: ``DefaultAzureCredential`` -> a search-audience token (``https://search.azure.com/.default``) for the
management PUT/DELETE/GET calls (delegated user identity; no stored secret).

Env (see .env.example):
  AZURE_SEARCH_ENDPOINT           https://<search-svc>.search.windows.net
  AZURE_SEARCH_API_VERSION        REST api-version (default 2026-05-01-preview)
  AZURE_SEARCH_KNOWLEDGE_SOURCE   knowledge-source name (default iqnpl-ontology-ks)
  AZURE_SEARCH_KNOWLEDGE_BASE     knowledge-base name (default iqnpl-ontology-kb)
  FABRIC_WORKSPACE_ID             Fabric workspace GUID hosting the ontology
  FABRIC_ONTOLOGY_ITEM_ID         ontology item GUID
  FOUNDRY_OPENAI_RESOURCE_URI     AOAI/Cognitive Services resource uri for the synthesis LLM
  FOUNDRY_MODEL_DEPLOYMENT_NAME   synthesis model deployment (swappable; --model overrides)

Usage:
  python scripts/provision_knowledge_base.py --model gpt-5.4            # (re)provision on gpt-5.4
  python scripts/provision_knowledge_base.py --model gpt-5.4 --dry-run  # print bodies, no live calls
  python scripts/provision_knowledge_base.py --cleanup                  # delete KB then KS
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_SEARCH_SCOPE = "https://search.azure.com/.default"
_DEFAULTS = {
    "AZURE_SEARCH_API_VERSION": "2026-05-01-preview",
    "AZURE_SEARCH_KNOWLEDGE_SOURCE": "iqnpl-ontology-ks",
    "AZURE_SEARCH_KNOWLEDGE_BASE": "iqnpl-ontology-kb",
}


def _cfg() -> dict[str, str]:
    """Resolve configuration from the environment, applying documented defaults."""
    def get(name: str, *, required: bool = False) -> str:
        val = os.environ.get(name) or _DEFAULTS.get(name, "")
        if required and not val:
            sys.exit(f"ERROR: environment variable {name} is required (see .env.example).")
        return val

    return {
        "endpoint": get("AZURE_SEARCH_ENDPOINT", required=True).rstrip("/"),
        "api": get("AZURE_SEARCH_API_VERSION"),
        "ks": get("AZURE_SEARCH_KNOWLEDGE_SOURCE"),
        "kb": get("AZURE_SEARCH_KNOWLEDGE_BASE"),
        "workspace_id": get("FABRIC_WORKSPACE_ID", required=True),
        "ontology_id": get("FABRIC_ONTOLOGY_ITEM_ID", required=True),
        "aoai_uri": get("FOUNDRY_OPENAI_RESOURCE_URI", required=True),
    }


def _ks_body(cfg: dict[str, str]) -> dict:
    return {
        "name": cfg["ks"],
        "kind": "fabricOntology",
        "description": "IQ-NPL water-quality ontology (Site / AlgaeSpecies / WaterQualityMeasurement / "
                       "TreatmentRecord). Bound to the live iqnpl_ontology over OneLake.",
        "fabricOntologyParameters": {
            "workspaceId": cfg["workspace_id"],
            "ontologyId": cfg["ontology_id"],
        },
    }


_BASELINE_ANSWER_INSTRUCTIONS = (
    "Answer only from retrieved ontology evidence. Do not invent sites, species, counts, or "
    "treatments. If no rows are returned, say the data is unavailable."
)


def _kb_body(cfg: dict[str, str], model: str, reasoning: str,
             retrieval_instructions: str | None = None,
             answer_instructions: str | None = None) -> dict:
    # fabricOntology REQUIRES a synthesis LLM (no 'minimal' reasoning). The LLM authenticates with the
    # search service system-assigned MI (authIdentity=null) which holds Cognitive Services User on the
    # AOAI resource — REQUIRED because that resource has key auth disabled. No key is ever stored (Art. VI).
    #
    # ``retrieval_instructions`` / ``answer_instructions`` are Phase-6 TUNABLE, frozen-weights TEXT knobs
    # (issue #29). Defaults reproduce the Phase-5 baseline KB byte-for-byte (no retrievalInstructions key;
    # the baseline answerInstructions), so an un-optimized re-provision is a no-op.
    body: dict = {
        "name": cfg["kb"],
        "description": "IQ-NPL ontology knowledge base — adopted grounding path for the Phase-5 agent.",
        "knowledgeSources": [{"name": cfg["ks"]}],
        "outputMode": "answerSynthesis",
        "answerInstructions": answer_instructions or _BASELINE_ANSWER_INSTRUCTIONS,
        "models": [{
            "kind": "azureOpenAI",
            "azureOpenAIParameters": {
                "resourceUri": cfg["aoai_uri"],
                "deploymentId": model,
                "modelName": model,
                "authIdentity": None,
            },
        }],
        "retrievalReasoningEffort": {"kind": reasoning},
    }
    if retrieval_instructions:
        body["retrievalInstructions"] = retrieval_instructions
    return body


def provision_kb(model: str, reasoning: str = "medium",
                 retrieval_instructions: str | None = None,
                 answer_instructions: str | None = None) -> dict:
    """(Re)provision the KS + KB with the given synthesis model and TUNABLE KB text params.

    Importable by the Phase-6 optimizer (scripts/optimize_harness.py) so a candidate that changes
    ``retrievalReasoningEffort`` / retrieval / answer instructions can re-provision the KB before rollout.
    Returns the KB body that was PUT (for the candidate/audit log). Live Azure calls; requires DefaultAzureCredential.
    """
    import requests
    from azure.identity import DefaultAzureCredential

    cfg = _cfg()
    token = DefaultAzureCredential().get_token(_SEARCH_SCOPE).token
    headers = _headers(token)

    r = requests.put(_url(cfg, f"knowledgesources/{cfg['ks']}"), headers=headers,
                     json=_ks_body(cfg), timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(f"KS provision failed {r.status_code}: {r.text[:500]}")

    kb_body = _kb_body(cfg, model, reasoning, retrieval_instructions, answer_instructions)
    r = requests.put(_url(cfg, f"knowledgebases/{cfg['kb']}"), headers=headers, json=kb_body, timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(f"KB provision failed {r.status_code}: {r.text[:500]}")
    return kb_body


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _url(cfg: dict[str, str], path: str) -> str:
    return f"{cfg['endpoint']}/{path}?api-version={cfg['api']}"


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    ap = argparse.ArgumentParser(description="Provision the Foundry IQ knowledge base grounding path.")
    ap.add_argument("--model", default=os.environ.get("FOUNDRY_MODEL_DEPLOYMENT_NAME"),
                    help="synthesis model deployment (swappable; e.g. gpt-5.4). Defaults to "
                         "FOUNDRY_MODEL_DEPLOYMENT_NAME.")
    ap.add_argument("--reasoning", default="medium", choices=["low", "medium"],
                    help="KB retrievalReasoningEffort (fabricOntology does not support 'minimal').")
    ap.add_argument("--retrieval-instructions", default=None,
                    help="optional KB retrievalInstructions (Phase-6 tunable; default omits the key).")
    ap.add_argument("--answer-instructions", default=None,
                    help="optional KB answerInstructions (Phase-6 tunable; default = baseline text).")
    ap.add_argument("--dry-run", action="store_true", help="print the request bodies; make no live calls.")
    ap.add_argument("--cleanup", action="store_true", help="delete the KB then the KS and exit.")
    args = ap.parse_args()

    cfg = _cfg()

    if args.dry_run:
        model = args.model or "<FOUNDRY_MODEL_DEPLOYMENT_NAME>"
        print("=== DRY RUN — no live calls ===")
        print(f"endpoint     : {cfg['endpoint']}")
        print(f"api-version  : {cfg['api']}")
        print(f"PUT knowledgesources/{cfg['ks']}")
        print(json.dumps(_ks_body(cfg), indent=2))
        print(f"PUT knowledgebases/{cfg['kb']}  (synthesis model = {model}, reasoning = {args.reasoning})")
        print(json.dumps(_kb_body(cfg, model, args.reasoning, args.retrieval_instructions,
                                  args.answer_instructions), indent=2))
        return

    import requests
    from azure.identity import DefaultAzureCredential

    token = DefaultAzureCredential().get_token(_SEARCH_SCOPE).token
    headers = _headers(token)

    if args.cleanup:
        for path in (f"knowledgebases/{cfg['kb']}", f"knowledgesources/{cfg['ks']}"):
            r = requests.delete(_url(cfg, path), headers=headers, timeout=60)
            print(f"DELETE {path} -> {r.status_code} {r.text[:200]}")
        return

    if not args.model:
        ap.error("no synthesis model: pass --model or set FOUNDRY_MODEL_DEPLOYMENT_NAME")

    # 1. knowledge source (fabricOntology)
    r = requests.put(_url(cfg, f"knowledgesources/{cfg['ks']}"), headers=headers,
                     json=_ks_body(cfg), timeout=120)
    print(f"PUT knowledgesources/{cfg['ks']} -> {r.status_code}")
    if r.status_code >= 400:
        print(r.text[:1500])
        sys.exit(1)

    # 2. knowledge base (answerSynthesis, synthesis LLM via search MI)
    r = requests.put(_url(cfg, f"knowledgebases/{cfg['kb']}"), headers=headers,
                     json=_kb_body(cfg, args.model, args.reasoning, args.retrieval_instructions,
                                   args.answer_instructions), timeout=120)
    print(f"PUT knowledgebases/{cfg['kb']} (model={args.model}, reasoning={args.reasoning}) -> {r.status_code}")
    if r.status_code >= 400:
        print(r.text[:1500])
        sys.exit(1)

    print(f"\nProvisioned KB '{cfg['kb']}' + KS '{cfg['ks']}' on synthesis model '{args.model}'.")


if __name__ == "__main__":
    main()
