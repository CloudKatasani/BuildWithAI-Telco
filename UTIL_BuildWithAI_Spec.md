# DataCrew BuildWithAI, Utilities Edition: Build Specification

| | |
|---|---|
| Version | 0.1 (draft for architecture review) |
| Date | 2026-11-15 |
| Prepared by | Durga Prasad Katasani, Sr Architect, Snowflake SME |
| Based on | `Agentic-Data-Engineering-Framework-BuildWithAI` (ADEF, build spec v2.0, skills v1.2.0) and `Agentic-Data-Engineering-Framework-OperateWithAI` |
| Companion | `UTIL_OperateWithAI_Spec.md` (phase 2), `UTIL_BuildWithAI_Demo.html` (demo) |

This specification says how to bind the existing BuildWithAI agent team to one utility client's
data path and what must be added so the agents can take a business request all the way to a
published, AI-ready data product:

```
IBM Db2 / Oracle ─▶ Oracle GoldenGate (CDC) ─────────┐
                 └▶ Python integration framework ────┤
                                                     ▼
                         AWS data lake: S3 + Apache Iceberg + Glue Data Catalog
                                                     ▼
                Snowflake: BRONZE ─▶ SILVER ─▶ GOLD   (dbt Core, medallion)
                                                     ▼
                     AI context + semantic layer (semantic views, search, agent)
                                                     ▼
                         Domain data product (contract, share, listing)
                                                     ▼
          Snowflake Internal Marketplace  +  other marketplaces (Collibra, others)

          Collibra: catalog, glossary, classification and lineage across every hop
```

It is written as a delta on the repository: section 2 says what is reused unchanged, and the
rest says what to add. A coding agent or engineer can build from sections 4 to 13.

---

## START HERE FIRST: decisions needed before build starts

These cannot be answered from the two repositories. Each has a default the spec assumes; a
wrong default changes the named section.

| # | Decision | Default assumed | Changes |
|---|---|---|---|
| D1 | Db2 platform: z/OS, LUW or both | Db2 for z/OS (mainframe) for CIS; Oracle for MDM and the EDW | 5.1, 10 (Collibra scans Db2 LUW only) |
| D2 | GoldenGate topology and version | GoldenGate Microservices at the source, GoldenGate for Distributed Applications and Analytics (DAA) writing Iceberg to S3 with the Glue catalog | 5.1, 9.1 |
| D3 | What the Python integration framework is | Client-owned, metadata-driven (one config per feed), runs on AWS, writes Iceberg through the Glue catalog | 5.2, 9.2. The adapter can only be written after its config schema is shared |
| D4 | Where bronze lives | Lake Iceberg tables stay in Glue; Snowflake reads them through a catalog-linked database; `BRONZE` schema holds thin views | 6, 9.3, ADR-001 |
| D5 | Silver and gold table type | Snowflake native tables in the domain database | 9.4, ADR-002 |
| D6 | How dbt Core is executed | dbt Core project in Git, deployed and run as a dbt Project object on Snowflake, scheduled by the client scheduler | 9.4, ADR-003 |
| D7 | Orchestrator, Git host, CI, ITSM | Not stated by the client. Profile leaves them as `to-confirm` | 4 |
| D8 | "Any other marketplace" | Collibra Data Marketplace as the second target, behind a marketplace adapter so more can be added | 9.6 |
| D9 | First slice | Meter-to-cash billed consumption (Customer domain), because the repository already ships its synthetic Db2 and Oracle data | 14 |
| D10 | Named approvers for the seven roles | Seats only until the client names people | 8 |
| D11 | Approved model providers | Client decision. Demo runs on the simulator | 11 |

---

## 1. Goal and scope

**Goal.** Show the client that an approval-gated agent team can shorten the build of a domain
data product on their stack, from request to marketplace listing, without weakening control:
people still decide every gate, and every artifact is traceable to a requirement.

**In scope (BuildWithAI, phase 1)**

- One run delivers one thin slice: one data product, its sources, pipelines, tests, semantic
  layer, AI context, contract, listing, catalog entries and lineage.
- Code generation for every hop of the client path in section 3.
- Dev sandbox execution with synthetic data. Promotion to shared and production
  environments through the client's own CI and change process, after gates G6a and G6b.
- A demo edition that runs without client access (simulator plus the local lakehouse).

**Out of scope for phase 1**

- Agents with write access to production. Production is observe-only (`agent_max_class: A0`).
- Reading business rows from Db2 or Oracle. Agents use metadata, profiles within the row
  cap, and synthetic data.
- Run operations. Stage 7 produces the handover pack that OperateWithAI consumes (phase 2).
- Decommissioning Informatica jobs. The run can list the jobs a slice replaces; retiring
  them is a client change.

---

## 2. What was reviewed and what it means

### 2.1 BuildWithAI repository

| Finding | Use for this client |
|---|---|
| Nine agents (one coordinator, eight stage owners), gates G0 to G8, seven approver roles, handoff envelopes, one writer per stage folder | Reuse unchanged for stages 0 to 7 |
| 24 capability slots, Stack Profiles, Domain Packs; logical artifacts stay vendor-neutral | Reuse. Five slots are added (section 4.2) |
| Enforcement in code: action classes A0 to A4, hash-bound approvals, scanners, hash-chained logs, 18 guardrail scenarios, segregation of duties | Reuse unchanged |
| Council of three reviewers, context packs per stage, document or code output per stage | Reuse unchanged |
| Reference path is "source database, Spark JDBC or DMS ingest, Spark SQL curate in the lake, publish to the analytics engine" | **Gap.** The client replicates with GoldenGate and a Python framework, and curates **inside Snowflake with dbt Core**, not in Spark. New adapters, section 9 |
| `ingestion` is a single slot | **Gap.** The client has two ingestion paths chosen per table. Split into `cdc_replication` and `batch_ingestion` |
| Stage 8 (`adef-data-consumption`) ends at a semantic model for BI and a catalog entry | **Gap.** The client's path continues to AI context, a data product contract and marketplace listings. Stage 8 is split in two (sections 7.9, 7.10) |
| Catalog and lineage are 16 export files written at final assembly | **Gap.** Collibra is the client's system of record and lineage must be stitched across six hops. A dedicated agent owns it (section 7.11) |
| Utilities Domain Pack is a starter (`status: starter-needs-client-review`), with a meter-to-cash demo pack on Db2 and Oracle | Extend (section 5.3). Use the demo pack for the first slice |
| Built-in code templates are flagged until a reviewed adapter exists; cloud pipelines are generated, not executed | Same honest limit applies here. Section 12 lists the adapters to review |

### 2.2 OperateWithAI repository

Nine operations agents (Watch Desk, Triage, Diagnosis, Resolution, Batch and SLA, Comms,
Service Request, Problem and Knowledge, Service Reporting) working from four knowledge files
(`environment.yaml`, `signals.yaml`, `kedb.yaml`, `actions.yaml`). Its demo estate already
includes Oracle, Db2, GoldenGate, Snowflake and dbt. What matters for phase 1: **Build must
emit the inputs Operate needs.** Stage 7 therefore writes its outputs in those four file
formats (section 7.8), so a data product built by this team can be onboarded to Operate
without re-keying.

