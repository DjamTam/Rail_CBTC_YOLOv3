from flask import Flask, jsonify
import threading

def create_app(shared_status: dict, status_lock: threading.Lock):
    """
    Créer une application Flask pour exposer le statut en temps réel via REST API
    
    Args:
        shared_status: Dictionnaire partagé contenant le statut actuel
        status_lock: Verrou pour éviter les conditions de course (thread-safety)
        
    Returns:
        Application Flask prête à être lancée
    """
    app = Flask(__name__)

    @app.get("/health")
    def health():
        """
        Endpoint de santé (health check)
        Utilisé pour vérifier si le serveur est opérationnel
        """
        try:
            return jsonify({"status": "ok"})
        except Exception as e:
            print(f"Erreur health: {e}")
            return jsonify({"error": str(e)}), 500

    @app.get("/status")
    def status():
        """
        Endpoint principal: retourne le statut en temps réel de la supervision
        
        Retourne:
        {
            "decision": "SAFE|UNCERTAIN|STOP_REQUEST|COOLDOWN",
            "persons_in_roi": 2,
            "max_confidence": 0.92,
            "fps_avg": 25.3,
            "recent_events": [...]  # Derniers événements enregistrés
        }
        """
        try:
            with status_lock:  # Vérrou pour éviter les modifications concurrentes
                # Copier le dictionnaire pour éviter les problèmes de sérialisation JSON
                status_copy = dict(shared_status)
            return jsonify(status_copy)
        except Exception as e:
            print(f"Erreur endpoint status: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    return app
