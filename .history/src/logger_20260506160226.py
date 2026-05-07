import json
import os
import time
from typing import Dict, Any
import numpy as np

class EventLogger:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def log(self, payload: Dict[str, Any]):
        payload["ts"] = time.time()
        # Convert numpy types to Python native types for JSON serialization
        payload = self._convert_numpy_types(payload)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    
    @staticmethod
    def _convert_numpy_types(obj):
        """Recursively convert numpy types to Python native types"""
        if isinstance(obj, dict):
            return {k: EventLogger._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [EventLogger._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        return obj
