import cv2
import numpy as np
from typing import List, Tuple

class YoloV3Detector:
    """Détecteur de personnes utilisant YOLOv3 (réseau de neurones)"""
    
    def __init__(self, cfg_path: str, weights_path: str, names_path: str,
                 input_size: int = 256, conf_th: float = 0.6, nms_th: float = 0.45):
        """
        Initialiser le détecteur YOLOv3
        
        Args:
            cfg_path: Chemin du fichier de configuration (.cfg)
            weights_path: Chemin des poids pré-entraînés (.weights)
            names_path: Chemin du fichier des classes (.names)
            input_size: Taille de l'image d'entrée (256x256, 416x416, etc)
            conf_th: Seuil de confiance minimum (0-1)
            nms_th: Seuil de suppression non-maximum (éviter doublons)
        """
        # Charger le réseau YOLOv3
        self.net = cv2.dnn.readNet(weights_path, cfg_path)
        self.input_size = input_size
        self.conf_th = conf_th
        self.nms_th = nms_th

        # Charger les noms des classes (ex: "person", "car", "dog", etc)
        with open(names_path, "r", encoding="utf-8") as f:
            self.classes = [line.strip() for line in f.readlines()]

        # Vérifier que "person" existe dans la liste des classes
        if "person" not in self.classes:
            raise ValueError("Classe 'person' non trouvée dans coco.names")

        # Trouver l'ID de la classe "person"
        self.person_id = self.classes.index("person")

        # Récupérer les couches de sortie du réseau
        layer_names = self.net.getLayerNames()
        self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers().flatten()]

    def detect_persons(self, frame: np.ndarray) -> Tuple[List[Tuple[int,int,int,int]], List[float]]:
        """
        Détecter les personnes dans une image/frame
        
        Returns:
            - boxes: Liste de boîtes englobantes [(x, y, width, height), ...]
            - confs: Liste des scores de confiance [0.85, 0.92, ...]
        """
        h, w = frame.shape[:2]  # Hauteur et largeur de l'image
        
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
