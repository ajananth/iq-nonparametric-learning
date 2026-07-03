# `infra/` — Infrastructure & provisioning (Phase 5+)

**Intent.** This directory will hold infrastructure-as-code and provisioning notes for the hosted Foundry
agent and its Fabric IQ connection. In the verified `azd ai agent init` layout, `azd` generates `infra/`
(and `azure.yaml`) alongside the agent config; those artifacts will live here.

> **Phase 2 is infra-free.** Nothing is provisioned and no `azd`/Azure/Fabric commands are run in this
> phase. This README records the intended provisioning flow only.

**Status: placeholder — populated in Phase 5+.**

## Intended provisioning flow (from `docs/verified-capabilities.md` §3a)
1. `azd ai agent init` — scaffold the agent (`agent.yaml`, `.agent_configs/baseline/`, dataset, and IaC into
   `infra/` + `azure.yaml`).
2. `azd provision` → `azd deploy` (or `azd up`) — provision and deploy.
3. `azd ai agent invoke "<prompt>"` — smoke-test the hosted agent.

## Prerequisites (see `PREREQUISITES.md`)
- Paid **F2+** Fabric capacity + workspace with the ontology tenant settings enabled.
- Foundry project + a GPT-5-family model deployment; RBAC **Foundry User** + **Foundry Project Manager**.
- **azd 1.21.3+**, the **`azure.ai.agents`** extension, and **Azure CLI**.

> **Cost note:** provisioning F2+ capacity and running Fabric IQ preview features may incur charges
> (verified-capabilities.md §2a; risk G5).
