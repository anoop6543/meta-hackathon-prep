#!/usr/bin/env python3
"""Agent activity dashboard for the Galaxy Watch 4.

Companion to the Pi's agent commands (pi_gadget/): reads the JSON trace spool
written by every agent.run and shows the latest run on a watch-friendly page —
command, plan intent, safety verdict, moves executed, final end-effector pose.

Stdlib only, read-only (exposes status, takes no actions).

Run on the Pi:
    python3 -m watch_dashboard.agent_dashboard --port 8101
Then open http://<pi-ip>:8101 in the Galaxy Watch 4 browser
(Wear OS Chrome handles the page fine; keep the watch on its charger).

Port note: 8099 is the home dashboard, 8100 is reserved for the Jetson
arm-bridge (see muse-home-lab docs/07-software.md), so this takes 8101.

Security: binds all interfaces so the watch can reach it, but this is
LAN-only. Do NOT port-forward it to the internet. No auth: read-only status.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "0.1.0"
DEFAULT_PORT = 8101
SPOOL_ENV = "AGENT_SPOOL_DIR"


def spool_dir_default() -> str:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.environ.get(SPOOL_ENV) or os.path.join(repo_root, "var", "agent")


def read_latest(spool_dir: str) -> dict | None:
    """Latest agent trace, or None if no run has happened yet."""
    try:
        with open(os.path.join(spool_dir, "latest.json"), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def summarize_trace(trace: dict) -> dict:
    """Small, watch-friendly view model for one trace."""
    plan = trace.get("plan") or {}
    verdict = trace.get("verdict") or {}
    execution = trace.get("execution") or {}
    moves = plan.get("moves") or []
    ee = execution.get("final_ee")
    return {
        "command": trace.get("command"),
        "intent": plan.get("intent"),
        "mode": trace.get("mode"),
        "target": trace.get("target"),
        "verdict_ok": bool(verdict.get("ok")),
        "reasons": verdict.get("reasons") or [],
        "moves_done": execution.get("moves_executed", 0),
        "moves_total": len(moves),
        "final_ee_m": [round(v, 3) for v in ee] if ee else None,
        "finished_utc": trace.get("finished_utc"),
    }


PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent</title>
<style>
  body {{ background:#0b0e14; color:#e6e9f0; font-family:system-ui,sans-serif;
         margin:0; padding:16px; }}
  h1 {{ font-size:22px; margin:0 0 4px; }}
  .sub {{ color:#8b93a7; font-size:13px; margin-bottom:14px; }}
  .card {{ background:#151a26; border-radius:12px; padding:12px 14px;
           margin-bottom:10px; }}
  .card h2 {{ font-size:14px; color:#8b93a7; margin:0 0 8px;
              text-transform:uppercase; letter-spacing:.06em; }}
  .row {{ display:flex; justify-content:space-between; padding:3px 0;
          font-size:15px; }}
  .row b {{ font-variant-numeric:tabular-nums; }}
  .big {{ font-size:20px; font-weight:700; }}
  .ok {{ color:#4ade80; }} .bad {{ color:#f87171; }}
  .cmd {{ font-size:17px; margin:2px 0 8px; }}
  .reasons {{ font-size:13px; color:#f87171; margin:6px 0 0; padding:0;
              list-style:none; }}
  button {{ width:100%; padding:14px; font-size:16px; border-radius:12px;
            border:0; background:#3b82f6; color:#fff; margin-top:6px; }}
</style></head>
<body>
<h1>🤖 Agent</h1>
<div class="sub" id="utc"></div>
<div class="card"><h2>Latest run</h2><div id="run"></div></div>
<button onclick="load()">Refresh</button>
<script>
async function load() {{
  try {{
    const r = await fetch("/api/agent");
    const j = await r.json();
    document.getElementById("utc").textContent = (j.utc || "") + " UTC";
    const s = j.latest;
    if (!s) {{
      document.getElementById("run").innerHTML =
        `<div class="sub">no runs yet — send agent.run from the Muse app</div>`;
      return;
    }}
    const v = s.verdict_ok
      ? `<span class="big ok">✓ SAFE</span>` : `<span class="big bad">✗ REJECTED</span>`;
    const ee = s.final_ee_m ? s.final_ee_m.map(x => x.toFixed(2)).join(", ") : "—";
    const reasons = (s.reasons || []).map(x => `<li>${{x}}</li>`).join("");
    document.getElementById("run").innerHTML =
      `<div class="cmd">“${{s.command}}”</div>` + v +
      `<div class="row"><span>Intent</span><b>${{s.intent || "?"}}</b></div>` +
      `<div class="row"><span>Mode / target</span><b>${{s.mode}} / ${{s.target}}</b></div>` +
      `<div class="row"><span>Moves</span><b>${{s.moves_done}} / ${{s.moves_total}}</b></div>` +
      `<div class="row"><span>End effector (m)</span><b>${{ee}}</b></div>` +
      (reasons ? `<ul class="reasons">${{reasons}}</ul>` : "") +
      `<div class="sub">finished ${{s.finished_utc || "?"}}</div>`;
  }} catch (e) {{
    document.getElementById("run").innerHTML = `<span class="bad">offline</span>`;
  }}
}}
load();
setInterval(load, 10000);
</script>
</body></html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "AgentDashboard/" + VERSION

    def log_message(self, *args):
        pass

    def _send(self, code: int, ctype: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        spool = self.server.spool_dir  # type: ignore[attr-defined]
        if self.path == "/":
            self._send(200, "text/html; charset=utf-8", PAGE.encode())
        elif self.path == "/api/agent":
            trace = read_latest(spool)
            body = json.dumps({
                "latest": summarize_trace(trace) if trace else None,
                "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }).encode()
            self._send(200, "application/json", body)
        else:
            self._send(404, "text/plain", b"not found")


def serve(host: str, port: int, spool_dir: str) -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer((host, port), Handler)
    srv.spool_dir = spool_dir  # type: ignore[attr-defined]
    return srv


def main() -> None:
    ap = argparse.ArgumentParser(description="Agent activity dashboard (read-only)")
    ap.add_argument("--host", default="0.0.0.0",
                    help="bind address (default all interfaces, LAN only)")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--spool-dir", default=None)
    args = ap.parse_args()
    spool = args.spool_dir or spool_dir_default()
    srv = serve(args.host, args.port, spool)
    print(f"Agent dashboard on http://{args.host}:{args.port}  (LAN only — "
          f"do not port-forward to the internet)")
    print(f"Reading traces from {spool}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
