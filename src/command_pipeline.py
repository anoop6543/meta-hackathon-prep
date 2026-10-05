"""End-to-end demo: NL command -> plan -> safety validation -> twin execution.

Usage:
    python3 -m src.command_pipeline "wave hello"
    python3 -m src.command_pipeline "pick up the block" --target twin
    python3 -m src.command_pipeline "..." --live --target physical --approve

Prints a JSON trace of the whole run. Exits 1 if the plan is rejected.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

from src.digital_twin import Arm6DOF
from src.meta_model_client import MetaModelClient
from src.safety_harness import validate_plan


SPOOL_ENV = "AGENT_SPOOL_DIR"


def _write_trace(spool_dir: str, trace: dict) -> str:
    """Write the trace JSON atomically; refresh latest.json. Returns the path."""
    os.makedirs(spool_dir, exist_ok=True)
    trace["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    data = json.dumps(trace, indent=2).encode()
    stamp = trace["finished_utc"].replace(":", "").replace("-", "")
    tmp = os.path.join(spool_dir, f".trace-{stamp}.tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
    path = os.path.join(spool_dir, f"trace-{stamp}.json")
    os.replace(tmp, path)
    latest_tmp = os.path.join(spool_dir, ".latest.tmp")
    with open(latest_tmp, "wb") as fh:
        fh.write(data)
    os.replace(latest_tmp, os.path.join(spool_dir, "latest.json"))
    return path


def run(command: str, live: bool = False, target: str = "twin",
        approve_physical: bool = False, spool_dir: str | None = None) -> dict:
    client = MetaModelClient(offline=not live)
    plan = client.plan_motion(command)

    verdict = validate_plan(plan, target=target, approve_physical=approve_physical)
    trace = {
        "command": command,
        "mode": "live" if live else "offline",
        "target": target,
        "plan": plan,
        "verdict": verdict.to_dict(),
        "execution": None,
    }

    if not verdict.ok:
        if spool_dir:
            _write_trace(spool_dir, trace)
        return trace

    arm = Arm6DOF()
    executed = []
    for move in plan["moves"]:
        summary = arm.execute_move(move["joints"], move["duration_s"])
        summary["gripper"] = move.get("gripper", 0.0)
        executed.append(summary)
    trace["execution"] = {
        "moves_executed": len(executed),
        "final_joints": executed[-1]["final_joints"],
        "final_ee": executed[-1]["final_ee"],
    }
    if spool_dir:
        _write_trace(spool_dir, trace)
    return trace


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Embodied-agent demo pipeline")
    ap.add_argument("command", help='natural-language command, e.g. "wave hello"')
    ap.add_argument("--live", action="store_true",
                    help="use the Meta Model API instead of the canned planner")
    ap.add_argument("--target", choices=("twin", "physical"), default="twin")
    ap.add_argument("--approve", action="store_true",
                    help="human approval for physical execution (see docs/SAFETY.md)")
    ap.add_argument("--spool-dir", default=None,
                    help="write the JSON trace here (default: $AGENT_SPOOL_DIR)")
    args = ap.parse_args(argv)

    trace = run(args.command, live=args.live, target=args.target,
                approve_physical=args.approve,
                spool_dir=args.spool_dir or os.environ.get(SPOOL_ENV))
    print(json.dumps(trace, indent=2))
    return 0 if trace["verdict"]["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
