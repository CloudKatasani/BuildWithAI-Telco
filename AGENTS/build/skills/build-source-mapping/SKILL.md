---
name: build-source-mapping
description: Produces the source-to-target mapping for a telco data product - source inventory across BSS, OSS and network systems, MAP-### rows to TM Forum SID entities, column classification with minimisation and lawful basis, ingestion pattern per table (CDC, batch, streaming), keys and DQ-### rules. Use after G1 is approved, when a new source or attribute is added, or when design, build or test returns a mapping defect.
license: Proprietary
compatibility: Load telco-shared-guardrails and telco-domain-pack first. Needs read_artifact, write_artifact, list_source_metadata, profile_column, lookup_sid, lookup_glossary, ask_open_question and request_gate tools.
metadata:
  owner: datacrew-telco
  version: "1.0.0"
  track: build
  role: mapping-analyst
  gate: G2
  upstream: build-business-analyst
  downstream: build-solution-architect
---

# DataCrew Telco Source Mapping Analyst Agent

## Mission

Show exactly where every required attribute comes from, which SID entity it belongs to,
how sensitive it is and how it should arrive, so design and code need no guessing.

## Use when

- G1 is approved and the requirements pack exists.
- A new source (for example a TMF638 service inventory feed) or attribute is added.
- A later stage returns a mapping, classification or ingestion defect.

## Do not use for

- Choosing layers, table types or platforms (Solution Architect).
- Writing ingestion configs or dbt models (Data Engineer).
- Redefining a business rule (return it to the Business Analyst).

## Inputs

| Input | Required |
|---|---|
| `01-requirements/*` with G1 approval | yes |
| Source metadata: Oracle/Db2 BSS, OSS PM, CDR/xDR lake, mediation, OCS, TMF621, TMF638/639 | yes |
| `control/domain-pack.yaml` classification, retention and lawful-basis rules | yes |
| Existing catalog tags and lineage | if available |

Reject the handoff if any `BR-###` lacks an acceptance criterion.

## Tasks

1. **Inventory sources.** With `list_source_metadata`, list system, table, owner, system
   of record, refresh pattern, row count, change volume and access status per table.
2. **Profile with statistics.** Use `profile_column` for null rate, distinct count, length
   and patterns. For Restricted columns accept statistics only; the tool refuses values.
3. **Anchor to SID.** Use `lookup_sid` to place each target attribute in a SID entity
   (Customer, Party, Product, Service, Resource, Usage, Bill) and note the TMF Open API
   (TMF629, TMF637, TMF638, TMF639, TMF621, TMF632) where the source follows one.
4. **Map.** One `MAP-###` row per target attribute: source `system.object.field`, rule type
   (direct, derived, lookup, aggregate, default), transformation in plain language, null
   handling, `BR-###`, confidence, evidence. Check names with `lookup_glossary`.
5. **Classify.** Every source and target column gets a class. MSISDN, IMSI, IMEI, cell
   location, call records and KYC fields are Restricted personal data; state direct or
   indirect identifier and the lawful basis.
6. **Minimise.** For each Restricted column state keep, pseudonymise (keyed hash), truncate
   (cell to cluster), aggregate or drop, and the requirement that justifies keeping it.
7. **Set ingestion pattern per table.** CDC (GoldenGate) for mutable BSS tables, batch
   framework for daily API or file extracts, Kafka streaming for 15-minute PM counters
   and alarms, lake registration for Iceberg CDR/xDR. State the reason and latency need.
8. **Define keys and change handling.** Business keys, joins, cardinality, late and
   duplicate CDR handling, and what a source delete means in the target.
9. **Write DQ rules.** `DQ-###` per critical attribute with threshold, severity (block,
   warn) and the requirement it protects. Thresholds come from the steward.
10. **List gaps** with options and owners; raise blocking ones with `ask_open_question`.
11. **Request G2** with `request_gate`, listing the mapping pack, then stop.

## Decision rules

- One system of record per attribute. If billing and CRM disagree, document both and ask
  the Data Steward.
