# Architecture — embodied agent (idea #1)

```
  voice / text command
        │
        ▼
┌───────────────────┐
│ Meta Model API    │  planner: NL → structured motion plan
│ (planner)         │  (offline canned planner until the API is live)
└────────┬──────────┘
         │ plan: { intent, moves[{joints[6], duration_s, gripper}] }
         ▼
┌───────────────────┐
│ Safety harness    │  joint limits · velocity caps · workspace sphere
│ (validator)       │  no-go zones · approval gate for physical target
└────────┬──────────┘
         │ verdict: ok / rejected + reasons
         ▼
┌───────────────────┐     ┌────────────────────┐
│ Executor          │────▶│ Digital twin       │  default demo target
│                   │     └────────────────────┘
│                   │     ┌────────────────────┐
│                   │────▶│ Jetson bridge      │  real arm (approval-gated)
└───────────────────┘     │ (muse-home-lab)    │
                          └────────────────────┘
         telemetry
             │
             ▼
      dashboard / video capture (demo artifact)
```

## Components

- **Planner** (`src/meta_model_client.py`). Owns all model interaction.
  Contract: natural-language string in, validated plan dict out. In offline
  mode it returns canned plans so the whole pipeline runs today; in live mode
  it calls the Meta Model API and parses the response into the plan schema.
  The rest of the pipeline never knows which mode it's in.
- **Safety harness** (`src/safety_harness.py`). Pure function
  `validate_plan(plan, target)` → verdict. No network, no state, no
  exceptions for control flow — every rejection carries machine-readable
  reasons. This is the component idea #3 would productize.
- **Digital twin** (`src/digital_twin.py`). 6DOF forward kinematics and motion
  integration. Geometry (link offsets, joint limits, velocity limits) is taken
  from `dofbot_pro.urdf` in the robot repo — not guessed. The twin is the
  *submitted* demo target: it runs anywhere, needs no hardware, and exercises
  the exact same plan schema the real arm will consume.
- **Executor** (`src/command_pipeline.py`). Wires planner → harness → twin,
  prints a JSON trace (the demo log). The physical path (Jetson bridge) is a
  second executor backend implementing the same interface; it is
  approval-gated and lives in muse-home-lab's bring-up sequence
  (`docs/05-device-dofbot-pro.md`, `docs/09-phases.md`).

## Trust boundaries

1. **Model output is untrusted.** The planner's JSON is validated, never
   executed blindly — this is the same posture as the agent red-team lab.
2. **The harness is the last software gate** before motion. It has no
   dependencies on the planner; a compromised planner still can't move the arm
   outside limits.
3. **Physical execution needs a human.** `target="physical"` requires an
   explicit approval flag *and* the physical-safety checklist in
   `docs/SAFETY.md`. No remote motion while anyone could be in reach.

## Sim-first strategy

Build and demo against the twin; promote the identical plan schema to
hardware only after the muse-home-lab bring-up phases pass. The hackathon
submission video can be recorded entirely from the twin — narrated telemetry
(plan → verdict → motion) is the story, not the room the robot sits in.

## Pi + Watch 4 wiring

- **Pi (gadget host).** `pi_gadget/agent_commands.py` adds `agent.plan`,
  `agent.run`, `agent.status` to the Pi's gadget executor (same command-spec
  pattern as `home.hello`/`home.lan_scan`). The Pi runs the whole pipeline
  locally: planner → harness → twin. Every `agent.run` writes a JSON trace
  to the spool dir (`var/agent/`, `AGENT_SPOOL_DIR` to override).
- **Watch 4 (docked display).** `watch_dashboard/agent_dashboard.py` serves a
  watch-friendly page on `:8101` (LAN-only, read-only) showing the latest
  trace: command, intent, safety verdict, moves, end-effector pose.
  Auto-refreshes every 10 s — this is the demo's live telemetry.
- Full bring-up and the submission-video demo script: `docs/PI_WATCH_SETUP.md`.
