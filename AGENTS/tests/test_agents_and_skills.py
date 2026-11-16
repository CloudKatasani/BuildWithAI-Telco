"""The agent and skill files are the product's instructions: keep them to the authoring contract."""
import re

import pytest

from telcocrew.registry import CLASS_ORDER, ROOT, SHARED_SKILLS, TRACKS, load_agents, load_skills, split_frontmatter, system_prompt
from telcocrew.tools import TOOLS

AGENTS = load_agents()
SKILLS = load_skills()
SECTIONS = ["Mission", "Use when", "Do not use for", "Inputs", "Tasks", "Decision rules", "Do not",
            "Escalate to the human when", "Enterprise controls", "Self-review before handover", "Outputs",
            "Definition of done", "Worked example", "Common failure modes"]
ROLES = {"Data Product Owner", "Data Architect", "Data Steward", "Engineering Lead", "QA Lead", "Change Manager (CAB)",
         "Security & Privacy Officer", "ML Lead / Model Risk", "NOC Shift Lead", "Service Delivery Manager",
         "Problem Manager", "Campaign Manager", "Customer Care Lead", "Research Lead"}
EXPECTED = {"build": 11, "operate": 9, "consume": 6}


def test_every_track_has_its_agents():
    for t in TRACKS:
        assert sum(a.track == t for a in AGENTS.values()) == EXPECTED[t], t


@pytest.mark.parametrize("agent_id", sorted(AGENTS))
def test_agent_definition_follows_contract(agent_id):
    a = AGENTS[agent_id]
    m = a.meta
    assert m["name"] == agent_id == a.path.stem
    assert m["title"].endswith(" Agent")
    assert m["track"] == a.track
    assert m["max_action_class"] in CLASS_ORDER and m["max_action_class"] != "A4"
    assert a.skills[:2] == list(SHARED_SKILLS) and agent_id in a.skills
    assert all(s in SKILLS for s in a.skills), [s for s in a.skills if s not in SKILLS]
    assert set(a.approvers) <= ROLES, set(a.approvers) - ROLES
    assert {"read_artifact", "write_artifact"} <= set(a.tools)
    for t in a.tools:
        assert t in TOOLS, f"{agent_id} declares unknown tool {t}"
        assert a.track in TOOLS[t].tracks, f"{t} is not a {a.track} tool"
    if a.gate:
        assert "request_gate" in a.tools and a.approvers
    assert a.body.startswith(f"You are the DataCrew Telco {m['title']}.")
    assert "Tool policy" in a.body
    for key in ("expects", "produces", "does", "does_not"):
        assert m.get(key), f"{agent_id} missing {key}"
        assert all(isinstance(x, str) for x in m[key]), f"{agent_id} {key} has a non-text item (quote items with a colon)"


def test_gates_are_unique_and_complete():
    gates = sorted(a.gate for a in AGENTS.values() if a.gate)
    assert gates == [f"G{i}" for i in range(10)]


@pytest.mark.parametrize("agent_id", sorted(AGENTS))
def test_skill_has_every_section_in_order(agent_id):
    s = SKILLS[agent_id]
    meta = s.meta
    assert meta["name"] == agent_id and meta["metadata"]["version"] == "1.0.0"
    assert meta["metadata"]["track"] == AGENTS[agent_id].track
    heads = re.findall(r"^## (.+)$", s.body, flags=re.M)
    assert heads == SECTIONS, heads
    review = s.body.split("## Self-review before handover")[1].split("\n## ")[0]
    assert all(x in review for x in ("*Accuracy.*", "*Risk.*", "*Handover.*"))
    example = s.body.split("## Worked example")[1].split("\n## ")[0]
    assert re.search(r"Rejected:.*\n(?:.*\n)*?.*Why:", example)
    assert 60 <= len(s.body.splitlines()) <= 200
    assert "ADEF" not in s.body


@pytest.mark.parametrize("agent_id", sorted(AGENTS))
def test_system_prompt_carries_every_declared_skill(agent_id):
    p = system_prompt(agent_id)
    for name in AGENTS[agent_id].skills:
        assert f"# Skill: {name}" in p
    assert p.index("# Skill: telco-shared-guardrails") < p.index("# Skill: telco-domain-pack") < p.index(f"# Skill: {agent_id}")
    assert "# Runtime contract" in p and "\n---\nname:" not in p


def test_shared_skills_exist_and_cover_core_rules():
    g = SKILLS["telco-shared-guardrails"].body
    for must in ("A4 Prohibited", "MSISDN", "segregation", "hash", "Untrusted content", "Escalate"):
        assert must.lower() in g.lower(), must
    d = SKILLS["telco-domain-pack"].body
    for must in ("TMF621", "TMF639", "SID", "DCR", "TEL-C4", "L4"):
        assert must in d, must


def test_skill_files_parse_and_nothing_is_orphaned():
    for p in ROOT.glob("*/skills/*/SKILL.md"):
        meta, body = split_frontmatter(p.read_text())
        assert meta.get("name") == p.parent.name
        assert p.parent.name in SHARED_SKILLS or p.parent.name in AGENTS, f"orphan skill {p.parent.name}"
