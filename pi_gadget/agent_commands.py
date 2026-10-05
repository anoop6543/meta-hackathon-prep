"""Gadget-side agent commands for the Raspberry Pi.

Drop-in for the Muse gadget executor (wiring instructions in
pi_gadget/README.md). Adds three commands, following the exact conventions of
first-gadget/executor.py in the muse-home-lab repo:

    agent.plan    dry run: NL command -> motion plan + safety verdict, no motion
    agent.run     full pipeline: plan -> validate -> execute (twin by default)
    agent.status  latest run summary, read from the trace spool

Command specs live in AGENT_COMMAND_SPECS (merge into the executor's
COMMAND_SPECS); handlers live on AgentCommands (call from Executor.run).

The pipeline itself lives in ../src (planner -> safety harness -> twin).
Every run writes a JSON trace to the spool dir, which agent.status and the
Watch 4 agent dashboard read.

Stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.command_pipeline import run as pipeline_run  # noqa: E402
from src.meta_model_client import ConfigError, MetaModelClient  # noqa: E402
from src.safety_harness import validate_plan  # noqa: E402

SPOOL_ENV = "AGENT_SPOOL_DIR"
DEFAULT_SPOOL_DIR = os.path.join(REPO_ROOT, "var", "agent")

AGENT_COMMAND_SPECS = {
    # --- agent commands (meta-hackathon-prep) ---
    "agent.plan": {
        "description": (
            "Dry-run a robot command: turn natural language into a motion plan "
            "and run it through the safety harness. Nothing moves. Returns the "
            "plan and the harness verdict (ok/rejected with reasons)."
        ),
        "required": {
            "command": {
                "type": "string",
                "description": 'Natural-language command, e.g. "wave hello".',
            },
        },
        "optional": {
            "live": {
                "type": "boolean",
                "description": "Use the Meta Model API planner instead of the offline demo planner. Default false.",
            },
        },
    },
    "agent.run": {
        "description": (
            "Run a robot command end to end: plan, safety-validate, then execute "
            "on the digital twin (default). Set target=physical only with "
            "approve_physical=true after the SAFETY.md checklist; without "
            "approval the harness rejects the run."
        ),
        "required": {
            "command": {
                "type": "string",
                "description": 'Natural-language command, e.g. "pick up the block".',
            },
        },
        "optional": {
            "target": {
                "type": "string",
                "description": 'Execution target: "twin" (default) or "physical".',
            },
            "approve_physical": {
                "type": "boolean",
                "description": "Human approval for physical execution. Default false. See docs/SAFETY.md.",
            },
            "live": {
                "type": "boolean",
                "description": "Use the Meta Model API planner instead of the offline demo planner. Default false.",
            },
        },
        "timeout_ms": 180000,
    },
    "agent.status": {
        "description": (
            "Latest agent run summary: command, plan intent, safety verdict, "
            "moves executed and final end-effector pose. Read-only."
        ),
        "required": {},
        "optional": {},
    },
    # --- end agent commands ---
}


def ok(payload: dict) -> dict:
    return {"ok": True, "payload": payload}


def error(message: str) -> dict:
    return {"ok": False, "error": message}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _summarize_trace(trace: dict) -> dict:
    verdict = trace.get("verdict", {})
    execution = trace.get("execution") or {}
    return {
        "command": trace.get("command"),
        "intent": (trace.get("plan") or {}).get("intent"),
        "mode": trace.get("mode"),
        "target": trace.get("target"),
        "verdict_ok": verdict.get("ok"),
        "reasons": verdict.get("reasons", []),
        "moves_executed": execution.get("moves_executed", 0),
        "final_ee_m": execution.get("final_ee"),
        "finished_utc": trace.get("finished_utc"),
    }


class AgentCommands:
    """Handler mixin for the gadget Executor. See pi_gadget/README.md."""

    def __init__(self, spool_dir: str | None = None):
        self.spool_dir = (
            spool_dir or os.environ.get(SPOOL_ENV) or DEFAULT_SPOOL_DIR
        )

    # -- wiring helper ----------------------------------------------------
    def dispatch(self, command: str, params: dict):
        """Return the handler result, or None if this isn't an agent command."""
        if command == "agent.plan":
            return self.agent_plan(params)
        if command == "agent.run":
            return self.agent_run(params)
        if command == "agent.status":
            return self.agent_status(params)
        return None

    # -- commands ----------------------------------------------------------
    def agent_plan(self, params: dict) -> dict:
        command = params.get("command")
        if not isinstance(command, str) or not command.strip():
            return error("command is required")
        live = bool(params.get("live", False))
        try:
            plan = MetaModelClient(offline=not live).plan_motion(command)
            verdict = validate_plan(plan, target="twin")
        except ConfigError as exc:
            return error(str(exc))
        except Exception as exc:  # never leak a traceback to the caller
            return error(f"{type(exc).__name__}: {exc}")
        return ok({
            "plan": plan,
            "verdict": verdict.to_dict(),
            "utc": _utc_now(),
        })

    def agent_run(self, params: dict) -> dict:
        command = params.get("command")
        if not isinstance(command, str) or not command.strip():
            return error("command is required")
        target = params.get("target", "twin")
        if target not in ("twin", "physical"):
            return error('target must be "twin" or "physical"')
        try:
            trace = pipeline_run(
                command,
                live=bool(params.get("live", False)),
                target=target,
                approve_physical=bool(params.get("approve_physical", False)),
                spool_dir=self.spool_dir,
            )
        except ConfigError as exc:
            return error(str(exc))
        except Exception as exc:
            return error(f"{type(exc).__name__}: {exc}")
        return ok({
            "summary": _summarize_trace(trace),
            "trace": trace,
            "utc": _utc_now(),
        })

    def agent_status(self, params: dict) -> dict:
        del params
        latest_path = os.path.join(self.spool_dir, "latest.json")
        try:
            with open(latest_path, "r", encoding="utf-8") as fh:
                trace = json.load(fh)
        except (OSError, ValueError):
            return ok({
                "latest": None,
                "note": "no agent runs yet",
                "spool_dir": self.spool_dir,
                "utc": _utc_now(),
            })
        return ok({
            "latest": _summarize_trace(trace),
            "spool_dir": self.spool_dir,
            "utc": _utc_now(),
        })
