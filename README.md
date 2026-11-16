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

## Real agents

`AGENTS/` holds the agent team itself: 26 agent definitions and skills (11 Build, 9 Operate,
6 Consume) plus shared telco guardrails and domain pack, and the `telcocrew` runtime that runs
them on Claude with guardrails enforced in code and named human approvers. See
[AGENTS/README.md](AGENTS/README.md).

## Run it

Open `demo/index.html` in a browser. No build step and no server needed. The **Agents & skills**
page shows the catalog; to run the agents from that page, start the runtime:

```bash
cd AGENTS && pip install -r requirements.txt && python -m telcocrew serve
```

and open http://127.0.0.1:8765/#agents (live on Claude with `ANTHROPIC_API_KEY`, otherwise the offline simulator).

To produce a single self-contained file: `node demo/build.mjs` (writes `demo/dist/`).

## Repository

| Path | Content |
|---|---|
| `AGENTS/` | Agent definitions, skills, `telcocrew` runtime and tests |
| `demo/` | The demo app (`index.html`, `styles.css`, `data.js`, `app.js`, generated `agents-manifest.js`) |
| `docs/AgentWorkflow_Build_Operate_Consume.md` | Agent catalog, gates, action classes, human roles, team enablement |
| `research/Telco_AI_Market_Research.md` | Market research with sources |
| `UTIL_BuildWithAI_Spec.md` | Original BuildWithAI spec (utilities edition) this demo extends |

All operator names, people, systems and figures in the demo are fictional or simulated.