---

## 3. Target data path and where the agents generate code

| Hop | From | To | Client technology | Generated by Build (stage 4) |
|---|---|---|---|---|
| H1a | Db2, Oracle tables with change capture | Lake raw Iceberg tables | GoldenGate Extract, trail, Distribution Service, DAA Replicat with the Iceberg handler, Glue catalog, S3 | Extract and Replicat parameter files, handler properties, table list, supplemental logging and key checks, initial-load plan |
| H1b | Db2, Oracle bulk or reference tables; files; APIs | Lake raw Iceberg tables | Python integration framework | One feed config per source object, watermark and reconciliation settings, unit tests |
| H2 | Glue Iceberg tables | Snowflake `BRONZE` | Catalog integration (Glue Iceberg REST), external volume, catalog-linked database, bronze views | Integration and database DDL, bronze views, freshness checks |
| H3 | `BRONZE` | `SILVER`, `GOLD` | dbt Core | dbt project: sources, staging, snapshots, conformed models, marts, tests, docs, exposures |
| H4 | `GOLD` | `SEMANTIC`, `CONTEXT`, `AGENTS` | Semantic views, search service, agent | Semantic view DDL, verified questions, context corpus load, agent definition, evaluation set |
| H5 | Domain objects | Consumers | Secure share, organizational listing, Collibra | Share and listing manifest, contract (ODCS), access request flow, marketplace entries |
| X | Every hop | Collibra | Collibra Edge, catalog and lineage | Asset import files, custom technical lineage for the hops Collibra cannot scan |

**Ingestion pattern rule (decided per table at G3, recorded in `ingestion-pattern.csv`).**

| Use GoldenGate when | Use the Python framework when |
|---|---|
| The table changes during the day and consumers need it within minutes to an hour | The table is loaded once a day or less often |
| Deletes and updates must be captured exactly (billing, account, asset state) | Source is a file, an API, or a query result rather than a logged table |
| The table has a primary key or agreed key columns | The table has no usable key and is small enough to reload |
| Log-based capture is permitted on the source | Log access is not granted, or the source is a reporting replica |

A table without a primary key and without agreed key columns is a blocking open question
for H1a: Iceberg replication needs a key to apply updates and deletes.

---

## 4. Stack Profile

### 4.1 Profile file

Save as `skills/adef-stack-binding/assets/stack-profile.utility-gg-iceberg-snowflake.yaml`
and copy into each run's `control/stack-profile.yaml`. No secrets in this file.

```yaml
profile_id: utility-gg-iceberg-snowflake
profile_version: "0.1.0"
portability_required: false

variables:
  org_prefix: "util"            # replace with the client's prefix
  domain: "customer"            # one run, one domain
  aws_region: "to-confirm"
  glue_database_pattern: "${org_prefix}_${domain}_raw"
  snowflake_domain_db: "${env}_${domain}"       # one database per domain
  snowflake_lake_db: "${env}_LAKE_${domain}"    # catalog-linked database (ADR-001)

environments:
  dev:  { purpose: sandbox,    agent_max_class: A1, secrets_ref: "secrets/adef/dev" }
  test: { purpose: shared,     agent_max_class: A2, secrets_ref: "secrets/adef/test" }
  prod: { purpose: production, agent_max_class: A0, secrets_ref: "secrets/adef/prod" }

slots:
  source_database:
    - { tool: db2,    variant: "zos (to-confirm D1)", role: "CIS and other mainframe systems" }
    - { tool: oracle, version: "to-confirm",          role: "MDM, EDW" }
  cloud:              { tool: aws }
  object_storage:     { tool: s3 }
  table_format:       { tool: iceberg, version: "2" }
  lake_catalog:       { tool: aws-glue-catalog, access: iceberg-rest }
  cdc_replication:    { tool: oracle-goldengate, target_handler: iceberg, version: "to-confirm D2" }   # new slot
  batch_ingestion:    { tool: client-python-framework, version: "to-confirm D3" }                      # new slot
  ingestion:          { tool: none, reason: "split into cdc_replication and batch_ingestion" }
  lakehouse_compute:  { tool: none, reason: "curation runs in the analytics engine, not in the lake" }
  transformation:     { tool: dbt-core, version: "pin at G0", runtime: "dbt-project-on-snowflake (ADR-003)" }
  compute_engine:     { tool: snowflake }
  orchestration:      { tool: to-confirm, options: [airflow, control-m, snowflake-tasks] }
  data_quality:       { tool: dbt-tests, extras: [dbt-expectations-if-approved] }
  catalog_governance: { tool: collibra, connectivity: edge }
  lineage:            { tool: collibra, method: "edge scanners + custom technical lineage" }
  virtualization:     { tool: none, reason: "not in the stated path; add if Denodo is in scope" }
  semantic_layer:     { tool: snowflake-semantic-views }
  ai_context:         { tool: snowflake-cortex, parts: [search-service, verified-questions, agent-instructions] }  # new slot
  ai_consumption:     { tool: snowflake-cortex-agents }
  data_contract:      { tool: odcs, version: "3" }                                                   # new slot
  marketplace:                                                                                       # new slot, list
    - { tool: snowflake-internal-marketplace, kind: organizational-listing, primary: true }
    - { tool: collibra-data-marketplace }
  bi:                 { tool: to-confirm, note: "Power BI and Cognos exist at the client; BI is not in this slice" }
  version_control:    { tool: to-confirm }
  cicd:               { tool: to-confirm }
  iac:                { tool: terraform, note: "to-confirm" }
  secrets:            { tool: aws-secrets-manager }
  observability:      { tool: platform-native }
  itsm:               { tool: servicenow, note: "to-confirm" }
  approval_channel:   { tool: adef-console }

limits:
  max_compute_size: "S"
  auto_suspend_seconds: 60
  query_timeout_seconds: 120
  profiling_row_cap: 10000
  monthly_cost_cap: 0            # 0 = every paid action needs approval

standards:
  layers: [bronze, silver, gold, semantic, context, agents]
  database_per: domain
  schema_per: layer
  naming_case: upper_snake
  lake_identifier_case: lower    # Glue identifiers are lower case
  history_default: type-2
  timezone: UTC
  branch_strategy: trunk-with-feature-branches
  protected_branches: [main]
  cross_domain_access: denied    # see UTL-C5
```

`lakehouse_compute` and `ingestion` are required slots in the repository. Binding them to
`none` needs the slot-rule change in 4.2, otherwise stack validation fails at G0.

### 4.2 Changes to `capability-slots.md` (Data Architect approval needed, per the slot rules)

| Slot | Required | Job to be done | Used by |
|---|---|---|---|
| `cdc_replication` | no | Log-based change capture from the source database into lake raw tables | design, build, test, operations |
| `batch_ingestion` | no | Scheduled extract of tables, files and APIs into lake raw tables | design, build, test, operations |
| `ai_context` | no | Business context an AI assistant needs beyond the semantic model: definitions, documents, verified questions, instructions | semantic-context |
| `data_contract` | no | Machine-readable contract of a data product | design, data-product-publish |
| `marketplace` | no (list) | Where data products are listed for discovery and access requests | data-product-publish |

