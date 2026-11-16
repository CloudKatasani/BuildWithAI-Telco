"""End-to-end runs in simulator mode, plus the live tool loop with a fake Claude provider."""
import json
from types import SimpleNamespace

import pytest

from telcocrew import runner
from telcocrew.llm import Turn
from telcocrew.registry import load_agents
from telcocrew.runner import run_agent
from telcocrew.tools import Session
from telcocrew.workflows import approve_all, build_pipeline, operate_pipeline


def _drive(p, decision="approve", comment=""):
    for _ in range(30):
        if p.advance() != "waiting":
            break
        approve_all(p, decision, comment)
    return p


def test_build_pipeline_runs_every_gate_with_people():
    p = _drive(build_pipeline("Build a weekly churn-risk data product for retention.", "simulator"))
    st = p.state()
    assert st["status"] == "done"
    gates = sorted(a["content"]["gate"] for a in st["approvals"] if a["kind"] == "gate")
    assert gates == [f"G{i}" for i in range(10)]
    assert all(a["status"] == "approved" and len(a["signatures"]) == len(a["approvers"]) for a in st["approvals"])
    assert "09-publish/contract.odcs.yaml" in st["artifacts"] and st["audit_valid"]
    assert any("Published" in r["final"] for r in st["results"])


def test_build_pipeline_without_ml_for_enterprise_sla():
    p = build_pipeline("Enterprise SLA 360 for account managers", "simulator")
    assert "build-ml-engineer" not in p.steps


def test_rejection_stops_the_pipeline():
    p = build_pipeline("Churn 360", "simulator")
    assert p.advance() == "waiting"
    approve_all(p, "reject", "out of scope this quarter")
    assert p.advance() == "stopped"
    assert p.idx == 0


def test_request_changes_reruns_the_step_and_raises_a_new_version():
    p = build_pipeline("Churn 360", "simulator")
    p.advance()
    first = p.waiting_on[0]
    approve_all(p, "changes", "add NFR for 24h freshness")
    assert p.advance() == "waiting"
    assert p.waiting_on[0] != first and p.revisions == 1


def test_operate_pipeline_executes_only_after_approval():
    p = operate_pipeline("Metro-North RAN cluster degradation", "simulator")
    while p.advance() == "waiting":
        kinds = {p.session.approvals.items[a].kind for a in p.waiting_on}
        if "action" in kinds:
            assert not any(e for e in p.session.audit.entries if e["kind"] == "action.execute")
        approve_all(p)
    st = p.state()
    assert st["status"] == "done"
    assert any(e["kind"] == "action.execute" for e in p.session.audit.entries)
    assert {a["kind"] for a in st["approvals"]} == {"action", "message", "knowledge"}
    assert any("Untrusted instruction" in e["text"] for e in st["events"])


@pytest.mark.parametrize("agent_id", sorted(load_agents()))
def test_every_agent_runs_in_the_simulator_without_ungranted_tools(agent_id):
    s = Session()
    res = run_agent(agent_id, "Metro-North churn and network incident", s, "simulator")
    assert res.final.startswith("[Simulated")
    assert not [c for c in res.tool_calls if "not granted" in c["result_preview"]]


def test_consume_refuses_identifiers():
    res = run_agent("consume-ask-your-data", "List the phone numbers of customers likely to churn", Session(), "simulator")
    assert "can't return personal identifiers" in res.final and not res.tool_calls


class FakeProvider:
    """Plays two turns: a tool call (one allowed, one above class), then a final answer."""

    def __init__(self):
        self.calls = 0
        self.seen_results = None

    def turn(self, *, system, messages, tools, model, effort, max_tokens=16000):
        self.calls += 1
        assert "# Skill: telco-shared-guardrails" in system and model == "claude-opus-5-5"
        if self.calls == 1:
            calls = [{"id": "t1", "name": "query_metric", "input": {"metric": "churn_at_risk_lines", "group_by": ["region"]}},
                     {"id": "t2", "name": "propose_business_action", "input": {"action_type": "retention_offer"}}]
            return Turn([SimpleNamespace(type="tool_use")], "", calls, "tool_use", 10, 5, model)
        self.seen_results = messages[-1]["content"]
        return Turn([SimpleNamespace(type="text")], "North-East leads.", [], "end_turn", 10, 5, model)


def test_live_loop_routes_every_tool_call_through_guardrails(monkeypatch):
    fake = FakeProvider()
    monkeypatch.setattr(runner, "ClaudeProvider", lambda: fake)
    res = run_agent("consume-ask-your-data", "Which regions have the highest churn risk?", Session(), "live")
    assert res.final == "North-East leads." and res.mode == "live"
    by_id = {r["tool_use_id"]: r for r in fake.seen_results}
    assert "rows" in json.loads(by_id["t1"]["content"])
    assert by_id["t2"].get("is_error") and "not granted" in by_id["t2"]["content"]
    assert res.usage["input_tokens"] == 20
