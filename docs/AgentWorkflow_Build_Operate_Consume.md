# DataCrew Telco: Agent Workflow for Build, Operate and Consume with AI

| | |
|---|---|
| Version | 0.1 (demo design) |
| Date | 2026-11-16 |
| Extends | `UTIL_BuildWithAI_Spec.md` (ADEF agent team, gates, action classes) to the telco industry |
| Demo | `demo/index.html` |

One agent workforce in three planes. Agents do the repeatable engineering, operations and
analysis work. Named people approve every step that changes something. The three planes feed
each other:

```
Business ask ─▶ [BUILD] ──Operate pack──▶ [OPERATE] ──certified data──▶ [CONSUME]
                   ▲                         ▲                              │
                   │                         └──── actions become changes ──┤
                   └──────────── new questions become Build requests ───────┘
```

## 1. Shared controls (all planes)

| Class | Name | What the agent may do | Approval |
|---|---|---|---|
| A0 | Observe | Read metadata, logs, metrics | None |
| A1 | Draft | Drafts, feature-branch code, sandbox runs | Reviewed at the next gate |
| A2 | Reversible | Low-risk reversible change, bounded scope | 1 named approver |
| A3 | Production | Production change, publication, customer message | 2 approvers + change record |
| A4 | Irreversible | Deletes, access grants, spend, external disclosure | Never by an agent; a person executes |

Rules:

1. Agents never sign a gate. Each gate lists the roles that must sign; one person cannot hold
   two roles on the same gate (segregation of duties).
2. An approval is bound to the hash of the evidence it covers. Any change creates a new
   version that needs new signatures.
3. Reviewers can approve, request changes (the agent revises and re-raises; return limit 3,
   then escalation to the Data Product Owner) or reject (the run stops; nothing is deployed).
4. Every event goes to a hash-chained audit log (SHA-256 in production).
5. Agents read business rows only within row caps, through masked views, or as synthetic data.

## 2. Build with AI

| # | Agent | Produces | Gate | Approvers |
|---|---|---|---|---|
| 0 | Delivery Orchestrator | Intake brief, plan, delivery pack | G0 Intake | Data Product Owner |
| 1 | Business Analyst | BR-###, NFR-###, consumer questions CQ-### | G1 Requirements | Data Product Owner + Data Steward |
| 2 | Source Mapping Analyst | Source inventory, TM Forum SID mapping, classification, DQ rules, ingestion pattern | G2 Mapping | Data Steward + Security & Privacy |
| 3 | Solution Architect | Medallion design, product boundary, ADRs, cost | G3 Design | Data Architect |
| 4 | Data Engineer | Ingest configs (GoldenGate / framework / streaming), dbt project, tests, PR | G4 Merge | Engineering Lead |
| 5 | Quality Engineer | Hop reconciliation, CDC tests, idempotency, masking evidence | G5 Quality | QA Lead |
| 6 | ML Engineer | Features, model, model card, bias test | G6 Model risk | ML Lead + Security & Privacy |
| 7 | Release Engineer | Release bundle, rollback rehearsal, change request | G7 Release | Change Manager + Engineering Lead |
| 8 | Semantic & AI Context | Semantic view, verified questions, AI context, eval report | G8 Certification | Data Steward + Data Product Owner |
| 9 | Data Product Publisher | ODCS contract, listings, Operate onboarding pack | G9 Publish | Data Product Owner + Data Steward |
| X | Governance & Lineage | Catalog assets, glossary drafts, lineage completeness | Evidence at G2, G3, G7, G9 | Data Steward |

Demo use cases: Subscriber Churn 360, RAN Energy Savings, Revenue Assurance usage-to-bill,
Enterprise SLA 360, SIM-box / IRSF fraud signals.

## 3. Operate with AI

