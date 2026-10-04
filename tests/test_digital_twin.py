"""Tests for the 6DOF digital twin (geometry from dofbot_pro.urdf)."""
import math

from src.digital_twin import JOINTS, Arm6DOF, forward_kinematics


def approx(a, b, tol=1e-6):
    return all(abs(x - y) < tol for x, y in zip(a, b))


def test_home_pose_points_straight_up():
    # All inter-joint offsets are along +z: 0.075+0.03+0.105+0.135+0.08+0.03
    assert approx(forward_kinematics([0] * 6), (0.0, 0.0, 0.455))


def test_shoulder_pitch_90deg_reaches_along_x():
    # j2 = +90deg about y maps the remaining chain onto +x
    ee = forward_kinematics([0, math.pi / 2, 0, 0, 0, 0])
    assert approx(ee, (0.35, 0.0, 0.105), tol=1e-3)


def test_six_joints_defined():
    assert len(JOINTS) == 6


def test_execute_move_lands_on_target():
    arm = Arm6DOF()
    summary = arm.execute_move([0, 0.5, -0.5, 0, 0, 0], 1.0)
    assert summary["final_joints"] == [0, 0.5, -0.5, 0, 0, 0]
    assert approx(arm.q, [0, 0.5, -0.5, 0, 0, 0])
