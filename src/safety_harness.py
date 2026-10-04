"""Safety harness: validate a motion plan before anything moves.

Pure function, no network, no state. Every rejection carries reasons.
Physical execution additionally requires an explicit human approval flag.

Standard library only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.digital_twin import JOINTS, HOME_Q, forward_kinematics


DERATE = 0.5               # run at 50% of URDF velocity limits
WORKSPACE_RADIUS_M = 0.50  # max reach is 0.455 m; small margin
MIN_HEIGHT_M = 0.02        # end-effector must stay above the table


@dataclass
class Verdict:
    ok: bool
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def to_dict(self):
        return {"ok": self.ok, "reasons": self.reasons, "warnings": self.warnings}


def _check_schema(plan) -> list:
    problems = []
    if not isinstance(plan, dict):
        return ["plan must be a dict"]
    moves = plan.get("moves")
    if not isinstance(moves, list) or not moves:
        return ["plan.moves must be a non-empty list"]
    for i, m in enumerate(moves):
        if not isinstance(m, dict):
            problems.append(f"move {i}: must be a dict")
            continue
        joints = m.get("joints")
        if not isinstance(joints, list) or len(joints) != 6 or not all(
            isinstance(v, (int, float)) for v in joints
        ):
            problems.append(f"move {i}: joints must be a list of 6 numbers")
        dur = m.get("duration_s")
        if not isinstance(dur, (int, float)) or dur <= 0:
            problems.append(f"move {i}: duration_s must be a positive number")
        grip = m.get("gripper", 0.0)
        if not isinstance(grip, (int, float)) or not 0.0 <= grip <= 1.0:
            problems.append(f"move {i}: gripper must be in [0, 1]")
    return problems


def validate_plan(plan: dict, target: str = "twin", approve_physical: bool = False) -> Verdict:
    """Validate a plan dict. target: 'twin' or 'physical'."""
    verdict = Verdict(ok=True)

    schema_problems = _check_schema(plan)
    if schema_problems:
        return Verdict(ok=False, reasons=schema_problems)

    if target not in ("twin", "physical"):
        return Verdict(ok=False, reasons=[f"unknown target {target!r}"])

    if target == "physical" and not approve_physical:
        verdict.ok = False
        verdict.reasons.append(
            "physical execution requires explicit human approval "
            "(pass approve_physical=True after the SAFETY.md checklist)"
        )

    prev = list(HOME_Q)
    for i, move in enumerate(plan["moves"]):
        joints = [float(v) for v in move["joints"]]
        duration = float(move["duration_s"])

        for j, (q, (_axis, _dz, lo, hi, vel)) in enumerate(zip(joints, JOINTS)):
            if not lo <= q <= hi:
                verdict.ok = False
                verdict.reasons.append(
                    f"move {i}: joint j{j + 1}={q:.3f} rad outside limits "
                    f"[{lo}, {hi}]"
                )
            peak_vel = abs(q - prev[j]) / duration
            if peak_vel > vel * DERATE:
                verdict.ok = False
                verdict.reasons.append(
                    f"move {i}: joint j{j + 1} peak velocity {peak_vel:.2f} rad/s "
                    f"exceeds derated limit {vel * DERATE:.2f} rad/s"
                )

        x, y, z = forward_kinematics(joints)
        r = (x * x + y * y + z * z) ** 0.5
        if r > WORKSPACE_RADIUS_M:
            verdict.ok = False
            verdict.reasons.append(
                f"move {i}: end-effector radius {r:.3f} m exceeds workspace "
                f"{WORKSPACE_RADIUS_M} m"
            )
        if z < MIN_HEIGHT_M:
            verdict.ok = False
            verdict.reasons.append(
                f"move {i}: end-effector height {z:.3f} m below minimum "
                f"{MIN_HEIGHT_M} m (table collision risk)"
            )

        prev = joints

    if not verdict.ok:
        verdict.warnings.append("plan rejected: nothing was executed")
    return verdict
