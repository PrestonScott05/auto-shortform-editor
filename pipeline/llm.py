"""Thin Anthropic wrapper that returns parsed JSON from a prompt."""
from __future__ import annotations

import json
import os
import re

from common import CFG


def _client():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit(
            "ANTHROPIC_API_KEY not set. Add it to .env (see .env.example). "
            "Needed for stages s2 (classify) and s3 (extract)."
        )
    import anthropic
    return anthropic.Anthropic(api_key=key)


def ask_json(system: str, user: str) -> dict | list:
    """Call the model and parse a JSON object/array from its reply."""
    client = _client()
    resp = client.messages.create(
        model=CFG["llm"]["model"],
        max_tokens=CFG["llm"]["max_tokens"],
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    return _extract_json(text)


def _extract_json(text: str):
    text = text.strip()
    # Strip ```json fences if present.
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fall back to the first {...} or [...] span.
        for opener, closer in (("{", "}"), ("[", "]")):
            i, j = text.find(opener), text.rfind(closer)
            if i != -1 and j != -1 and j > i:
                return json.loads(text[i : j + 1])
        raise
