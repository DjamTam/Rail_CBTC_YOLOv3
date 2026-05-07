import cv2
import numpy as np
import json
import os
from typing import List, Tuple

def polygon_mask(frame_shape, polygon: List[Tuple[int,int]]):
    h, w = frame_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    pts = np.array(polygon, dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)
    return mask

def is_box_in_roi(box, roi_mask) -> bool:
    x, y, w, h = box
    cx = x + w // 2
    cy = y + h // 2
    return roi_mask[cy, cx] == 255

def draw_roi(frame, polygon: List[Tuple[int,int]]):
    pts = np.array(polygon, dtype=np.int32)
    cv2.polylines(frame, [pts], isClosed=True, color=(255, 180, 0), thickness=2)
    cv2.putText(frame, "ROI (trackside zone)", (pts[0][0], max(0, pts[0][1]-10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 180, 0), 2)

def load_roi_polygon(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("roi_polygon", None)