Rule changes: `ingestion` is satisfied when `cdc_replication` or `batch_ingestion` is bound.
`lakehouse_compute` becomes not required when `transformation` runs on `compute_engine`.
Stack validation (T1) must check both.

---

## 5. Source, lake and domain bindings

### 5.1 GoldenGate path (H1a)

```
Db2 / Oracle ─ Extract ─ trail ─ Distribution Service ─▶ DAA Replicat (Iceberg handler)
                                                              │ writes data + metadata files
                                                              ▼
                                           s3://<lake-bucket>/<domain>/raw/<source>/<table>/
                                                              │ registers and commits
                                                              ▼
                                           Glue database  <org>_<domain>_raw
```

Design points the Data Architect Agent must settle in ADRs, because they change silver:

| Topic | Options | Default proposed |
|---|---|---|
| Apply mode in raw | (a) Mirror: the handler applies inserts, updates and deletes, raw holds current state. (b) Change log: every operation is appended with operation type, commit timestamp and log position | (b) for tables that need history or audit; (a) for reference tables. Confirm handler support for (b) in adapter review |
| Initial load | GoldenGate initial load, or a one-time Python framework bulk load followed by CDC from a recorded log position | Python bulk load plus CDC start position, with a count and checksum reconciliation |
| Schema change at source | Handler evolves the Iceberg schema; bronze view and dbt source must follow | Additive changes flow and raise a notice; breaking changes stop the replicat and open a change request |
| Small files | Many small commits from continuous replication | Commit interval set per table; scheduled compaction and snapshot expiry as generated lake maintenance jobs |
| Keys | Iceberg apply needs a primary key or key columns | Blocking question per keyless table |

Type mapping the adapter must carry (the agent proposes, the Data Steward approves at G2):

| Source | Lake (Iceberg) | Snowflake | Watch for |
|---|---|---|---|
| Db2 `CHAR`, `VARCHAR` (EBCDIC) | `string` | `VARCHAR` | Code page conversion happens in replication; trailing blanks in `CHAR` |
| Db2 `DECIMAL(p,s)` | `decimal(p,s)` | `NUMBER(p,s)` | Keep precision and scale exactly; never widen to float |
| Db2 `TIMESTAMP(12)` | `timestamp` (microseconds) | `TIMESTAMP_NTZ(6)` | Fractional seconds beyond 6 digits are lost: record as a known difference |
| Db2 `CHAR FOR BIT DATA`, `GRAPHIC` | `binary`, `string` | `BINARY`, `VARCHAR` | Needs a rule per column |
| Oracle `NUMBER` (no precision) | `decimal(38,s)` | `NUMBER(38,s)` | Scale must be decided per column from profiling |
| Oracle `DATE` | `timestamp` | `TIMESTAMP_NTZ` | Oracle `DATE` carries a time part |
| Oracle `TIMESTAMP WITH TIME ZONE` | `timestamptz` | `TIMESTAMP_TZ` | Standardise to UTC in silver |

### 5.2 Python integration framework path (H1b)

The agents do not write new Python pipelines. They write **configuration for the client's
existing framework** and the tests around it. Until the framework's config schema is shared
(D3), the adapter uses this neutral feed contract, which is then mapped to the real schema:

```yaml
feed_id: cis_rate_class_ref
source: { system: cis, object: CIS.RATE_CLASS, connection_ref: "secrets/adef/${env}/cis-db2" }
extract: { mode: incremental, watermark_column: LAST_UPDATED_TS, lookback_minutes: 30 }
target:  { glue_database: "${glue_database_pattern}", table: cis_rate_class, format: iceberg, write: merge, keys: [RATE_CLASS] }
schedule: { cron: "0 2 * * *", timezone: UTC }
controls: { reconcile: [row_count, sum:RATE_PER_KWH], on_mismatch: fail, max_runtime_minutes: 30 }
lineage:  { map_ids: [MAP-031, MAP-032] }
```

### 5.3 Utilities Domain Pack extension

Extend `domain-pack.utilities.yaml` to version 0.2.0. Additions only; the four existing
controls stay.

```yaml
domains:                       # data product ownership boundaries
  - { id: generation,   owner_role: "Generation Data Owner" }
  - { id: transmission, owner_role: "Transmission Data Owner" }
  - { id: distribution, owner_role: "Distribution Data Owner" }
  - { id: customer,     owner_role: "Customer Data Owner" }

controls_added:
  - id: UTL-C5
    text: "No cross-domain access. A role of one domain cannot read another domain's database; sharing between domains happens only through a published listing with an approved access request."
  - id: UTL-C6
    text: "Change data from a system of record is retained in the lake in a form that can reproduce the state of a regulatory dataset at a past date."
  - id: UTL-C7
    text: "An AI assistant answers only from certified semantic objects of the data product and shows which metric definition it used."
  - id: UTL-C8
    text: "A data product is listed only with a contract, an owner, a classification, quality results and lineage to the system of record."
```

The pack remains a starter. Security and Compliance confirm the controls against the
client's own obligations (critical-infrastructure protection, energy regulator reporting,
privacy law) before first use.

---

## 6. Snowflake layout

One production account. One database per domain. Layers are schemas. No database per data
product or per layer.

```
<ENV>_CUSTOMER                      domain database
  ├─ BRONZE     views over the lake tables (typed, upper-case names, no logic)
  ├─ SILVER     conformed, deduplicated, history kept (dbt)
  ├─ GOLD       dimensional and data-product tables (dbt)
  ├─ SEMANTIC   semantic views, one per data product
  ├─ CONTEXT    glossary, definitions, document chunks, verified questions, search service
  └─ AGENTS     agent objects and their evaluation results
<ENV>_LAKE_CUSTOMER                 catalog-linked database on the domain's Glue database (read-only to dbt)
```

**ADR-001 (needs a decision).** A catalog-linked database is itself a database, so the lake
layer cannot be a schema of the domain database. Proposal: keep it as a companion database
that only the domain's transformation role can read, and expose it through `BRONZE` views.
This keeps "one database per domain, schema per layer" true for everything people and
agents consume, and hides the lower-case quoted identifiers that Glue requires.

**Roles (generated as code, applied only by the release pipeline after approval).**

| Role | Can |
|---|---|
| `<DOMAIN>_TRANSFORM` | Read lake database and `BRONZE`; write `SILVER`, `GOLD` (dbt service identity) |
| `<DOMAIN>_SEMANTIC_ENG` | Read `GOLD`; write `SEMANTIC`, `CONTEXT`, `AGENTS` |
| `<DOMAIN>_PRODUCT_OWNER` | Own the share and listing; approve access requests |
| `<DOMAIN>_CONSUMER_<PRODUCT>` | Read the listed objects only; granted through the listing |
| `ADEF_AGENT_DEV` | Dev sandbox only. No grant in test or production |

