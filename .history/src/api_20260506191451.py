from flask import Flask, jsonify
import threading

def create_app(shared_status: dict):
    app = Flask(__name__)
    lock = threading.Lock()

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/status")
    def status():
        with lock:
            # Make a copy to avoid race conditions
            status_copy = shared_status.copy()
        return jsonify(status_copy)

    return app