| Agent | Does | Max class |
|---|---|---|
| Watch Desk | Watches network, platform and model signals | A0 |
| Triage & Correlation | Groups alarms into incidents; scores customer and revenue impact | A0 |
| Diagnosis (RCA) | Tests hypotheses against topology, changes, KEDB | A0 |
| Resolution | Proposes runbook actions with blast radius, rollback, verification; executes only after approval | A2 / A3 |
| SLA & Batch Guard | Forecasts SLA breaches for jobs and enterprise circuits | A0 |
| Comms | Drafts stakeholder and customer updates | A1 |
| Problem & Knowledge | Writes known-error entries and runbook updates | A1 |
| FinOps & Capacity | Tracks compute, energy and licence cost | A0 |
| Service Reporting | MTTD, MTTR, autonomy metrics, service review | A0 |

Human decisions: action plan (NOC Shift Lead / Service Delivery Manager; plus Change Manager
for A3), stakeholder message (Service Delivery Manager), known-error entry (Problem Manager),
model promotion (ML Lead + Data Product Owner). Autonomy is tracked per scenario on the TM
Forum L0–L5 scale and raised only after validated runs.

Demo scenarios: RAN cluster degradation after a parameter change (Network NOC), churn mart SLA
breach from an upstream schema rename (Data Platform AMS), churn model drift after a tariff
launch (MLOps).

## 4. Consume with AI

| Agent | Does | Max class |
|---|---|---|
| Ask-Your-Data | Answers through the certified semantic layer only; shows SQL and lineage | A0 |
| Insight Scout | Finds anomalies and drivers | A0 |
| Next-Best-Action | Turns an insight into an action proposal with expected value | A2 (proposal) |
| Care Copilot | Case summaries and suggested replies with masked data | A1 |
| Enterprise Account Agent | SLA reviews and renewal risk briefs | A1 |
| Exec Briefing | Weekly steering brief across domains | A0 |

Guardrails: refuses personal identifiers, out-of-scope questions and system changes.
Unanswerable questions become candidate consumer questions for the next Build intake. Actions
go to named approvers (for example a retention offer needs the Campaign Manager and the
Security & Privacy Officer; a cell-sleep pilot becomes an Operate change for the NOC Shift Lead
and Change Manager).

## 5. Human roles

| Role | Team | Decides |
|---|---|---|
| Data Product Owner | Business | G0, G1, G8, G9; model promotion |
| Data Architect | Dev | G3 |
| Data Steward | Governance | G1, G2, G8, G9 |
| Engineering Lead | Dev | G4, G7; hotfix PRs |
| QA Lead | Dev | G5 |
| Change Manager (CAB) | Managed Services | G7; all A3 production actions |
| Security & Privacy Officer | Risk | G2, G6; customer-data actions |
| ML Lead / Model Risk | AI | G6; retrain and promotion |
| NOC Shift Lead | Managed Services | Network actions (A2/A3) |
| Service Delivery Manager | Managed Services | A2 platform actions; stakeholder comms |
| Problem Manager | Managed Services | Known-error entries |
| Campaign Manager | Business | Retention and marketing actions |
| Customer Care Lead | Business | Proactive care actions |
| Research Lead | Research | Experiment charters; graduation into Build |

## 6. Team enablement

| Team | What changes | Owns | Measures |
|---|---|---|---|
| Dev & Data Engineering | From writing pipelines to reviewing agent PRs against an approved design | G3, G4, G5, G7 | Lead time, PR first-pass rate, defects after G5 |
| Managed Services (AMS / NOC) | From reading alarms to approving ranked, evidenced actions with rollback | A2/A3 actions, comms, KEDB | MTTD/MTTR, alarm compression, accepted fixes, repeat incidents |
| AI & ML Engineering | From one model at a time to a governed model factory on certified data | G6, G8, promotion | Data-to-shadow time, eval pass rate, drift-to-retrain time |
| Research & Innovation | From one-off notebooks to experiments that graduate through the same gates | Charters, graduation at G1, telco benchmarks | Experiments graduated, idea-to-prototype time |

90-day path for each team: shadow mode with people running every gate (days 1–30), two domains
or scenarios in parallel with one-click A2 approvals (31–60), agents own the repeatable work by
default and autonomy is raised for validated scenarios only (61–90).