Every grant is an A3 action: its own approval by Security and Compliance with a before and
after access diff, even inside an approved gate.

---

## 7. The agent team

Eleven agents: the coordinator and seven stage owners from the repository unchanged in
role, stage 8 split in two, and one new governance agent that works alongside every stage.

| # | Agent (identifier) | Role title | Phase | Produces | Gate |
|---|---|---|---|---|---|
| 0 | `adef-orchestrator` | Service Delivery Lead Agent | Plan | Intake brief, stack validation, routing, delivery pack | G0 |
| 1 | `adef-intent-requirements` | Business Analyst Agent | Plan | Requirements, business rules, consumer questions | G1 |
| 2 | `adef-source-target-mapping` | Data Mapping Analyst Agent | Design | Source inventory, mapping, quality rules, classification, ingestion pattern proposal | G2 |
| 3 | `adef-solution-design` | Data Architect Agent | Design | Logical model, medallion physical design, data product boundary, ADRs, cost | G3 |
| 4 | `adef-pipeline-build` | Data Engineer Agent | Build | Code base for hops H1 to H3 on a feature branch | G4 |
| 5 | `adef-test-quality` | Quality Engineer Agent | Assure | Executed tests, reconciliation across hops, evidence pack | G5 |
| 6 | `adef-release-deploy` | Release Engineer Agent | Transition | Release scripts as code, rollback rehearsal | G6a, G6b |
| 7 | `adef-operations-observability` | Service Operations Agent | Run | Monitors, runbook, Operate onboarding pack | G7 |
| 8 | `adef-semantic-context` **(new)** | AI Context and Semantic Engineer Agent | Enable | Semantic view, AI context, agent, evaluation results | G8 |
| 9 | `adef-data-product-publish` **(new)** | Data Product Manager Agent | Enable | Contract, share, listings, consumer guide | G9 |
| X | `adef-catalog-lineage` **(new)** | Governance and Lineage Agent | All | Collibra assets, classification sync, stitched lineage | Evidence at G2, G3, G6b, G9 |

`adef-data-consumption` is retired for this profile; its duties move to agents 8 and 9. Its
skill text is the starting point for both new skills. BI semantic models (Power BI) can be
added to agent 8 later as another `semantic_layer` binding.

Every new agent gets a definition in `agents/` and a skill in `skills/` with the same
sections, in the same order, as the existing stage skills (Mission through Common failure
modes), and loads `adef-shared-guardrails` first. `tests/test_skills.py` must pass.

Below, "stack specifics" lists only what this client's stack adds to the existing skill.

### 7.1 `adef-orchestrator`: no change in role

Stack specifics: validates the profile in section 4, including the two-path ingestion rule;
refuses G0 while any required slot is `to-confirm`; records D1 to D11 answers in
`00-intake/decisions.md`.

### 7.2 `adef-intent-requirements`: no change in role

Stack specifics: Domain Pack controls UTL-C1 to C8 become `NFR-###`. Captures **consumer
questions** (`CQ-###`) in business language, because stage 8 is tested against them. Records
freshness need per entity, which later drives the ingestion pattern.

### 7.3 `adef-source-target-mapping`

Stack specifics:

- Reads source metadata only: Db2 catalog (`SYSIBM` or `SYSCAT` views), Oracle dictionary
  views, the Collibra export for the systems in scope, and copybooks or DCLGENs where the
  Db2 catalog lacks descriptions.
- Proposes, per source table: key columns, change-capture readiness (logging, supplemental
  logging, key present), volume and change rate from catalog statistics, and a recommended
  ingestion pattern using the rule in section 3.
- Applies the type map in 5.1 and flags every lossy conversion as a `GAP-###`.
- Lists the Informatica mappings the slice replaces, when an inventory is attached as
  context, so legacy business rules are not lost. It never executes or edits them.
- Outputs added: `source-inventory.csv`, `ingestion-pattern-proposal.csv`, `type-map.csv`.

### 7.4 `adef-solution-design`

Stack specifics:

- `03-design/logical/` stays vendor-neutral. The technology-term scan stays on.
- `03-design/physical/` binds to section 6: lake table layout and partitioning, bronze
  views, silver history strategy from the apply mode (5.1), gold model, and the **data
  product boundary**: which gold objects are the product's output ports.
- Mandatory ADRs for this stack: ADR-001 lake database placement, ADR-002 silver and gold
  table type, ADR-003 dbt runtime and scheduler, ADR-004 apply mode per table, ADR-005
  initial load and cutover, ADR-006 lake maintenance (compaction, snapshot expiry).
- Cost estimate with arithmetic for: replication host, S3 storage and requests, Glue,
  Snowflake warehouses for dbt, search service, agent usage.
- Work packages: `WP-1 ingest`, `WP-2 lake-to-bronze`, `WP-3 dbt`, plus `WP-4 semantic` and
  `WP-5 publish` for stages 8 and 9.

### 7.5 `adef-pipeline-build`

Role unchanged: turn each approved work package into small, tested, idempotent code that
implements the design exactly. The three pipelines become these three work packages:

| Pipeline | Repository default | This client |
|---|---|---|
| `01_ingest` | PySpark JDBC extract or DMS | GoldenGate parameter and properties files, **or** Python framework feed configs, per `ingestion-pattern.csv` |
| `02_curate` | Spark SQL in the lake | Snowflake lake integration and bronze views, then the dbt Core project (bronze to silver to gold) |
| `03_publish` | Publish gold to the analytics engine | Not needed as a copy step: gold is already in Snowflake. Becomes gold contract tests and masked output views |

Does not: start, stop or alter a GoldenGate process; create an integration, volume or
database outside the dev sandbox; run anything against Db2 or Oracle. Those files are
generated, reviewed in the pull request and applied by the client's pipeline after G6.

### 7.6 `adef-test-quality`

Stack specifics, in addition to the existing rule execution and mutation check:

- **Hop reconciliation.** Row counts and control totals compared source to raw, raw to
  bronze, bronze to silver, silver to gold, and gold to the semantic metric, each computed
  two independent ways. Source totals come from a control query the client runs, or from
  the synthetic source in the demo edition.
- **Change-capture tests** on synthetic change sets: insert, update, delete, key update,
  out-of-order arrival, duplicate delivery, schema addition.
- dbt: `dbt build` in the sandbox, run twice for idempotency; every `DQ-###` is a dbt test
  with its severity.
- Masking and row access verified per role, including the UTL-C5 cross-domain denial.

### 7.7 `adef-release-deploy`

Stack specifics: one release bundle, four ordered parts, each with verify and rollback:
(1) lake objects and replication files handed to the GoldenGate and platform teams with a
runbook, (2) Snowflake integration, database, schemas and roles, (3) dbt project
deployment, (4) lake maintenance jobs. The existing rules hold: tested commit equals
deployed commit, production refuses without a change record. GoldenGate changes go through
the client's change process; the agent prepares the change, people execute it.

### 7.8 `adef-operations-observability`

