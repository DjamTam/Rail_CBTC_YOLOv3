import cv2
import numpy as np
import json
import os
from typing import List, Tuple

def polygon_mask(frame_shape, polygon: List[Tuple[int,int]]):
    """
    Créer un masque binaire pour la ROI (Zone d'intérêt)
    
    Args:
        frame_shape: Dimensions de l'image (hauteur, largeur, canaux)
        polygon: Liste des points du polygone [(x1,y1), (x2,y2), ...]
        
    Returns:
        Masque binaire où 255 = intérieur, 0 = extérieur
    """
    h, w = frame_shape[:2]  # Extraire hauteur et largeur
    mask = np.zeros((h, w), dtype=np.uint8)  # Créer un masque noir
    pts = np.array(polygon, dtype=np.int32)  # Convertir points en format NumPy
    cv2.fillPoly(mask, [pts], 255)  # Remplir le polygone en blanc
    return mask

def is_box_in_roi(box, roi_mask) -> bool:
    """
    Vérifier si une boîte englobante est dans la ROI
    
    Args:
        box: Boîte englobante (x, y, width, height)
        roi_mask: Masque binaire de la ROI
        
    Returns:
        True si le centre de la boîte est dans la ROI
    """
    x, y, w, h = box
    cx = x + w // 2  # Centre X de la boîte
    cy = y + h // 2  # Centre Y de la boîte
    return roi_mask[cy, cx] == 255  # Vérifier si le centre est blanc (dans la ROI)

def draw_roi(frame, polygon: List[Tuple[int,int]]):
    """
    Dessiner la ROI sur l'image pour visualisation
    
    Args:
        frame: Image/frame OpenCV
        polygon: Liste des points du polygone
    """
    pts = np.array(polygon, dtype=np.int32)
    cv2.polylines(frame, [pts], isClosed=True, color=(255, 180, 0), thickness=2)  # Tracer les contours
    cv2.putText(frame, "ROI (zone critique)", (pts[0][0], max(0, pts[0][1]-10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 180, 0), 2)  # Ajouter texte

def load_roi_polygon(path: str):
    """
    Charger les points de la ROI depuis un fichier JSON
    
    Args:
        path: Chemin du fichier JSON
        
    Returns:
        Liste des points du polygone ou None si le fichier n'existe pas
    """
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("roi_polygon", None)  # Extraire la clé "roi_polygon"
