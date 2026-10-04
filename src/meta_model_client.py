"""Thin client for the Meta Model API (motion-plan backend).

Runs in OFFLINE mode by default: returns canned demo plans so the whole
pipeline works today with zero API spend. Flip to live mode once the hackathon
publishes the endpoint and issues API keys (see docs/META_MODEL_API.md).

Standard library only.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request


class ConfigError(RuntimeError):
    """Raised when live mode is requested but not configured."""


# NOTE: the request payload shape below is a placeholder. The real endpoint,
# auth scheme, and model identifiers will be filled in when Meta publishes
# the Model API docs for the hackathon.
SYSTEM_PROMPT = (
    "You are a robot motion planner for a 6DOF arm. "
    "Output ONLY JSON matching this schema: "
    '{"intent": str, "moves": [{"joints": [6 floats, radians], '
    '"duration_s": float, "gripper": float in [0,1]}]}. '
    "Joint limits (rad): j1 ±1.5708, j2 ±1.31, j3 ±1.31, j4 ±1.31, "
    "j5 ±1.5708, j6 ±1.22. Keep moves smooth and conservative."
)


def _canned_wave():
    return {
        "intent": "wave",
        "notes": "offline canned plan",
        "moves": [
            {"joints": [0, 0, 0, 0, 0, 0], "duration_s": 1.5, "gripper": 0.0},
            {"joints": [0, 0.35, -0.55, 0.45, 0.0, 0.25], "duration_s": 2.0, "gripper": 0.0},
            {"joints": [0, 0.35, -0.55, 0.45, 0.75, 0.25], "duration_s": 1.2, "gripper": 0.0},
            {"joints": [0, 0.35, -0.55, 0.45, -0.75, 0.25], "duration_s": 1.2, "gripper": 0.0},
            {"joints": [0, 0.35, -0.55, 0.45, 0.75, 0.25], "duration_s": 1.2, "gripper": 0.0},
            {"joints": [0, 0, 0, 0, 0, 0], "duration_s": 2.0, "gripper": 0.0},
        ],
    }


def _canned_pick():
    return {
        "intent": "pick",
        "notes": "offline canned plan",
        "moves": [
            {"joints": [0, 0, 0, 0, 0, 0], "duration_s": 1.5, "gripper": 0.0},
            {"joints": [0, 0.55, -0.95, 0.55, 0, 0.35], "duration_s": 2.5, "gripper": 0.0},
            {"joints": [0, 0.55, -0.95, 0.55, 0, 0.35], "duration_s": 1.0, "gripper": 1.0},
            {"joints": [0, 0.25, -0.45, 0.35, 0, 0.35], "duration_s": 2.5, "gripper": 1.0},
            {"joints": [0, 0, 0, 0, 0, 0], "duration_s": 2.0, "gripper": 0.0},
        ],
    }


def _canned_home():
    return {
        "intent": "home",
        "notes": "offline canned plan",
        "moves": [
            {"joints": [0, 0, 0, 0, 0, 0], "duration_s": 1.5, "gripper": 0.0},
        ],
    }


def offline_plan(nl_command: str) -> dict:
    """Keyword-routed canned planner. Deterministic, zero cost."""
    import re

    def has(cmd: str, *words: str) -> bool:
        return any(re.search(rf"\b{w}\b", cmd) for w in words)

    cmd = nl_command.lower()
    if has(cmd, "wave", "hello", "hi", "greet"):
        return _canned_wave()
    if has(cmd, "pick", "grab", "take", "block"):
        return _canned_pick()
    plan = _canned_home()
    plan["notes"] = f"offline fallback for unrecognized command {nl_command!r}"
    return plan


class MetaModelClient:
    def __init__(self, api_key=None, endpoint=None, offline: bool = True):
        self.api_key = api_key or os.environ.get("META_MODEL_API_KEY")
        self.endpoint = endpoint or os.environ.get("META_MODEL_API_ENDPOINT")
        self.offline = offline

    def plan_motion(self, nl_command: str) -> dict:
        """Natural-language command -> motion plan dict."""
        if self.offline:
            return offline_plan(nl_command)
        if not self.api_key or not self.endpoint:
            raise ConfigError(
                "live mode needs META_MODEL_API_KEY and META_MODEL_API_ENDPOINT "
                "(see docs/META_MODEL_API.md); running with offline=True instead"
            )
        payload = json.dumps(
            {
                "model": os.environ.get("META_MODEL_NAME", "tbd"),
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": nl_command},
                ],
            }
        ).encode()
        req = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        # One-line usage record for the $150 credit budget (docs/META_MODEL_API.md).
        print(f"[api] POST {self.endpoint} payload_bytes={len(payload)}", file=sys.stderr)
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
        # Expect the model to return the plan JSON; extract the first {...} block.
        start, end = body.find("{"), body.rfind("}")
        if start < 0 or end < 0:
            raise ValueError(f"model response contained no JSON: {body[:200]!r}")
        return json.loads(body[start : end + 1])