Stack specifics: besides the monitoring spec and runbook, writes the **Operate onboarding
pack** in the formats OperateWithAI reads:

| File | Content for this data product |
|---|---|
| `07-operations/operate/environment.fragment.yaml` | Systems, the data chain of this product, its deliverable and deadline, owning tower |
| `07-operations/operate/signals.fragment.yaml` | Feeds to watch: replication lag and process state, feed run records, lake table freshness, dbt `run_results.json` and `sources.json`, listing and agent health |
| `07-operations/operate/kedb.seed.yaml` | Known-error candidates found during test, each with read-only checks |
| `07-operations/operate/actions.proposed.yaml` | Runbook actions with the role that must approve each |

### 7.9 `adef-semantic-context` (new)

| | |
|---|---|
| Mission | Make every approved consumer question answerable through one governed definition per metric, by people and by an AI assistant, with the business context the assistant needs to answer correctly |
| Expects | Approved design, production release evidence (G6b), requirements with `CQ-###` and `BR-###`, glossary from Collibra, access and masking policy |
| Produces | `08-semantic/`: semantic view DDL, metric catalogue, context corpus manifest, verified questions, agent definition, evaluation report, request for G8 |
| Does | Ties each metric to its `BR-###` and glossary term. Reuses a certified metric before defining a new one. Builds context from approved sources only: glossary, the requirements, the contract, approved documents. Runs the evaluation set and reports accuracy per question |
| Does not | Publish, share or grant. Read from bronze or silver. Redefine a business measure. Put unapproved documents or any Restricted value into context. Tune the agent to pass a question by hard-coding its answer |
| Escalates | Conflicting metric definitions; a consumer question that cannot be answered from gold; evaluation below the agreed threshold |
| Tool policy | May create objects in `SEMANTIC`, `CONTEXT`, `AGENTS` in dev. Other environments through the release pipeline after G8 |

Definition of done:

1. Every `CQ-###` maps to a metric or dimension, or is listed as not answerable with a reason.
2. Each metric returns the same value through the semantic view as through the test
   stage's reference SQL.
3. Each semantic object has a business description, synonyms and a glossary link.
4. The evaluation set covers every `CQ-###` plus at least one out-of-scope question and one
   access-denied case per consumer role; results are in `evaluation-report.md` with the
   failures listed, not averaged away.
5. The agent's instructions state what it must refuse, and UTL-C7 is evidenced.

### 7.10 `adef-data-product-publish` (new)

| | |
|---|---|
| Mission | Package the certified outputs as a data product and list it where consumers look, with a contract they can rely on and an access path that respects domain boundaries |
| Expects | G8 approval, the contract draft from design, quality results from G5, lineage completeness report from agent X, named Product Owner and Data Owner |
| Produces | `09-publish/`: final contract (ODCS), share definition, listing manifest per marketplace, access request flow, consumer guide, publication request for G9 |
| Does | Fills the listing from approved artifacts only. Checks the UTL-C8 checklist. Proposes consumer roles and the approval route. Prepares the same product for each bound marketplace through the marketplace adapter |
| Does not | Publish, list, share or announce before G9. Grant access. List outside the organization. Change the contract after approval without re-opening G9 |
| Escalates | Consumers outside the owning domain (Security and Compliance join G9); a contract term the quality results do not support |
| Tool policy | Drafts only. Publication is carried out by the runtime after G9, as an A3 action with the exact content and audience attached |

Publication checklist (blocks the G9 request when any item is missing): contract with
version and service levels; owner and support contact; classification; quality results;
lineage to the system of record; sample questions; usage examples; access request route;
semantic view and agent included in the share where the listing offers them.

### 7.11 `adef-catalog-lineage` (new, alongside every stage)

| | |
|---|---|
| Mission | Keep Collibra true to what the team designed and built, and prove lineage from the system of record to the listing |
| Does at G2 | Pulls glossary terms and existing classifications for the sources in scope; proposes new terms and classifications as drafts for the Data Steward |
| Does at G3 | Registers planned assets as candidates (domain, data product, data sets, columns) with links to requirements |
| Does at G6b | Prepares scanner inputs and custom lineage for the deployed objects; runs the completeness check |
| Does at G9 | Proposes the data product asset for certification with contract, owner, quality and listing links |
| Does not | Approve or certify an asset. Change an approved glossary definition. Write to Collibra outside the draft or candidate status without the Data Steward's approval |
| Writes | `control/governance/` only: import files, lineage files, completeness report |

Lineage completeness report: for each output column of the data product, the path back to a
source column is either scanned, custom-declared with its `MAP-###`, or listed as a gap.
G9 cannot be requested with an open gap on a contract column.

---

## 8. Workflow, gates and approvers

```
[0 Intake] ─G0─▶ [1 Requirements] ─G1─▶ [2 Mapping] ─G2─▶ [3 Design] ─G3─▶ [4 Build] ─G4 merge─▶
[5 Test] ─G5─▶ [6 Release] ─G6a─▶ test ─G6b─▶ production ─▶ [7 Operations] ─G7─▶
[8 Semantic and AI context] ─G8─▶ [9 Data product and marketplace] ─G9 publish─▶ delivery pack

[X Governance and lineage] contributes evidence at G2, G3, G6b and G9
```

Gates G0 to G7 and their approvers are unchanged from the repository's approval matrix.

| Gate | Decision | Required approvers | Also required when |
|---|---|---|---|
| G8 Semantic certification | Metric definitions, AI context and agent behaviour are correct and safe to expose | Data Steward + Product Owner | Security and Compliance if context contains Confidential material |
| G9 Publication | The data product is listed to the stated audience | Product Owner + Data Steward | Security and Compliance if consumers are outside the owning domain |

Segregation of duties, hash-bound approvals, approval expiry, the council of three, context
packs, the return and rejection limits, and emergency stop all apply to G8 and G9 as they
do to the existing gates. Workspace folders added: `08-semantic/`, `09-publish/`,
`control/governance/`; each has exactly one writer.

---

## 9. Generated code base

Repository layout the Build stage commits to the feature branch:

```
ingest/
  goldengate/<source>/            extract.prm, replicat.prm, iceberg.properties, tables.txt, PRECHECKS.md
  python-framework/feeds/         one <feed_id>.yaml per object (framework config, D3)
lake/
  glue/                           Iceberg table definitions where the framework needs them pre-created
  maintenance/                    compaction and snapshot-expiry job definitions
snowflake/
  00_integrations/                external volume, catalog integration, catalog-linked database
  01_domain_db/                   database, schemas, roles and grants (as code, applied by release)
  02_bronze_views/                one view per lake table
dbt/<domain>/
  dbt_project.yml, packages.yml (approved list only)
  models/staging/                 stg_<source>__<table>.sql      (BRONZE to typed, renamed)
  snapshots/ or models/silver/    history and conformance
  models/gold/                    dimensions, facts, data product output views
  models/**/schema.yml            descriptions, tests (DQ-###), contracts, meta: {map_ids, br_ids}
  exposures.yml                   the data product and its semantic view
semantic/<product>/               semantic_view.sql, verified_questions.yaml, context_manifest.yaml,
                                  agent.yaml, evaluation_set.yaml
product/<product>/                data-contract.odcs.yaml, share.sql, listing.snowflake.yaml,
                                  listing.collibra.json, consumer-guide.md
governance/collibra/              assets.import.json, custom-lineage/*.json, completeness-report.md
orchestration/ ci/ scripts/ deploy/   as in the repository (check_sql.py, verify_release_hash.py, REL-###)
```

