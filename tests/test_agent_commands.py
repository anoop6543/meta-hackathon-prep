"""Tests for the Pi gadget agent commands."""
import json
import os

import pytest

from pi_gadget.agent_commands import (
    AGENT_COMMAND_SPECS,
    AgentCommands,
    DEFAULT_SPOOL_DIR,
)


@pytest.fixture()
def agent(tmp_path):
    return AgentCommands(spool_dir=str(tmp_path / "agent"))


def test_specs_register_three_commands():
    assert set(AGENT_COMMAND_SPECS) == {"agent.plan", "agent.run", "agent.status"}
    assert "command" in AGENT_COMMAND_SPECS["agent.plan"]["required"]
    assert "command" in AGENT_COMMAND_SPECS["agent.run"]["required"]


def test_dispatch_unknown_returns_none(agent):
    assert agent.dispatch("system.run", {}) is None


def test_plan_dry_run_moves_nothing(agent):
    res = agent.dispatch("agent.plan", {"command": "wave hello"})
    assert res["ok"]
    assert res["payload"]["verdict"]["ok"]
    assert res["payload"]["plan"]["intent"] == "wave"


def test_plan_requires_command(agent):
    assert not agent.dispatch("agent.plan", {})["ok"]
    assert not agent.dispatch("agent.plan", {"command": "  "})["ok"]


def test_run_executes_and_spools_trace(agent):
    res = agent.dispatch("agent.run", {"command": "pick up the block"})
    assert res["ok"]
    summary = res["payload"]["summary"]
    assert summary["verdict_ok"]
    assert summary["moves_executed"] == 5
    latest = os.path.join(agent.spool_dir, "latest.json")
    assert os.path.exists(latest)
    with open(latest, encoding="utf-8") as fh:
        assert json.load(fh)["command"] == "pick up the block"


def test_run_physical_without_approval_rejected(agent):
    res = agent.dispatch(
        "agent.run", {"command": "wave hello", "target": "physical"})
    assert res["ok"]  # command ran; the *verdict* is the rejection
    assert not res["payload"]["summary"]["verdict_ok"]
    assert any("approval" in r for r in res["payload"]["summary"]["reasons"])


def test_run_physical_with_approval_executes(agent):
    res = agent.dispatch("agent.run", {
        "command": "wave hello",
        "target": "physical",
        "approve_physical": True,
    })
    assert res["ok"]
    assert res["payload"]["summary"]["verdict_ok"]
    assert res["payload"]["summary"]["target"] == "physical"


def test_status_before_and_after_run(agent):
    first = agent.dispatch("agent.status", {})
    assert first["ok"]
    assert first["payload"]["latest"] is None
    agent.dispatch("agent.run", {"command": "go home"})
    second = agent.dispatch("agent.status", {})
    assert second["payload"]["latest"]["intent"] == "home"


def test_default_spool_under_repo_root():
    repo_root = os.path.dirname(os.path.dirname(
        os.path.abspath(__import__("pi_gadget.agent_commands", fromlist=["x"]).__file__)))
    assert DEFAULT_SPOOL_DIR == os.path.join(repo_root, "var", "agent")
