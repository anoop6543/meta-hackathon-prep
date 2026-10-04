"""Tests for the safety harness."""
from src.meta_model_client import offline_plan
from src.safety_harness import validate_plan


def _plan(moves, **kw):
    return {"intent": "test", "moves": moves, **kw}


def _move(joints, duration=2.0, gripper=0.0):
    return {"joints": joints, "duration_s": duration, "gripper": gripper}


def test_canned_plans_pass_on_twin():
    for cmd in ("wave hello", "pick up the block", "go home"):
        verdict = validate_plan(offline_plan(cmd), target="twin")
        assert verdict.ok, (cmd, verdict.reasons)


def test_joint_limit_violation_rejected():
    plan = _plan([_move([0, 0, 0, 0, 0, 2.0])])  # j6 max is 1.22
    verdict = validate_plan(plan)
    assert not verdict.ok
    assert any("outside limits" in r for r in verdict.reasons)


def test_velocity_violation_rejected():
    plan = _plan([_move([0, 0, 0, 0, 1.5, 0], duration=0.5)])
    verdict = validate_plan(plan)
    assert not verdict.ok
    assert any("velocity" in r for r in verdict.reasons)


def test_below_table_rejected():
    # folds the arm under the table plane
    plan = _plan([_move([0, -1.31, -1.31, 0, 0, 0])])
    verdict = validate_plan(plan)
    assert not verdict.ok
    assert any("below minimum" in r for r in verdict.reasons)


def test_physical_needs_approval():
    plan = offline_plan("wave hello")
    denied = validate_plan(plan, target="physical", approve_physical=False)
    assert not denied.ok
    assert any("approval" in r for r in denied.reasons)
    allowed = validate_plan(plan, target="physical", approve_physical=True)
    assert allowed.ok, allowed.reasons


def test_bad_schema_rejected():
    assert not validate_plan({"moves": []}).ok
    assert not validate_plan({"moves": [{"joints": [0, 0]}]}).ok
    assert not validate_plan(offline_plan("hi"), target="moon").ok
