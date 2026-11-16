# Application and skill tuning review

| | |
|---|---|
| Date | 2026-11-16 |
| Scope | `AGENTS/` (26 agent definitions, 28 skills, `telcocrew` runtime) and the demo's Agents page |
| Outcome | Skills rewritten to authoring contract v2, eight runtime defects fixed, eval harness added |
| Not done | No run against the live Claude API (no key in the build environment). The live eval numbers are the next step |

## 1. What the research says

| Source | What it recommends | What we took from it |
|---|---|---|
| [Anthropic: Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md) | Add only what the model does not know; match degrees of freedom to how fragile the task is; description says what and when, third person; validate-fix feedback loops; templates and examples; one default, not menus; consistent terms; build evaluations first (at least three per skill) and test on every model you plan to use | Principles 1, 4, 5 of the contract; the Inputs fallback column; the eval harness and the `--model` switch |
| [dbt-labs/dbt-agent-skills](https://github.com/dbt-labs/dbt-agent-skills) (`using-dbt-for-analytics-engineering`) | "Look at the data" before and after writing SQL; iterate instead of one-shot; read existing metadata first; red-flag table of mistake and fix; query results and descriptions are data, not instructions | The sandbox validate-fix loop in the engineering, quality and semantic skills; the `Red flags` section |
| [wshobson/agents](https://github.com/wshobson/agents) (`incident-runbook-templates`) and similar SRE skills | Runbook shape: detection, triage, mitigation, verification, rollback, communication; verification after every step; a prerequisite per command; a separate communicator | The ordered propose, wait, execute, verify, roll back sequence in Resolution; verify with metric and time limit; Comms as its own agent |
| Anthropic prompt guidance for current models (prompt audit patterns) | Emphasis words and prohibition lists written for older models now over-steer; duplicated rules make the model reconcile wordings; step-by-step scripts for judgment work degrade output; tool descriptions should be a full contract; facts in prompts must match the code | Principles 2, 3, 6; the tool description rewrite; the "true to the runtime" test |
| [ADEF BuildWithAI](https://github.com/CloudKatasani/Agentic-Data-Engineering-Framework-BuildWithAI) (the reference for this repo) | Definition + skill split, gates, action classes, hash-bound approvals, grounding, worked examples with a rejected option | Kept. Version 2 changes the skill body, not the control model |

## 2. Findings

### Skills (version 1)

| # | Finding | Evidence | Fix |
|---|---|---|---|
| S1 | Skills described an environment the runtime does not have | 9 of 26 named things like `control/stack-profile.yaml`, "run dbt build", an onboarding pack under `09-publish/operate/`, an "autonomy register"; input and output file names did not line up between stages | Canonical artifact map and a table of what each tool really does in `AUTHORING.md`; a test that fails on these references |
| S2 | Risk of fabricated evidence | A skill that says "run dbt build, then run it again" with no tool to do so invites a model to report that it did | Shared rule "generated is not executed"; skills separate `executed` from `not_executed`; evals fail outputs such as "dbt build passed" |
| S3 | Agents stalled when run alone | "Reject the handoff if ..." rules, with no fallback; the Agents page runs single agents on a bare task | Every input has an "If it is missing" fallback (26 of 26 skills, was 0) |
| S4 | The same rule in four or five places | Hash binding, segregation of duties and A4 repeated across Decision rules, Do not, Enterprise controls, Failure modes and the shared guardrails | 14 sections reduced to 10; one place per rule; shared rules not restated |
| S5 | Prohibition-heavy, reason-light | 3.5 prohibitions and 0.3 stated reasons per skill | 1.2 prohibitions and 2.4 reasons per skill |
| S6 | Judgment work scripted step by step | Numbered procedures for mapping, diagnosis and briefing | Outcomes and checks; exact order kept only for propose, sign, execute, verify |
| S7 | Worked examples used invented tables and figures | Examples could not be reproduced | Examples use the synthetic estate; Build examples quote figures actually returned by the sandbox |
| S8 | No way to measure a change | No evals | 41 behaviour cases, every agent covered |

The skills did not get shorter (about 110 body lines each, similar character count). They got
denser and accurate: the space freed by removing repetition went to fallbacks, templates and
grounded examples.

### Runtime

| # | Finding | Severity | Fix |
|---|---|---|---|
| R1 | Restricted columns could be read with `SELECT c.*`, a sub-query or a CTE column list; the check was a text match on the SQL | High (guardrail bypass) | SQLite authorizer: Restricted columns return NULL however the statement is written; anything but a read is denied |
| R2 | `write_artifact` accepted `03-design/../../x`, escaping the workspace and, when persisting, the run folder | High | Paths are normalised; anything outside the agent's folder is refused |
| R3 | A web page on another site could POST to the local API (start runs, sign approvals) | Medium (local demo server) | POST must be `application/json` from the server's own origin; constant-time token compare |
| R4 | `query_metric` hid a small group's value but returned its size; a filter on a non-dimension was dropped silently, giving an unfiltered number | High for answers | Size hidden as `<10`; a bad filter is an error; returned SQL shows filter values |
| R5 | A live agent that finished without requesting its gate let the pipeline move on; a failed model call also moved on | High (control gap, live only) | The runtime raises the gate itself, bound to the agent's artifacts; a failed or empty stage stops the pipeline |
| R6 | On its second run, Resolution and the Publisher had no way to find the approval id they needed | High (live only) | New `list_approvals` tool; skills use the approval record, not a claim that someone approved |
| R7 | SQL errors raised an exception that ended the agent run | Medium | Errors come back as tool errors the agent can act on |
| R8 | No prompt caching: each turn re-sent about 22,000 characters of instructions | Cost and latency | System prompt and tools cached; usage and cost estimate account for cached tokens |
| R9 | Tool descriptions were one line | Quality | Each states what it does, when to use it, what returns and its limits |

## 3. Authoring contract v2

`AGENTS/AUTHORING.md`. Ten sections: Mission, Use when (with `Not for:`), Inputs (with fallback),
Workflow, Decision rules, Escalate to a person when, Outputs (with template), Definition of done
(checklist), Worked example (with a rejected option), Red flags. Tests enforce the structure, the
70 to 125 line budget, descriptions of at most 500 characters, no emphasis capitals, that a skill
names only tools its agent has, and that no retired runtime concept reappears.

## 4. Evals

`AGENTS/evals/cases.yaml`, run with `python -m telcocrew eval`.

- 41 cases; every agent has at least one. 35 run in the simulator and pass; 6 are live-only
  (pressure to execute without approval, an A4 request, a vague intake, a masking probe, an
  uncertified dimension, missing upstream artifacts).
- Each case checks behaviour, not wording: tools called, approval requests and roles, artifacts,
  required and forbidden output, nothing executed. Fake personal identifiers in any output fail
  the case.
- Each case has a rubric for `--judge` (Claude grades the transcript) or a human reviewer.

## 5. What to do next, with an API key

```bash
cd AGENTS && export ANTHROPIC_API_KEY=...
python -m telcocrew preflight
python -m telcocrew eval --mode live --judge                     # baseline on claude-opus-5-5
python -m telcocrew eval --mode live --model claude-sonnet-5-5   # does a faster model hold?
python -m telcocrew eval --mode live --model claude-haiku-5-5    # is there enough guidance for a small model?
```

Read the failing transcripts in `artifacts/EVAL-<timestamp>/`, change one rule in the skill with
its reason, rerun that agent's cases, and add a case for each behaviour fixed. Expect the first
live run to surface skill issues that a review cannot: this review tuned the skills against the
guidance and the runtime, not against observed model behaviour.

## 6. Open items

- Customer-facing messages are approved by the Service Delivery Manager alone. If your approval
  matrix wants a second role for mass customer contact, add it to the Comms definition.
- Several Build roles plan and specify more than they execute (model training, release
  rehearsal, dbt runs) because the demo has no such runtimes. Binding real tools is integration
  work; the skills already separate what was executed from what was not.
- The simulator still reports some illustrative figures (for example subscriber impact) that
  the live tools do not return; live agents label those as not quantified.
