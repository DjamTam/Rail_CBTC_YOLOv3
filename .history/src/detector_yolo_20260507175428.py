import cv2
import numpy as np
from typing import List, Tuple, Dict

class YoloV3Detector:
    """Détecteur multi-classe utilisant YOLOv3 (personnes, voitures, etc.)"""
    
    def __init__(self, cfg_path: str, weights_path: str, names_path: str,
                 input_size: int = 256, conf_th: float = 0.6, nms_th: float = 0.45,
                 detect_classes: List[str] = None):
        """
        Initialiser le détecteur YOLOv3
        
        Args:
            cfg_path: Chemin du fichier de configuration (.cfg)
            weights_path: Chemin des poids pré-entraînés (.weights)
            names_path: Chemin du fichier des classes (.names)
            input_size: Taille de l'image d'entrée (256x256, 416x416, etc)
            conf_th: Seuil de confiance minimum (0-1)
            nms_th: Seuil de suppression non-maximum (éviter doublons)
            detect_classes: Liste des classes à détecter (ex: ["person", "car"])
                           Si None = détecter uniquement "person"
        """
        # Charger le réseau YOLOv3
        self.net = cv2.dnn.readNet(weights_path, cfg_path)
        self.input_size = input_size
        self.conf_th = conf_th
        self.nms_th = nms_th
        
        # Classes à détecter par défaut
        if detect_classes is None:
            detect_classes = ["person"]
        self.detect_classes = detect_classes

        # Charger les noms des classes (ex: "person", "car", "dog", etc)
        with open(names_path, "r", encoding="utf-8") as f:
            self.classes = [line.strip() for line in f.readlines()]

        # Vérifier que toutes les classes cibles existent
        self.class_ids = {}  # Dictionnaire: "person" → ID, "car" → ID
        for class_name in detect_classes:
            if class_name not in self.classes:
                raise ValueError(f"Classe '{class_name}' non trouvée dans coco.names")
            self.class_ids[class_name] = self.classes.index(class_name)

        # Récupérer les couches de sortie du réseau
        layer_names = self.net.getLayerNames()
        self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers().flatten()]

    def detect_objects(self, frame: np.ndarray) -> Dict[str, Tuple[List[Tuple[int,int,int,int]], List[float]]]:
        """
        Détecter tous les objets demandés dans une image/frame
        
        Returns:
            Dictionnaire: {"person": (boxes, confs), "car": (boxes, confs), ...}
        """
        h, w = frame.shape[:2]  # Hauteur et largeur de l'image
        
        # Préparer l'image pour le réseau (normalisation, redimensionnement)
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (self.input_size, self.input_size), swapRB=True, crop=False)
        self.net.setInput(blob)  # Entrer l'image dans le réseau
        outputs = self.net.forward(self.output_layers)  # Exécuter l'inférence

        # Dictionnaire pour stocker les détections par classe
        detections_by_class = {class_name: ([], []) for class_name in self.detect_classes}
        all_boxes_for_nms = []  # Pour NMS groupé
        all_confs_for_nms = []
        all_class_names = []

        # Parcourir toutes les détections
        for output in outputs:
            for det in output:
                # Récupérer les scores de chaque classe
                scores = det[5:]
                class_id = int(np.argmax(scores))  # Classe avec le plus haut score
                conf = float(scores[class_id])  # Score de confiance
                
                # Trouver le nom de la classe
                class_name = self.classes[class_id] if class_id < len(self.classes) else None

                # Garder seulement les détections des classes cibles au-dessus du seuil
                if class_name in self.detect_classes and conf >= self.conf_th:
                    # Coordonnées au format YOLOv3 (normalisées 0-1)
                    cx, cy, bw, bh = det[0], det[1], det[2], det[3]
                    # Convertir en coordonnées image (pixels)
                    x = int((cx - bw/2) * w)
                    y = int((cy - bh/2) * h)
                    bw = int(bw * w)
                    bh = int(bh * h)
                    
                    all_boxes_for_nms.append([x, y, bw, bh])
                    all_confs_for_nms.append(conf)
                    all_class_names.append(class_name)

        # Suppression non-maximum (NMS): éliminer les boîtes chevauchantes
        if len(all_boxes_for_nms) > 0:
            idxs = cv2.dnn.NMSBoxes(all_boxes_for_nms, all_confs_for_nms, self.conf_th, self.nms_th)
            if len(idxs) > 0:
                for i in idxs.flatten():
                    box = tuple(all_boxes_for_nms[i])
                    conf = all_confs_for_nms[i]
                    class_name = all_class_names[i]
                    # Ajouter à la classe correspondante
                    boxes, confs = detections_by_class[class_name]
                    boxes.append(box)
                    confs.append(conf)

        return detections_by_class
    
    def detect_persons(self, frame: np.ndarray) -> Tuple[List[Tuple[int,int,int,int]], List[float]]:
        """
        Détecter uniquement les personnes (compatibilité arrière)
        
        Returns:
            - boxes: Liste de boîtes englobantes [(x, y, width, height), ...]
            - confs: Liste des scores de confiance [0.85, 0.92, ...]
        """
        detections = self.detect_objects(frame)
        boxes, confs = detections.get("person", ([], []))
        return boxes, confs
        
        # Préparer l'image pour le réseau (normalisation, redimensionnement)
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (self.input_size, self.input_size), swapRB=True, crop=False)
        self.net.setInput(blob)  # Entrer l'image dans le réseau
        outputs = self.net.forward(self.output_layers)  # Exécuter l'inférence

        boxes, confs = [], []

        # Parcourir toutes les détections
        for output in outputs:
            for det in output:
                # Récupérer les scores de chaque classe
                scores = det[5:]
                class_id = int(np.argmax(scores))  # Classe avec le plus haut score
                conf = float(scores[class_id])  # Score de confiance

                # Garder seulement les détections de "person" au-dessus du seuil
                if class_id == self.person_id and conf >= self.conf_th:
                    # Coordonnées au format YOLOv3 (normalisées 0-1)
                    cx, cy, bw, bh = det[0], det[1], det[2], det[3]
                    # Convertir en coordonnées image (pixels)
                    x = int((cx - bw/2) * w)
                    y = int((cy - bh/2) * h)
                    bw = int(bw * w)
                    bh = int(bh * h)
                    boxes.append([x, y, bw, bh])
                    confs.append(conf)

        # Suppression non-maximum (NMS): éliminer les boîtes chevauchantes
        idxs = cv2.dnn.NMSBoxes(boxes, confs, self.conf_th, self.nms_th)
        final_boxes, final_confs = [], []
        if len(idxs) > 0:
            for i in idxs.flatten():
                final_boxes.append(tuple(boxes[i]))
                final_confs.append(confs[i])

        return final_boxes, final_confs
