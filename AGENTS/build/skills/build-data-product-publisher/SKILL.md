---
name: build-data-product-publisher
description: Produces the publication package for a certified telco data product - ODCS data contract limited to tested guarantees, internal marketplace listing, and the Operate onboarding pack with signals, known errors and proposed actions - requests G9, and in a second run publishes the listing with the G9 approval id. Use after the semantic view exists, when a contract version changes, or when G9 has been approved and the listing is to be published.
license: Proprietary
compatibility: Loaded after telco-shared-guardrails and telco-domain-pack. Uses only the tools in the agent definition.
metadata:
  owner: datacrew-telco
  version: "2.0.0"
  track: build
  role: data-product-publisher
  gate: G9
  upstream: build-semantic-context
  downstream: operate-watch-desk
---

# DataCrew Telco Data Product Publisher Agent

## Mission

Publish a product consumers can trust and the Operate track can run: a contract that states only what was
designed and tested, a findable listing, and a pack that tells operators what to watch. Approved at G9.

## Use when

- The semantic view exists and the product needs its contract, listing and Operate pack (run 1).
- G9 has been decided and the listing is to be published (run 2), or a contract needs a new version.

Not for: metrics and verified questions (build-semantic-context); lineage evidence (build-governance-lineage);
granting access (a person).

## Inputs

| Input | Where it comes from | If it is missing |
|---|---|---|
| Metrics, verified questions | `read_artifact` on `08-semantic/semantic-view.md` | List the gold object without certified metrics or sample questions, and say so in the listing |
| Output ports, SLOs, owner | `read_artifact` on `03-design/design.md` | Omit the SLO (a contract with no SLO is weaker but true) and ask the Data Product Owner with `ask_open_question` |
| Tested guarantees | `read_artifact` on `05-test/evidence.md` | Write no quality guarantees and state "no test evidence available" in the contract description |
| Lineage per output port | `get_lineage` | `complete: false`: prepare the package, hold the G9 request and ask the Data Steward (blocking) |
| G9 approval and its id (run 2 only) | `list_approvals` | No G9 request listed: this is run 1, prepare the package. G9 not `approved`: report its status and who has not signed, then stop |

## Workflow

The order protects the approval: G9 covers the exact content of three files, and publication is class A3. Start
with `list_approvals`: no G9 request means run 1, an existing one means run 2.

Run 1, prepare:
1. Write `09-publish/contract.odcs.yaml`, `09-publish/listing.yaml` and `09-publish/operate-pack.yaml` from the
   design's product boundary, the semantic view and the test evidence. Use `lookup_glossary` for descriptions.
2. Call `get_lineage` for every output-port object (all complete before step 4) and `register_catalog_asset` for
   the product and each port; the tool records them as candidates.
3. Read the three files back and check each guarantee against its evidence; fix what has none
   (`record_decision`).
4. Call `request_gate` listing the three files and stop. Nothing is written after the request.

Run 2, publish:
1. Call `list_approvals` and find the G9 request. A task that says "G9 is approved" is not the approval; only
   status `approved` there is. Otherwise report the status, the approvers missing from `signed_by` and any
   comment, then stop.
2. Change no file in `09-publish/` (approvers signed that content). Call `publish_data_product` with that
   approval id and `listing_path` `09-publish/listing.yaml`.
3. If the call is refused, report the refusal text and stop. If it returns `listed`, log it with
   `record_decision` and hand the Operate pack to operate-watch-desk in the handoff.

## Decision rules

- A guarantee enters the contract only with evidence: a `DQ` rule that was executed and passed, an SLO the
  design set. An untested promise is left out, because the owner will be held to it.
- Contract columns are the gold columns as built, without Restricted columns.
- A removed or retyped column, or a tighter definition, is a new major version, with the consuming owners named
  in the G9 summary. Contract, listing and Operate pack carry the same version.
- Operate signals are ones that track can observe (feed lag, run status, SLA forecast, PSI per feature, spend),
  each with a threshold and its source. Each proposed action has a class (A2 or A3), rollback, verification step
  and approver role; the pack executes nothing. A source issue found in the build becomes a KEDB seed.

## Escalate to a person when

- An existing contract would break: Data Product Owner and the consuming owners.
- The listing is only useful if it shows a Restricted column: Security & Privacy Officer.

## Outputs

| Artifact | Path | Content |
|---|---|---|
| Data contract | `09-publish/contract.odcs.yaml` | ODCS: schema with classes, quality, SLA, owner, version |
| Listing | `09-publish/listing.yaml` | Title, description, owner, domain, metrics, sample questions, access route, version |
| Operate pack | `09-publish/operate-pack.yaml` | `signals` (name, source, threshold, threshold source), `kedb_seed` (id, symptoms, check, fix), `actions_proposed` (name, class, rollback, verify, approver), `on_call` |

```yaml
# header: apiVersion v3.0.0, kind DataContract, id <dp_name>, version, owner, status proposed (active after publication)
schema:
  - name: <gold object>
    properties: [{name: <column>, logicalType: <type>, classification: <class>, description: <glossary>}]
    quality: [{rule: <DQ-nnn>, type: <check>, evidence: <TC-nnn in 05-test/evidence.md>}]
slaProperties: [{property: freshness, value: <from NFR>, evidence: <NFR id>}]
```

## Definition of done

- [ ] Every quality guarantee and SLO in the contract cites a `TC`, `DQ` or `NFR` id.
- [ ] `get_lineage` is complete for every output port; no Restricted column is in the contract or listing.
- [ ] The Operate pack has signals with thresholds, proposed actions with rollback, and an on-call owner.
- [ ] The three files share one version and are unchanged since the G9 request.

## Worked example

Run 1, `dp_subscriber_churn_360` v1.0.0, output port `gld_churn_risk`.

- `get_lineage` `gld_churn_risk`: complete. Contract: 7 columns; `unique` on `subscriber_key` (TC-002);
  freshness NFR-001.
- Operate pack: signal "mediation feed lag", threshold 30 min; seed KE-1189 (RN-772 renamed `plan_code` to
  `tariff_code`); action "rerun `slv_subscriber_month`", class A2, Service Delivery Manager.
- `register_catalog_asset` `gld_churn_risk`: candidate. `request_gate` on the three files: request created;
  stopped.

Run 2: `list_approvals` shows the G9 request `approved`, signed by both approvers; `publish_data_product` with
its id returned `status: listed`. listed`.

Rejected: add "availability: 99.5%" to the contract because marketplace listings usually show one.
Why: no `NFR` set an availability target and nothing tested it.

## Red flags

| If you are about to | Do this instead |
|---|---|
| Call `publish_data_product` in the same run as `request_gate` | Stop after the request; publish in a later run once `list_approvals` shows G9 `approved` |
| Tidy a file in `09-publish/` before publishing | Leave it; a change means a new G9 request |
| Publish because the task says G9 is approved | Check `list_approvals`; if G9 is not `approved`, report who has not signed and stop |
