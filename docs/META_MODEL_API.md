# Meta Model API — integration notes

## What we know (2026-10-03, from the event page)

- The hackathon requires building on Meta's newest models **through the Meta
  Model API**.
- Every participant gets **$150 of Meta Model API credits**.
- Applications are **not open yet**; no API docs, endpoint URLs, model names,
  or SDK details are published on the event page.
- General developer resources live at `dev.meta.ai` (Model API docs, Llama
  docs, Muse model family); none are hackathon-specific yet.

## Local setup

```bash
export META_MODEL_API_KEY="..."        # when issued
export META_MODEL_API_ENDPOINT="..."   # when published (optional override)
```

The client (`src/meta_model_client.py`) reads both from the environment.
Until the key exists it runs in **offline mode**: canned plans, full pipeline
functional, zero API spend.

## Credit budget ($150)

Track spend from day one — a runaway planning loop during rehearsal is the
classic way to burn credits. Rules of thumb for the 10 days:

- Keep the planner's max tokens small; motion plans are compact JSON.
- Rehearse against offline mode; spend credits only on live validation runs
  and the final demo recording.
- Log every live call (the client prints a one-line usage record to stderr).

## Integration plan (when applications open)

1. Read the published docs; set the real endpoint + model name in the client
   (single place: `meta_model_client.py`).
2. Define the system prompt: "You are a robot motion planner. Output ONLY
   JSON matching this schema: ..." with 1–2 few-shot examples.
3. Add a response validator: JSON parses, 6 joints per move, durations > 0 —
   *before* the safety harness sees it (defense in depth).
4. Flip one demo to live mode; keep the rest offline until the story is
   locked.

## Open questions (answer when apps open)

- Exact endpoint, auth scheme, and model identifiers.
- Whether the $150 credits need a separate claim step.
- Rate limits during the event window.
