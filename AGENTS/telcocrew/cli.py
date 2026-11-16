"""Command line: list agents, show a prompt, run an agent or a track pipeline, serve the API, write the manifest."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .guardrails import PEOPLE
from .registry import load_agents, manifest, system_prompt
from .runner import run_agent
from .tools import Session


def _print_events(s: Session, since: int = 0) -> int:
    for e in s.events[since:]:
        print(f"{e['ts']} {e['kind']:<7} {e['who']:<30} {e['text'][:220]}")
    return len(s.events)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="telcocrew", description="DataCrew Telco agents: Build, Operate, Consume")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="List agents by track")
    p = sub.add_parser("prompt", help="Print an agent's full system prompt")
    p.add_argument("agent")
    r = sub.add_parser("run", help="Run one agent on a task")
    r.add_argument("agent")
    r.add_argument("task")
    r.add_argument("--mode", choices=["live", "simulator"])
    w = sub.add_parser("pipeline", help="Run a Build or Operate pipeline; approvals are signed interactively or with --auto-approve")
    w.add_argument("track", choices=["build", "operate"])
    w.add_argument("request")
    w.add_argument("--mode", choices=["live", "simulator"])
    w.add_argument("--auto-approve", action="store_true", help="Simulated approvers sign every request (demo only)")
    sv = sub.add_parser("serve", help="Serve the API and the web demo")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8765)
    ds = sub.add_parser("datasets", help="Show the synthetic datasets in inputs/, or regenerate them")
    ds.add_argument("--generate", action="store_true", help="Rewrite inputs/datasets from the deterministic generator")
    ds.add_argument("--rows", type=int, default=6000)
    sub.add_parser("scenarios", help="List demo scenarios in inputs/scenarios")
    dm = sub.add_parser("demo", help="Run a scenario pack end to end; outputs go to artifacts/<run-id>/")
    dm.add_argument("scenario")
    dm.add_argument("--mode", choices=["live", "simulator"])
    dm.add_argument("--model", help="Override every agent's model (e.g. claude-sonnet-5-5 for a faster demo)")
    dm.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], help="Override every agent's effort")
    dm.add_argument("--auto-approve", action="store_true", help="Simulated approvers sign every request")
    pf = sub.add_parser("preflight", help="Check SDK, key, model access and inputs before a live demo")
    pf.add_argument("--model", default="claude-opus-5-5")
    mf = sub.add_parser("manifest", help="Write the agent catalog for the static web demo")
    mf.add_argument("--out", default=str(Path(__file__).resolve().parent.parent.parent / "demo" / "agents-manifest.js"))
    a = ap.parse_args(argv)

    if a.cmd == "list":
        for ag in load_agents().values():
            print(f"{ag.track:<8} {ag.id:<32} {ag.max_class}  gate={ag.gate or '-':<5} {ag.title}")
        return 0
    if a.cmd == "prompt":
        print(system_prompt(a.agent))
        return 0
    if a.cmd == "run":
        s = Session(persist=True)
        s.meta.update(agent=a.agent, task=a.task)
        res = run_agent(a.agent, a.task, s, a.mode)
        _print_events(s)
        print("\n" + res.final)
        print(f"\nstatus={res.status} approvals={res.approvals} run record -> {s.out_dir}")
        return 0
    if a.cmd == "pipeline":
        from .workflows import approve_all, build_pipeline, operate_pipeline
        pl = build_pipeline(a.request, a.mode) if a.track == "build" else operate_pipeline(a.request, a.mode)
        pl.session.persist = True
        print(f"Run record: {pl.session.out_dir}")
        seen = 0
        while True:
            status = pl.advance()
            seen = _print_events(pl.session, seen)
            if status != "waiting":
                break
            for aid in pl.waiting_on:
                apv = pl.session.approvals.items[aid]
                print(f"\n>> {aid} [{apv.action_class}] {apv.title}  approvers: {', '.join(apv.approvers)}  hash {apv.content_hash[:12]}")
            if a.auto_approve:
                approve_all(pl)
                continue
            ans = input("Decision for all pending requests [a]pprove / [c]hanges / [r]eject: ").strip().lower()[:1]
            decision = {"a": "approve", "c": "changes", "r": "reject"}.get(ans, "approve")
            comment = input("Comment: ") if decision != "approve" else ""
            approve_all(pl, decision, comment)
        print(json.dumps({k: pl.state()[k] for k in ("status", "artifacts", "audit_valid", "audit_entries")}, indent=1))
        return 0
    if a.cmd == "datasets":
        from . import data, inputs
        if a.generate:
            m = inputs.write_datasets(a.rows)
            data.reset()
            print(f"Wrote {inputs.datasets_dir()}")
        else:
            import yaml
            p = inputs.datasets_dir() / "MANIFEST.yaml"
            if not p.exists():
                print("No datasets folder; run `python -m telcocrew datasets --generate`.")
                return 1
            m = yaml.safe_load(p.read_text())
        for t, v in m["tables"].items():
            print(f"  {t:<24} {v['rows']:>7} rows  {v['system']:<10} {v['classification']}")
        print(f"  reference: {', '.join(m['reference'])}\n  operations: {', '.join(m['operations'])}")
        return 0
    if a.cmd == "scenarios":
        from .inputs import list_scenarios
        for sc in list_scenarios():
            print(f"{sc['track']:<8} {sc['id']:<28} {sc['kind']:<9} {sc['title']}  [{sc.get('live_duration_minutes', '')}]")
        return 0
    if a.cmd == "preflight":
        from . import data, inputs
        from .llm import preflight
        ok = True
        for name, passed, detail in preflight(a.model):
            ok &= passed
            print(f"  [{'ok' if passed else 'FAIL'}] {name}: {detail}")
        data.db()
        n = len(inputs.list_scenarios())
        print(f"  [ok] Synthetic datasets loaded from: {data.LOADED_FROM}")
        print(f"  [{'ok' if n else 'FAIL'}] Scenario packs: {n} in {inputs.scenarios_dir()}")
        from .tools import artifacts_dir
        print(f"  [ok] Artifacts will be written to: {artifacts_dir()}")
        print("Ready for a live demo." if ok and n else "Not ready for live mode; the simulator still works.")
        return 0 if ok else 2
    if a.cmd == "demo":
        from .inputs import load_scenario
        from .workflows import approve_all, scenario_pipeline
        sc = load_scenario(a.scenario)
        pl = scenario_pipeline(sc, a.mode, a.model, a.effort)
        print(f"Scenario: {sc['title']}  ({sc['track']}, {sc['kind']})\nPresenter notes: {sc.get('presenter_notes', '')}\n"
              f"Artifacts: {pl.session.out_dir}\n")
        seen = 0
        while True:
            status = pl.advance()
            seen = _print_events(pl.session, seen)
            if status != "waiting":
                break
            for aid in pl.waiting_on:
                apv = pl.session.approvals.items[aid]
                print(f"\n>> {aid} [{apv.action_class}] {apv.title}  approvers: {', '.join(apv.approvers)}  hash {apv.content_hash[:12]}")
            if a.auto_approve:
                approve_all(pl)
                continue
            ans = input("Decision for the pending request(s) [a]pprove / [c]hanges / [r]eject: ").strip().lower()[:1]
            decision = {"a": "approve", "c": "changes", "r": "reject"}.get(ans, "approve")
            comment = input("Comment: ") if decision != "approve" else ""
            approve_all(pl, decision, comment)
        for r in pl.results[-3:]:
            print("\n" + r["final"][:2500])
        print(f"\nStatus: {pl.status}. Run record: {pl.session.out_dir}")
        return 0
    if a.cmd == "serve":
        from .server import serve
        serve(a.host, a.port)
        return 0
    if a.cmd == "manifest":
        m = manifest()
        m["people"] = PEOPLE
        Path(a.out).write_text("/* Generated by `python -m telcocrew manifest`. Do not edit. */\nwindow.AGENTS_MANIFEST = "
                               + json.dumps(m, indent=1) + ";\n")
        print(f"wrote {a.out}: {len(m['agents'])} agents, {len(m['skills'])} skills")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