The snippets below show the **shape** each adapter template must produce. They are patterns
for adapter review (section 12), not copy-ready code: object names are placeholders and
every vendor option must be verified against the client's installed versions.

### 9.1 GoldenGate (H1a)

```
-- ingest/goldengate/cis/replicat.prm            MAP-001..009, BR-002
REPLICAT rcisice
MAP CIS.ACCOUNT, TARGET util_customer_raw.cis_account;
MAP CIS.PREMISE, TARGET util_customer_raw.cis_premise;
MAP CIS.BILL,    TARGET util_customer_raw.cis_bill;
```

```properties
# ingest/goldengate/cis/iceberg.properties  (values by reference; no keys in the file)
gg.target=iceberg
gg.eventhandler.iceberg.catalogType=glue
gg.eventhandler.iceberg.fileSystemScheme=s3://
gg.eventhandler.iceberg.awsS3Bucket=${lake_bucket}
gg.eventhandler.iceberg.awsS3Region=${aws_region}
# authentication: instance role, never access keys in the file
```

`PRECHECKS.md` lists what a DBA must confirm before the change: logging or supplemental
logging per table, key columns, privileges of the capture user, the start position agreed
with the initial load.

### 9.2 Python framework feeds (H1b)

One YAML per object in the framework's own schema (section 5.2), plus a unit test that
loads the config and checks keys, watermark and reconciliation rules are present.

### 9.3 Lake to Snowflake bronze (H2)

```sql
-- snowflake/00_integrations/catalog_integration.sql   (applied by release, A3)
CREATE CATALOG INTEGRATION IF NOT EXISTS GLUE_REST_${ENV}
  CATALOG_SOURCE = ICEBERG_REST
  TABLE_FORMAT = ICEBERG
  CATALOG_NAMESPACE = '${glue_database}'
  REST_CONFIG = ( CATALOG_URI = 'https://glue.${aws_region}.amazonaws.com/iceberg'
                  CATALOG_API_TYPE = AWS_GLUE
                  CATALOG_NAME = '${aws_account_ref}' )
  REST_AUTHENTICATION = ( TYPE = SIGV4
                          SIGV4_IAM_ROLE = '${iam_role_ref}'
                          SIGV4_SIGNING_REGION = '${aws_region}' )
  ENABLED = TRUE;

CREATE DATABASE IF NOT EXISTS ${ENV}_LAKE_CUSTOMER
  LINKED_CATALOG = ( CATALOG = 'GLUE_REST_${ENV}', ALLOWED_NAMESPACES = ('${glue_database}') )
  EXTERNAL_VOLUME = '${external_volume}';
```

```sql
-- snowflake/02_bronze_views/cis_account.sql        MAP-001..005
CREATE OR REPLACE VIEW ${ENV}_CUSTOMER.BRONZE.CIS_ACCOUNT AS
SELECT "account_id" AS ACCOUNT_ID, "account_status" AS ACCOUNT_STATUS, "rate_class" AS RATE_CLASS,
       "customer_name" AS CUSTOMER_NAME, "open_date" AS OPEN_DATE, "last_updated_ts" AS LAST_UPDATED_TS,
       "op_type" AS _OP_TYPE, "op_ts" AS _OP_TS            -- change metadata (apply mode b)
FROM ${ENV}_LAKE_CUSTOMER."${glue_database}"."cis_account";
```

### 9.4 dbt Core (H3)

```sql
-- dbt/customer/models/gold/fct_bill.sql      REQ-001, REQ-002  BR-001, BR-002  MAP-018..027
{{ config(materialized='incremental', unique_key='bill_id', on_schema_change='fail') }}
select
    b.bill_id,
    a.customer_account_sk,
    b.period_start, b.period_end,
    b.billed_kwh,
    m.metered_kwh,
    b.billed_kwh - m.metered_kwh                    as variance_kwh,        -- BR-002
    m.estimated_reads / nullif(m.total_reads, 0)    as estimated_read_share -- BR-003
from {{ ref('slv_bill') }} b
join {{ ref('dim_customer_account') }} a
  on b.account_id = a.customer_account_id and b.period_end between a.valid_from and a.valid_to
left join {{ ref('int_metered_kwh_by_bill') }} m on m.bill_id = b.bill_id
{% if is_incremental() %} where b._loaded_at > (select max(_loaded_at) from {{ this }}) {% endif %}
```

Rules for the dbt adapter: staging models are the only ones that read `BRONZE`; every model
has a description and tests; each `DQ-###` is a test with `meta: {dq_id, severity}`; model
contracts are enforced on gold; no `select *` in persisted models; packages only from the
approved list; `target/manifest.json` and `run_results.json` are published for Collibra and
for Operate.

### 9.5 Semantic layer and AI context (H4)

```sql
-- semantic/billed_consumption/semantic_view.sql        CQ-001..006
CREATE OR REPLACE SEMANTIC VIEW ${ENV}_CUSTOMER.SEMANTIC.BILLED_CONSUMPTION
  TABLES (
    bills    AS ${ENV}_CUSTOMER.GOLD.FCT_BILL              PRIMARY KEY (BILL_ID),
    accounts AS ${ENV}_CUSTOMER.GOLD.DIM_CUSTOMER_ACCOUNT  PRIMARY KEY (CUSTOMER_ACCOUNT_SK),
    premises AS ${ENV}_CUSTOMER.GOLD.DIM_PREMISE           PRIMARY KEY (PREMISE_ID)
  )
  RELATIONSHIPS ( bills (CUSTOMER_ACCOUNT_SK) REFERENCES accounts )
  DIMENSIONS ( accounts.rate_class AS RATE_CLASS  COMMENT = 'Tariff rate class',
               premises.region     AS REGION_CODE COMMENT = 'Operating region' )
  METRICS ( bills.billed_kwh   AS SUM(BILLED_KWH)   COMMENT = 'BR-001 billed energy',
            bills.variance_kwh AS SUM(VARIANCE_KWH) COMMENT = 'BR-002 billed minus metered' )
  COMMENT = 'Meter-to-cash billed consumption. Owner: Customer domain.';
```

AI context is three governed parts in `CONTEXT`, each listed in `context_manifest.yaml` with
its source, approver and hash:

| Part | Content | Source of truth |
|---|---|---|
| Definitions | Glossary terms, metric definitions, business rules in plain language | Collibra glossary, `01-requirements/` |
| Documents | Approved reference text (tariff notes, read-quality codes, the consumer guide), chunked for a search service | Attached and approved at G8 |
| Verified questions | Question, expected SQL or metric, expected result on the test data | `evaluation_set.yaml`, from `CQ-###` |

