"""Track workflows. A pipeline runs agents in order and pauses whenever a step creates approval requests;
it resumes only when every request of that step is fully signed by people."""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field

from .guardrails import sha
from .registry import get_agent
from .runner import run_agent
from .tools import Session

BUILD_STEPS = [
    "build-orchestrator", "build-business-analyst", "build-source-mapping", "build-governance-lineage",
    "build-solution-architect", "build-data-engineer", "build-quality-engineer", "build-ml-engineer",
    "build-release-engineer", "build-semantic-context", "build-data-product-publisher", "build-data-product-publisher",
]
OPERATE_STEPS = [
    "operate-watch-desk", "operate-triage-correlation", "operate-diagnosis-rca", "operate-resolution",
    "operate-resolution", "operate-comms", "operate-problem-knowledge", "operate-service-reporting",
]
STEP_TASKS = {
    "operate-resolution": ["Propose runbook actions for the top hypothesis.", "Execute the approved actions and verify."],
    "build-data-product-publisher": ["Prepare contract, listing and Operate pack; request G9.", "G9 is approved: publish the listing."],
}


@dataclass
class Pipeline:
    track: str
    request: str
    steps: list[str]
    mode: str | None = None
    session: Session = field(default_factory=Session)
    context: str = ""
    model: str | None = None
    effort: str | None = None
    id: str = field(default_factory=lambda: f"PL-{uuid.uuid4().hex[:6]}")
    idx: int = 0
    status: str = "ready"          # ready | running | waiting | done | stopped
    waiting_on: list[str] = field(default_factory=list)
    results: list[dict] = field(default_factory=list)
    revisions: int = 0

    def __post_init__(self):
        self._lock = threading.Lock()
        self._seen: dict[str, int] = {}

    # ---------------------------------------------------------------- one step
    def _task_for(self, agent_id: str, comment: str = "") -> str:
        n = self._seen.get(agent_id, 0)
        if getattr(self, "task_list", None):
            return self.task_list[min(self.idx, len(self.task_list) - 1)] + (f"\n\nReviewer requested changes: {comment}" if comment else "")
        extra = STEP_TASKS.get(agent_id, [])
        step_task = extra[min(n, len(extra) - 1)] if extra else ""
        task = f"{self.request}\n\n{step_task}".strip()
        if comment:
            task += f"\n\nReviewer requested changes: {comment}. Fix exactly that, keep all IDs, and request approval again."
        return task

    def _run_step(self, comment: str = "") -> None:
        agent_id = self.steps[self.idx]
        before = set(self.session.approvals.items)
        res = run_agent(agent_id, self._task_for(agent_id, comment), self.session, self.mode, self.context, self.model, self.effort)
        self._seen[agent_id] = self._seen.get(agent_id, 0) + 1
        new = [a for a in self.session.approvals.items if a not in before]
        if res.status == "blocked":      # a model or runtime failure never passes a stage silently
            self.results.append({"step": self.idx, "agent": agent_id, "status": "blocked", "approvals": new, "final": res.final})
            self.status = "stopped"
            self.session.emit("blocked", "runtime", f"{agent_id} could not finish ({res.final[:160]}). Pipeline stopped at this step.")
            return
        agent = get_agent(agent_id)
        gate_open = any(a.content.get("gate") == agent.gate and a.status in ("pending", "approved")
                        for a in self.session.approvals.items.values()) if agent.gate else True
        if agent.gate and not gate_open:
            # The stage ended without asking for its gate. People still decide: the runtime raises the request itself,
            # bound to everything the agent wrote, and says so.
            mine = {p: sha(c) for p, c in self.session.artifacts.items() if p.startswith(agent.workspace)}
            if not mine:
                self.results.append({"step": self.idx, "agent": agent_id, "status": "blocked", "approvals": new, "final": res.final})
                self.status = "stopped"
                self.session.emit("blocked", "runtime", f"{agent_id} produced no artifacts and requested no gate. Pipeline stopped.")
                return
            ap = self.session.approvals.request(
                kind="gate", title=f"{agent.gate} - {agent.title.replace(' Agent', '')}", requested_by=agent_id,
                action_class="A3" if len(set(agent.approvers)) > 1 else "A2", approvers=agent.approvers, run_id=self.session.id,
                content={"gate": agent.gate, "summary": "Raised by the runtime: the agent finished without requesting its gate.",
                         "risks": "Review the handoff for anything the agent left open.", "artifacts": mine})
            new.append(ap.id)
            self.session.emit("gate", "runtime", f"{agent_id} did not request {agent.gate}; the runtime raised {ap.id} for "
                                                 f"{', '.join(agent.approvers)}", approval_id=ap.id)
        if agent_id == "operate-problem-knowledge":
            ke = [p for p in self.session.artifacts if p.startswith("ops/problem/")]
            if ke:   # the runtime asks the Problem Manager to approve the known-error entry the agent drafted
                ap = self.session.approvals.request(kind="knowledge", title="Known-error entry update", requested_by=agent_id,
                                                    action_class="A2", approvers=["Problem Manager"],
                                                    content={p: self.session.artifacts[p] for p in ke}, run_id=self.session.id)
                new.append(ap.id)
                self.session.emit("gate", agent_id, f"Approval requested: {ap.id} -> Problem Manager", approval_id=ap.id)
        self.results.append({"step": self.idx, "agent": agent_id, "status": res.status, "approvals": new, "final": res.final})
        pending = [a for a in new if self.session.approvals.items[a].status == "pending"]
        if pending:
            self.status, self.waiting_on = "waiting", pending
        else:
            self.idx += 1
            self.status = "running" if self.idx < len(self.steps) else "done"

    # ---------------------------------------------------------------- drive
    def advance(self, max_steps: int = 50) -> str:
        """Run steps until the pipeline waits for people, finishes or is stopped."""
        with self._lock:
            for _ in range(max_steps):
                if self.status in ("done", "stopped"):
                    break
                if self.status == "waiting":
                    states = [self.session.approvals.items[a] for a in self.waiting_on]
                    if any(a.status == "rejected" for a in states):
                        self.status = "stopped"
                        self.session.emit("blocked", "runtime", "A reviewer rejected the request. Pipeline stopped; nothing further runs.")
                        break
                    changes = [a for a in states if a.status == "changes"]
                    if changes:
                        if self.revisions >= 3:
                            self.status = "stopped"
                            self.session.emit("blocked", "runtime", "Return limit reached; escalated to the Data Product Owner.")
                            break
                        self.revisions += 1
                        self.waiting_on = []
                        self.status = "running"
                        self._run_step(comment=changes[0].comment)
                        continue
                    if all(a.status == "approved" for a in states):
                        self.waiting_on, self.idx = [], self.idx + 1
                        self.status = "running" if self.idx < len(self.steps) else "done"
                        continue
                    break
                self.status = "running"
                self._run_step()
            if self.status == "done":
                self.session.emit("done", "runtime", f"{self.track} pipeline complete. Audit chain valid: {self.session.audit.verify()}")
            self.session.meta.update(pipeline=self.track, pipeline_status=self.status, step=self.idx, steps=self.steps)
            self.session.flush()
            return self.status

    def state(self) -> dict:
        s = self.session
        return {"id": self.id, "run_record": str(s.out_dir) if s.persist else None, "meta": s.meta, "track": self.track, "request": self.request, "status": self.status, "step": self.idx,
                "steps": self.steps, "waiting_on": self.waiting_on, "results": self.results,
                "approvals": [a.as_dict() for a in s.approvals.items.values()], "artifacts": sorted(s.artifacts),
                "questions": s.questions, "events": s.events[-200:], "audit_valid": s.audit.verify(), "audit_entries": len(s.audit.entries)}


