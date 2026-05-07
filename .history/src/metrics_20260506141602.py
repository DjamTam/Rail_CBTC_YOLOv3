import json
import os
import time

class Metrics:
    def __init__(self):
        self.start = time.time()
        self.frames = 0
        self.stop_requests = 0
        self.uncertain = 0
        self.max_conf = 0.0

    def update(self, max_conf: float, decision: str):
        self.frames += 1
        self.max_conf = max(self.max_conf, max_conf)
        if decision == "STOP_REQUEST":
            self.stop_requests += 1
        if decision == "UNCERTAIN":
            self.uncertain += 1

    def to_dict(self):
        elapsed = max(1e-6, time.time() - self.start)
        return {
            "frames": self.frames,
            "elapsed_sec": elapsed,
            "fps_avg": self.frames / elapsed,
            "stop_requests": self.stop_requests,
            "uncertain_frames": self.uncertain,
            "max_confidence_seen": self.max_conf
        }

def save_metrics(path: str, metrics: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

def write_report(path: str, metrics: dict, notes: str = ""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = []
    lines.append("# Rail/CBTC Supervision – Validation Report (Prototype)\n\n")
    lines.append("## Key Metrics\n")
    for k, v in metrics.items():
        lines.append(f"- **{k}**: {v}\n")
    if notes:
        lines.append("\n## Notes / Limitations\n")
        lines.append(notes + "\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
