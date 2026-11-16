"""Guardrails enforced in code: action classes, redaction, injection scanning, hash-chained audit,
hash-bound approvals with segregation of duties."""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field

from .registry import CLASS_ORDER

# Fictional named people for each human role (same as the web demo).
PEOPLE = {
    "Data Product Owner": "Aisha Rahman", "Data Architect": "Marco Bianchi", "Data Steward": "Lena Fischer",
    "Engineering Lead": "Rahul Menon", "QA Lead": "Sofia Alvarez", "Change Manager (CAB)": "Tom O'Neill",
    "Security & Privacy Officer": "Grace Okafor", "ML Lead / Model Risk": "Kenji Watanabe",
    "NOC Shift Lead": "Priya Natarajan", "Service Delivery Manager": "David Kowalski",
    "Problem Manager": "Nadia Haddad", "Campaign Manager": "Chloe Martin", "Customer Care Lead": "Samuel Adeyemi",
    "Research Lead": "Ines Duarte",
}


class GuardrailBlocked(Exception):
    def __init__(self, rule: str, message: str):
        super().__init__(message)
        self.rule, self.message = rule, message


def class_allowed(agent_max: str, needed: str) -> bool:
    return needed != "A4" and CLASS_ORDER.get(needed, 4) <= CLASS_ORDER.get(agent_max, 0)


# ---------------------------------------------------------------- redaction
_PATTERNS = [
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("imsi_imei", re.compile(r"\b\d{15}\b")),
    ("card", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    ("msisdn", re.compile(r"(?<![\w.])\+?\d{1,3}[ -]?\(?\d{2,4}\)?[ -]?\d{3,4}[ -]?\d{3,4}(?![\w.])")),
    ("secret", re.compile(r"(?i)\b(sk-ant-[\w-]{8,}|sk-[\w]{16,}|AKIA[0-9A-Z]{16}|password\s*[:=]\s*\S+)")),
]


def redact(text: str) -> tuple[str, list[str]]:
    """Replace personal identifiers and secrets with labelled placeholders. Returns (text, kinds found)."""
    found: list[str] = []
    for kind, rx in _PATTERNS:
        if rx.search(text):
            found.append(kind)
            text = rx.sub(f"[REDACTED:{kind}]", text)
    return text, found


_INJECTION = re.compile(r"(?i)(ignore (all |any )?(previous|prior) instructions|you are now|system prompt|"
                        r"approve (this|the) (gate|request)|disable (the )?(alarm|masking|audit)|grant (me|admin))")


def scan_injection(text: str) -> list[str]:
    return [m.group(0) for m in _INJECTION.finditer(text)]


def untrusted(label: str, payload) -> str:
    body = payload if isinstance(payload, str) else json.dumps(payload, indent=1, default=str)
    body, _ = redact(body)
    return f'<untrusted_data source="{label}">\n{body}\n</untrusted_data>'


def sha(obj) -> str:
    raw = obj if isinstance(obj, str) else json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------- audit log
class AuditLog:
    """Append-only, SHA-256 hash-chained. Each entry hashes the previous entry's hash."""

    def __init__(self):
        self.entries: list[dict] = []
        self._lock = threading.Lock()

    def append(self, actor: str, kind: str, detail: dict | str) -> dict:
        with self._lock:
            prev = self.entries[-1]["hash"] if self.entries else "0" * 64
            e = {"seq": len(self.entries) + 1, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "actor": actor, "kind": kind, "detail": detail, "prev": prev}
            e["hash"] = sha({k: v for k, v in e.items() if k != "hash"})
            self.entries.append(e)
            return e

    def verify(self) -> bool:
        prev = "0" * 64
        for e in self.entries:
            if e["prev"] != prev or e["hash"] != sha({k: v for k, v in e.items() if k != "hash"}):
                return False
            prev = e["hash"]
        return True


# ---------------------------------------------------------------- approvals
@dataclass
class Approval:
    id: str
    kind: str                  # gate | action | business_action | message
    title: str
    requested_by: str          # agent id
    action_class: str
    approvers: list[str]       # role titles
    content: dict              # what is being approved (artifacts, action spec ...)
    content_hash: str
    status: str = "pending"    # pending | approved | rejected | changes
    signatures: dict = field(default_factory=dict)   # role -> {person, ts}
    comment: str = ""
    run_id: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


class ApprovalStore:
    def __init__(self, audit: AuditLog):
        self.audit = audit
        self.items: dict[str, Approval] = {}
        self._lock = threading.Lock()

    def request(self, *, kind: str, title: str, requested_by: str, action_class: str, approvers: list[str],
                content: dict, run_id: str | None = None) -> Approval:
        if action_class == "A4":
            raise GuardrailBlocked("A4", "A4 actions are never requested or executed by an agent")
        if not approvers:
            raise GuardrailBlocked("no-approver", "An approval request must name at least one human role")
        unknown = [r for r in approvers if r not in PEOPLE]
        if unknown:
            raise GuardrailBlocked("unknown-role", f"Unknown approver roles: {unknown}")
        if action_class == "A3" and len(set(approvers)) < 2:
            raise GuardrailBlocked("A3-two-approvers", "A3 needs two different named approvers")
        ap = Approval(id=f"APR-{uuid.uuid4().hex[:8]}", kind=kind, title=title, requested_by=requested_by,
                      action_class=action_class, approvers=list(dict.fromkeys(approvers)), content=content,
                      content_hash=sha(content), run_id=run_id)
        with self._lock:
            self.items[ap.id] = ap
        self.audit.append(requested_by, "approval.request", {"id": ap.id, "title": title, "class": action_class,
                                                              "approvers": ap.approvers, "hash": ap.content_hash})
        return ap

    def sign(self, approval_id: str, role: str, person: str, decision: str = "approve", comment: str = "") -> Approval:
        ap = self.items.get(approval_id)
        if not ap:
            raise GuardrailBlocked("unknown-approval", f"No approval {approval_id}")
        if ap.status != "pending":
            raise GuardrailBlocked("not-pending", f"{approval_id} is {ap.status}")
        if person.startswith(("agent:", "build-", "operate-", "consume-")):
            raise GuardrailBlocked("agent-cannot-approve", "Agents never sign approvals")
        if role not in ap.approvers:
            raise GuardrailBlocked("wrong-role", f"{role} is not an approver for {approval_id}")
        if role in ap.signatures:
            raise GuardrailBlocked("already-signed", f"{role} already signed")
        if any(s["person"] == person for s in ap.signatures.values()):
            raise GuardrailBlocked("segregation-of-duties", f"{person} already signed this request under another role")
        if decision == "reject":
            ap.status, ap.comment = "rejected", comment
        elif decision == "changes":
            ap.status, ap.comment = "changes", comment
        else:
            ap.signatures[role] = {"person": person, "ts": time.strftime("%H:%M:%S")}
            if all(r in ap.signatures for r in ap.approvers):
                ap.status = "approved"
        self.audit.append(f"{person} ({role})", f"approval.{decision}", {"id": ap.id, "hash": ap.content_hash,
                                                                         "status": ap.status, "comment": comment})
        return ap

    def require_approved(self, approval_id: str, content: dict | None = None) -> Approval:
        ap = self.items.get(approval_id or "")
        if not ap or ap.status != "approved":
            raise GuardrailBlocked("not-approved", f"Approval {approval_id} is missing or not fully signed")
        if content is not None and sha(content) != ap.content_hash:
            raise GuardrailBlocked("hash-mismatch", "Content changed after approval; a new approval is needed")
        return ap

    def pending(self) -> list[Approval]:
        return [a for a in self.items.values() if a.status == "pending"]
