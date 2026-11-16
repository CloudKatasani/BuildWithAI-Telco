"""Run one agent on one task. Live mode: Claude drives the tool loop. Simulator mode: a deterministic script
drives the same tools. In both modes every tool call goes through tools.run_tool (guardrails, audit)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from .guardrails import redact, untrusted
from .llm import ClaudeProvider, LLMError, live_available, validate_input
from .registry import get_agent, system_prompt
from .tools import TOOLS, Ctx, Session, run_tool, tools_for

MAX_TURNS = 24


@dataclass
class AgentResult:
    agent: str
    mode: str
    final: str
    tool_calls: list[dict] = field(default_factory=list)
    approvals: list[str] = field(default_factory=list)
    status: str = "done"
    usage: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _record(session: Session, agent_id: str, name: str, args: dict, result: dict, is_error: bool, out: AgentResult):
    short = json.dumps(result, default=str)
    out.tool_calls.append({"tool": name, "args": args, "error": is_error, "result_preview": short[:400]})
    if isinstance(result, dict) and result.get("approval_id"):
        out.approvals.append(result["approval_id"])
        session.emit("gate", agent_id, f"Approval requested: {result['approval_id']} -> {', '.join(result.get('approvers', []))}",
                     approval_id=result["approval_id"])
    else:
        session.emit("tool", agent_id, f"{name}({', '.join(f'{k}={str(v)[:40]}' for k, v in args.items())})" + (" -> error" if is_error else ""))


def run_agent(agent_id: str, task: str, session: Session | None = None, mode: str | None = None,
              context: str = "") -> AgentResult:
    session = session or Session()
    agent = get_agent(agent_id)
    mode = mode or ("live" if live_available() else "simulator")
    ctx = Ctx(session, agent)
    session.emit("start", agent_id, f"{agent.title} started ({mode}): {task[:160]}")
    session.audit.append(agent_id, "agent.start", {"task": redact(task)[0][:500], "mode": mode, "model": agent.model if mode == "live" else "simulator"})
    out = AgentResult(agent_id, mode, "")

    if mode == "simulator":
        from .simulator import script_for

        def call(name: str, args: dict) -> dict:
            res, err = run_tool(ctx, name, args)
            _record(session, agent_id, name, args, res, err, out)
            return res

        out.final = script_for(agent_id)(task, call, session)
    else:
        try:
            _live_loop(ctx, task, context, out)
        except LLMError as e:
            out.status, out.final = "blocked", f"Model call failed: {e}"
            session.emit("blocked", agent_id, out.final)
    if out.approvals and out.status == "done":
        out.status = "needs-approval"
    session.emit("done", agent_id, out.final[:1200], status=out.status)
    session.audit.append(agent_id, "agent.finish", {"status": out.status, "approvals": out.approvals})
    return out


def _live_loop(ctx: Ctx, task: str, context: str, out: AgentResult) -> None:
    agent, session = ctx.agent, ctx.session
    provider = ClaudeProvider()
    tools = tools_for(agent)
    defs = [t.api_def() for t in tools]
    schemas = {t.name: t.schema for t in tools}
    intro = f"Task from the requester:\n{untrusted('request', task)}"
    if session.artifacts:
        intro += f"\n\nWorkspace artifacts available (read with read_artifact): {sorted(session.artifacts)}"
    if context:
        intro += f"\n\nAttached context:\n{untrusted('context', context)}"
    messages: list = [{"role": "user", "content": intro}]
    system = system_prompt(agent.id)
    tin = tout = 0
    for _ in range(MAX_TURNS):
        turn = provider.turn(system=system, messages=messages, tools=defs, model=agent.model, effort=agent.effort)
        tin, tout = tin + turn.input_tokens, tout + turn.output_tokens
        messages.append({"role": "assistant", "content": turn.history_content})
        if turn.text.strip():
            session.emit("think", agent.id, turn.text.strip()[:600])
        if turn.stop_reason == "max_tokens":
            out.status, out.final = "blocked", (turn.text or "") + "\n[stopped: output limit reached]"
            break
        if not turn.tool_calls:
            out.final = turn.text
            break
        results = []
        for c in turn.tool_calls:
            problems = validate_input(schemas.get(c["name"], {}), c["input"]) if c["name"] in schemas else []
            if problems:
                res, err = {"error": "INVALID_INPUT: " + "; ".join(problems)}, True
            else:
                res, err = run_tool(ctx, c["name"], c["input"])
            _record(session, agent.id, c["name"], c["input"], res, err, out)
            content = redact(json.dumps(res, default=str))[0]
            results.append({"type": "tool_result", "tool_use_id": c["id"], "content": content, **({"is_error": True} if err else {})})
        messages.append({"role": "user", "content": results})
    else:
        out.status, out.final = "blocked", "Stopped after the maximum number of turns."
    out.usage = {"input_tokens": tin, "output_tokens": tout, "model": agent.model}


def known_tools() -> list[str]:
    return sorted(TOOLS)
