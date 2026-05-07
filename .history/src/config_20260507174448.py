from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Config:
    # === Fichiers YOLOv3 (Réseau de neurones) ===
    YOLO_CFG: str = "assets/yolov3.cfg"  # Architecture du réseau (structure)
    YOLO_WEIGHTS: str = "assets/yolov3.weights"  # Poids pré-entraînés (cerveau du modèle)
    COCO_NAMES: str = "assets/coco.names"  # Noms des classes détectables (ex: "person")

    # === Source d'entrée (vidéo ou caméra) ===
    USE_CAMERA: bool = False  # True = utiliser webcam, False = utiliser fichier vidéo
    CAMERA_INDEX: int = 0  # Index de la caméra (0 = caméra par défaut)
    VIDEO_PATH: str = "data/sample_track_video.mp4"  # Chemin du fichier vidéo

    # === Paramètres YOLOv3 (performance/précision) ===
    INPUT_SIZE: int = 256  # Taille d'entrée du réseau (256x256 pixels, plus petit = plus rapide)
    CONF_THRESHOLD: float = 0.60  # Seuil de confiance (0-1): ne garder que 60% de confiance minimum
    NMS_THRESHOLD: float = 0.45  # Seuil de suppression non-maximum (éviter les doublons)
    DETECT_CLASSES: List[str] = None  # Classes à détecter (None = "person" uniquement)

    # === Décision robuste de sécurité (N images consécutives) ===
    CONFIRM_FRAMES: int = 5  # Nombre de frames consécutives pour confirmer une détection
    COOLDOWN_SECONDS: float = 2.0  # Délai d'attente avant une nouvelle alerte STOP

    # === Zone d'intérêt (ROI - Region Of Interest) / Zone critique ===
    ROI_POLYGON: List[Tuple[int, int]] = None  # Polygone définissant la zone de surveillance (points X,Y)
    ROI_FILE: str = "outputs/roi_polygon.json"  # Fichier JSON où sauvegarder les points de la ROI

    # === Fichiers de sortie (résultats, logs, rapports) ===
    EVENTS_PATH: str = "outputs/events.jsonl"  # Fichier log des événements (STOP_REQUEST, UNCERTAIN)
    METRICS_PATH: str = "outputs/metrics.json"  # Métriques de performance (FPS, nombre d'images)
    REPORT_PATH: str = "outputs/report.md"  # Rapport final (rapport de validation)

    # === API Flask (serveur web pour consulter le statut en temps réel) ===
    API_HOST: str = "127.0.0.1"  # Adresse IP (localhost)
    API_PORT: int = 5000  # Port (port réseau)
