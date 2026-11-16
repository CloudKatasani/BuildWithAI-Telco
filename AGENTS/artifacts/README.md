# artifacts/

Every agent run, pipeline and scenario writes its full record here, one folder per run. The
folder is written as the run progresses, so you can open it during a live demo.

```
artifacts/RUN-20261116-181203-a1b2/
  run.json                    scenario, mode, model, status, steps, token usage and cost estimate, audit status
  inputs/request.md           the exact request the agents received (scenario runs)
  inputs/context.md           the context attached to the run (standards, answers, policies)
  workspace/                  every artifact the agents wrote, in their own folders
    00-intake/ ... 09-publish/      Build track
    ops/<agent>/                    Operate track
    consume/<agent>/                Consume track
  transcript.md               per agent: task, every tool call with arguments and result, final handoff
  approvals.json              every approval request: approvers, content hash, signatures, decision
  audit.jsonl                 append-only, SHA-256 hash-chained audit log
  events.jsonl                the live event stream shown in the web page
  decisions-and-questions.json  decision log and open questions raised by the agents
```

Run folders are ignored by Git (see `.gitignore`); only this README is committed. Delete old runs
whenever you like. Point the runtime somewhere else with `TELCOCREW_ARTIFACTS_DIR=/path`.

Everything here is produced from synthetic inputs and is AI-generated. In live mode the
transcript and `run.json` show which model produced it.