def build_pipeline(request: str, mode: str | None = None, with_ml: bool | None = None, **kw) -> Pipeline:
    steps = list(BUILD_STEPS)
    if with_ml is False or (with_ml is None and any(k in request.lower() for k in ("sla", "enterprise", "b2b"))):
        steps.remove("build-ml-engineer")
    return Pipeline("build", request, steps, mode, **kw)


def operate_pipeline(request: str, mode: str | None = None, **kw) -> Pipeline:
    return Pipeline("operate", request, list(OPERATE_STEPS), mode, **kw)


def scenario_pipeline(sc: dict, mode: str | None = None, model: str | None = None, effort: str | None = None,
                      persist: bool = True) -> Pipeline:
    """A pipeline for a scenario pack (inputs/scenarios/<id>). Agent-kind scenarios run their tasks as steps."""
    session = Session(persist=persist, ops_scenario=sc.get("ops_scenario"))
    session.meta.update(scenario=sc["id"], title=sc.get("title"), track=sc["track"])
    kw = dict(session=session, context=sc.get("context", ""), model=model, effort=effort)
    if persist:   # keep the exact inputs next to the outputs
        d = session.out_dir / "inputs"
        d.mkdir(parents=True, exist_ok=True)
        (d / "request.md").write_text(sc.get("request") or "\n\n".join(sc.get("tasks", [])))
        if sc.get("context"):
            (d / "context.md").write_text(sc["context"])
    if sc.get("kind") == "agent":
        p = Pipeline(sc["track"], sc["tasks"][0], [sc["agent"]] * len(sc["tasks"]), mode, **kw)
        p.task_list = list(sc["tasks"])
        return p
    if sc["track"] == "build":
        return build_pipeline(sc["request"], mode, sc.get("with_ml"), **kw)
    return operate_pipeline(sc["request"], mode, **kw)


def approve_all(p: Pipeline, decision: str = "approve", comment: str = "") -> None:
    """Demo helper: each named person signs every pending request of the step (simulated approvers)."""
    from .guardrails import PEOPLE
    for aid in list(p.waiting_on):
        ap = p.session.approvals.items[aid]
        for role in ap.approvers:
            if ap.status == "pending" and role not in ap.signatures:
                p.session.approvals.sign(aid, role, PEOPLE[role], decision, comment)