The agent definition (`agent.yaml`) names its tools (the semantic view and the search
service only), its instructions, its refusals and the roles allowed to use it.

### 9.6 Data product and marketplaces (H5)

```sql
-- product/billed_consumption/share.sql        (applied by the runtime after G9, A3)
CREATE SHARE IF NOT EXISTS CUSTOMER_BILLED_CONSUMPTION;
GRANT USAGE ON DATABASE ${ENV}_CUSTOMER TO SHARE CUSTOMER_BILLED_CONSUMPTION;
GRANT USAGE ON SCHEMA ${ENV}_CUSTOMER.SEMANTIC TO SHARE CUSTOMER_BILLED_CONSUMPTION;
GRANT SELECT, REFERENCES ON SEMANTIC VIEW ${ENV}_CUSTOMER.SEMANTIC.BILLED_CONSUMPTION
  TO SHARE CUSTOMER_BILLED_CONSUMPTION;
-- plus the secure output views of the product and, where offered, the agent
```

```yaml
# product/billed_consumption/listing.snowflake.yaml   (organizational listing manifest)
title: "Billed Consumption (Meter-to-Cash)"
description: "One row per final bill with billed and metered kWh, variance and estimated-read share."
organization_profile: "INTERNAL"
organization_targets:
  discovery: [ { all_internal_accounts: true } ]
  access:    [ { account: "${account_ref}", roles: ["CUSTOMER_CONSUMER_BILLED_CONSUMPTION"] } ]
support_contact: "${owner_contact_ref}"
approver_contact: "${approver_contact_ref}"
```

**Marketplace adapter contract.** Each marketplace binding implements four operations so
another marketplace can be added without touching the agent: `render(contract, listing
inputs)` to the marketplace's format; `validate()` against its required fields;
`publish()` executed only by the runtime after G9; `withdraw()` as the rollback. Phase 1
implements the Snowflake organizational listing and the Collibra Data Marketplace entry.

---

## 10. Lineage and catalog in Collibra

