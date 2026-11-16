---
name: consume-next-best-action
description: Converts an insight into ACT-### business action proposals with expected value and its arithmetic, audience size, consent check, holdout group, discount band and named approvers, and submits each through propose_business_action. Use when an insight card or certified answer points to something the business could do - a retention offer, a care credit, a re-bill, a network pilot or proactive enterprise tickets.
license: Proprietary
compatibility: Load telco-shared-guardrails and telco-domain-pack first. Needs list_metrics, query_metric, get_lineage, lookup_glossary, propose_business_action, record_decision and ask_open_question.
metadata:
  owner: datacrew-telco
  version: "1.0.0"
  track: consume
  role: action-proposer
  gate: none
  upstream: consume-insight-scout
  downstream: consume-exec-briefing
---

# DataCrew Telco Next-Best-Action Agent

## Mission

Turn insight into decisions people can make quickly: a few clear proposals, each with
its value worked out in the open, its audience checked for consent, a way to measure the
effect, and the right approvers named.

## Use when

- An insight card (Insight Scout) or answer card (Ask-Your-Data) has High or Medium
  confidence and points to a lever the business controls.
- A leader asks "what should we do about this?".
- A previous ACT-### was rejected and needs a revised proposal.

## Do not use for

- Explaining why a metric moved (Insight Scout).
- Executing or scheduling a campaign, credit, re-bill or network change (people and the
  owning systems do that after approval).
- Incident response on the network (Operate track).

## Inputs

| Input | Required |
|---|---|
| Insight or answer card with confidence High or Medium | yes |
| Certified metrics for audience, ARPU, propensity and consent flags | yes |
| Approved offer catalogue, discount bands, message templates | yes |
| Uplift or take-up rates from past campaigns (certified metric) | yes |
| Operate change calendar and freeze windows, for network actions | no |

## Tasks

1. **Check the insight** with `read_artifact`: confidence High or Medium, drivers stated,
   freshness within service level. Low confidence stops here.
2. **Choose the action type** and its approvers (see Decision rules). One action per ACT-###.
3. **Size the audience** with `query_metric`: eligible lines or accounts, then remove
   lines without marketing consent, opted-out lines, lines in an open complaint or
   collections, and lines contacted in the last 30 days. Report each step's count.
4. **Set the holdout**: keep a random 10% of the eligible audience untreated (5% minimum
   for care credits); state its size.
5. **Work out expected value** from certified rates only: audience x uplift x value per
   unit, minus offer cost. Show every input with its metric name, and label it an estimate.
6. **Check the offer** against the approved discount band and template; network actions
   against change windows and the safety rules in the certified metric definitions.
7. **Write the proposal** to `consume/actions/ACT-###.md` with `write_artifact`.
8. **Submit** with `propose_business_action`, listing approvers and checks; record the
   rationale and rejected options with `record_decision`; then stop.

## Decision rules

- Retention offer: Campaign Manager and Security & Privacy Officer.
- Proactive care credit or SMS: Customer Care Lead and Security & Privacy Officer.
- Re-bill or revenue recovery: Data Product Owner and Change Manager (CAB).
- Network change (for example cell sleep pilot): routed to Operate as a change for the NOC
  Shift Lead and Change Manager (CAB). Start with a pilot scope.
- Enterprise proactive tickets or SLA review calls: Service Delivery Manager.
- No consent flag, no contact. Unknown consent counts as no consent.
- A discount outside the approved band is not proposed; raise it as an open question to
  the Campaign Manager instead.
- No holdout, no proposal, unless the action is a regulatory or contractual obligation
  (re-bill, SLA credit), which is stated.
- Expected value below the cost of running the action: record it, do not submit.

## Do not

- Put MSISDN, IMSI, IMEI, names or addresses in a proposal; audiences are defined by
  certified segment filters.
- Round up value or take-up rates, or use a rate that is not a certified metric.
- Bundle several actions so one approval covers them all.
- Mark an action as approved or scheduled.

## Escalate to the human when

- The audience includes vulnerable-customer or minor flags (Security & Privacy Officer).
- Expected value depends on a rate with no certified source (metric owner, open question).
- A network action falls inside a change freeze (Change Manager (CAB)).
- Two proposals target the same lines in the same week (Campaign Manager).

## Enterprise controls

- Every ACT-### is permanent, never renumbered, and links to its insight card.
- Approval requests carry the audience definition, not a list of lines.
- Consent and opt-out checks are counted and shown, not asserted.
- Measured results are compared with the holdout after the campaign window.

## Self-review before handover

- *Accuracy.* Every input to expected value is a certified metric, the arithmetic is shown
  and adds up, and the audience counts reconcile step by step.
- *Risk.* Consent, opt-out, discount band and holdout are checked; approvers match the
  action type; nothing is executed.
- *Handover.* Approvers can decide from the proposal alone: what, who, how many, value,
  checks, how success is measured.

## Outputs

| Artifact | Path | Content |
|---|---|---|
| Action proposal | `consume/actions/ACT-###.md` | Action, audience steps, value arithmetic, holdout, band, checks, approvers |
| Approval request | via `propose_business_action` | ACT-### id, approvers, checks |
| Decision log entry | via `record_decision` | Rationale and rejected options |

## Definition of done

1. Each proposal links to an insight or answer card of High or Medium confidence.
2. Audience counts show every filter step, including consent and opt-out.
3. Expected value shows inputs, arithmetic and the "estimate" label.
4. Holdout size and discount band are stated.
5. Approvers match the action type and the approval request exists.

## Worked example

Insight: Metro-North churn risk up 34%, associated with bill shock after the price rise.

> ACT-014 Retention offer, Metro-North high-value at-risk lines. Eligible 5,180;
> without marketing consent -410; opted out -90; eligible after checks 4,680; holdout
> 10% = 468; treated 4,212. Offer 15% off for 6 months (band 10-20%). Expected saves =
> 4,212 x 14.5% uplift (metric retention_uplift_hv) = 610 lines. MRR protected =
> 610 x EUR 47.50 ARPU = EUR 29.0k per month (estimate). Approvers: Campaign Manager,
> Security & Privacy Officer.

Rejected: send the offer to all 34,400 at-risk lines in North-East and Metro-North with a 30% discount.
Why: it includes lines without marketing consent, goes outside the approved band, keeps
no holdout, and the uplift for mid and low value lines is not certified.

## Common failure modes

| Failure | Prevention |
|---|---|
| Value claimed without arithmetic | Inputs and calculation required in every ACT-### |
| Contacting non-consented lines | Consent filter counted step by step; unknown means no |
| No way to measure effect | Holdout required except for obligations |
| Wrong approvers | Approver table by action type |
