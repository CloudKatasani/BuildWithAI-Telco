# Authoring contract for DataCrew Telco agents and skills (v2)

Every agent is two files: a **definition** (`<track>/agents/<id>.md`) and its **skill**
(`<track>/skills/<id>/SKILL.md`). The runtime builds the agent's system prompt from the
definition body, then `telco-shared-guardrails`, `telco-domain-pack`, the agent's own skill and
the runtime contract. `tests/test_agents_and_skills.py` enforces this contract, and
`evals/cases.yaml` measures behaviour (`python -m telcocrew eval`).

Version 2 applies what the review in `docs/SKILL_TUNING_REVIEW.md` found. The principles:

1. **Only what the model does not already know.** Operator facts, thresholds, routing, formats and
   the judgment calls of this role. No general explanations of dbt, SQL, ITIL or churn.
2. **One place per rule.** A rule appears once in the skill. Rules in the shared guardrails
   (action classes, approvals, hashes, segregation of duties, PII, audit, injection) are not
   restated; a skill only adds what is specific to its role.
3. **Reasons, not volume.** State a constraint plainly with its reason ("because ..."). No
   capitals for emphasis, no stacked prohibitions. Describe what good looks like.
4. **Match freedom to fragility.** Outcomes and heuristics for judgment work (analysis, design,
   drafting). Exact, ordered steps only where order protects something: propose, wait for
   signatures, execute, verify, roll back.
5. **Close the loop.** Where a validating tool exists, the workflow runs it, reads the result
   and fixes before handover (`run_sandbox_sql`, `run_dq_checks`, `query_metric`, `get_kpis`).
6. **True to the runtime.** A skill names only tools the agent has, paths from the canonical
   artifact map, and capabilities that exist. It says "generated" for code that was written and
   "executed" only for what a tool actually ran.
7. **Degrade, do not stall.** Each input says what to do when it is missing. An agent run alone
   on a task still produces useful, labelled work.

## 1. Agent definition

Frontmatter fields are unchanged from v1: `name`, `title` (ends with " Agent"), `track`,
`phase`, `description`, `model`, `effort`, `max_action_class`, `gate`, `approvers`, `workspace`,
`skills` (shared two first), `tools`, `expects`, `produces`, `does`, `does_not`. List items that
contain a colon are quoted. `expects` and `produces` use canonical artifact paths.

Body: starts with `You are the DataCrew Telco <title>.`, then the job in one or two sentences,
a `Tool policy` block (May / May not, three lines at most each), how to start and how to finish.
10 to 22 lines. It does not repeat the skill.

## 2. Skill file

Frontmatter: `name`, `description`, `license: Proprietary`, `compatibility`, `metadata`
(`owner: datacrew-telco`, `version: "2.0.0"`, `track`, `role`, `gate`, `upstream`, `downstream`).

`description`: third person, what it produces and when to use it, at most 500 characters, built
from intent categories rather than lists of example phrases.

Body: `# DataCrew Telco <Title>` then exactly these sections, in this order:

1. `## Mission` : one or two sentences; the outcome and who relies on it.
2. `## Use when` : bullets for when to use, then a line starting `Not for:` naming the neighbouring
   agent for each excluded job.
3. `## Inputs` : table `Input | Where it comes from | If it is missing`. The third column is a
   concrete fallback: derive from a named tool, proceed and label as `assumption`, ask a named role
   with `ask_open_question` (blocking or not), or stop (only when continuing would be unsafe).
4. `## Workflow` : what to achieve, in the order that matters. Name the tool for each tool-backed
   step. Include the validate-fix loop where a validating tool exists. End with how the stage
   hands over (`request_gate`, a proposal tool, or the handoff).
5. `## Decision rules` : the judgment calls of this role, each with its reason. Role-specific
   limits live here too (there is no separate prohibition list).
6. `## Escalate to a person when` : conditions and the role to escalate to.
7. `## Outputs` : table `Artifact | Path | Content`, canonical paths, and a fenced template for
   the main artifact when its shape matters to the next agent or the approver.
8. `## Definition of done` : a checklist (`- [ ]`) of verifiable items. It covers accuracy
   (complete, traceable, nothing invented), risk (class, data exposure, reversibility) and
   handover (the next agent or approver can act without asking).
9. `## Worked example` : grounded in the synthetic estate below (real table, column, metric and
   scenario names). Shows tool calls and their results in brief. Contains one rejected option as
   a line starting `Rejected:` followed by a line starting `Why:`.
10. `## Red flags` : table `If you are about to | Do this instead`, three to six rows, only
    mistakes that are plausible for this role and costly.

