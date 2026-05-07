from flask import Flask, jsonify

def create_app(shared_status: dict):
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/status")
    def status():
        return jsonify(shared_status)

    return app
