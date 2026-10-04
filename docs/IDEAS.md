# Idea matrix

Scored 1–5 on: **Edge** (how much Viswa's background matters),
**Feasibility** (demoable in a 10-day virtual hackathon),
**Differentiation** (how memorable vs. a typical submission),
**Risk** (lower is better; hardware/travel/schedule risk).

| # | Idea | Edge | Feas. | Diff. | Risk | Verdict |
|---|---|---|---|---|---|---|
| 1 | Embodied agent: Meta model drives the DOFBOT-PRO arm, safety harness in between | 5 | 4 | 5 | 3 | **Recommended** |
| 2 | Factory-floor copilot (PLC/vision diagnostics explainer) | 5 | 4 | 4 | 2 | Strong backup |
| 3 | Physical-agent safety harness as a standalone product | 4 | 5 | 4 | 2 | Strong backup / merges into #1 |
| 4 | Conversational home-lab status (Pi + Watch 4 + arm narrated by the model) | 3 | 5 | 3 | 2 | Fallback demo |
| 5 | Civic-service demo (BharatMitra-style) | 2 | 3 | 2 | 3 | Parked — weak fit for this event |

## Idea 1 — Embodied agent (recommended)

A natural-language command layer: the user says "wave at the camera" or "pick
up the block", the Meta model produces a structured motion plan, the safety
harness validates it, and it executes — on the digital twin for the guaranteed
demo, on the real arm when hardware is available.

**Demo options (pick one for the submission video):**
- **A. Pick-and-place.** "Pick up the red block and put it in the tray."
  Strongest story: multi-step planning, gripper control, visible success.
- **B. Wave / greet.** "Wave at the camera." Simplest, lowest risk, still
  shows model→hardware.
- **C. Tidy the desk.** Multi-object, longer horizon. Highest wow, highest
  risk — only if A is solid early.

**Why it wins:** judges see hundreds of chat UIs; almost nobody shows a
foundation model moving physical hardware with a principled safety layer.
Viswa's controls background (TwinCAT/EtherCAT/servos) is the moat.

**Risks & mitigations:** hardware not online (mitigated: twin-first, twin is
the submitted demo); model produces unsafe plans (mitigated: the harness);
10 days is short (mitigated: baseline already runs — see `src/`).

## Idea 2 — Factory-floor copilot

A Meta-model assistant for automation engineers: paste a TwinCAT/EtherCAT
diagnostic log or a photo of a fault, get a plain-language explanation, likely
causes ranked, and a safe recovery procedure. Optionally generates a work
instruction document.

**Options:** A) log analyzer (text in → diagnosis out); B) vision fault
narrator (photo in → explanation out); C) both, sharing one backend.

**Why it's strong:** it's Viswa's day job (Bright Machines) — credibility no
other team can fake. Fully software, zero hardware risk, demoable anywhere.

**Weakness vs. #1:** less visually memorable; more teams can attempt "AI
explains logs".

## Idea 3 — Safety harness for physical agents (standalone)

Productize the validation layer from idea #1: a drop-in gate between any
LLM planner and any actuator — joint/velocity/workspace limits, no-go zones,
human approval gates — plus a red-team suite that throws adversarial commands
at it (prompt-injected motion, limit-adjacent values) and shows the harness
catching them.

**Why it's strong:** merges Viswa's agent red-team lab with his controls
background; safety is the #1 objection to embodied AI, so the narrative is
timely. Can also ship *inside* idea #1 — they're complementary, not rivals.

## Idea 4 — Conversational home-lab status

"How's the lab doing?" → the model reads Pi health, Watch 4 dashboard state,
and arm status, then answers conversationally, with follow-ups ("home the arm
if it's idle"). Builds on the existing `home.hello` / `home.lan_scan` gadget
commands in muse-home-lab.

**Weakness:** it's a nicer dashboard — real, but less differentiated.

## Idea 5 — Civic demo (parked)

A BharatMitra-style demo on Meta models. Worthwhile project, wrong event: the
hackathon rewards building *on Meta's models*, and this idea's strength is
domain/product, not model capability. Revisit for a civic-tech venue.