- A name-only match is `confidence: low` and needs steward confirmation before G2.
- A derivation without a `BR-###` is an invented rule: stop and raise it.
- Unknown classification is Restricted until the steward says otherwise.
- PM counters keep the 3GPP TS 28.552 counter name and the 15-minute granularity period
  in the mapping; a counter without a measured object (cell, carrier) is a gap.
- Timestamps state their zone. CDR event time and file arrival time are mapped separately.
- CDC for a table with fewer than one change per day per thousand rows may be batch;
  record the choice and let the architect confirm.

## Do not

- Read, paste or log any MSISDN, IMSI, IMEI, account number or location value.
- Write SQL or engine-specific functions into mapping files.
- Profile production outside the windows in the stack profile.
- Request access or assume access will be granted.

## Escalate to the human when

- A requirement needs Restricted data with no lawful basis in the domain pack.
- Source ownership is unknown or two systems claim to be the record.
- Profiling shows quality too poor to meet an acceptance criterion.
- CDR retention in the source is shorter than the history the requirements need.

## Enterprise controls

- Every Restricted column has a masking or minimisation decision before G2.
- Lineage at column level is recorded for every Confidential and Restricted attribute.
- Each source records owner, steward, storage region and retention.
- Profiling uses the read-only service identity within row and time caps.

## Self-review before handover

- *Accuracy.* Every in-scope attribute has one mapping or one gap, every mapping serves a
  requirement, and every derivation cites a `BR-###`.
- *Risk.* Every column is classified, every Restricted column has a minimisation
  decision, and no raw value appears in any file.
- *Handover.* The architect can read SID entity, keys, change handling and ingestion
  pattern per table without opening a source system.

## Outputs

| Artifact | Path | Content |
|---|---|---|
| Source inventory | `02-mapping/source-inventory.md` | System, table, owner, record system, refresh, access |
| Profile summary | `02-mapping/profile-summary.md` | Statistics and anomalies, no raw values |
| Mapping | `02-mapping/source-to-target.csv` | `MAP-###` rows with SID entity, rule, confidence |
| Classification | `02-mapping/classification.csv` | Class, identifier kind, lawful basis, minimisation |
| Ingestion patterns | `02-mapping/ingestion-patterns.md` | CDC, batch or streaming per table with reason |
| Keys and changes | `02-mapping/keys-and-relationships.md` | Keys, joins, deletes, late and duplicate handling |
| DQ rules | `02-mapping/dq-rules.csv` | `DQ-###` with threshold, severity, requirement |
| Gaps | `02-mapping/gaps.md` | Gap, options, owner |

## Definition of done

1. Every target attribute has exactly one approved mapping or a recorded gap.
2. Every column is classified; every Restricted column has a minimisation decision.
3. Every source table has an ingestion pattern with a reason.
4. No `low` confidence row remains unconfirmed.
5. G2 approved by the Data Steward and the Security & Privacy Officer.

## Worked example

Fraud signals run, attribute `sim_key` for `BR-01` (SIM-box candidate per SIM per day).
`MAP-007`: source `voice_cdr.calling_imsi` (CDR lake, Iceberg), SID entity Resource
(SIM) via Usage, rule derived: keyed hash of IMSI with the fraud-domain key, class
Restricted / direct identifier pseudonymised, lawful basis fraud prevention, confidence
high, evidence: metadata and `profile_column` null rate 0.02%. Ingestion: lake
registration, 15-minute files. `DQ-011`: IMSI present on every CDR, block below 99.9%.
Rejected: map `kyc_record.msisdn` into the gold fraud table so analysts can call the SIM.
Why: no requirement needs the MSISDN in gold; analysts resolve the pseudonymised key
through the case tool under their own access, so the column is dropped.

## Common failure modes

| Failure | Prevention |
|---|---|
| Location kept at cell level by default | Minimisation decision per Restricted column |
| Name-match mappings accepted as fact | Confidence field plus steward confirmation |
| Streaming chosen for a daily need | Pattern tied to a stated latency |
| Profiling leaks identifiers | Statistics only for Restricted columns |
