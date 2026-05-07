import cv2
import threading
import time

from config import Config
from detector_yolo import YoloV3Detector
from roi import polygon_mask, is_box_in_roi, draw_roi, load_roi_polygon
from decision import SafetyDecision
from logger import EventLogger
from metrics import Metrics, save_metrics, write_report
from api import create_app


def draw_boxes(frame, detections_dict, roi_mask):
    """
    Dessiner toutes les détections (personnes, voitures, etc.) sur la frame
    
    Args:
        frame: Image OpenCV
        detections_dict: {"person": (boxes, confs), "car": (boxes, confs), ...}
        roi_mask: Masque de la ROI
    """
    # Couleurs par classe
    colors = {
        "person": (0, 220, 0),      # Vert
        "car": (0, 165, 255),       # Orange
        "motorcycle": (255, 0, 0),  # Bleu
        "truck": (0, 0, 255),       # Rouge
    }
    
    for class_name, (boxes, confs) in detections_dict.items():
        color = colors.get(class_name, (255, 255, 0))  # Cyan par défaut
        
        for (x, y, w, h), conf in zip(boxes, confs):
            in_roi = is_box_in_roi((x, y, w, h), roi_mask)
            
            # Seulement les personnes deviennent vert si dans ROI (surbrillance)
            # Les voitures restent orange même dans la ROI
            if class_name == "person" and in_roi:
                box_color = (0, 255, 0)  # Vert pour les personnes dans la ROI
            else:
                box_color = color  # Couleur de classe (orange pour voitures, etc.)
            
            # Tracer la boîte
            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
            
            # Tracer le label
            label = f"{class_name} {conf:.2f}"
            if in_roi:
                label += " [ROI]"
            cv2.putText(frame, label, (x, max(0, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, box_color, 2)


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
                              input_size=cfg.INPUT_SIZE, conf_th=cfg.CONF_THRESHOLD, 
                              nms_th=cfg.NMS_THRESHOLD,
                              detect_classes=cfg.DETECT_CLASSES or ["person", "car"])

    decision = SafetyDecision(confirm_frames=cfg.CONFIRM_FRAMES, cooldown_seconds=cfg.COOLDOWN_SECONDS)
    logger = EventLogger(cfg.EVENTS_PATH)
    metrics = Metrics()
    
    # Thread-safe status dictionary
    status_lock = threading.Lock()
    shared_status = {
        "decision": "SAFE",
        "persons_in_roi": 0,
        "cars_in_roi": 0,
        "max_confidence": 0.0,
        "max_confidence_person": 0.0,
        "max_confidence_car": 0.0,
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

        # Détecter toutes les classes (personnes, voitures, etc.)
        detections = detector.detect_objects(frame)
        
        # Extraire les détections de chaque classe
        person_boxes, person_confs = detections.get("person", ([], []))
        car_boxes, car_confs = detections.get("car", ([], []))
        
        # Vérifier quelles détections sont dans la ROI
        persons_in_roi = sum(1 for box in person_boxes if is_box_in_roi(box, roi_mask))
        cars_in_roi = sum(1 for box in car_boxes if is_box_in_roi(box, roi_mask))
        
        # ⚠️ ALERTE de sécurité: personne OU voiture dans la zone critique
        detected_in_roi = persons_in_roi > 0 or cars_in_roi > 0

        dec = decision.update(detected_in_roi)
        max_conf_person = float(max(person_confs) if person_confs else 0.0)
        max_conf_car = float(max(car_confs) if car_confs else 0.0)
        max_conf = max(max_conf_person, max_conf_car)

        metrics.update(max_conf=max_conf, decision=dec)
        kpi = metrics.to_dict()

        with status_lock:
            shared_status["decision"] = str(dec)
            shared_status["persons_in_roi"] = int(persons_in_roi)
            shared_status["cars_in_roi"] = int(cars_in_roi)
            shared_status["max_confidence"] = float(max_conf)
            shared_status["max_confidence_person"] = float(max_conf_person)
            shared_status["max_confidence_car"] = float(max_conf_car)
            shared_status["fps_avg"] = float(kpi["fps_avg"])

        if dec in ("STOP_REQUEST", "UNCERTAIN"):
            event_payload = {
                "event": dec,
                "persons_in_roi": int(persons_in_roi),
                "cars_in_roi": int(cars_in_roi),
                "max_confidence": float(max_conf)
            }
            logger.log(event_payload)
            
            # Add to real-time buffer with timestamp (keep last 50)
            event_with_ts = dict(event_payload)
            event_with_ts["ts"] = time.time()
            with status_lock:
                shared_status["recent_events"].append(event_with_ts)
                if len(shared_status["recent_events"]) > 50:
                    shared_status["recent_events"].pop(0)

        draw_roi(frame, cfg.ROI_POLYGON)
        draw_boxes(frame, detections, roi_mask)

        cv2.putText(frame, f"Decision: {dec}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2)
        cv2.putText(frame, f"Persons in ROI: {persons_in_roi} | Cars in ROI: {cars_in_roi}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(frame, f"Confidence: Pers={max_conf_person:.2f} Car={max_conf_car:.2f}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

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
