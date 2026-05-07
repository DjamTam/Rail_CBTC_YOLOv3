from flask import Flask, jsonify
import threading

def create_app(shared_status: dict, status_lock: threading.Lock):
    app = Flask(__name__)

    @app.get("/health")
    def health():
        try:
            return jsonify({"status": "ok"})
        except Exception as e:
            print(f"Health error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.get("/status")
    def status():
        try:
            with status_lock:
                # Make a copy to avoid race conditions
                status_copy = dict(shared_status)
            return jsonify(status_copy)
        except Exception as e:
            print(f"Status endpoint error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    return app
