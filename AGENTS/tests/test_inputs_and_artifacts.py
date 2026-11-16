"""Inputs (synthetic datasets, scenario packs) and the per-run artifacts folder."""
import csv
import json
import os

import pytest
import yaml

from telcocrew import data, inputs
from telcocrew.registry import load_agents
from telcocrew.runner import run_agent
from telcocrew.workflows import approve_all, scenario_pipeline

SCENARIOS = [s["id"] for s in inputs.list_scenarios()]


def test_datasets_are_loaded_from_the_inputs_folder():
    data.db()
    assert data.LOADED_FROM == str(inputs.datasets_dir())
    manifest = yaml.safe_load((inputs.datasets_dir() / "MANIFEST.yaml").read_text())
    for table, meta in manifest["tables"].items():
        assert data.query(f"SELECT COUNT(*) FROM {table}")[1][0][0] == meta["rows"], table
    assert data.METRICS and data.ALARMS and data.SOURCES


def test_committed_datasets_match_the_generator():
    gen = data.generate_tables()
    for table in ("gld_churn_risk", "crm_customer", "pm_cell_kpi"):
        with open(inputs.datasets_dir() / "tables" / f"{table}.csv", newline="") as f:
            rows = list(csv.reader(f))[1:]
        assert len(rows) == len(gen[table])
        assert [str(v) for v in gen[table][0]] == rows[0]


def test_personal_looking_values_are_fake_and_restricted():
    with open(inputs.datasets_dir() / "tables" / "crm_customer.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert all(r["msisdn"].startswith("+999 ") for r in rows)
    assert data.classification_of("crm_customer", "msisdn") == "Restricted"


def test_scenarios_are_valid():
    agents = load_agents()
    assert len(SCENARIOS) >= 10
    for sid in SCENARIOS:
        sc = inputs.load_scenario(sid)
        assert sc["track"] in ("build", "operate", "consume") and sc["kind"] in ("pipeline", "agent")
        assert sc.get("presenter_notes") and sc.get("datasets")
        if sc["kind"] == "agent":
            assert sc["agent"] in agents and agents[sc["agent"]].track == sc["track"] and sc["tasks"]
        else:
            assert sc["request"]
        if sc["track"] == "operate":
            assert sc["ops_scenario"] in ("noc", "dataops", "mlops")


def test_unknown_or_unsafe_scenario_id_is_rejected():
    with pytest.raises(KeyError):
        inputs.load_scenario("../../etc")


@pytest.mark.parametrize("sid", SCENARIOS)
def test_every_scenario_runs_and_writes_a_complete_run_record(sid, tmp_path, monkeypatch):
    monkeypatch.setenv("TELCOCREW_ARTIFACTS_DIR", str(tmp_path))
    sc = inputs.load_scenario(sid)
    p = scenario_pipeline(sc, "simulator")
    for _ in range(40):
        if p.advance() != "waiting":
            break
        approve_all(p)
    assert p.status == "done"
    d = p.session.out_dir
    for f in ("run.json", "transcript.md", "approvals.json", "audit.jsonl", "events.jsonl", "inputs/request.md"):
        assert (d / f).exists(), f
    run = json.loads((d / "run.json").read_text())
    assert run["scenario"] == sid and run["pipeline_status"] == "done" and run["audit_valid"]
    for path in run["artifacts"]:
        assert (d / "workspace" / path).exists()
    assert "AI-generated" in (d / "transcript.md").read_text()


def test_operate_tools_default_to_the_scenario_of_the_session(tmp_path, monkeypatch):
    monkeypatch.setenv("TELCOCREW_ARTIFACTS_DIR", str(tmp_path))
    p = scenario_pipeline(inputs.load_scenario("operate-churn-mart-sla"), "simulator")
    from telcocrew.registry import get_agent
    from telcocrew.tools import Ctx, run_tool
    res, _ = run_tool(Ctx(p.session, get_agent("operate-watch-desk")), "get_alarms", {})
    assert {a["scenario"] for a in res["alarms"]} == {"dataops"}


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="live test needs ANTHROPIC_API_KEY")
def test_live_claude_answers_through_the_semantic_layer(tmp_path, monkeypatch):
    monkeypatch.setenv("TELCOCREW_ARTIFACTS_DIR", str(tmp_path))
    from telcocrew.tools import Session
    s = Session(persist=True)
    res = run_agent("consume-ask-your-data", "Which regions have the highest churn risk this week?", s, "live", effort="low")
    assert res.status == "done" and any(c["tool"] == "query_metric" for c in res.tool_calls)
    assert res.usage["input_tokens"] > 0 and s.audit.verify()
