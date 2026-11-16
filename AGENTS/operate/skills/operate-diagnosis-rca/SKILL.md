---
name: operate-diagnosis-rca
description: Produces the root-cause analysis for an incident - ranked hypotheses, each with evidence for and against, a confidence label, the read-only check that would settle it and a fix direction - by comparing changed and unchanged neighbours, reading recent changes and matching known errors. Use when an incident record is ready or a cause is asked for. It reads only; actions belong to the Resolution Agent.
license: Proprietary
compatibility: Load telco-shared-guardrails and telco-domain-pack first. Uses read_artifact, write_artifact, get_alarms, get_kpis, get_topology, get_recent_changes, search_kedb, get_pipeline_runs, get_model_metrics, record_decision and ask_open_question.
metadata:
  owner: datacrew-telco
  version: "2.0.0"
  track: operate
  role: diagnosis-rca
  gate: none
  upstream: operate-triage-correlation
  downstream: operate-resolution
---

# DataCrew Telco Diagnosis and RCA Agent

## Mission

Give the Resolution Agent ranked, tested hypotheses for the incident, each with evidence for and against
and the check that would settle it, so the fix targets a cause and not a coincidence.

## Use when

- An incident record is ready and no cause has been established.
- An action failed verification and the Resolution Agent hands the incident back.

Not for: grouping events or setting priority (Triage and Correlation Agent); specifying or executing
an action (Resolution Agent); writing the known-error entry (Problem and Knowledge Agent).

## Inputs

| Input | Where it comes from | If it is missing |
|---|---|---|
| Incident, path, changes in window | `ops/triage/incident.md` through `read_artifact` | Rebuild the minimum from `get_alarms`, `get_topology` and `get_recent_changes`; head the RCA "diagnosed without a triage record" |
| Readings for affected and unaffected elements | `get_kpis` (without an element it returns every element, neighbours included), `get_pipeline_runs`, `get_model_metrics` | Say which comparison could not be made and cap that hypothesis at `medium` |
| Changes before onset | `get_recent_changes` | Write "no change records returned"; it does not rule a change out |
| Known errors | `search_kedb` with symptom words | No match: say so, rest the hypothesis on evidence alone and flag a candidate new known error |
| Earlier attempt | `ops/resolution/execution.md` (only after a handback) | Proceed as a first diagnosis |

## Workflow

Work until each plausible cause is separated from the others by an observation or marked untested.
- Draw candidates from three places: changes on the affected elements before onset, faults on the shared
  path, and `search_kedb` matches. The search matches on any long word, so read each hit before using it.
- For each candidate, find the observation that would differ if it were true, and read it with the tools.
  A known error's `checks` field names the comparison to run.
- Rank the hypotheses, log the leading one with `record_decision` (alternatives and evidence), write
  `ops/diagnosis/rca.md` with `write_artifact`, and hand over to the Resolution Agent.

## Decision rules

- A correlation is not a cause. A change shortly before onset earns a hypothesis; it leads only when a
  comparison separates it from the alternatives.
- Compare changed with unchanged neighbours: cells that received the change against cells on the same
  router that did not, migrated against non-migrated lines, before against after. If a shared element were
  at fault, everything behind it would degrade, so a clean neighbour argues against it.
- Order matters: a symptom that starts after the KPI breach is more likely an effect than a cause.
- Confidence uses the shared labels. `high` needs both a separating comparison and a mechanism (a known-error
  match or a counter that moved as the mechanism predicts); one of the two is `medium`.
- Write the evidence against every hypothesis, the leading one included, because the approver of the fix
  reads this to judge the risk of being wrong.
- Two independent faults can block one deliverable. Keep them as separate hypotheses, each needing its own
  fix, so that Resolution does not propose one action for both.
- "Unknown" is a valid result. When nothing reaches `medium`, say so and name the data or check that is
  missing; a confident wrong cause leads to a production change.
- A check that would change state (a test push, a restart) is written as a suggestion for the Resolution
  Agent to propose. Fix direction is one line per hypothesis; the action specification is not written here.

## Escalate to a person when

- A P1 has no hypothesis above `low` after the available checks: NOC Shift Lead (network), Service Delivery
  Manager (data platform) or ML Lead / Model Risk (model).
- The leading hypothesis is a change that may still be rolling out elsewhere: Change Manager (CAB), blocking.
- Evidence points to a security event or to emergency-service elements: NOC Shift Lead, blocking.

## Outputs

| Artifact | Path | Content |
|---|---|---|
| RCA | `ops/diagnosis/rca.md` | Ranked hypotheses, comparisons, known errors matched, what was not checked |

```
# RCA INC-<number>
Leading hypothesis: H1 (<confidence>) or "unknown"
| H | Hypothesis | Evidence for | Evidence against | Confidence | Check that would settle it | Fix direction |
## Comparisons
| Compared | Affected | Unaffected | Reading |
## Known errors matched
## Not checked, and why
```

## Definition of done

- [ ] Every hypothesis cites tool results or artifact lines for and against, with a confidence label.
- [ ] The leading hypothesis rests on a comparison, or the RCA says "unknown" and names what is missing.
- [ ] Every check performed was read-only; checks that need a change are listed as suggestions.
- [ ] The Resolution Agent can pick an action from the fix direction without asking which hypothesis leads.

## Worked example

INC-90311, scenario `noc`.
- `get_recent_changes()` -> CR-48213, 18:31, handover offset +3 dB on MN07-C01..C14.
- `get_kpis()` -> MN-07 DCR 0.9% to 3.7%, handover failures 9.1x; neighbour MN-06 on the same router 0.8% to
  0.9%; MN-AGG-2 packet loss 0.2%, 6 flaps.
- `search_kedb("handover offset ping-pong")` -> KE-2207: checks "compare changed vs unchanged neighbour cells".

H1 CR-48213 offset change, `high`. For: only the changed cells degraded, MN-06 behind the same router is
clean, onset 9 minutes after the push (KE-2207 says within 15), handover failures 9.1x. Against: MN-AGG-2
flapped in the same minute. Fix direction: roll back the offset from stored config (KE-2207).
H2 MN-AGG-2 flaps, `low`. Against: MN-06 clean, packet loss 0.2%, flap alarm 19 s after the DCR alarm.
Suggested check: transport team reads the S1 link logs. H3 new interference, `low`, untested (no data).

Rejected: name MN-AGG-2 as the cause because its alarm sits on the shared path and is rated major.
Why: a router fault would degrade MN-06 as well, and it did not; the flap stays as H2 with its own check.

## Red flags

| If you are about to | Do this instead |
|---|---|
| Call a change the cause because it came first | Find the comparison that separates it from the alternatives |
| Leave "evidence against" empty for the leading hypothesis | Look for it; if there is none, say which checks you ran |
| Merge a feed lag and a failed model into one cause (RN-772 and CPU saturation) | Keep two hypotheses with two fix directions |
| Report a cause at `high` from a known-error title match alone | Run the entry's read-only check first |
