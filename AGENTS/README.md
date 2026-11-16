# AGENTS: DataCrew Telco agent team

26 AI agents in three tracks, each with its own skill, plus two shared skills. The `telcocrew`
runtime runs them on Claude with real tool calls against a synthetic NorthStar Telecom estate,
enforces guardrails in code, and stops for named human approvers. With no API key it runs the
same tools through an offline simulator.

Modelled on [Agentic-Data-Engineering-Framework-BuildWithAI](https://github.com/CloudKatasani/Agentic-Data-Engineering-Framework-BuildWithAI):
the same split between agent definitions and skills, the same gates, action classes and
hash-bound approvals, rewritten for telco and extended from Build to Operate and Consume.

```
AGENTS/
  AUTHORING.md                 contract for agent and skill files (enforced by tests)
  shared/skills/               telco-shared-guardrails, telco-domain-pack (loaded by every agent)
  build/agents/*.md            11 agent definitions        build/skills/<id>/SKILL.md
  operate/agents/*.md          9 agent definitions         operate/skills/<id>/SKILL.md
  consume/agents/*.md          6 agent definitions         consume/skills/<id>/SKILL.md
  telcocrew/                   runtime: registry, guardrails, tools, Claude provider, simulator,
                               runner, workflows, HTTP API, CLI
  inputs/                      synthetic datasets (CSV/YAML/JSON) and 11 demo scenario packs
  artifacts/                   one folder per run: inputs used, workspace outputs, transcript, approvals, audit
  tests/                       contract, guardrail, inputs/artifacts and end-to-end tests
```

## The agents

| Track | Agents (gate, approvers) |
|---|---|
| **Build** | Delivery Orchestrator (G0, Data Product Owner) · Business Analyst (G1, Data Product Owner + Data Steward) · Source Mapping Analyst (G2, Data Steward + Security & Privacy Officer) · Solution Architect (G3, Data Architect) · Data Engineer (G4, Engineering Lead) · Quality Engineer (G5, QA Lead) · ML Engineer (G6, ML Lead / Model Risk + Security & Privacy Officer) · Release Engineer (G7, Change Manager (CAB) + Engineering Lead) · Semantic and AI Context (G8, Data Steward + Data Product Owner) · Data Product Publisher (G9, Data Product Owner + Data Steward) · Governance and Lineage (evidence at every gate) |
| **Operate** | Watch Desk · Triage and Correlation · Diagnosis and RCA · Resolution (A2/A3 actions: NOC Shift Lead, Service Delivery Manager, Change Manager (CAB)) · SLA and Batch Guard · Comms (Service Delivery Manager) · Problem and Knowledge (Problem Manager) · FinOps and Capacity · Service Reporting |
| **Consume** | Ask-Your-Data · Insight Scout · Next-Best-Action (approvers set by action type) · Care Copilot (Customer Care Lead) · Enterprise Account (Service Delivery Manager) · Exec Briefing |

Each agent's system prompt is: its definition body, then `telco-shared-guardrails`, then
`telco-domain-pack`, then its own skill, then the runtime contract. Print one with
`python -m telcocrew prompt build-source-mapping`.

## What the runtime enforces

| Control | Where |
|---|---|
| Action classes A0–A4: a tool above the agent's `max_action_class` is refused; A4 is never proposed or run | `tools.run_tool`, `guardrails.class_allowed` |
| Approvals bound to a SHA-256 of the content; execution and publication need a fully signed approval for the same content | `guardrails.ApprovalStore` |
| Named people only; agents never sign; one person cannot sign two roles; A3 needs two approvers | `ApprovalStore.sign/request` |
| One writer per folder: an agent writes only inside its `workspace` | `write_artifact` |
| Restricted telco data: MSISDN, IMSI/IMEI, names never selectable; profiling returns counts only; groups under 10 subscribers suppressed | `run_sandbox_sql`, `profile_column`, `query_metric` |
| Redaction of phone numbers, IMSI/IMEI, emails, cards and keys before any model call | `guardrails.redact` |
| Prompt-injection text in alarms or tickets flagged and treated as data | `guardrails.scan_injection` |
| Append-only, hash-chained audit log | `guardrails.AuditLog` |
| Pipelines pause on every approval request; reject stops, "request changes" reruns the step (return limit 3) | `workflows.Pipeline` |

## Live demo runbook (real Claude, synthetic data)

1. **Install and check** (once, before the audience arrives):
   ```bash
   cd AGENTS && pip install -r requirements.txt
   export ANTHROPIC_API_KEY=...
   python -m telcocrew preflight          # SDK, key, model access (no tokens spent), datasets, scenarios, artifacts path
   python -m telcocrew scenarios          # what you can run
   ```
2. **Start the web runtime** and open http://127.0.0.1:8765/#agents:
   ```bash
   python -m telcocrew serve
   ```
   Pick a track, choose a **Demo scenario**, optionally set model and effort (Sonnet 5.5 or low
   effort for a faster room), press **Start scenario**, and approve, request changes or reject each
   request as it appears. The panel shows the run record folder.
3. **Or run from the terminal**, approving at the prompt:
   ```bash
   python -m telcocrew demo operate-ran-incident
   python -m telcocrew demo build-churn-360 --model claude-sonnet-5-5
   python -m telcocrew demo consume-guardrail-probe
   ```
4. **Show the evidence**: open `artifacts/<run-id>/transcript.md` (every tool call the model made),
   `workspace/` (what the agents produced), `approvals.json` (who signed which hash) and `run.json`
   (tokens and cost estimate).

Inputs are described in [inputs/README.md](inputs/README.md) and the run record in
[artifacts/README.md](artifacts/README.md). Without a key everything runs in the simulator, so a
dry run the day before costs nothing.

## Run it

```bash
cd AGENTS
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

Offline (no key, deterministic simulator):

```bash
TELCOCREW_MODE=simulator python -m telcocrew pipeline build "Weekly churn-risk data product for retention" --auto-approve
TELCOCREW_MODE=simulator python -m telcocrew pipeline operate "Metro-North RAN cluster degradation"
TELCOCREW_MODE=simulator python -m telcocrew run consume-ask-your-data "Which regions have the highest churn risk this week?"
```

Live on Claude (each agent uses `claude-opus-5-5` with the effort set in its definition):

```bash
export ANTHROPIC_API_KEY=...
python -m telcocrew run operate-diagnosis-rca "Dropped calls up on 14 Metro-North cells since 18:40"
python -m telcocrew pipeline build "Weekly churn-risk data product for retention"     # you approve each gate at the prompt
```

Web demo with the live runtime (the Agents page connects automatically):

```bash
python -m telcocrew serve            # http://127.0.0.1:8765/#agents
```

The server listens on localhost only unless `TELCOCREW_API_TOKEN` is set (clients send it as
`X-API-Token`). Artifacts from CLI runs are written to `AGENTS/.runs/<run-id>/`.

API: `GET /api/agents`, `GET /api/agents/<id>`, `POST /api/agents/<id>/run {task, mode?, session_id?}`,
`POST /api/pipelines {track, request, mode?}`, `GET /api/pipelines/<id>`, `GET /api/sessions/<id>`,
`GET /api/approvals`, `POST /api/approvals/<id>/decide {role, decision: approve|changes|reject, comment}`.

## Tests

```bash
python -m pytest -q
```

Covers the authoring contract for all 26 agents and skills, every guardrail above, the full
Build pipeline through G0–G9, the Operate pipeline (execution only after approval), rejection
and rework, every agent in the simulator, and the live tool loop with a stubbed Claude.

## Adding an agent

1. Write `<track>/agents/<id>.md` and `<track>/skills/<id>/SKILL.md` following `AUTHORING.md`.
2. Use tools from the table in `AUTHORING.md`; add a new tool in `telcocrew/tools.py` with its class.
3. Add a simulator script in `telcocrew/simulator.py` (optional; live mode works without one).
4. Run the tests, then `python -m telcocrew manifest` to refresh the web demo's catalog.

## Limits

- The data, systems, people and incidents are synthetic. Tools that would change a real system
  (`open_pull_request`, `execute_approved_action`, `publish_data_product`) act on simulated
  targets or a digital twin; binding them to a client's Git host, NOC tooling or marketplace is
  client integration work.
- The simulator replays fixed tool sequences. It proves the controls, not the reasoning; use
  live mode for that.
