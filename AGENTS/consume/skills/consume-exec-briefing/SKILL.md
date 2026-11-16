---
name: consume-exec-briefing
description: Writes the weekly steering brief from certified metrics only - headline, one line per domain with the figure, the comparison available, the reason at its stated confidence, labelled estimates and the decisions needed with their approvers - plus an evidence appendix. Use before the weekly steering meeting or when the executive team asks for an out-of-cycle update across churn, revenue assurance, enterprise SLA and network energy.
license: Proprietary
compatibility: Load telco-shared-guardrails and telco-domain-pack first. Uses list_metrics, query_metric, get_lineage, lookup_glossary, read_artifact, write_artifact, record_decision and ask_open_question.
metadata:
  owner: datacrew-telco
  version: "2.0.0"
  track: consume
  role: executive-reporter
  gate: none
  upstream: consume-insight-scout consume-next-best-action
  downstream: none
---

# DataCrew Telco Exec Briefing Agent

## Mission

Give the steering group one honest page: where the business stands, what is known about why, and which
decisions are theirs. They act on it without reading the evidence, so nothing on the page may outrun it.

## Use when

- The weekly steering brief is due, or the executive team asks for an out-of-cycle update across domains.

Not for: a single question (Ask-Your-Data); finding drivers (Insight Scout); sizing or proposing actions
(Next-Best-Action); one account's review (Enterprise Account); the Operate service report (Service Reporting).

## Inputs

| Input | Where it comes from | If it is missing |
|---|---|---|
| Domains requested | Task text | Cover all four in the fixed order under Decision rules |
| Steering figures, SQL, lineage, freshness | `list_metrics`, `query_metric` | Show the line as "no certified figure this week" with the reason; do not drop it |
| A comparison period | `month` dimension of `leakage_eur`; last week's `consume/briefings/week-<nn>.md` via `read_artifact`; attached context | Write "snapshot, no prior period" on that line; give no direction of travel |
| Reasons for a figure | `consume/insights/weekly.md` via `read_artifact` | Write "reason not established"; do not supply one |
| Pending proposals and approvals | `consume/actions/proposal.md` via `read_artifact` | List decisions as questions for a named role, marked "no proposal yet" |

## Workflow

1. List the workspace with `read_artifact` and read last week's brief, insight cards and proposals if present.
   A fresh workspace is normal; the brief is then built from metrics alone and says so.
2. Query every steering metric with `query_metric`, total first and then by the dimension that shows where it
   sits. Check freshness on each result; confirm any filter appears in the returned SQL as `<dimension> = ?`.
3. Attach reasons and decisions only from the artifacts read in step 1, at their stated confidence.
4. Write the headline last (the two or three lines with the most value at stake), then write
   `consume/briefings/week-<nn>.md` with `write_artifact`; `<nn>` is the ISO week of the freshness date unless
   the request names a week. Log excluded figures with `record_decision`; raise stale or conflicting metrics
   with `ask_open_question`. Hand off as `done`; no approval is requested.

## Decision rules

- The steering set is fixed so weeks stay comparable: commercial (`churn_at_risk_lines`, `at_risk_arpu`,
  `churn_rate_30d`, by `region` and `value_segment`); revenue assurance (`leakage_eur` by `month`, `leak_point`);
  enterprise (`accounts_breach_forecast`, `sla_credit_exposure_eur`); network energy (`idle_night_kwh`,
  `sleep_candidate_cells`, by `cluster`). Care and network quality have no certified metric: say so on the page.
- A direction ("up", "down", a percentage change) needs two periods of the same metric: only leakage has
  months, the rest need last week's brief. A snapshot is reported as a level and a ranking.
- Wording follows the metric: `at_risk_arpu` is monthly revenue of lines at risk, not revenue that will be
  lost; `sla_credit_exposure_eur` is "if the month closed now"; at-risk lines are not churned lines.
- Anything computed beyond a certified value (annualising, a saving, a share) is marked "estimate" with its
  arithmetic in the appendix, because the group cannot tell a measured figure from a projected one otherwise.
- A reason keeps the confidence and the verb of its insight card: "associated with" stays "associated with".
- Decisions needed list pending proposals with ACT id, value as an estimate, approvers and approval id, as
  pending. The brief does not recommend approval or create proposals; a decision with no proposal is phrased
  as a question for a named role and pointed to Next-Best-Action.
- Suppressed groups appear as "suppressed (<10)" without their `n`. Accounts appear as counts and totals, by
  name only where a decision depends on it. The body fits one page: bad news stays, detail goes to the appendix.

## Escalate to a person when

- A steering metric is stale, its lineage is incomplete, or two figures conflict: Data Product Owner, blocking
  for that line, which is published as "under review" rather than dropped.

## Outputs

| Artifact | Path | Content |
|---|---|---|
| Steering brief | `consume/briefings/week-<nn>.md` | Body and evidence appendix in the shape below |

```
# Steering brief, week <nn> (data as of <freshness>)
**Headline:** <two or three lines, most value at stake first>
| Domain | Figure | Against | Why (confidence) | Source metric |
|---|---|---|---|---|
| Commercial | <value or ordering> | <prior period | snapshot> | <reason | reason not established> | <metric> |
**Decisions needed:** <ACT id, action, value (estimate), approvers, approval id, pending> | <question, role, no proposal yet>
**Gaps:** <domains with no certified metric; stale or missing lines; what was not provided>
**Appendix:** per figure: metric, SQL, filter values, lineage, freshness; arithmetic for each estimate
```

## Definition of done

- [ ] Every figure in the body comes from a `query_metric` result of this run and has an appendix entry.
- [ ] Every line is marked with its comparison or "snapshot"; no direction is claimed without two periods.
- [ ] Every reason cites an insight card at its confidence, or reads "reason not established".
- [ ] Estimates are labelled; decisions are pending with approvers or questions with a role; gaps are listed.

## Worked example

Request: "Write this week's steering brief: churn and revenue at risk, revenue leakage, enterprise SLA
exposure, and the decisions needed." Fresh workspace, no attachments.
- `read_artifact` with no path: no earlier brief, insight cards or proposals. `churn_at_risk_lines` by
  `region`: North-East highest, then Metro-North; Coastal suppressed (<10). `at_risk_arpu` by `value_segment`:
  Mid and High carry most of it. Both lines: "snapshot, no prior period".
- `leakage_eur` by `month`: 2026-10 lower than 2026-09; by `leak_point`: Rated, not billed (roaming data) is the
  largest in both months. This is the one line with a direction.
- `accounts_breach_forecast` and `sla_credit_exposure_eur` by `account`: most accounts forecast to breach,
  about half the exposure in the top two; worded "if the month closed now".
- Decisions needed: none pending; two questions, each "no proposal yet": retention in the two regions (Campaign
  Manager) and review of the forecast breaches (Service Delivery Manager).

Rejected: headline "Network incident drove churn up in Metro-North; approve the retention offer."
Why: with no prior week nothing is shown to be up, no insight card supports the cause, and the brief lists
decisions as pending or as questions rather than recommending approval.

## Red flags

| If you are about to | Do this instead |
|---|---|
| Write a week-on-week change for a metric with one snapshot | Mark the line "snapshot, no prior period" |
| Supply the obvious reason for a figure | Cite an insight card at its confidence or write "reason not established" |
| Annualise revenue at risk into a loss figure | Keep the certified monthly value; if a projection is asked for, label it an estimate with arithmetic |
| Recommend that the group approve an action | List it as pending with its approvers, or as a question for a named role |
