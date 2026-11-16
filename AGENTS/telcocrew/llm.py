"""Claude via the official Anthropic SDK: one agent turn = stream a request with the agent's tools, return the
assistant content and the tool calls. The runner owns the loop, so every tool call passes the guardrails."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

FALLBACK_MODELS = {"claude-fable-5-2", "claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}


class LLMError(Exception):
    pass


@dataclass
class Turn:
    history_content: list            # assistant content to append to messages unchanged (keeps thinking blocks)
    text: str
    tool_calls: list[dict] = field(default_factory=list)   # {id, name, input}
    stop_reason: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


def live_available() -> bool:
    if os.environ.get("TELCOCREW_MODE", "").lower() == "simulator":
        return False
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
                or os.environ.get("TELCOCREW_MODE", "").lower() == "live")


class ClaudeProvider:
    type = "anthropic"

    def __init__(self):
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise LLMError("Install the Anthropic SDK: pip install anthropic") from e
        self._anthropic = anthropic
        self.client = anthropic.Anthropic(max_retries=3)

    def turn(self, *, system: str, messages: list, tools: list[dict], model: str, effort: str, max_tokens: int = 16000) -> Turn:
        a = self._anthropic
        tool_defs = [{**t, "eager_input_streaming": True} for t in tools]
        kw: dict = {"model": model, "max_tokens": max_tokens, "system": system, "messages": messages, "tools": tool_defs,
                    "output_config": {"effort": effort}}
        if model in FALLBACK_MODELS:
            kw["betas"] = ["server-side-fallback-2026-07-01"]
            kw["fallbacks"] = "default"
        try:
            with self.client.beta.messages.stream(**kw) as stream:
                msg = stream.get_final_message()
        except a.AuthenticationError as e:
            raise LLMError("Anthropic rejected the credentials (401)") from e
        except a.NotFoundError as e:
            raise LLMError(f"Model {model} not found or not available to this key") from e
        except a.RateLimitError as e:
            raise LLMError("Rate limited by the Anthropic API; retry later") from e
        except a.APIStatusError as e:
            raise LLMError(f"Anthropic API error {e.status_code}: {e.message}") from e
        except a.APIConnectionError as e:
            raise LLMError("Cannot reach the Anthropic API") from e
        if msg.stop_reason == "refusal":
            cat = getattr(getattr(msg, "stop_details", None), "category", None)
            raise LLMError(f"Model declined the request (category={cat})")
        text = "".join(b.text for b in msg.content if b.type == "text")
        calls = [{"id": b.id, "name": b.name, "input": b.input if isinstance(b.input, dict) else {}}
                 for b in msg.content if b.type == "tool_use"]
        return Turn(msg.content, text, calls, msg.stop_reason, msg.usage.input_tokens, msg.usage.output_tokens, msg.model)


def validate_input(schema: dict, args: dict) -> list[str]:
    """Light check of a streamed tool input (eager streaming may deliver a truncated object)."""
    if not isinstance(args, dict):
        return ["input is not an object"]
    problems = [f"missing required field `{k}`" for k in schema.get("required", []) if k not in args]
    for k, v in args.items():
        spec = schema.get("properties", {}).get(k)
        if spec is None:
            problems.append(f"unknown field `{k}`")
        elif spec.get("type") == "array" and not isinstance(v, list):
            problems.append(f"`{k}` must be an array")
        elif spec.get("type") == "string" and not isinstance(v, str):
            problems.append(f"`{k}` must be a string")
    return problems
