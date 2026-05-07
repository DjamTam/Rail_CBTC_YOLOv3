import json
import os
import time

class Metrics:
    """
    Collecteur de métriques pendant l'exécution du pipeline
    Calcule: FPS, nombre de détections, événements STOP, etc.
    """
    
    def __init__(self):
        """Initialiser les compteurs à zéro"""
        self.start = time.time()  # Temps de démarrage
        self.frames = 0  # Nombre total d'images traitées
        self.stop_requests = 0  # Nombre d'alertes STOP_REQUEST
        self.uncertain = 0  # Nombre de frames avec UNCERTAIN
        self.max_conf = 0.0  # Confiance maximale observée

    def update(self, max_conf: float, decision: str):
        """
        Mettre à jour les métriques après chaque frame
        
        Args:
            max_conf: Score de confiance maximum de la frame
            decision: Décision prise (SAFE, UNCERTAIN, STOP_REQUEST, COOLDOWN)
        """
        self.frames += 1
        self.max_conf = max(self.max_conf, max_conf)  # Garder la confiance max
        if decision == "STOP_REQUEST":
            self.stop_requests += 1
        if decision == "UNCERTAIN":
            self.uncertain += 1

    def to_dict(self):
        """
        Retourner un dictionnaire avec les métriques calculées
        
        Returns:
            Dictionnaire contenant: frames, elapsed_sec, fps_avg, stop_requests, etc.
        """
        elapsed = max(1e-6, time.time() - self.start)  # Temps écoulé (minimum 1µs)
        return {
            "frames": self.frames,  # Nombre d'images traitées
            "elapsed_sec": elapsed,  # Temps écoulé en secondes
            "fps_avg": self.frames / elapsed,  # Images par seconde (moyenne)
            "stop_requests": self.stop_requests,  # Nombre d'alertes STOP
            "uncertain_frames": self.uncertain,  # Frames avec détections
            "max_confidence_seen": self.max_conf  # Confiance maximale observée
        }

def save_metrics(path: str, metrics: dict):
    """
    Sauvegarder les métriques dans un fichier JSON
    
    Args:
        path: Chemin du fichier JSON (ex: outputs/metrics.json)
        metrics: Dictionnaire des métriques
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

def write_report(path: str, metrics: dict, notes: str = ""):
    """
    Générer un rapport de validation en Markdown
    
    Args:
        path: Chemin du fichier rapport (ex: outputs/report.md)
        metrics: Dictionnaire des métriques
        notes: Notes supplémentaires (limitations, améliorations futures)
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = []
    lines.append("# Rail/CBTC Supervision – Rapport de Validation (Prototype)\n\n")
    lines.append("## Métriques Clés\n")
    for k, v in metrics.items():
        lines.append(f"- **{k}**: {v}\n")
    if notes:
        lines.append("\n## Notes et Limitations\n")
        lines.append(notes + "\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
