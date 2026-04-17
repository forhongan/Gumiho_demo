import json
import os

from flask import jsonify, request

from Record import Record


class FRecordAPI:
    def __init__(self, app):
        self.register_routes(app)

    def register_routes(self, app):
        app.add_url_rule("/f_record", view_func=self.get_f_record, methods=["GET"])
        app.add_url_rule("/f_record", view_func=self.update_f_record, methods=["POST"])
        app.add_url_rule("/f_record_group", view_func=self.get_f_record_group_by_title, methods=["GET"])

    def get_f_record(self):
        record_path = request.args.get("recordPath")
        if not record_path or not os.path.exists(record_path):
            return jsonify({"error": "非法的recordPath"}), 400
        record_instance = Record(record_path)
        data = record_instance.read_record()
        return jsonify(data), 200

    def update_f_record(self):
        data = request.get_json()
        record_path = data.get("recordPath")
        content = data.get("content")
        if not record_path or not os.path.exists(record_path) or content is None:
            return jsonify({"error": "非法的参数"}), 400
        try:
            new_data = json.loads(content)
            record_instance = Record(record_path)
            record_instance.write_record(new_data)
            return jsonify({"message": "f_record已更新"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def get_f_record_group_by_title(self):
        """根据前端选取的章节的标题,获得该章节的翻译记录"""
        title = request.args.get("title")
        if not title or not os.path.exists() or title not in self.chapters:
            return jsonify({"error": "找不到该章节"}), 400
        try:
            record_path = request.args.get("recordPath")
            record_instance = Record(record_path)
            records_by_title = record_instance.get_records_by_paragraph_title()
            return jsonify(records_by_title), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def rewrite_changed_record(self):
        """添加新的翻译记录,并放弃旧的翻译记录"""
        try:
            record_path = request.args.get("recordPath")
            record_timestamp = request.args.get("timestamp")
            new_record = request.get_json("new_record")
            record_instance = Record(record_path)
            record_instance.rewrite_one_record(record_timestamp, new_record)
            return jsonify({"message": f"已更新记录于{record_timestamp}的记录,注意记录需要重用才能反应到翻译文件"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


class PRecordAPI:
    def __init__(self, app):
        self.register_routes(app)

    def register_routes(self, app):
        app.add_url_rule("/p_record", view_func=self.get_p_record, methods=["GET"])
        app.add_url_rule("/p_record", view_func=self.update_p_record, methods=["POST"])

    def get_p_record(self):
        record_path = request.args.get("recordPath")
        if not record_path or not os.path.exists(record_path):
            return jsonify({"error": "非法的recordPath"}), 400
        record_instance = Record(record_path)
        data = record_instance.read_record()
        return jsonify(data), 200

    def update_p_record(self):
        data = request.get_json()
        record_path = data.get("recordPath")
        content = data.get("content")
        if not record_path or not os.path.exists(record_path) or content is None:
            return jsonify({"error": "非法的参数"}), 400
        try:
            new_data = json.loads(content)
            record_instance = Record(record_path)
            record_instance.write_record(new_data)
            return jsonify({"message": "p_record已更新"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
