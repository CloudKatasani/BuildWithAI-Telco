---
name: telco-domain-pack
description: Telco domain knowledge every DataCrew Telco agent shares - TM Forum SID entities and Open APIs, OSS/BSS systems, network KPIs and counters, usage records, classification defaults, regulatory controls and autonomy levels. Load after telco-shared-guardrails and before the agent's own skill.
license: Proprietary
compatibility: Reference only; no tools needed.
metadata:
  owner: datacrew-telco
  version: "2.0.0"
  scope: all-agents
  status: starter-needs-client-review
---

# DataCrew Telco Domain Pack

Reference facts and defaults for a mobile and fixed operator. The demo operator is the fictional
**NorthStar Telecom**. Client values (thresholds, targets, tariffs) always override the defaults
here and must come from an approved artifact or a named person.

## 1. TM Forum SID entities

| Business term | SID entity | Typical source | TMF Open API |
|---|---|---|---|
| Customer, account holder | Customer, Party, PartyRole | CRM | TMF629 Customer, TMF632 Party |
| Billing account | BillingAccount | Billing | TMF666 Account |
| Tariff, plan, offer | ProductOffering, ProductSpecification | Catalog | TMF620 Product Catalog |
| Subscription, line | Product (instance) | BSS order/inventory | TMF637 Product Inventory |
| Order | ProductOrder | Order management | TMF622 Product Ordering |
| Service (voice, data, VPN, circuit) | Service | Service inventory | TMF638 Service Inventory |
| Cell, site, router, port | Resource | Network inventory | TMF639 Resource Inventory |
| Alarm | Alarm | Fault management | TMF642 Alarm Management |
| Trouble ticket | TroubleTicket | Ticketing | TMF621 Trouble Ticket |
| Service quality, SLA | ServiceLevelAgreement, ServiceQuality | Assurance | TMF657 SLM, TMF656 Service Problem |
| Usage, CDR, xDR | Usage | Mediation, OCS | TMF635 Usage |
| Invoice, bill | CustomerBill | Billing | TMF678 Customer Bill |

## 2. Systems and feeds

| System | Data | Cadence | Usual ingestion |
|---|---|---|---|
| Billing (Oracle / Db2) | Accounts, invoices, invoice lines, tariffs | Changes all day | CDC (GoldenGate) |
| CRM | Customers, contracts, consent | Daily or API | Batch / API |
| Mediation | Mediated CDRs | 5-15 min files | File batch or streaming |
| OCS / charging | Rated events, balances | Real time | CDC or streaming |
| OSS performance management | PM counters per cell, 15 min | 15 min | Streaming (Kafka) |
| Fault management | Alarms | Real time | Streaming |
| Network / service inventory | Sites, cells, circuits, services | Hourly or daily | API batch |
| Ticketing | Trouble tickets | Changes all day | CDC |
| xDR lake | Data session and voice records | Hourly | Iceberg / Delta on object storage |

## 3. Network KPIs (3GPP-style defaults; confirm targets with the client)

| KPI | Definition | Default watch threshold |
|---|---|---|
| DCR (dropped call rate) | Abnormal releases / established calls | > 1.5% per cell-hour |
| CSSR (call setup success rate) | Successful setups / attempts | < 98.5% |
| PRB utilisation | Used physical resource blocks / available | > 85% (congestion), < 10% (sleep candidate) |
| DL user throughput p10 | 10th percentile downlink user throughput | < 3 Mbps |
| Handover success rate | Successful / attempted handovers | < 97% |
| Availability | Up time / scheduled time (cell, circuit) | Per SLA |
| kWh per TB | Site energy / data volume | Trend, no fixed threshold |

## 4. Business metrics (glossary defaults)

| Metric | Definition |
|---|---|
| churn_rate_30d | Post-paid lines disconnected or ported out within 30 days / active lines at start |
| at_risk_arpu | Monthly ARPU of lines with churn score >= 0.7 |
| arpu | Revenue / average active lines in the month |
| leakage_eur | Value of chargeable events without an invoice line in their bill cycle |
| recon_match_rate | Matched events / chargeable events, switch to invoice |
| availability_pct | Up minutes / scheduled minutes, excluding approved maintenance |
| sla_credit_exposure_eur | Credits due if the month closed now, per contract |
| mttr_hours | Mean time to restore customer-impacting incidents |

## 5. Classification defaults

- Restricted (personal): MSISDN, IMSI, IMEI, ICCID, name, address, email, date of birth,
  national id, precise location, single-subscriber CDR/xDR, payment data.
- Confidential: invoices, rated events, tariffs, contracts, revenue, SLA credits, fraud cases.
- Internal: PM counters, alarms, topology, inventory, pipeline runs.
- Aggregates over fewer than 10 subscribers are treated as Restricted (small-cell suppression).

## 6. Regulatory controls (defaults; confirm per country)

| Control | Requirement |
|---|---|
| TEL-C1 Data minimisation | Map only attributes a requirement needs |
| TEL-C2 Traffic data retention | CDR/xDR retained only for the period the law and purpose allow |
| TEL-C3 Marketing consent | Marketing use of usage data needs a consent flag per line |
| TEL-C4 Pseudonymisation | Analytics joins on a pseudonymous subscriber key, never on MSISDN |
| TEL-C5 Outage reporting | Outages above the regulator threshold are escalated for notification |
| TEL-C6 Network security (NIS2) | Production network changes go through change management with rollback |
| TEL-C7 AI oversight (EU AI Act) | AI used in operating critical digital infrastructure has human oversight, logging and risk management |
| TEL-C8 Lawful intercept and emergency services | Out of scope for every agent |

## 7. Autonomy levels (TM Forum)

L0 manual, L1 assisted, L2 partial (agent proposes, person acts), L3 conditional (agent acts on
approved A2 runbooks in defined scenarios), L4 high (closed loop in a validated scenario with person
on exception), L5 full. Autonomy is granted per scenario after validated runs, never per network.

## 8. Medallion conventions

`brz_` raw as received, `slv_` conformed to SID with history, `gld_` business-ready marts and
data product output ports, `SEMANTIC.` certified metrics. Gold objects carry an ODCS contract.
