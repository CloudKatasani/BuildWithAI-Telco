"""Local HTTP API for the agents, plus the web demo as static files. Standard library only.

Binds to 127.0.0.1. Listening on any other address requires TELCOCREW_API_TOKEN, sent by clients as
the X-API-Token header."""
from __future__ import annotations

import json
import os
import re
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .guardrails import PEOPLE, GuardrailBlocked
from .llm import live_available
from .registry import get_agent, load_skills, manifest, system_prompt
from .runner import run_agent
from .tools import Session
from .workflows import Pipeline, build_pipeline, operate_pipeline

DEMO_DIR = Path(__file__).resolve().parent.parent.parent / "demo"
SESSIONS: dict[str, Session] = {}
PIPELINES: dict[str, Pipeline] = {}
RUNS: dict[str, dict] = {}
_lock = threading.Lock()


def _session(sid: str | None) -> Session:
    with _lock:
        if sid and sid in SESSIONS:
            return SESSIONS[sid]
        s = Session()
        SESSIONS[s.id] = s
        return s


def _find_approval(aid: str):
    for s in SESSIONS.values():
        if aid in s.approvals.items:
            return s, s.approvals.items[aid]
    return None, None


def _session_state(s: Session) -> dict:
    return {"session_id": s.id, "events": s.events[-300:], "approvals": [a.as_dict() for a in s.approvals.items.values()],
            "artifacts": {k: v[:6000] for k, v in s.artifacts.items()}, "questions": s.questions,
            "audit": s.audit.entries[-100:], "audit_valid": s.audit.verify()}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DEMO_DIR), **kw)

    def log_message(self, fmt, *args):  # quieter console
        if os.environ.get("TELCOCREW_HTTP_LOG"):
            super().log_message(fmt, *args)

    # ------------------------------------------------------------ helpers
    def _json(self, code: int, obj) -> None:
        body = json.dumps(obj, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n > 200_000:
            raise ValueError("request too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def _authorised(self) -> bool:
        token = os.environ.get("TELCOCREW_API_TOKEN")
        return not token or self.headers.get("X-API-Token") == token

    # ------------------------------------------------------------ routes
    def do_GET(self):  # noqa: N802
        if not self.path.startswith("/api/"):
            return super().do_GET()
        if not self._authorised():
            return self._json(401, {"error": "missing or wrong X-API-Token"})
        p = self.path.split("?")[0]
        if p == "/api/health":
            return self._json(200, {"ok": True, "mode": "live" if live_available() else "simulator", "people": PEOPLE})
        if p == "/api/agents":
            return self._json(200, manifest())
        m = re.fullmatch(r"/api/agents/([\w-]+)", p)
        if m:
            try:
                a = get_agent(m.group(1))
            except KeyError as e:
                return self._json(404, {"error": str(e)})
            skills = load_skills()
            return self._json(200, {**a.summary(), "body": a.body, "system_prompt_chars": len(system_prompt(a.id)),
                                    "skill_text": {n: skills[n].body for n in a.skills if n in skills}})
        m = re.fullmatch(r"/api/sessions/([\w-]+)", p)
        if m and m.group(1) in SESSIONS:
            st = _session_state(SESSIONS[m.group(1)])
            st["runs"] = [r for r in RUNS.values() if r["session_id"] == m.group(1)]
            return self._json(200, st)
        m = re.fullmatch(r"/api/pipelines/([\w-]+)", p)
        if m and m.group(1) in PIPELINES:
            return self._json(200, PIPELINES[m.group(1)].state())
        if p == "/api/approvals":
            return self._json(200, [a.as_dict() for s in SESSIONS.values() for a in s.approvals.items.values()])
        return self._json(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        if not self._authorised():
            return self._json(401, {"error": "missing or wrong X-API-Token"})
        try:
            body = self._body()
        except (ValueError, json.JSONDecodeError) as e:
            return self._json(400, {"error": str(e)})
        p = self.path.split("?")[0]
        mode = body.get("mode") if body.get("mode") in ("live", "simulator") else None

        m = re.fullmatch(r"/api/agents/([\w-]+)/run", p)
        if m:
            try:
                get_agent(m.group(1))
            except KeyError as e:
                return self._json(404, {"error": str(e)})
            task = str(body.get("task") or "").strip()
            if not task:
                return self._json(400, {"error": "task is required"})
            s = _session(body.get("session_id"))
            run = {"id": f"R-{len(RUNS) + 1}", "agent": m.group(1), "session_id": s.id, "status": "running"}
            RUNS[run["id"]] = run

            def work():
                try:
                    res = run_agent(m.group(1), task, s, mode, str(body.get("context") or ""))
                    run.update(status=res.status, final=res.final, usage=res.usage, mode=res.mode)
                except Exception as e:  # noqa: BLE001
                    run.update(status="error", final=str(e))
                    s.emit("blocked", m.group(1), f"Run failed: {e}")
            threading.Thread(target=work, daemon=True).start()
            return self._json(202, run)

        if p == "/api/pipelines":
            track, req = body.get("track"), str(body.get("request") or "").strip()
            if track not in ("build", "operate") or not req:
                return self._json(400, {"error": "track (build|operate) and request are required"})
            pl = build_pipeline(req, mode) if track == "build" else operate_pipeline(req, mode)
            PIPELINES[pl.id] = pl
            SESSIONS[pl.session.id] = pl.session
            threading.Thread(target=pl.advance, daemon=True).start()
            return self._json(202, {"id": pl.id, "session_id": pl.session.id, "steps": pl.steps})

        m = re.fullmatch(r"/api/approvals/([\w-]+)/decide", p)
        if m:
            s, ap = _find_approval(m.group(1))
            if not ap:
                return self._json(404, {"error": "unknown approval"})
            role = body.get("role")
            decision = body.get("decision", "approve")
            if decision not in ("approve", "reject", "changes"):
                return self._json(400, {"error": "decision must be approve, reject or changes"})
            person = body.get("person") or PEOPLE.get(role, "")
            try:
                s.approvals.sign(ap.id, role, person, decision, str(body.get("comment") or ""))
            except GuardrailBlocked as g:
                return self._json(409, {"error": g.message, "rule": g.rule})
            for pl in PIPELINES.values():
                if pl.session is s and ap.id in pl.waiting_on:
                    threading.Thread(target=pl.advance, daemon=True).start()
            return self._json(200, ap.as_dict())
        return self._json(404, {"error": "not found"})


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    if host not in ("127.0.0.1", "localhost") and not os.environ.get("TELCOCREW_API_TOKEN"):
        raise SystemExit("Refusing to listen beyond localhost without TELCOCREW_API_TOKEN")
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"DataCrew Telco runtime on http://{host}:{port}  (mode: {'live (Claude)' if live_available() else 'simulator'})")
    print(f"Open http://{host}:{port}/#agents for the Agents page.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
