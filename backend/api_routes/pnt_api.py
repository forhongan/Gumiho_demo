import json
import os

from flask import jsonify, request

from PNT import PNT


class PNTAPI:
    def __init__(self, app):
        self.register_routes(app)

    def register_routes(self, app):
        app.add_url_rule("/pnt", view_func=self.get_pnt, methods=["GET"])
        app.add_url_rule("/pnt", view_func=self.update_pnt, methods=["POST"])

        app.add_url_rule("/pnt/characters_in_paragraph", view_func=self.get_characters_in_paragraph, methods=["GET"])
        app.add_url_rule("/pnt/characters_by_str", view_func=self.get_characters_by_str, methods=["GET"])

    def get_pnt(self):
        pnt_path = request.args.get("PNTPath")
        if not pnt_path or not os.path.exists(pnt_path):
            return jsonify({"error": "非法的PNTPath"}), 400
        pnt_instance = PNT(pnt_path)
        data = pnt_instance.read_pnt()
        return jsonify(data), 200

    def update_pnt(self):
        data = request.get_json()
        pnt_path = data.get("PNTPath")
        content = data.get("content")
        if not pnt_path or not os.path.exists(pnt_path) or content is None:
            return jsonify({"error": "非法的参数"}), 400
        try:
            new_data = json.loads(content)
            pnt_instance = PNT(pnt_path)
            pnt_instance.write_pnt(new_data)
            return jsonify({"message": "PNT已更新"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def get_characters_in_paragraph(self):
        title = request.args.get("title")
        pnt_path = request.args.get("PNTPath")
        if not title or not pnt_path or not os.path.exists(pnt_path):
            return jsonify({"error": "非法的参数"}), 400
        try:
            pnt_instance = PNT(pnt_path)
            characters = pnt_instance.get_characters_in_one_chapter(title)
            return jsonify({"characters": characters}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def get_characters_by_str(self):
        query_str = request.args.get("str")
        pnt_path = request.args.get("PNTPath")
        if not pnt_path or not os.path.exists(pnt_path):
            return jsonify({"error": "非法的参数"}), 400
        try:
            pnt_instance = PNT(pnt_path)
            characters = pnt_instance.get_characters_by_str(query_str)
            return jsonify({"characters": characters}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
