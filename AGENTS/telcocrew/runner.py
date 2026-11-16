"""Run one agent on one task. Live mode: Claude drives the tool loop. Simulator mode: a deterministic script
drives the same tools. In both modes every tool call goes through tools.run_tool (guardrails, audit)."""
from __future__ import annotations

import json
import os
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


ALLOWED_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5", "claude-fable-5-2"}
ALLOWED_EFFORT = {"low", "medium", "high", "xhigh", "max"}


def model_and_effort(agent, model: str | None = None, effort: str | None = None) -> tuple[str, str]:
    """The agent's own binding, unless the presenter overrides it (argument, or TELCOCREW_MODEL / TELCOCREW_EFFORT)."""
    m = model or os.environ.get("TELCOCREW_MODEL") or agent.model
    e = effort or os.environ.get("TELCOCREW_EFFORT") or agent.effort
    if m not in ALLOWED_MODELS:
        raise ValueError(f"Model {m} is not on the approved list: {sorted(ALLOWED_MODELS)}")
    if e not in ALLOWED_EFFORT:
        raise ValueError(f"Effort {e} must be one of {sorted(ALLOWED_EFFORT)}")
    return m, e


def run_agent(agent_id: str, task: str, session: Session | None = None, mode: str | None = None,
              context: str = "", model: str | None = None, effort: str | None = None) -> AgentResult:
    session = session or Session()
    agent = get_agent(agent_id)
    mode = mode or ("live" if live_available() else "simulator")
    model, effort = model_and_effort(agent, model, effort)
    session.meta.setdefault("mode", mode)
    if mode == "live":
        session.meta["model"] = model
    ctx = Ctx(session, agent)
    session.emit("start", agent_id, f"{agent.title} started ({mode}): {task[:160]}")
    session.audit.append(agent_id, "agent.start", {"task": redact(task)[0][:500], "mode": mode, "model": model if mode == "live" else "simulator"})
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
            _live_loop(ctx, task, context, out, model, effort)
        except LLMError as e:
            out.status, out.final = "blocked", f"Model call failed: {e}"
            session.emit("blocked", agent_id, out.final)
    if out.approvals and out.status == "done":
        out.status = "needs-approval"
    session.emit("done", agent_id, out.final[:1200], status=out.status)
    session.audit.append(agent_id, "agent.finish", {"status": out.status, "approvals": out.approvals})
    session.transcript.append({"agent": agent_id, "mode": mode, "task": redact(task)[0], "tool_calls": out.tool_calls,
                               "final": out.final, "status": out.status, "usage": out.usage})
    session.flush()
    return out


def _live_loop(ctx: Ctx, task: str, context: str, out: AgentResult, model: str, effort: str) -> None:
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
    tin = tout = cached = 0
    for n in range(1, MAX_TURNS + 1):
        session.emit("think", agent.id, f"Calling {model} (effort {effort}), turn {n}")
        turn = provider.turn(system=system, messages=messages, tools=defs, model=model, effort=effort)
        tin, tout, cached = tin + turn.input_tokens, tout + turn.output_tokens, cached + getattr(turn, 'cached_tokens', 0)
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
        session.flush()
    else:
        out.status, out.final = "blocked", "Stopped after the maximum number of turns."
    out.usage = {"input_tokens": tin, "output_tokens": tout, "cached_input_tokens": cached, "model": model, "effort": effort}


def known_tools() -> list[str]:
    return sorted(TOOLS)
