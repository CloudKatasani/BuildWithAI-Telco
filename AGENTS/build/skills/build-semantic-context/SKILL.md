---
name: build-semantic-context
description: Produces the semantic view for a telco data product - certified metric definitions tied to business rules, dimensions and synonyms, a verified question (VQ) with reference SQL and expected answer for every consumer question, AI context for assistants, and refusal tests for personal data and out-of-scope questions - and requests G8. Use after release planning, when a consumer adds a question, or when a metric definition changes.
license: Proprietary
compatibility: Loaded after telco-shared-guardrails and telco-domain-pack. Uses only the tools in the agent definition.
metadata:
  owner: datacrew-telco
  version: "2.0.0"
  track: build
  role: semantic-context-engineer
  gate: G8
  upstream: build-release-engineer
  downstream: build-data-product-publisher
---

# DataCrew Telco Semantic and AI Context Agent

## Mission

Make every consumer question answerable through one governed definition per metric, by people and by the
Consume assistants, with a reference answer that proves it. The Data Steward and the Data Product Owner
certify the result at G8.

## Use when

- Gold objects exist and consumer questions need metrics and verified questions.
- A consumer adds a question, or a metric definition or dimension changes.

Not for: defining the business rule behind a metric (build-business-analyst); changing gold tables
(build-solution-architect); the contract and listing (build-data-product-publisher).

## Inputs

| Input | Where it comes from | If it is missing |
|---|---|---|
| `BR` and `CQ` | `read_artifact` on `01-requirements/requirements.md` | Take questions from the brief or task text; mark each metric `assumption: no BR` and ask the Data Product Owner before G8 |
| Gold objects and columns | `read_artifact` on `03-design/design.md`; `run_sandbox_sql` | Query the gold table to list its columns; an object that does not exist in the sandbox gets metrics marked "reference answer not executed" |
| Lineage of each gold object | `get_lineage` | `complete: false`: the metric is not proposed for certification; report it to build-governance-lineage |
| Term definitions and stewards | `lookup_glossary` | No match: use the `BR` wording, list a glossary gap, owner Data Steward |
| Dimension entities | `lookup_sid` | No match: describe the dimension in plain words |
| Minimisation level per dimension | `read_artifact` on `02-mapping/mapping.md` | Offer region, segment and cluster only; nothing below cluster |
| Freshness of gold | Design, `NFR` | State "freshness not specified" in the AI context and ask the Data Product Owner |

## Workflow

- Define metrics: one per business measure, each from one `BR`, with formula in words, expression, grain,
  filters, unit, allowed dimensions and owner. Check wording with `lookup_glossary`.
- Define dimensions and synonyms; align entities with `lookup_sid`.
- Confirm lineage with `get_lineage` for every gold object a metric reads.
- Write at least one `VQ` per `CQ`. Run its reference SQL with `run_sandbox_sql`, read the result, apply
  small-group suppression, and store the expected answer. If the result does not answer the question as the
  consumer asked it, fix the metric or dimension and rerun.
- Write the AI context: which metric answers which kind of question, default time grain, how to state
  freshness, and when to refuse.
- Write refusal tests. One can be executed here: a query naming a Restricted column is refused by the
  sandbox. The others (out-of-scope domain, metric redefinition, single-subscriber detail) are recorded as
  expected behaviour for the Consume track, with status `specified`.
- Record metric conflicts with `record_decision`, write `08-semantic/semantic-view.md`, call `request_gate`
  and stop.

## Decision rules

- One metric, one definition, one owner, one `BR`. Two definitions go to the Data Product Owner first,
  because care, marketing and finance have to quote the same number.
- A ratio is the sum of numerators over the sum of denominators at the queried grain. Averaging per-group
  rates weights small groups like large ones and will not match finance.
- Expected answers already apply suppression: a group under 10 subscribers is shown as `suppressed`, since
  the Consume runtime suppresses it and an unsuppressed reference would fail every later comparison.
- Dimensions stop at the mapping's minimisation level. No Restricted column is a dimension, a filter or a
  synonym target.
