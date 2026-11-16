# DataCrew Telco: Build, Operate and Consume with AI

An interactive demo of one AI agent workforce for telco data and AI, split into three planes,
with named people reviewing and approving agent output at every gate.

| Plane | Agents | What it shows |
|---|---|---|
| **Build with AI** | 11 | Business ask → requirements → TM Forum SID mapping → design → dbt/ingest code → tests → model → release → semantic layer → data product, with gates G0–G9 |
| **Operate with AI** | 9 | Agentic NOC / DataOps / MLOps: alarm correlation, RCA, runbook actions with blast radius and rollback, comms, known-error entries |
| **Consume with AI** | 6 | Ask-your-data on certified metrics (SQL + lineage shown), guardrails, next-best-action proposals routed to approvers |

Also in the demo: a cross-plane approvals queue by role, a hash-chained audit trail, team
enablement for Dev, Managed Services, AI and Research teams, and a market research page.

## Run it

Open `demo/index.html` in a browser. No build step and no server needed.

To produce a single self-contained file: `node demo/build.mjs` (writes `demo/dist/`).

## Repository

| Path | Content |
|---|---|
| `demo/` | The demo app (`index.html`, `styles.css`, `data.js`, `app.js`) |
| `docs/AgentWorkflow_Build_Operate_Consume.md` | Agent catalog, gates, action classes, human roles, team enablement |
| `research/Telco_AI_Market_Research.md` | Market research with sources |
| `UTIL_BuildWithAI_Spec.md` | Original BuildWithAI spec (utilities edition) this demo extends |

All operator names, people, systems and figures in the demo are fictional or simulated.
