import cv2
import numpy as np
from typing import List, Tuple

class YoloV3Detector:
    def __init__(self, cfg_path: str, weights_path: str, names_path: str,
                 input_size: int = 320, conf_th: float = 0.6, nms_th: float = 0.45):
        self.net = cv2.dnn.readNet(weights_path, cfg_path)
        self.input_size = input_size
        self.conf_th = conf_th
        self.nms_th = nms_th

        with open(names_path, "r", encoding="utf-8") as f:
            self.classes = [line.strip() for line in f.readlines()]

        if "person" not in self.classes:
            raise ValueError("Class 'person' not found in coco.names")

        self.person_id = self.classes.index("person")

        layer_names = self.net.getLayerNames()
        self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers().flatten()]

    def detect_persons(self, frame: np.ndarray) -> Tuple[List[Tuple[int,int,int,int]], List[float]]:
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (self.input_size, self.input_size), swapRB=True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward(self.output_layers)

        boxes, confs = [], []

        for output in outputs:
            for det in output:
                scores = det[5:]
                class_id = int(np.argmax(scores))
                conf = float(scores[class_id])

                if class_id == self.person_id and conf >= self.conf_th:
                    cx, cy, bw, bh = det[0], det[1], det[2], det[3]
                    x = int((cx - bw/2) * w)
                    y = int((cy - bh/2) * h)
                    bw = int(bw * w)
                    bh = int(bh * h)
                    boxes.append([x, y, bw, bh])
                    confs.append(conf)

        idxs = cv2.dnn.NMSBoxes(boxes, confs, self.conf_th, self.nms_th)
        final_boxes, final_confs = [], []
        if len(idxs) > 0:
            for i in idxs.flatten():
                final_boxes.append(tuple(boxes[i]))
                final_confs.append(confs[i])

        return final_boxes, final_confs
