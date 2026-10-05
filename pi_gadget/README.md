# Pi gadget — agent commands

Wires the hackathon pipeline (`src/`: planner → safety harness → twin) into
the Muse gadget executor on the Raspberry Pi, as three new gadget commands:
`agent.plan`, `agent.run`, `agent.status`.

## Deploy

1. On the Pi, clone this repo next to the gadget service, e.g.:
   `~/meta-hackathon-prep` (any path works — the module finds its own repo
   root, and `AGENT_SPOOL_DIR` overrides the trace location).
2. In the Pi's `executor.py` (the drop-in from muse-home-lab's
   `first-gadget/`), apply this patch:

```python
# near the other imports:
import sys
sys.path.insert(0, "/home/<user>/meta-hackathon-prep")  # <-- your clone path
from pi_gadget.agent_commands import AGENT_COMMAND_SPECS, AgentCommands

# in COMMAND_SPECS, alongside the other entries:
COMMAND_SPECS.update(AGENT_COMMAND_SPECS)

# in Executor.__init__, after self.account = account:
self.agent = AgentCommands()

# in Executor.run(), before the final `return error(...)`:
agent_result = self.agent.dispatch(command, params)
if agent_result is not None:
    return agent_result
```

3. Restart the gadget service (same procedure as the `first-gadget` deploy in
   muse-home-lab `docs/07-software.md`), then verify from the Muse app:
   `agent.status` should answer `{"latest": None, ...}` until the first run.

## Design notes

- The handlers never import the executor: `ok()`/`error()` envelopes are
  defined locally (same intentional-duplication rule as the neighbor parser
  shared between `executor.py` and `dashboard.py`).
- `agent.run` defaults to `target="twin"`. `target="physical"` without
  `approve_physical=true` is rejected by the harness — there is no silent
  path to real motion.
- Every `agent.run` writes a JSON trace to the spool dir
  (`var/agent/` by default, `AGENT_SPOOL_DIR` to override). `agent.status`
  and the Watch 4 agent dashboard (`watch_dashboard/`) read `latest.json`
  from there.
- Offline planner by default; pass `live=true` only with
  `META_MODEL_API_KEY` set (see `docs/META_MODEL_API.md`).
