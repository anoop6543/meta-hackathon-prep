# Pi + Watch 4 setup

How the Raspberry Pi and the Galaxy Watch 4 join the hackathon build.

## Roles

| Device | Role in the demo |
|---|---|
| Raspberry Pi (Muse gadget) | Runs `agent.plan` / `agent.run` / `agent.status` gadget commands → the pipeline (planner → safety harness → twin) executes on the Pi |
| Galaxy Watch 4 (docked) | Shows the agent dashboard (`:8101`): latest command, safety verdict, moves, end-effector pose — the demo's live telemetry |

## Pi bring-up

1. Finish the gadget bring-up in muse-home-lab first (`docs/03-device-raspberry-pi.md`,
   `docs/09-phases.md`) — the agent commands extend that executor, they don't
   replace it.
2. Clone this repo on the Pi:
   `git clone https://github.com/anoop6543/meta-hackathon-prep ~/meta-hackathon-prep`
3. Wire the commands into the Pi's `executor.py` exactly as shown in
   `pi_gadget/README.md`, then restart the gadget service.
4. Verify from the Muse app:
   - `agent.status` → `{"latest": None, "note": "no agent runs yet", ...}`
   - `agent.plan` with `{"command": "wave hello"}` → plan + `"ok": true` verdict
   - `agent.run` with `{"command": "wave hello"}` → full trace, 6 moves on the twin

## Watch 4 dashboard

1. On the Pi, start the agent dashboard:
   `python3 -m watch_dashboard.agent_dashboard --port 8101`
   (from `~/meta-hackathon-prep`; stdlib only, no dependencies).
2. On the Watch 4 (on its charger, same LAN), open `http://<pi-ip>:8101`.
   The page auto-refreshes every 10 seconds.
3. Send `agent.run` from the Muse app and watch the verdict and moves land on
   the watch.

Port map (all LAN-only, never port-forwarded): `:8099` home dashboard,
`:8100` reserved for the Jetson arm-bridge, `:8101` agent dashboard.

## Demo script (for the submission video)

1. Watch shows "no runs yet".
2. From the Muse app: `agent.run` → `"pick up the block"`.
3. Watch flips to the run: intent `pick`, verdict ✓ SAFE, moves 5/5, final
   end-effector pose.
4. Optional second take: a deliberately bad command (or `target=physical`
   without approval) → watch shows ✗ REJECTED with the reasons. This is the
   safety story — keep it in the video.

## Rehearsal notes

- Rehearse in offline mode (the default). Flip `live=true` only for takes
  that need the real Meta model, and watch the $150 credit budget
  (`docs/META_MODEL_API.md`).
- The twin is the submitted demo target; the same plan schema drives the real
  arm later via the muse-home-lab Jetson bridge (`docs/ARCHITECTURE.md`).
