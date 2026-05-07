from src.decision import SafetyDecision
import time

def test_confirm_frames():
    d = SafetyDecision(confirm_frames=3, cooldown_seconds=0.0)
    assert d.update(False) in ("SAFE", "UNCERTAIN")
    assert d.update(True) == "UNCERTAIN"
    assert d.update(True) == "UNCERTAIN"
    assert d.update(True) == "STOP_REQUEST"

def test_cooldown():
    d = SafetyDecision(confirm_frames=2, cooldown_seconds=2.0)
    assert d.update(True) == "UNCERTAIN"
    assert d.update(True) == "STOP_REQUEST"
    assert d.update(True) == "COOLDOWN"
    time.sleep(2.1)
    assert d.update(True) == "STOP_REQUEST"