70 to 125 lines. Identifiers (`BR`, `NFR`, `CQ`, `MAP`, `DQ`, `ADR`, `TC`, `REL`, `INC`, `ACT`,
`KE`, `VQ` + three or more digits or the estate's own ids) are permanent.

Terminology, used consistently: *approval request* (what a tool creates), *gate* (G0 to G9),
*approver* (a named person in a role), *workspace* (the run's artifact folders), *artifact* (a file
in the workspace), *certified metric* (in the semantic layer), *action class* (A0 to A4),
*attached context* (documents a person attached to the run).

## 3. What the runtime really provides

### Tools

| Tool | Class | Tracks | Behaviour |
|---|---|---|---|
| `read_artifact` | A0 | all | With `path`: content and hash. Without: list of artifact paths in the workspace |
| `write_artifact` | A1 | all | Writes text under the agent's own workspace folder only; other folders are refused. Personal identifiers are redacted |
| `request_gate` | A1 | build | Creates the approval request for the agent's gate, bound to the hashes of the listed artifacts (they must exist). The agent stops afterwards |
| `record_decision` | A1 | all | Appends decision, options, evidence to the decision log |
| `ask_open_question` | A1 | all | Records a question for a named role, blocking or not |
| `list_source_metadata` | A0 | build | Systems, owners, tables, row counts, ingestion pattern, columns with type, key, classification, description. No values |
| `profile_column` | A0 | build | Row count, null rate, distinct count, length range; top values only for non-Restricted columns |
| `lookup_sid` | A0 | build | SID entity and TMF Open API for a term |
| `lookup_glossary` | A0 | build, consume | Glossary term, definition, steward |
| `run_sandbox_sql` | A1 | build | One read-only SELECT on the synthetic SQLite sandbox, 200-row cap. Restricted columns come back as NULL. This is the only way to execute SQL; there is no dbt, Spark or warehouse runner |
| `run_dq_checks` | A1 | build | Executes rules of type `not_null`, `unique`, `min_value`, `allowed_values` on a table and column; returns failing row counts |
| `estimate_platform_cost` | A0 | build | Monthly cost from warehouse hours, credits per hour, storage TB, model calls; returns the arithmetic |
| `get_lineage` | A0 | build, consume | Lineage of a gold object back to sources, and whether it is complete |
| `open_pull_request` | A2 | build | Records a pull request for listed workspace files on a feature branch (simulated Git host) |
| `register_catalog_asset` | A1 | build | Adds a catalog asset in candidate status for the Data Steward |
| `publish_data_product` | A3 | build | Lists the data product; refused without the approved G9 approval id |
| `get_alarms` | A0 | operate | Alarms (TMF642 shape) for the session's scenario; optional element filter |
| `get_kpis` | A0 | operate | KPI snapshots for a cluster, router or neighbour around the incident |
| `get_topology` | A0 | operate | Cell to site to router to service to enterprise account |
| `get_recent_changes` | A0 | operate | Change records and config pushes for the scenario |
| `search_kedb` | A0 | operate | Known-error entries matching keywords |
| `get_pipeline_runs` | A0 | operate | Feed lag, dbt run status, SLA forecast |
| `get_model_metrics` | A0 | operate | PSI per feature and precision by segment |
| `get_cost_usage` | A0 | operate | Spend vs budget per item |
| `propose_action` | A1 | operate | Creates an approval request for one runbook action (class A2 or A3, steps, blast radius, rollback, verify, approvers). A4 content is refused |
| `execute_approved_action` | A2/A3 | operate | Runs one fully signed action on the digital twin and returns its verification result. Refused without a signed approval |
| `draft_message` | A1 | operate, consume | Saves a message draft and creates its approval request for the named roles. Nothing is sent |
| `list_metrics` | A0 | consume | Certified metrics, their dimensions and verified questions |
| `query_metric` | A0 | consume | A certified metric by allowed dimensions and filters; returns rows, SQL, lineage, freshness; groups under 10 subscribers suppressed |
| `propose_business_action` | A1 | consume | Creates an approval request; approvers are set by `action_type` (`retention_offer`, `care_credit`, `rebill`, `network_change`, `enterprise_ticket`). Nothing is executed |

Not available to any agent: running dbt, GoldenGate, Kafka or a warehouse; a real Git host,
ticketing system, catalog, marketplace, NOC tooling or messaging channel. Generated code and
configuration are artifacts for people and client pipelines to run after the gates.

### Canonical artifact map

| Agent | Primary artifacts |
|---|---|
| build-orchestrator | `00-intake/brief.md` |
| build-business-analyst | `01-requirements/requirements.md` |
| build-source-mapping | `02-mapping/source-inventory.csv`, `02-mapping/mapping.md` |
| build-solution-architect | `03-design/design.md` (logical, physical, ADRs, cost, work packages) |
| build-data-engineer | `04-build/models/<model>.sql`, `04-build/models/<model>.yml`, `04-build/ingest/<feed>.yaml`, `04-build/sandbox-run.json` |
| build-quality-engineer | `05-test/evidence.md` |
| build-ml-engineer | `06-ml/model-card.md` |
| build-release-engineer | `07-release/release-plan.md` |
| build-semantic-context | `08-semantic/semantic-view.md` |
| build-data-product-publisher | `09-publish/contract.odcs.yaml`, `09-publish/listing.yaml`, `09-publish/operate-pack.yaml` |
| build-governance-lineage | `control/governance/lineage-completeness.md`, `control/governance/catalog-candidates.jsonl` |
| operate-watch-desk | `ops/watch/events.md` |
| operate-triage-correlation | `ops/triage/incident.md` |
| operate-diagnosis-rca | `ops/diagnosis/rca.md` |
| operate-resolution | `ops/resolution/action-plan.md`, `ops/resolution/execution.md` |
| operate-sla-batch-guard | `ops/sla/forecast.md` |
| operate-comms | `ops/comms/message-<approval id>.md` (written by `draft_message`) |
| operate-problem-knowledge | `ops/problem/<KE id>-update.md` |
| operate-finops-capacity | `ops/finops/cost-report.md` |
| operate-service-reporting | `ops/reporting/service-report.md` |
| consume-ask-your-data | none (returns the answer; action class A0) |
| consume-insight-scout | `consume/insights/weekly.md` |
| consume-next-best-action | `consume/actions/proposal.md` |
| consume-care-copilot | `consume/care/case-brief.md` |
| consume-enterprise-account | `consume/accounts/account-brief.md` |
| consume-exec-briefing | `consume/briefings/week-<nn>.md` |

Operate and Consume runs usually start in a fresh workspace, so Build artifacts such as
`09-publish/operate-pack.yaml` are optional inputs there; the tools are the source of truth.
Operating notes (freeze windows, autonomy level, notification thresholds, approval matrix) and
team standards arrive as attached context when a scenario provides them.

### Synthetic estate (use these names in examples)

- Sources: `crm_customer` (customer_id, msisdn R, full_name R, date_of_birth R, region, segment,
  consent_marketing, created_date), `billing_account` (account_id, customer_id, tariff_code,
  monthly_fee, status), `billing_invoice` (invoice_id, account_id, bill_month, total_amount),
  `xdr_daily` (subscriber_key, day, data_mb, voice_min, dropped_calls, cell_id R), `care_ticket`
  (ticket_id, customer_id, opened_at, category, status), `pm_cell_kpi` (cell_id, hour_ts, prb_util,
  dcr, users, kwh), `inventory_cell` (cell_id, site_id, cluster, router_id, emergency_coverage).
  R = Restricted.
- Gold: `gld_churn_risk` (subscriber_key, region, value_segment, arpu, risk_score, top_driver,
  churned_30d), `gld_cell_energy_daily` (cell_id, cluster, idle_night_kwh, sleep_candidate),
  `gld_recon_daily` (month, leak_point, leakage_eur), `gld_account_sla` (account,
  availability_mtd, sla_target, credit_exposure_eur, breach_forecast).
- Regions: North-East, Metro-North, Coastal, Capital, Industrial-South. Segments: High, Mid, Low.
  Tariffs: UL-25, PLUS-35, MAX-55, BASIC-15.
- Certified metrics: `churn_at_risk_lines`, `at_risk_arpu`, `churn_rate_30d` (dims region,
  value_segment, top_driver), `idle_night_kwh`, `sleep_candidate_cells` (cluster), `leakage_eur`
  (month, leak_point), `sla_credit_exposure_eur`, `accounts_breach_forecast` (account).
- Operate scenarios: `noc` (INC-90311: DCR 3.7% on 14 cells of cluster MN-07 from 18:40, change
  CR-48213 handover offset +3 dB pushed 18:31, router MN-AGG-2 flaps, KE-2207, one care alarm
  carries an embedded instruction), `dataops` (mediation feed lag 118 min, dbt model
  `slv_subscriber_month` fails after RN-772 renamed `plan_code` to `tariff_code`, KE-1189, mart SLA
  06:00), `mlops` (churn_gbm v7 PSI 0.31 on data_throughput_p10 after tariff UL-25 launch, precision
  0.41 on migrated lines vs 0.77, KE-3011).

## 4. Human approver role titles

Data Product Owner · Data Architect · Data Steward · Engineering Lead · QA Lead ·
Change Manager (CAB) · Security & Privacy Officer · ML Lead / Model Risk · NOC Shift Lead ·
Service Delivery Manager · Problem Manager · Campaign Manager · Customer Care Lead · Research Lead
