import os
import sys

import json

import flask
from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from werkzeug.exceptions import HTTPException

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from api_routes import register_all


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"ok": True, "pid": os.getpid(), "marker": "GUMIHO_BACKEND_2026-04-15"}), 200


@app.route("/debug/raise", methods=["GET"])
def debug_raise():
    raise RuntimeError("debug_raise")

apis = register_all(app, socketio, current_dir=current_dir)


if __name__ == "__main__":
    projects_api = apis.get("projects_api")
    if projects_api is not None:
        socketio.start_background_task(target=projects_api.background_thread, socketio=socketio)
    socketio.run(app, debug=False, host="0.0.0.0")

