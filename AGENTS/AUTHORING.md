# Authoring contract for DataCrew Telco agents and skills

Every agent is two files: a **definition** (`<track>/agents/<id>.md`) and its **skill**
(`<track>/skills/<id>/SKILL.md`). The runtime (`telcocrew`) builds the agent's system
prompt from the definition body, then every skill it declares, shared skills first.
`tests/test_agents_and_skills.py` enforces this contract.

Reference model: `Agentic-Data-Engineering-Framework-BuildWithAI` (ADEF). Same discipline,
telco content.

## 1. Agent definition

```markdown
---
name: build-source-mapping                 # = file stem = skill folder name
title: Source Mapping Analyst Agent         # always ends with " Agent"
track: build                                # build | operate | consume
phase: Design                               # free text, one word or two
description: One sentence on what the agent does and when it is used.
model: claude-opus-5-5
effort: high                                # low | medium | high | xhigh
max_action_class: A1                        # highest class it may perform itself
gate: G2                                    # gate it requests, or none
approvers: [Data Steward, Security & Privacy Officer]   # human role titles, [] if none
workspace: 02-mapping/                      # the only folder it may write
skills: telco-shared-guardrails, telco-domain-pack, build-source-mapping
tools: read_artifact, write_artifact, list_source_metadata, profile_column, lookup_sid, lookup_glossary, request_gate
expects:
- ...
produces:
- ...
does:
- ...
does_not:
- ...
---

You are the DataCrew Telco Source Mapping Analyst Agent.

Follow `telco-shared-guardrails` first, then `telco-domain-pack`, then `build-source-mapping`.

Your job: ... (one or two sentences)

Tool policy
- May: ...
- May not: ...

Start by ... Finish by ... then stop.
```

Rules:

- `skills` always starts with `telco-shared-guardrails, telco-domain-pack`, then the agent's own skill.
- `tools` uses only names from section 3. Every agent gets `read_artifact` and `write_artifact`.
- Body: 12 to 30 lines. Plain, direct sentences.

## 2. Skill file

```markdown
---
name: build-source-mapping
description: What it produces, and when to use it (one paragraph, starts with a verb).
license: Proprietary
compatibility: Load telco-shared-guardrails and telco-domain-pack first. Needs ... tools.
metadata:
  owner: datacrew-telco
  version: "1.0.0"
  track: build
  role: mapping-analyst
  gate: G2                 # or none
  upstream: build-business-analyst
  downstream: build-solution-architect
---

# DataCrew Telco <Title>
```

Then these sections, **all present, in this order**, each as a `## ` heading:

1. `## Mission`
2. `## Use when`
3. `## Do not use for`
4. `## Inputs` (a table: Input | Required)
5. `## Tasks` (numbered, each step starts with a bold verb phrase; name the tool used)
6. `## Decision rules`
7. `## Do not`
8. `## Escalate to the human when`
9. `## Enterprise controls`
10. `## Self-review before handover` (three bullets starting `*Accuracy.*`, `*Risk.*`, `*Handover.*`)
11. `## Outputs` (a table: Artifact | Path | Content)
12. `## Definition of done` (numbered, checkable)
13. `## Worked example` (a short telco example with synthetic values; includes one rejected option written as `Rejected: ...` followed by `Why: ...`)
14. `## Common failure modes`

Rules:

- 70 to 180 lines. Telco-specific: use TM Forum SID entities, TMF Open API names (TMF620,
  TMF621, TMF622, TMF629, TMF632, TMF637, TMF638, TMF639, TMF642, TMF656), 3GPP counters,
  CDR/xDR, MSISDN/IMSI/IMEI handling, OSS/BSS terms, TM Forum autonomy levels where relevant.
- Never include real customer data, real operator names as the client, or credentials.
  Synthetic values only (operator: NorthStar Telecom).
- Identifiers: `BR-###`, `NFR-###`, `CQ-###`, `MAP-###`, `DQ-###`, `ADR-###`, `TC-###`,
  `REL-###`, `INC-###`, `ACT-###`, `KE-###`, `VQ-###`. Permanent, never renumbered.
- Do not restate the shared guardrails; refer to them.

## 3. Tools (exact names and classes)

| Tool | Class | Tracks | What it does |
|---|---|---|---|
| `read_artifact` | A0 | all | Read a workspace file (any folder) |
| `write_artifact` | A1 | all | Write a file, only inside the agent's `workspace` folder |
| `request_gate` | A1 | build | Ask the named approvers to approve a gate; binds to the hash of listed artifacts. The agent stops after this |
| `record_decision` | A1 | all | Append to the decision log |
| `ask_open_question` | A1 | all | Raise an open question to a named role, blocking or not |
| `list_source_metadata` | A0 | build | Systems, tables, columns, types, keys, classification, row counts (no values) |
| `profile_column` | A0 | build | Null rate, distinct count, min/max length, top patterns. Refuses raw values for Restricted columns |
| `lookup_sid` | A0 | build | TM Forum SID entity and TMF Open API for a business term |
| `lookup_glossary` | A0 | build, consume | Business glossary term, definition, steward |
| `run_sandbox_sql` | A1 | build | Read-only SELECT on the synthetic sandbox; 200-row cap; masked views only |
| `run_dq_checks` | A1 | build | Execute `DQ-###` rules on the sandbox; returns pass/fail counts |
| `estimate_platform_cost` | A0 | build | Warehouse, storage and model-serving cost estimate from inputs |
| `open_pull_request` | A2 | build | Open a PR on a feature branch (simulated Git host) |
| `register_catalog_asset` | A1 | build | Register a catalog asset in draft or candidate status |
| `publish_data_product` | A3 | build | Publish a listing; needs the G9 approval id |
| `get_alarms` | A0 | operate | Active and recent alarms (TMF642 shape) with filters |
| `get_kpis` | A0 | operate | Cell, circuit or service KPIs over a window |
| `get_topology` | A0 | operate | Topology neighbours: cell → site → router → service → enterprise account |
| `get_recent_changes` | A0 | operate | Change records and config pushes in a window |
| `search_kedb` | A0 | operate | Known-error database search |
| `get_pipeline_runs` | A0 | operate | Data pipeline and dbt run results, feed lag, freshness |
| `get_model_metrics` | A0 | operate | Model drift (PSI), precision, volume |
| `get_cost_usage` | A0 | operate | Compute, energy and licence usage vs budget |
| `propose_action` | A1 | operate | Propose a runbook action with class, blast radius, rollback, verify step; creates an approval request |
| `execute_approved_action` | A2/A3 | operate | Execute an action only with a matching, fully signed approval id (digital twin in demo) |
| `draft_message` | A1 | operate, consume | Draft a stakeholder or customer message for approval |
| `list_metrics` | A0 | consume | Certified metrics and verified questions in the semantic layer |
| `query_metric` | A0 | consume | Compute a certified metric with dimensions and filters; returns rows, SQL and lineage |
| `get_lineage` | A0 | build, consume | Column lineage for a gold object back to source |
| `propose_business_action` | A1 | consume | Propose a business action with expected value, audience and checks; creates an approval request |

## 4. Human approver role titles

Data Product Owner · Data Architect · Data Steward · Engineering Lead · QA Lead ·
Change Manager (CAB) · Security & Privacy Officer · ML Lead / Model Risk · NOC Shift Lead ·
Service Delivery Manager · Problem Manager · Campaign Manager · Customer Care Lead · Research Lead
