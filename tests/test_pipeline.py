"""End-to-end pipeline tests (offline mode)."""
from src.command_pipeline import run


def test_wave_pipeline_ok():
    trace = run("wave hello")
    assert trace["verdict"]["ok"], trace["verdict"]["reasons"]
    assert trace["execution"]["moves_executed"] == 6
    # ends back home, arm pointing straight up
    assert trace["execution"]["final_ee"][2] > 0.45


def test_pick_pipeline_ok():
    trace = run("pick up the block")
    assert trace["verdict"]["ok"], trace["verdict"]["reasons"]
    assert trace["execution"]["moves_executed"] == 5


def test_unknown_command_falls_back_home():
    trace = run("do something mysterious")
    assert trace["verdict"]["ok"]
    assert trace["plan"]["intent"] == "home"
