# Safety — physical execution rules

These rules govern **any** motion of the real arm. The digital twin is exempt
(it can't hurt anyone); everything else here is mandatory.

## Standing rules

1. **Clear area.** No people or pets within arm's reach before any motion.
2. **No remote motion with people nearby.** Never trigger arm motion remotely
   while someone could be in reach — this includes "quick tests".
3. **Approval gate.** `target="physical"` requires an explicit human approval
   flag on every run. There is no "always approve" mode.
4. **E-stop within reach.** Know where the power cutoff is before starting.
5. **Servos stay derated.** The harness enforces 50% of the URDF velocity
   limits; do not raise the derate without a written reason.
6. **Bring-up order.** The arm's own safety doc is authoritative for hardware:
   `~/workspace/dofbot-pro-robot/docs/14-safety.md` — read it before the first
   real motion. Power-chain checks in `docs/01-unboxing-inventory.md` come
   before any servo is energized (6.0–7.4V rail; never 12V direct).

## Software gates (enforced in code)

- Joint position limits and velocity caps from the URDF (`src/digital_twin.py`,
  checked by `src/safety_harness.py`).
- Workspace sphere (0.50 m) + minimum height above the table.
- Gripper range check.
- Plan schema validation before the harness runs.

## Incident rule

Any unexpected motion → power off, preserve the JSON trace from
`command_pipeline.py`, write up what happened before the next run.
