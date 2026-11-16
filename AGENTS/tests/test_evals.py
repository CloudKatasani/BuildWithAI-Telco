"""The eval harness: every simulator-playable case passes, every agent is covered, and failures are detected."""
import pytest

from telcocrew.evals import check, load_cases, run_case
from telcocrew.registry import load_agents
from telcocrew.runner import run_agent
from telcocrew.tools import Session

CASES = load_cases()


def test_every_agent_has_an_eval_and_cases_are_well_formed():
    agents = load_agents()
    covered = {c["agent"] for c in CASES}
    assert covered == set(agents), set(agents) - covered
    for c in CASES:
        assert c["task"] and c.get("rubric"), c["id"]
        assert all(a in agents for a in c.get("setup", [])), c["id"]
        assert c.get("expect") or c.get("live"), c["id"]


@pytest.mark.parametrize("case", [c for c in CASES if not c.get("live_only")], ids=lambda c: c["id"])
def test_case_passes_in_the_simulator(case):
    out = run_case(case, "simulator")
    assert out["passed"], out["failures"]


def test_checks_detect_real_failures():
    case = {"id": "x", "agent": "consume-ask-your-data", "task": "Which regions have the highest churn risk?",
            "expect": {"calls": ["propose_business_action"], "approvals": 1, "artifacts": ["nope.md"], "output_all": ["zebra"],
                       "output_none": ["Metro-North"], "status": ["needs-approval"]}}
    s = Session()
    res = run_agent(case["agent"], case["task"], s, "simulator")
    fails = check(case, res, s, set(), "simulator")
    assert len(fails) == 6, fails


def test_leaked_identifiers_fail_any_case():
    case = {"id": "x", "agent": "consume-insight-scout", "task": "t", "expect": {}}
    s = Session()
    res = run_agent(case["agent"], case["task"], s, "simulator")
    res.final += "\nCall +999 045 350 4657"
    assert any("forbidden pattern" in f for f in check(case, res, s, set(), "simulator"))
