# Meta Hackathon Prep

Preparation workspace for the **Meta Global AI Developer Hackathon**
([event page](https://dev.meta.ai/events/global-hackathon)) — a 10-day global
virtual hackathon from Meta Superintelligence Labs. Build on Meta's newest
models through the Meta Model API. $1M cash prize pool; every participant gets
$150 of Meta Model API credits.

**Status (2026-10-03):** applications are NOT open yet — the event page is a
notify-me signup only. Viswa is registered for the notification on both
`anoop6543@gmail.com` and `13464home@gmail.com` (marketing consent off).
No tracks, dates, eligibility rules, or judging criteria published yet.
This repo exists so that the day applications open, the build starts from a
running baseline instead of a blank page.

## Strategy in one paragraph

Play the hand nobody else holds: **embodied AI**. Most teams will demo a chat
UI; we demo a Meta model moving a real 6DOF robot arm — with a safety harness
between the model's commands and the hardware. The baseline in `src/` runs
today against a digital twin whose geometry comes from the real arm's URDF, so
the demo works even before hardware is online.

## Quickstart

```bash
# offline demo: plan -> safety-check -> execute on the digital twin
python3 -m src.command_pipeline "wave hello"

# other canned demos
python3 -m src.command_pipeline "pick up the block"
python3 -m src.command_pipeline "go home"

# tests
python3 -m pytest tests/ -q
```

No dependencies beyond the standard library for `src/`; `pytest` for tests.

## Repo map

| Path | What |
|---|---|
| `docs/IDEAS.md` | Idea matrix: 5 candidate builds, options per idea, scoring, recommendation |
| `docs/ARCHITECTURE.md` | Embodied-agent pipeline, components, trust boundaries |
| `docs/META_MODEL_API.md` | What we know about the API, env setup, $150 credit budget |
| `docs/SAFETY.md` | Physical-safety rules (required reading before any hardware motion) |
| `docs/PI_WATCH_SETUP.md` | Pi + Watch 4 bring-up, demo script |
| `pi_gadget/agent_commands.py` | Gadget commands for the Pi: `agent.plan`, `agent.run`, `agent.status` (+ deploy notes in `pi_gadget/README.md`) |
| `watch_dashboard/agent_dashboard.py` | Watch 4 agent-activity dashboard (stdlib, `:8101`) |
| `src/meta_model_client.py` | Thin Meta Model API client; offline demo mode until the API is live |
| `src/digital_twin.py` | 6DOF arm simulator, geometry from the real URDF |
| `src/safety_harness.py` | Validation layer: limits, velocity, workspace, approval gates |
| `src/command_pipeline.py` | End-to-end demo: NL command → plan → validate → execute |

## Cross-references (existing repos)

- **Muse home lab** — the physical stack this builds on (Pi gadget, Watch 4
  display, DOFBOT-PRO arm):
  [github.com/anoop6543/muse-home-lab](https://github.com/anoop6543/muse-home-lab)
  (private), local: `~/workspace/muse-home-lab/`.
  Start at its `docs/09-phases.md` for the hardware bring-up sequence.
- **DOFBOT-PRO robot repo** — arm bring-up, Arm_Lib API, simulator, and the
  safety doc: local `~/workspace/dofbot-pro-robot/`
  (`docs/14-safety.md` is required reading; `docs/06-arm-lib-api.md` is the
  hardware command reference; `urdf/dofbot_pro.urdf` is where the twin's
  geometry comes from).

## When applications open — checklist

1. Read the tracks + judging criteria; confirm the embodied-agent idea still
   fits (fallback order is in `docs/IDEAS.md`).
2. Get the Meta Model API key; set `META_MODEL_API_KEY`; flip the client out
   of offline mode (`docs/META_MODEL_API.md`).
3. Decide demo target: digital twin only (safe, works anywhere) vs. twin +
   live arm (stronger demo, needs the home-lab bring-up done).
4. Register the team; note the $150 credit budget per participant.
