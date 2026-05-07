from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Config:
    # YOLOv3 assets
    YOLO_CFG: str = "assets/yolov3.cfg"
    YOLO_WEIGHTS: str = "assets/yolov3.weights"
    COCO_NAMES: str = "assets/coco.names"

    # Input video/camera
    USE_CAMERA: bool = False
    CAMERA_INDEX: int = 0
    VIDEO_PATH: str = "data/sample_track_video.mp4"

    # YOLO params
    INPUT_SIZE: int = 256
    CONF_THRESHOLD: float = 0.60
    NMS_THRESHOLD: float = 0.45
    SKIP_FRAMES: int = 2  # Process every Nth frame (1 = all frames, 2 = every 2nd, 3 = every 3rd)

    # Robust decision (safety-friendly)
    CONFIRM_FRAMES: int = 5
    COOLDOWN_SECONDS: float = 3.0

    # ROI polygon (x,y) in image coordinates
    ROI_POLYGON: List[Tuple[int, int]] = None
    ROI_FILE: str = "outputs/roi_polygon.json"  # created by roi_picker.py

    # Outputs
    EVENTS_PATH: str = "outputs/events.jsonl"
    METRICS_PATH: str = "outputs/metrics.json"
    REPORT_PATH: str = "outputs/report.md"

    # API
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 5000
