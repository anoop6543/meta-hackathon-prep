"""Tests for the Watch 4 agent dashboard."""
import json
import threading
import urllib.error
import urllib.request

from watch_dashboard.agent_dashboard import (
    read_latest,
    serve,
    summarize_trace,
)
from src.command_pipeline import run as pipeline_run


def _trace(spool_dir):
    return pipeline_run("wave hello", spool_dir=spool_dir)


def test_summarize_trace_shape(tmp_path):
    trace = _trace(str(tmp_path))
    s = summarize_trace(trace)
    assert s["command"] == "wave hello"
    assert s["intent"] == "wave"
    assert s["verdict_ok"] is True
    assert s["moves_done"] == s["moves_total"] == 6
    assert s["final_ee_m"][2] > 0.45
    assert s["finished_utc"].endswith("Z")


def test_read_latest_none_when_empty(tmp_path):
    assert read_latest(str(tmp_path)) is None


def test_http_endpoints(tmp_path):
    spool = str(tmp_path)
    _trace(spool)
    srv = serve("127.0.0.1", 0, spool)
    port = srv.server_address[1]
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/agent") as r:
            body = json.load(r)
        assert body["latest"]["intent"] == "wave"
        assert body["latest"]["verdict_ok"] is True
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r:
            page = r.read().decode()
        assert "Agent" in page
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/nope")
            raise AssertionError("expected 404")
        except urllib.error.HTTPError as e:
            assert e.code == 404
    finally:
        srv.shutdown()
        thread.join()
