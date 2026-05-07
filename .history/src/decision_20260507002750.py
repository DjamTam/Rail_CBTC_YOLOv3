import time
from dataclasses import dataclass

@dataclass
class DecisionState:
    """État de la machine à états pour la décision de sécurité"""
    consecutive_hits: int = 0  # Nombre de frames consécutives avec détection
    last_stop_time: float = 0.0  # Timestamp du dernier STOP_REQUEST

class SafetyDecision:
    """
    Logique de décision robuste et sûre pour la supervision ferroviaire.
    
    Utilise une approche en deux étapes:
    1. Confirmation (N frames consécutives) pour éviter les faux positifs
    2. Cooldown (délai d'attente) pour éviter les alertes répétées
    """
    
    def __init__(self, confirm_frames: int = 5, cooldown_seconds: float = 3.0):
        """
        Args:
            confirm_frames: Nombre de frames ConsécuTIVES avant alerte (ex: 5 = 5 détections d'affilée)
            cooldown_seconds: Délai minimum entre deux alertes STOP_REQUEST (ex: 3 secondes)
        """
        self.confirm_frames = confirm_frames
        self.cooldown_seconds = cooldown_seconds
        self.state = DecisionState()

    def update(self, detected_in_roi: bool) -> str:
        """
        Mettre à jour l'état et retourner une décision
        
        Args:
            detected_in_roi: True si une personne est détectée dans la ROI
            
        Returns:
            - "SAFE": Pas de personne détectée
            - "UNCERTAIN": Personne détectée mais moins de N frames (accumulation)
            - "STOP_REQUEST": Alerte! N frames consécutives ET cooldown écoulé
            - "COOLDOWN": N frames consécutives MAIS toujours en cooldown
        """
        now = time.time()

        # Compter les frames consécutives avec détection
        if detected_in_roi:
            self.state.consecutive_hits += 1  # Incrémenter le compteur
        else:
            self.state.consecutive_hits = 0  # Réinitialiser si pas de détection

        # Vérifier si on a atteint le seuil de confirmation
        if self.state.consecutive_hits >= self.confirm_frames:
            # Vérifier le cooldown pour éviter les alertes répétées
            if (now - self.state.last_stop_time) >= self.cooldown_seconds:
                # ✅ Toutes les conditions sont réunies → ALERTE!
                self.state.last_stop_time = now
                return "STOP_REQUEST"
            else:
                # Seuil atteint mais cooldown actif → attendre
                return "COOLDOWN"

        # Pas encore au seuil de confirmation
        return "SAFE" if not detected_in_roi else "UNCERTAIN"
