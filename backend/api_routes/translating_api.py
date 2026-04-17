import json
import queue
import threading
import time
import uuid

from flask import jsonify, request, Response

from translate import Translating


# 定义全局变量用于暂存Translating实例
translating_instances = {}

# 全局字典存储SSE通道
sse_channels = {}


class TranslatingAPI:
    def __init__(self, app):
        self.register_routes(app)

    def register_routes(self, app):
        app.add_url_rule("/translating/start", view_func=self.translating_start, methods=["POST"])
        app.add_url_rule("/translating/submit_check", view_func=self.translating_submit_check, methods=["POST"])
        app.add_url_rule("/translating/stream/<trans_id>", view_func=self.sse_stream, methods=["GET"])

    def sse_stream(self, trans_id):
        """SSE事件流处理"""

        def generate():
            channel = sse_channels.get(trans_id)
            if not channel:
                yield 'event: error\ndata: {"message": "无效的翻译ID"}\n\n'
                return
            while True:
                msg = channel.get()
                if msg == "DONE":
                    yield "event: end\ndata: {}\n\n"
                    break
                yield f"event: {msg.get('type', 'message')}\ndata: {json.dumps(msg)}\n\n"

        return Response(generate(), mimetype="text/event-stream")

    def translating_start(self):
        data = request.get_json()
        project_name = data.get("project_name")
        if not project_name:
            return jsonify({"error": "缺少project_name参数"}), 400
        trans_id = uuid.uuid4().hex
        sse_channels[trans_id] = queue.Queue()

        translator = Translating(
            project_name,
            "translating",
            sse_callback=lambda msg: sse_channels[trans_id].put(msg),
        )

        threading.Thread(target=self.run_translation, args=(translator, trans_id)).start()
        return jsonify({"trans_id": trans_id, "stream_url": f"/translating/stream/{trans_id}"})

    def run_translation(self, translator, trans_id):
        """在后台线程中运行翻译"""
        try:
            print("[DEBUG] 开始运行翻译任务")
            translator.translating_to_result()
            print("[DEBUG] 翻译进度完成，准备发送SSE消息")
            if translator.Config.data[translator.now_setting].get("human_involvement", False):
                check_data = translator.get_human_check_list()
                translating_instances[trans_id] = translator
                sse_channels[trans_id].put({"type": "result", "need_human_check": True, "check_list": check_data})
            else:
                translator.save_f_record()
                translator.record_to_file()
                sse_channels[trans_id].put({"type": "result", "need_human_check": False, "message": "翻译完成并保存"})
        except Exception as e:
            sse_channels[trans_id].put({"type": "error", "message": str(e)})
        finally:
            sse_channels[trans_id].put("DONE")
            time.sleep(1)
            del sse_channels[trans_id]

    def translating_submit_check(self):
        data = request.get_json()
        trans_id = data.get("trans_id")
        checked_record = data.get("new_record")
        if not trans_id or trans_id not in translating_instances:
            return jsonify({"error": "无效的trans_id"}), 400
        translator = translating_instances.pop(trans_id)
        translator.new_record = checked_record
        translator.save_f_record()
        translator.record_to_file()
        return jsonify({"message": "校对结果已提交并保存"})
