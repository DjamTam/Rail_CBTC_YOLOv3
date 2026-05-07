import json
import os
import time
from typing import Dict, Any
import numpy as np

class EventLogger:
    """
    Enregistreur d'événements pour l'audit et la traçabilité
    Sauvegarde tous les événements importants en format JSONL (JSON Lines)
    """
    
    def __init__(self, path: str):
        """
        Args:
            path: Chemin du fichier de log (ex: outputs/events.jsonl)
        """
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)  # Créer le dossier s'il n'existe pas

    def log(self, payload: Dict[str, Any]):
        """
        Enregistrer un événement avec timestamp
        
        Args:
            payload: Dictionnaire contenant les informations de l'événement
                     (ex: {"event": "STOP_REQUEST", "persons_in_roi": 2, "max_confidence": 0.92})
        """
        payload["ts"] = time.time()  # Ajouter le timestamp (heure de l'événement)
        # Convertir les types NumPy en types Python natifs (compatible JSON)
        payload = self._convert_numpy_types(payload)
        # Écrire une ligne JSON par événement (format JSONL = une ligne par événement)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    
    @staticmethod
    def _convert_numpy_types(obj):
        """
        Convertir les types NumPy/Tenseurs en types Python natifs
        (Nécessaire car JSON ne peut pas sérialiser int64, float64, etc)
        """
        if isinstance(obj, dict):
            return {k: EventLogger._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [EventLogger._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)  # Convertir int64 → int
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)  # Convertir float64 → float
        return obj