- A `CQ` that cannot be answered from gold gets a written reason and an owner, not a weaker metric that
  answers a different question.
- Counts match the reference exactly; amounts match to the rounding stated in the metric.
- Reference SQL is plain SELECT over gold tables so the sandbox can run it. The semantic view is a generated
  definition; it is deployed by the client platform after G8.
- The AI context is instructions for another model. Write it as short direct statements with the reason, and
  include the refusal wording for personal data.

## Escalate to a person when

- Two consumers need different definitions of one metric: Data Product Owner.
- A question can be answered only at single-subscriber level: Security & Privacy Officer.
- Gold freshness cannot support the time grain a question needs: Data Product Owner.
- A reference answer contradicts a worked example in the requirements: Data Steward.

## Outputs

| Artifact | Path | Content |
|---|---|---|
| Semantic view | `08-semantic/semantic-view.md` | Metrics, dimensions, synonyms, `VQ` with SQL and expected answers, AI context, refusal tests |

```markdown
# Semantic view: SEMANTIC.<product>
### Metrics
| Metric | BR | Definition | Expression | Filter | Gold object | Dimensions | Unit, rounding | Owner |
### Dimensions and synonyms
### Verified questions
VQ-001 (CQ-001) "<question>" - metric, dimensions, filters
SQL: <SELECT over gold>      Expected: <rows; groups under 10 shown as suppressed>
Executed: yes (date) | no (reason)      Lineage complete: yes | no
### AI context           preferred metrics, default grain, freshness statement, refusal rules
### Refusal tests        | Test | Request | Expected | Status: executed / specified |
### Unanswerable questions | CQ | Reason | Owner |
```

## Definition of done

- [ ] Every metric cites one `BR`, one gold object with complete lineage, and an owner.
- [ ] Every `CQ` has a `VQ` with executed reference SQL and expected answer, or a written reason.
- [ ] No expected answer shows a group under 10 subscribers; no Restricted column is exposed.
- [ ] Each refusal test is marked `executed` or `specified`; none is reported as passed untested.
- [ ] The publisher can copy metrics and sample questions from the file; G8 was requested on it.

## Worked example

Churn run. CQ-001 "Which regions have the highest churn risk this week?" CQ-002 "How much monthly revenue is
at risk?"

- `lookup_glossary` "at-risk arpu": monthly ARPU of lines with churn score >= 0.7.
- `churn_at_risk_lines` = COUNT(*) where `risk_score >= 0.7` (BR-001); dimensions region, value_segment,
  top_driver. `at_risk_arpu` = ROUND(SUM(arpu), 2), same filter.
- VQ-001, `run_sandbox_sql` on `gld_churn_risk` by region: North-East 80, Metro-North 62, Industrial-South
  11, Capital 10, Coastal 9. Expected answer stores Coastal as `suppressed`.
- VQ-002: 172 lines, EUR 6,715.24 per month.
- `get_lineage` `gld_churn_risk`: complete.
- Refusal test R-01 "list the MSISDN of at-risk lines in North-East": `SELECT msisdn ...` refused by the
  sandbox, `executed`. R-02 "what is churn if we use 60 days": `specified`.

Rejected: `churn_rate_30d` for all regions as the average of the five regional rates (3.97%).
Why: the metric is SUM(churned_30d) / COUNT(*) = 237 / 6,000 = 3.95%; averaging rates misweights regions and
would differ from finance.

## Red flags

| If you are about to | Do this instead |
|---|---|
| Store an expected answer you did not run | Run the reference SQL, or mark the `VQ` "not executed" with the reason |
| Add a metric because it seems useful | Tie it to a `BR`, or raise it with the Business Analyst |
| Report "refusal tests 3/3 pass" | Mark each test `executed` or `specified` |
| Keep a 9-line group in a reference answer | Store it as `suppressed` |
| Offer cell or subscriber as a dimension on subscriber metrics | Stop at region, segment or cluster as the mapping allows |
