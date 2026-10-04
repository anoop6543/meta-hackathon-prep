"""6DOF digital twin for the Yahboom DOFBOT-PRO arm.

Geometry (link offsets, joint limits, velocity limits) is taken from the real
arm description: ~/workspace/dofbot-pro-robot/urdf/dofbot_pro.urdf
(j1..j6, all inter-joint translations along +z, axes alternating z/y/y/y/z/y).

Standard library only.
"""
from __future__ import annotations

import math

# (axis, dz_offset_m, lower_rad, upper_rad, vel_limit_rad_s) per joint.
# Source: dofbot_pro.urdf <joint> entries (limit/effort/velocity).
JOINTS = [
    ("z", 0.075, -1.5708, 1.5708, 2.0),  # j1 base yaw
    ("y", 0.030, -1.31, 1.31, 2.0),      # j2 shoulder
    ("y", 0.105, -1.31, 1.31, 2.0),      # j3 elbow
    ("y", 0.135, -1.31, 1.31, 2.0),      # j4 wrist pitch
    ("z", 0.080, -1.5708, 1.5708, 3.0),  # j5 wrist roll
    ("y", 0.030, -1.22, 1.22, 3.0),      # j6 flange
]

HOME_Q = [0.0] * 6
MAX_REACH_M = sum(dz for _, dz, _, _, _ in JOINTS)  # 0.455 m


def _rot(axis: str, q: float):
    c, s = math.cos(q), math.sin(q)
    if axis == "z":
        return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))
    if axis == "y":
        return ((c, 0.0, s), (0.0, 1.0, 0.0), (-s, 0.0, c))
    raise ValueError(f"unknown axis {axis!r}")


def _mat_vec(m, v):
    return (
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    )


def _mat_mat(a, b):
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )


def forward_kinematics(q) -> tuple:
    """End-effector (x, y, z) in metres for joint angles q (radians)."""
    if len(q) != 6:
        raise ValueError("expected 6 joint angles")
    r = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    p = (0.0, 0.0, 0.0)
    for (axis, dz, _lo, _hi, _vel), qi in zip(JOINTS, q):
        p = tuple(pi + vi for pi, vi in zip(p, _mat_vec(r, (0.0, 0.0, dz))))
        r = _mat_mat(r, _rot(axis, qi))
    return p


class Arm6DOF:
    """Minimal joint-space simulator: linear interpolation between waypoints."""

    def __init__(self, q=None):
        self.q = list(HOME_Q if q is None else q)

    def pose(self):
        return forward_kinematics(self.q)

    def execute_move(self, target, duration_s: float, dt: float = 0.05) -> dict:
        """Step toward target joints over duration_s; returns a move summary."""
        if len(target) != 6:
            raise ValueError("expected 6 target joints")
        steps = max(1, int(duration_s / dt))
        start = self.q
        for i in range(1, steps + 1):
            a = i / steps
            self.q = [s + (t - s) * a for s, t in zip(start, target)]
        return {
            "duration_s": duration_s,
            "steps": steps,
            "final_joints": [round(v, 4) for v in self.q],
            "final_ee": [round(v, 4) for v in self.pose()],
        }
