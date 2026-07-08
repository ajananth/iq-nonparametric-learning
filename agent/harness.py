#!/usr/bin/env python3
"""Foundry agent harness — Phase 5, REWIRED to knowledge-base grounding (issue #24, EPIC D #4).

Grounds a hosted Microsoft Foundry agent in the live Fabric IQ ``iqnpl_ontology`` through the **adopted**
Foundry IQ **Knowledge Base** path (docs/verified-capabilities.md §2b): Azure AI Search agentic retrieval
over a ``fabricOntology`` knowledge source. Before the model answers, the harness POSTs the question to
``/knowledgebases/{kb}/retrieve`` and injects the **verbatim ontology rows** it returns into the agent's
context. This bypasses the hosted-MCP *tool* paths (``fabric_iq_preview`` / generic ``MCPTool``) which
RAG-chunk the ontology result into an opaque stub with no rows and cause hallucination (§2a).

The agent's text-space config (instructions, grounding description, skills) lives under
``.agent_configs/baseline/`` and is loaded here so the *same code* runs with or without the Agent Optimizer.

Governance:
  * Art. II  — weights are FROZEN. ``--model`` is a deployment-name string; there is no fine-tuning step.
  * Art. III — the model is the ONLY thing that changes to swap it; it is used END-TO-END (agent
               orchestration model == knowledge-base synthesis model). No code path is model-specific.
  * Art. IV  — no schema/SQL here; the agent reaches all semantics through the ontology knowledge base.
  * Art. VI  — search endpoint / KB names / project endpoint come from env; nothing secret is committed.
               Auth is delegated user identity (DefaultAzureCredential); the end-user token is forwarded to
               Fabric so retrieval runs under the caller's identity/permissions.

Env (see .env.example):
  FOUNDRY_PROJECT_ENDPOINT          the project endpoint (…/api/projects/<project>)
  FOUNDRY_MODEL_DEPLOYMENT_NAME     default model deployment (overridable via --model)
  AZURE_SEARCH_ENDPOINT             https://<search-svc>.search.windows.net
  AZURE_SEARCH_API_VERSION          knowledge-base REST api-version
  AZURE_SEARCH_KNOWLEDGE_SOURCE     fabricOntology knowledge-source name
  AZURE_SEARCH_KNOWLEDGE_BASE       knowledge-base name

One-off smoke test:
  python agent/harness.py --model gpt-5.4 --prompt "How many monitored sites are there?"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_AGENT_DIR = Path(__file__).resolve().parent
_ENV_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")
_SEARCH_SCOPE = "https://search.azure.com/.default"


def _substitute_env(text: str, *, strict: bool) -> str:
    """Replace ``${VAR}`` tokens from the environment.

    When ``strict`` is True (runtime), a missing var raises; when False (hashing), the token is kept
    verbatim so the config hash is deterministic and secret-free.
    """
    def repl(match: "re.Match[str]") -> str:
        name = match.group(1)
        val = os.environ.get(name)
        if val is None:
            if strict:
                raise KeyError(f"environment variable {name} is not set (needed by agent config)")
            return match.group(0)
        return val

    return _ENV_RE.sub(repl, text)


@dataclass
class AgentConfig:
    """Loaded, optimizer-ready text-space config for the baseline agent."""

    instructions: str
    tool_spec: dict[str, Any]
    skills: list[str] = field(default_factory=list)
    config_dir: Path = _AGENT_DIR / ".agent_configs" / "baseline"

    def config_hash(self) -> str:
        """Deterministic hash of the *tunable* config, with env tokens un-substituted (no secrets).

        This is the fairness fingerprint: identical across every model in a run proves that only the model
        deployment string varied (Art. III / experiment protocol single-variable control).
        """
        raw_tools = (self.config_dir / "tools.json").read_text(encoding="utf-8")
        payload = {
            "instructions": self.instructions,
            "tools": _substitute_env(raw_tools, strict=False),
            "skills": self.skills,
        }
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    @property
    def grounding(self) -> dict[str, Any]:
        """The knowledge-base grounding spec (env already substituted at load time)."""
        g = self.tool_spec.get("grounding")
        if not g:
            raise ValueError("no 'grounding' block found in tools.json")
        return g


def load_config(config_dir: Path | str = AgentConfig.config_dir) -> AgentConfig:
    """Load instructions.md, tools.json (env-substituted), and any skills/*/SKILL.md."""
    config_dir = Path(config_dir)
    instructions = (config_dir / "instructions.md").read_text(encoding="utf-8")

    raw_tools = (config_dir / "tools.json").read_text(encoding="utf-8")
    tool_spec = json.loads(_substitute_env(raw_tools, strict=True))

    skills: list[str] = []
    skills_dir = config_dir / "skills"
    if skills_dir.is_dir():
        for skill_file in sorted(skills_dir.rglob("SKILL.md")):
            skills.append(skill_file.read_text(encoding="utf-8"))

    return AgentConfig(
        instructions=instructions, tool_spec=tool_spec, skills=skills, config_dir=config_dir
    )


def _compose_instructions(cfg: AgentConfig) -> str:
    """Instructions + skill bodies, appended so skill guidance travels with the system prompt."""
    parts = [cfg.instructions]
    for skill in cfg.skills:
        parts.append("\n\n---\n\n# Loaded skill\n\n" + skill)
    return "".join(parts)


# --------------------------------------------------------------------------------------------------
# Knowledge-base grounding (the adopted path — §2b)
# --------------------------------------------------------------------------------------------------
@dataclass
class GroundingResult:
    """Evidence from one knowledge-base /retrieve call: the verbatim ontology rows fed to the model."""

    query: str
    kb_name: str
    http_status: int
    synthesized_answer: str
    raw_rows: list[str]          # verbatim fabricRawData (CSV) per reference
    reference_count: int
    error: str | None = None

    @property
    def has_rows(self) -> bool:
        return any(r and r.strip() for r in self.raw_rows)

    def as_tool_call(self) -> dict[str, Any]:
        """Shape the retrieve as a tool-call so the scorer's grounding/traversal detection is unchanged.

        The scorer credits grounding when a tool-call ``type``/``name`` contains ``fabric``/``mcp`` — so the
        eval/scorer/ground-truth stay byte-for-byte identical across the tool-path and KB-path baselines.
        """
        return {
            "type": "fabric_kb_retrieve",
            "name": self.kb_name,
            "arguments": self.query,
            "output": {
                "http_status": self.http_status,
                "reference_count": self.reference_count,
                "has_rows": self.has_rows,
                "synthesized_answer": self.synthesized_answer,
                "fabric_raw_data": self.raw_rows,
                "error": self.error,
            },
        }


def _kb_retrieve(credential: Any, question: str, spec: dict[str, Any]) -> GroundingResult:
    """POST the question to the knowledge base and return the verbatim ontology rows.

    Replicates the empirically-validated Path-A' request shape (2026-07-08):
      * ``rerankerThreshold: 0`` — the default reranker filters multi-hop answers to empty.
      * ``includeReferenceSourceData: true`` — returns ``sourceData.fabricRawData`` (verbatim CSV).
      * header ``x-ms-query-source-authorization`` = the (bare) search-audience end-user token — forwards
        the caller's identity to Fabric so retrieval honours Fabric permissions/governance.
    """
    import requests

    endpoint = str(spec["search_endpoint"]).rstrip("/")
    api = spec["api_version"]
    kb = spec["knowledge_base"]
    ks = spec["knowledge_source"]
    rp = spec.get("retrieve_params", {})

    token = credential.get_token(_SEARCH_SCOPE).token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-ms-query-source-authorization": token,
    }
    ks_param = {
        "knowledgeSourceName": ks,
        "kind": rp.get("kind", "fabricOntology"),
        "includeReferences": rp.get("includeReferences", True),
        "includeReferenceSourceData": rp.get("includeReferenceSourceData", True),
        "rerankerThreshold": rp.get("rerankerThreshold", 0),
    }
    body = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
        "knowledgeSourceParams": [ks_param],
    }
    url = f"{endpoint}/knowledgebases/{kb}/retrieve?api-version={api}"

    try:
        r = requests.post(url, headers=headers, json=body, timeout=180)
        status = r.status_code
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    except Exception as exc:  # noqa: BLE001 - grounding failure must surface, not crash
        return GroundingResult(question, kb, 0, "", [], 0, error=f"{type(exc).__name__}: {exc}")

    raw_rows: list[str] = []
    synthesized = ""
    refs = data.get("references", []) if isinstance(data, dict) else []
    for ref in refs or []:
        sd = ref.get("sourceData") or {}
        raw = sd.get("fabricRawData")
        if raw:
            raw_rows.append(raw)
        if not synthesized and sd.get("fabricAnswer"):
            synthesized = sd["fabricAnswer"]
    if not synthesized:
        for msg in data.get("response", []) or []:
            for c in msg.get("content", []) or []:
                if c.get("type") == "text" and c.get("text"):
                    synthesized = c["text"]
                    break
            if synthesized:
                break

    err = None if status < 400 else f"HTTP {status}: {json.dumps(data)[:300]}"
    return GroundingResult(
        query=question, kb_name=kb, http_status=status, synthesized_answer=synthesized,
        raw_rows=raw_rows, reference_count=len(refs or []), error=err,
    )


def _compose_grounded_input(question: str, gr: GroundingResult) -> str:
    """Build the agent input: the question plus the authoritative grounded rows (or an explicit no-data
    marker). The instructions require the model to answer ONLY from this block."""
    lines = [
        "# Question",
        question,
        "",
        "# Grounded ontology evidence (AUTHORITATIVE — answer ONLY from this)",
    ]
    if gr.error:
        lines.append(f"RETRIEVAL ERROR: {gr.error}")
        lines.append("NO ROWS were returned. You must reply that the data is unavailable.")
    elif not gr.has_rows:
        lines.append("NO ROWS were returned for this question.")
        lines.append("You must reply that the data is unavailable; do NOT fabricate an answer.")
    else:
        if gr.synthesized_answer:
            lines.append("## Fabric IQ summary")
            lines.append(gr.synthesized_answer)
            lines.append("")
        lines.append("## Verbatim rows (CSV)")
        for i, raw in enumerate(gr.raw_rows, 1):
            lines.append(f"### reference {i}")
            lines.append(raw.strip())
    return "\n".join(lines)


@dataclass
class InvokeResult:
    """Everything the scorer needs from one agent turn."""

    model: str
    prompt: str
    answer: str
    tool_calls: list[dict[str, Any]]
    input_tokens: int
    output_tokens: int
    latency_ms: int
    config_hash: str
    grounded: bool = False
    error: str | None = None
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d.pop("raw", None)
        return d


class AgentHarness:
    """Create, invoke, and tear down a hosted Foundry agent version. Model is a parameter used end-to-end."""

    def __init__(self, endpoint: str | None = None) -> None:
        self.endpoint = endpoint or os.environ["FOUNDRY_PROJECT_ENDPOINT"]
        self._cfg = load_config()
        self._credential = None
        self._project = None
        self._openai = None
        self._agent = None

    def __enter__(self) -> "AgentHarness":
        from azure.identity import DefaultAzureCredential
        from azure.ai.projects import AIProjectClient

        self._credential = DefaultAzureCredential()
        self._project = AIProjectClient(endpoint=self.endpoint, credential=self._credential)
        self._openai = self._project.get_openai_client()
        return self

    def __exit__(self, *exc: Any) -> None:
        try:
            self.delete_agent()
        finally:
            for obj in (self._openai, self._project, self._credential):
                try:
                    obj.close()  # type: ignore[union-attr]
                except Exception:
                    pass

    @property
    def config_hash(self) -> str:
        return self._cfg.config_hash()

    def create_agent(self, model: str, *, name: str = "iqnpl-water-analyst") -> Any:
        from azure.ai.projects.models import PromptAgentDefinition

        # No server-side tool: grounding is injected client-side from the knowledge-base retrieve (§2b).
        definition = PromptAgentDefinition(
            model=model,
            instructions=_compose_instructions(self._cfg),
        )
        self._agent = self._project.agents.create_version(agent_name=name, definition=definition)
        return self._agent

    def delete_agent(self) -> None:
        if self._agent is not None and self._project is not None:
            try:
                self._project.agents.delete_version(
                    agent_name=self._agent.name, agent_version=self._agent.version
                )
            except Exception:
                pass
            self._agent = None

    def invoke(self, prompt: str, model: str) -> InvokeResult:
        """Ground the prompt via the knowledge base, then answer with a freshly created agent version."""
        if self._agent is None or getattr(self._agent.definition, "model", None) != model:
            self.delete_agent()
            self.create_agent(model)

        start = time.perf_counter()
        error: str | None = None
        answer = ""
        in_tok = out_tok = 0
        raw: dict[str, Any] | None = None

        # 1. Grounding — retrieve verbatim ontology rows (the retrieve is the groundedness evidence).
        gr = _kb_retrieve(self._credential, prompt, self._cfg.grounding)
        tool_calls = [gr.as_tool_call()]
        grounded_input = _compose_grounded_input(prompt, gr)

        # 2. Answer — the agent reasons ONLY over the injected rows (same model as KB synthesis).
        try:
            response = self._openai.responses.create(
                input=grounded_input,
                extra_body={"agent_reference": {"name": self._agent.name, "type": "agent_reference"}},
            )
            answer = getattr(response, "output_text", "") or ""
            usage = getattr(response, "usage", None)
            if usage is not None:
                in_tok = int(getattr(usage, "input_tokens", 0) or 0)
                out_tok = int(getattr(usage, "output_tokens", 0) or 0)
            try:
                raw = response.model_dump()  # type: ignore[attr-defined]
            except Exception:
                raw = None
        except Exception as exc:  # noqa: BLE001 - report, don't crash the run
            error = f"{type(exc).__name__}: {exc}"
        if gr.error and not error:
            error = f"grounding: {gr.error}"
        latency_ms = int((time.perf_counter() - start) * 1000)

        return InvokeResult(
            model=model,
            prompt=prompt,
            answer=answer,
            tool_calls=tool_calls,
            input_tokens=in_tok,
            output_tokens=out_tok,
            latency_ms=latency_ms,
            config_hash=self.config_hash,
            grounded=gr.has_rows,
            error=error,
            raw=raw,
        )


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    parser = argparse.ArgumentParser(description="Invoke the baseline KB-grounded Foundry agent.")
    parser.add_argument("--model", default=os.environ.get("FOUNDRY_MODEL_DEPLOYMENT_NAME"),
                        help="model deployment name (swappable; used for BOTH the agent and KB synthesis)")
    parser.add_argument("--prompt", required=True, help="natural-language question for the agent")
    parser.add_argument("--endpoint", default=None, help="override FOUNDRY_PROJECT_ENDPOINT")
    args = parser.parse_args()

    if not args.model:
        parser.error("no model: pass --model or set FOUNDRY_MODEL_DEPLOYMENT_NAME")

    with AgentHarness(endpoint=args.endpoint) as harness:
        result = harness.invoke(args.prompt, model=args.model)
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
