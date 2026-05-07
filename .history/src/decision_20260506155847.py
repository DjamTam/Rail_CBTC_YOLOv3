import time
from dataclasses import dataclass

@dataclass
class DecisionState:
    consecutive_hits: int = 0
    last_stop_time: float = 0.0

class SafetyDecision:
    """Safety-friendly decision:
    - STOP_REQUEST only after N consecutive detections inside ROI
    - cooldown prevents repeated STOP spam
    """
    def __init__(self, confirm_frames: int = 5, cooldown_seconds: float = 3.0):
        self.confirm_frames = confirm_frames
        self.cooldown_seconds = cooldown_seconds
        self.state = DecisionState()

    def update(self, detected_in_roi: bool) -> str:
        now = time.time()

        if detected_in_roi:
            self.state.consecutive_hits += 1
        else:
            self.state.consecutive_hits = 0

        if self.state.consecutive_hits >= self.confirm_frames:
            if (now - self.state.last_stop_time) >= self.cooldown_seconds:
                self.state.last_stop_time = now
                return "STOP_REQUEST"
            return "COOLDOWN"

        return "SAFE" if not detected_in_roi else "UNCERTAIN"
