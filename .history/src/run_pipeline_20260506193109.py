import cv2
import threading

from config import Config
from detector_yolo import YoloV3Detector
from roi import polygon_mask, is_box_in_roi, draw_roi, load_roi_polygon
from decision import SafetyDecision
from logger import EventLogger
from metrics import Metrics, save_metrics, write_report
from api import create_app


def draw_boxes(frame, boxes, confs, in_roi_flags):
    for (x, y, w, h), conf, in_roi in zip(boxes, confs, in_roi_flags):
        color = (0, 220, 0) if in_roi else (0, 120, 255)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        label = f"person {conf:.2f} {'IN_ROI' if in_roi else ''}"
        cv2.putText(frame, label, (x, max(0, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)


def default_roi(frame):
    h, w = frame.shape[:2]
    return [
        (int(0.2 * w), int(0.6 * h)),
        (int(0.8 * w), int(0.6 * h)),
        (int(0.95 * w), int(0.95 * h)),
        (int(0.05 * w), int(0.95 * h))
    ]


def main():
    cfg = Config()

    cap = cv2.VideoCapture(cfg.CAMERA_INDEX if cfg.USE_CAMERA else cfg.VIDEO_PATH)
    if not cap.isOpened():
        raise RuntimeError("Cannot open video/camera input")

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("Cannot read first frame")

    # Load ROI from file if available
    file_polygon = load_roi_polygon(cfg.ROI_FILE)
    if file_polygon is not None:
        cfg.ROI_POLYGON = file_polygon
    elif cfg.ROI_POLYGON is None:
        cfg.ROI_POLYGON = default_roi(first_frame)

    roi_mask = polygon_mask(first_frame.shape, cfg.ROI_POLYGON)

    detector = YoloV3Detector(cfg.YOLO_CFG, cfg.YOLO_WEIGHTS, cfg.COCO_NAMES,
                              input_size=cfg.INPUT_SIZE, conf_th=cfg.CONF_THRESHOLD, nms_th=cfg.NMS_THRESHOLD)

    decision = SafetyDecision(confirm_frames=cfg.CONFIRM_FRAMES, cooldown_seconds=cfg.COOLDOWN_SECONDS)
    logger = EventLogger(cfg.EVENTS_PATH)
    metrics = Metrics()
    
    # Thread-safe status dictionary
    status_lock = threading.Lock()
    shared_status = {
        "decision": "SAFE",
        "persons_in_roi": 0,
        "max_confidence": 0.0,
        "fps_avg": 0.0,
        "recent_events": []  # Real-time event buffer
    }

    app = create_app(shared_status, status_lock)
    api_thread = threading.Thread(target=lambda: app.run(host=cfg.API_HOST, port=cfg.API_PORT, debug=False, use_reloader=False), daemon=True)
    api_thread.start()

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        boxes, confs = detector.detect_persons(frame)

        in_roi_flags = [is_box_in_roi(box, roi_mask) for box in boxes]
        persons_in_roi = sum(in_roi_flags)
        detected_in_roi = persons_in_roi > 0

        dec = decision.update(detected_in_roi)
        max_conf = float(max(confs) if confs else 0.0)

        metrics.update(max_conf=max_conf, decision=dec)
        kpi = metrics.to_dict()

        with status_lock:
            shared_status["decision"] = str(dec)
            shared_status["persons_in_roi"] = int(persons_in_roi)
            shared_status["max_confidence"] = float(max_conf)
            shared_status["fps_avg"] = float(kpi["fps_avg"])

        if dec in ("STOP_REQUEST", "UNCERTAIN"):
            event_payload = {
                "event": dec,
                "persons_in_roi": int(persons_in_roi),
                "max_confidence": float(max_conf),
                "ts": time.time()
            }
            logger.log(event_payload)
            
            # Add to real-time buffer (keep last 50)
            with status_lock:
                shared_status["recent_events"].append(event_payload)
                if len(shared_status["recent_events"]) > 50:
                    shared_status["recent_events"].pop(0)

        draw_roi(frame, cfg.ROI_POLYGON)
        draw_boxes(frame, boxes, confs, in_roi_flags)

        cv2.putText(frame, f"Decision: {dec}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2)
        cv2.putText(frame, f"Persons in ROI: {persons_in_roi}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        cv2.imshow("Rail/CBTC Supervision – YOLOv3", frame)

        if cv2.waitKey(1) == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

    final_metrics = metrics.to_dict()
    save_metrics(cfg.METRICS_PATH, final_metrics)

    notes = (
        "- Prototype uses pretrained YOLOv3 (COCO). No fine-tuning.\n"
        "- ROI must be calibrated per scene using roi_picker.py.\n"
        "- Safety note: STOP_REQUEST is simulated only.\n"
        "- Next steps: dataset, evaluation (precision/recall), embedded optimization (Tiny-YOLO, quantization).\n"
    )

    write_report(cfg.REPORT_PATH, final_metrics, notes)


if __name__ == "__main__":
    main()