| Hop | How lineage is obtained | Produced by |
|---|---|---|
| Oracle source objects | Collibra Edge scan (JDBC) | Client's Collibra team; agent X prepares scope |
| Db2 source objects | Edge scan if Db2 LUW. **If Db2 for z/OS: registered as assets from the Db2 catalog export and linked by custom lineage** (Collibra's technical lineage scanner supports Db2 LUW only) | Agent X |
| Source to lake raw (GoldenGate) | Custom technical lineage generated from the `MAP` statements and `MAP-###` rows | Agent X from stage 4 files |
| Source to lake raw (Python framework) | Custom technical lineage generated from feed configs | Agent X from stage 4 files |
| Lake raw to `BRONZE` | Snowflake scan covers the views; the Glue table to view link is custom lineage | Agent X |
| `BRONZE` to `SILVER` to `GOLD` | Collibra dbt Core scan of the `target/` folder, plus the Snowflake scan | Edge; agent X supplies artifacts |
| `GOLD` to semantic view, share, listing | Custom lineage and asset relations (data product, data set, listing) | Agent X |

Notes for the build: create technical lineage through Collibra Edge; the command-line
lineage harvester reached end of life on 31 July 2026. Custom lineage files are generated
from the approved mapping, so a mapping change at G2 regenerates them. Business lineage
(data product to glossary term to report) is proposed as draft relations for the Data
Steward.

---

## 11. Guardrails and enterprise controls

Everything in `adef-shared-guardrails` v1.2.0 applies unchanged. Additions for this stack,
each to be enforced in code where marked:

| Rule | Mechanism |
|---|---|
| Agents never connect to Db2, Oracle or a GoldenGate deployment | No connector exists in the agent runtime; source facts arrive as metadata exports (code) |
| Replication, integration, grant, share and listing statements are A3 | `ActionGuard` action catalogue entries; unknown actions already default to A3 (code) |
| No cross-domain read (UTL-C5) | Generated role model plus a guardrail scenario that fails if any grant crosses domains (code) |
| Context corpus only from approved, hashed items | `context_manifest.yaml` checked against approvals before load (code) |
| An agent answer set cannot be tuned by hard-coding | Evaluation set is owned by the test stage's reference results; the semantic agent cannot edit them (one writer per folder) |
| Restricted values never enter prompts or context | Existing prompt data boundary and scanners (code) |
| Listing content equals approved content | Publication hash check: listing manifest hash must equal the G9-approved hash (code) |

New guardrail scenarios to add to the suite (GT-19 onward): cross-domain grant attempt;
listing publish before G9; context item without approval; replicat mapping for a table not
in the approved mapping; semantic metric without a business rule ID; custom lineage that
references an unapproved `MAP-###`.

---

## 12. Build backlog

| Epic | Item | Done when |
|---|---|---|
| U1 Profile | Add the five slots and the two slot-rule changes; add the profile and Domain Pack 0.2.0 | T1 stack validation passes for the profile and fails when both ingestion slots are `none` |
| U2 Adapters | `cdc_replication/oracle-goldengate` (Db2 and Oracle capture, Iceberg handler, Glue) | Generated files pass a syntax check and a GoldenGate engineer's review; type map reviewed |
| U2 | `batch_ingestion/client-python-framework` | Generated feed configs validate against the client's schema (D3) |
| U2 | `compute_engine/snowflake` lake integration and bronze views | Applies cleanly in a dev account against a Glue database with synthetic tables |
| U2 | `transformation/dbt-core` medallion templates | `dbt build` passes twice on synthetic data; every `DQ-###` is a test |
| U2 | `semantic_layer/snowflake-semantic-views`, `ai_context/snowflake-cortex` | Semantic view creates; evaluation harness runs the verified questions |
| U2 | `marketplace/snowflake-internal-marketplace`, `marketplace/collibra-data-marketplace` | Render and validate pass; publish works in a non-production account behind G9 |
| U2 | `catalog_governance/collibra` and `lineage/collibra` | Import file loads to a Collibra sandbox; custom lineage renders the full path for one column |
| U3 Agents | Three new agent definitions and skills; stack sections added to eight existing skills | `tests/test_skills.py` passes with the new agents; each skill has an accepted and a rejected worked example |
| U4 Runtime | Stages 8 and 9, gates G8 and G9, folders `08-semantic/`, `09-publish/`, `control/governance/` | Full lifecycle test passes for the utilities domain on the new profile |
| U5 Local proof | Demo edition: extend the local lakehouse runner so bronze comes from simulated change sets and the semantic step is checked against reference SQL | `python -m adef demo --domain utilities --stack utility-gg-iceberg-snowflake` completes |
| U6 Guardrails | GT-19 onward (section 11) | Suite passes |
| U7 Operate handover | Stage 7 writes the four Operate fragments | OperateWithAI loads them without edits |

Build order: U1, U3 (skills first, as documents), U4, U2 adapters in hop order, U5, U6, U7.

---

## 13. Quality-control plan

| Check | Where |
|---|---|
| Every requirement traces to mapping, model, code, test, metric and contract clause | Traceability matrix at final assembly; G9 blocked on an orphan |
| Counts and control totals reconcile across all hops | Stage 5, evidence pack |
| Change-capture behaviours (update, delete, key change, duplicate, late) tested | Stage 5 |
| Metric equals reference SQL through every access path | Stage 8 |
| Each role sees only what it should; cross-domain denied | Stages 5 and 8 |
| Lineage complete for every contract column | Agent X, before G9 |
| Listing equals approved content | Runtime at publish |

Failure modes specific to this stack, with the prevention:

| Failure mode | Prevention |
|---|---|
| Keyless table replicated, updates silently become duplicates | Key check at G2; blocking question |
| Decimal or timestamp precision lost between Db2 and Snowflake | Type map approved at G2; reconciliation on sums, not only counts |
| History wrong in silver because raw was a mirror, not a change log | ADR-004 per table; change-capture tests |
| Small-file growth slows bronze queries | ADR-006 maintenance jobs generated and tested |
| Legacy business rule lost when an Informatica job is replaced | Mapping lists replaced jobs; each legacy rule becomes a `BR-###` or a documented drop |
| Semantic metric drifts from the dbt logic | Metric equals reference SQL check on every release |
| Assistant answers from general knowledge | Tools limited to the semantic view and search service; out-of-scope questions in the evaluation set |
| Listing promises a service level the pipeline cannot meet | Contract terms checked against stage 5 results and stage 7 monitors |

---

## 14. First slice and demo

**Slice.** *Billed Consumption (Meter-to-Cash)*, Customer domain. Sources: `CIS.ACCOUNT`,
`CIS.PREMISE`, `CIS.BILL` (Db2), `MDM.METER`, `MDM.DAILY_READ` (Oracle). The repository's
utilities demo pack already contains these tables for Db2 and Oracle, 13 Jira issues, and
planted anomalies (an orphan bill, estimated reads, billed below metered) that make the
quality and reconciliation story visible. Proposed ingestion pattern: GoldenGate for
`ACCOUNT`, `PREMISE`, `BILL`, `METER`; Python framework for `DAILY_READ` (daily, high volume).

**Demo walkthrough (about 20 minutes).** The HTML demo follows this order:

1. The client path and where each agent contributes.
2. Start the run from the Jira export. The planted instruction in `UTIL-8` is flagged at intake.
3. Mapping: the proposed ingestion pattern and type map, approved by the Data Steward.
4. Design: medallion layout and the ADRs a person must decide.
5. Build: the generated GoldenGate files, feed config, bronze views and dbt models, with
   requirement IDs in the code.
6. Test: reconciliation across hops; the orphan bill caught by `DQ-003`.
7. Semantic and AI context: the semantic view, a verified question, the evaluation result.
8. Publish: the listing card, the contract, and the lineage back to Db2.
9. What changes for the team: who decides what, and how the gain is measured.

Next slices after the first: one each for Generation, Transmission and Distribution, which
exercises UTL-C5 across domains.

---

## 15. How to tell whether the team is helping

Measure on the first two slices; do not quote a saving before then. Baseline is the
client's own last comparable data product.

| Measure | How it is taken |
|---|---|
| Elapsed days, request to listing | Run event log, G0 request to G9 approval |
| Person-hours per stage | Approver review time from the console plus engineer rework time |
| First-pass gate approval rate | Gates approved without a rejection, from `approvals.jsonl` |
| Defects found after G5 | Incidents and returns traced to a stage |
| Share of generated code merged unchanged | Diff between generated commit and merged commit |
| Requirement coverage | Traceability matrix |
| Assistant answer accuracy | Evaluation report at G8 and monthly after |
| Cost per run | Model spend and sandbox compute from run metrics |

---

## 16. Plan

| Step | Outcome |
|---|---|
| 1. Demo and decisions | HTML demo shown; D1 to D11 answered; first slice agreed |
| 2. Profile, pack and skills (U1, U3) | Agents produce documents for stages 0 to 3 on the client's real metadata, with the simulator or an approved model |
| 3. Adapters for hops H1 to H3 (U2) and runtime (U4) | Build and test stages run in the dev sandbox on synthetic data |
| 4. Semantic, publish, Collibra adapters (U2), guardrails (U6) | Stages 8, 9 and agent X run; first listing in a non-production account |
| 5. Pilot slice | First slice through G9 in production, with the measures in section 15 |
| 6. Operate handover (U7) | Phase 2 starts from the onboarding pack |

---

## 17. Honest limits

- Vendor syntax in section 9 is a pattern. Each adapter is reviewed by an engineer for that
  tool against the client's installed version before first use, as the repository requires.
- The repository executes pipelines only on its local lakehouse. Cloud code is generated and
  checked, then run by the client's own pipeline after approval.
- GoldenGate and the Python framework are operated by the client's teams. The agents
  prepare changes; they do not run them.
- The Domain Pack controls are not legal or compliance advice.
- The demo is a simulation with synthetic data and scripted agent output.

## 18. Sources

- [BuildWithAI repository](https://github.com/CloudKatasani/Agentic-Data-Engineering-Framework-BuildWithAI/tree/main): README, `docs/spec/BUILD_SPEC.md`, `agents/`, `skills/`, `demo-data/utilities/`
- [OperateWithAI repository](https://github.com/CloudKatasani/Agentic-Data-Engineering-Framework-OperateWithAI/tree/main): README, `OPERATING_MODEL.md`, `operatewithai/knowledge/`
- [Oracle GoldenGate: Apache Iceberg handler and supported catalogs](https://docs.oracle.com/en/middleware/goldengate/big-data/23/gadbd/apache-iceberg.html)
- [Oracle: replicating Oracle Database to Iceberg with GoldenGate for DAA (Glue and S3)](https://blogs.oracle.com/dataintegration/seamless-data-movement-replicating-oracle-database-to-apache-iceberg-with-goldengate-for-daa)
- [Snowflake: catalog integration for AWS Glue Iceberg REST](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-catalog-integration-rest-glue)
- [Snowflake: Apache Iceberg tables and catalog-linked databases](https://docs.snowflake.com/en/user-guide/tables-iceberg)
- [dbt: Snowflake and Apache Iceberg, Glue catalog-linked databases](https://docs.getdbt.com/docs/mesh/iceberg/snowflake-iceberg-support)
- [Snowflake: dbt Projects on Snowflake, general availability](https://docs.snowflake.com/en/release-notes/2025/other/2025-11-06-dbt-projects-on-snowflake-ga)
- [Snowflake: sharing semantic views in listings](https://docs.snowflake.com/En/release-notes/2025/other/2025-11-04-sharing-semantic-views)
- [Snowflake: share Cortex Agents](https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-agents-sharing)
- [Snowflake: automatic data agents for listings and shares](https://docs.snowflake.com/en/collaboration/auto-generated-data-agents)
- [Collibra: supported data sources for technical lineage](https://productresources.collibra.com/docs/collibra/latest/Content/CollibraDataLineage/TechnicalLineage/ref_technical-lineage-supported-data-sources.htm)
