#!/usr/bin/env python3
"""Hosted Foundry agent harness — Phase 5 (issue #24, EPIC D #4).

Builds and invokes a hosted Microsoft Foundry agent grounded in the live Fabric IQ ``iqnpl_ontology``
through the **verified** ``fabric_iq_preview`` server-side tool (docs/verified-capabilities.md §2a; Learn
``foundry/agents/how-to/tools/fabric-iq``). The agent's text-space config (instructions, tool description,
skills) lives under ``.agent_configs/baseline/`` and is loaded here so the *same code* runs with or without
the Agent Optimizer (§3b, "optimizer-ready").

Governance:
  * Art. II  — weights are FROZEN. ``--model`` is a deployment-name string; there is no fine-tuning step.
  * Art. III — the model is the ONLY thing that changes to swap LLM<->SLM. No code path is model-specific.
  * Art. IV  — no schema/SQL here; semantics are reached only through the ontology tool.
  * Art. VI  — the Fabric IQ connection id / project endpoint come from env; nothing secret is committed.

Env (see .env.example):
  FOUNDRY_PROJECT_ENDPOINT          the project endpoint (…/api/projects/<project>)
  FOUNDRY_MODEL_DEPLOYMENT_NAME     default model deployment (overridable via --model)
  FABRIC_IQ_PROJECT_CONNECTION_ID   id/name of the Fabric IQ (OneLake Catalog) project connection (REQUIRED)
  FABRIC_WORKSPACE_ID               Fabric workspace GUID (for server_url)
  FABRIC_ONTOLOGY_ITEM_ID           ontology item GUID (for server_url)

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

        This is the fairness fingerprint: identical across every model in the H1 matrix proves that only
        the model deployment string varied (Art. III / experiment protocol single-variable control).
        """
        raw_tools = (self.config_dir / "tools.json").read_text(encoding="utf-8")
        payload = {
            "instructions": self.instructions,
            "tools": _substitute_env(raw_tools, strict=False),
            "skills": self.skills,
        }
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()


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


def _build_fabric_iq_tool(cfg: AgentConfig):
    """Instantiate the verified FabricIQPreviewTool from the loaded tools.json spec."""
    from azure.ai.projects.models import FabricIQPreviewTool

    tool = next(
        (t for t in cfg.tool_spec.get("tools", []) if t.get("type") == "fabric_iq_preview"), None
    )
    if tool is None:
        raise ValueError("no fabric_iq_preview tool found in tools.json")

    conn_id = tool.get("project_connection_id")
    if not conn_id:
        raise ValueError("fabric_iq_preview tool is missing project_connection_id")

    kwargs: dict[str, Any] = {
        "project_connection_id": conn_id,
        "require_approval": tool.get("require_approval", "never"),
    }
    if tool.get("server_label"):
        kwargs["server_label"] = tool["server_label"]
    if tool.get("server_url"):
        kwargs["server_url"] = tool["server_url"]
    return FabricIQPreviewTool(**kwargs)


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
    error: str | None = None
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d.pop("raw", None)
        return d


def _extract_tool_calls(response: Any) -> list[dict[str, Any]]:
    """Pull Fabric IQ / MCP tool-call items from a Responses API result.

    Robust to shape drift: scans ``response.output`` for items whose type references fabric/mcp/tool and
    records the tool name, the natural-language query the model dispatched (arguments), and any returned
    output. This is the groundedness / traversal-correctness evidence (did it call the ontology, and what
    did it ask?).
    """
    calls: list[dict[str, Any]] = []
    output = getattr(response, "output", None) or []
    for item in output:
        itype = str(getattr(item, "type", "") or (item.get("type") if isinstance(item, dict) else ""))
        low = itype.lower()
        if not any(tok in low for tok in ("fabric", "mcp", "tool_call", "tool")):
            continue
        if "message" in low or "reasoning" in low:
            continue
        get = (lambda k: getattr(item, k, None)) if not isinstance(item, dict) else item.get
        calls.append(
            {
                "type": itype,
                "name": get("name") or get("server_label"),
                "arguments": get("arguments") or get("input"),
                "output": get("output") or get("result"),
            }
        )
    return calls


class AgentHarness:
    """Create, invoke, and tear down a hosted Foundry agent version. Model is a parameter."""

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

        definition = PromptAgentDefinition(
            model=model,
            instructions=_compose_instructions(self._cfg),
            tools=[_build_fabric_iq_tool(self._cfg)],
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
        """Run one prompt against a freshly created agent version for ``model`` and capture metrics."""
        if self._agent is None or getattr(self._agent.definition, "model", None) != model:
            self.delete_agent()
            self.create_agent(model)

        start = time.perf_counter()
        error: str | None = None
        answer = ""
        tool_calls: list[dict[str, Any]] = []
        in_tok = out_tok = 0
        raw: dict[str, Any] | None = None
        try:
            response = self._openai.responses.create(
                input=prompt,
                extra_body={"agent_reference": {"name": self._agent.name, "type": "agent_reference"}},
            )
            answer = getattr(response, "output_text", "") or ""
            tool_calls = _extract_tool_calls(response)
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
            error=error,
            raw=raw,
        )


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    parser = argparse.ArgumentParser(description="Invoke the baseline Fabric-IQ-grounded Foundry agent.")
    parser.add_argument("--model", default=os.environ.get("FOUNDRY_MODEL_DEPLOYMENT_NAME"),
                        help="model deployment name (swappable; e.g. gpt-5.4 or gpt-5.4-mini)")
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
