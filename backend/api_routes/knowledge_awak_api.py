import os

from flask import jsonify, request

from PNT import PNT
from knowledge_awak import KnowledgeAwakener


class KnowledgeAwakAPI:
    def __init__(self, app):
        self.register_routes(app)

    def register_routes(self, app):
        app.add_url_rule("/ka/cards", view_func=self.list_cards, methods=["GET"])
        app.add_url_rule("/ka/card", view_func=self.upsert_card, methods=["POST"])
        app.add_url_rule("/ka/card/delete", view_func=self.delete_card, methods=["POST"])

        app.add_url_rule("/ka/build_ai_knowledge", view_func=self.build_ai_knowledge, methods=["POST"])
        app.add_url_rule("/ka/build_ai_knowledge_from_range", view_func=self.build_ai_knowledge_from_range, methods=["POST"])
        app.add_url_rule("/ka/build_ai_knowledge_from_chapters", view_func=self.build_ai_knowledge_from_chapters, methods=["POST"])

        app.add_url_rule("/ka/material", view_func=self.get_material, methods=["GET"])

    def list_cards(self):
        pnt_path = request.args.get("PNTPath")
        query = request.args.get("q", "")
        if not pnt_path or not os.path.exists(pnt_path):
            return jsonify({"error": "非法的PNTPath"}), 400
        try:
            pnt = PNT(pnt_path)
            cards = pnt.search_knowledge_awaken_cards(query)
            return jsonify({"cards": cards}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def upsert_card(self):
        data = request.get_json() or {}
        pnt_path = data.get("PNTPath")
        card = data.get("card") or {}
        if not pnt_path or not os.path.exists(pnt_path):
            return jsonify({"error": "非法的PNTPath"}), 400
        try:
            pnt = PNT(pnt_path)
            entry = pnt.upsert_knowledge_awaken_card(
                card_id=card.get("id"),
                keyword_expr=card.get("keyword_expr", ""),
                knowledge_content=card.get("knowledge_content", ""),
                enabled=card.get("enabled", True),
                meta=card.get("meta"),
            )
            return jsonify({"card": entry}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def delete_card(self):
        data = request.get_json() or {}
        pnt_path = data.get("PNTPath")
        card_id = data.get("id")
        if not pnt_path or not os.path.exists(pnt_path) or not card_id:
            return jsonify({"error": "非法的参数"}), 400
        try:
            pnt = PNT(pnt_path)
            ok = pnt.delete_knowledge_awaken_card(card_id)
            return jsonify({"ok": bool(ok)}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def build_ai_knowledge(self):
        """输入原文/译文（可任一为空），用 AI 生成 keyword_expr 与 knowledge_content（不写入）。"""
        data = request.get_json() or {}
        project_name = data.get("projectName")
        original_text = data.get("original_text", "")
        translated_text = data.get("translated_text", "")
        requirement = data.get("requirement", "")
        keyword_hint = data.get("keyword_hint")
        status = data.get("status", "translating")

        if not project_name or not requirement:
            return jsonify({"error": "缺少必要参数 projectName/requirement"}), 400
        try:
            awakener = KnowledgeAwakener(project_name=project_name)
            result = awakener.build_ai_knowledge(
                original_text=original_text,
                translated_text=translated_text,
                requirement=requirement,
                keyword_hint=keyword_hint,
                status=status,
            )
            return jsonify({"result": result}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def build_ai_knowledge_from_range(self):
        """输入 start_id/end_id（段落 id 范围），用 AI 生成（不写入）。"""
        data = request.get_json() or {}
        project_name = data.get("projectName")
        start_id = data.get("start_id")
        end_id = data.get("end_id")
        requirement = data.get("requirement", "")
        keyword_hint = data.get("keyword_hint")
        status = data.get("status", "translating")

        if not project_name or start_id is None or end_id is None or not requirement:
            return jsonify({"error": "缺少必要参数 projectName/start_id/end_id/requirement"}), 400
        try:
            awakener = KnowledgeAwakener(project_name=project_name)
            result = awakener.build_ai_knowledge_from_range(
                start_id=int(start_id),
                end_id=int(end_id),
                requirement=requirement,
                keyword_hint=keyword_hint,
                status=status,
            )
            return jsonify({"result": result, "resolved": {"start_id": int(start_id), "end_id": int(end_id)}}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def build_ai_knowledge_from_chapters(self):
        """输入 start_title/end_title（章节标题），后端解析到 id 范围后生成（不写入）。"""
        data = request.get_json() or {}
        project_name = data.get("projectName")
        start_title = data.get("start_title")
        end_title = data.get("end_title")
        requirement = data.get("requirement", "")
        keyword_hint = data.get("keyword_hint")
        status = data.get("status", "translating")

        if not project_name or not start_title or not end_title or not requirement:
            return jsonify({"error": "缺少必要参数 projectName/start_title/end_title/requirement"}), 400

        try:
            awakener = KnowledgeAwakener(project_name=project_name)
            tf = awakener.TranslateFile
            start_id = tf.get_id_from_chapter_name(start_title)
            end_title_id = tf.get_id_from_chapter_name(end_title)
            if start_id is None or end_title_id is None:
                return jsonify({"error": "未找到章节标题对应的 id"}), 400
            end_id = tf.get_chapter_end_from_id(end_title_id)
            if end_id is None:
                return jsonify({"error": "无法计算章节结束 id"}), 400

            result = awakener.build_ai_knowledge_from_range(
                start_id=int(start_id),
                end_id=int(end_id),
                requirement=requirement,
                keyword_hint=keyword_hint,
                status=status,
            )
            return jsonify({
                "result": result,
                "resolved": {
                    "start_title": start_title,
                    "end_title": end_title,
                    "start_id": int(start_id),
                    "end_id": int(end_id),
                }
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def get_material(self):
        """调试/预览：返回按 id 范围拼接的材料文本。"""
        project_name = request.args.get("projectName")
        start_id = request.args.get("start_id")
        end_id = request.args.get("end_id")
        include_translation = request.args.get("include_translation", "1")

        if not project_name or start_id is None or end_id is None:
            return jsonify({"error": "缺少必要参数 projectName/start_id/end_id"}), 400

        try:
            awakener = KnowledgeAwakener(project_name=project_name)
            material = awakener.build_material_from_range(
                int(start_id),
                int(end_id),
                include_translation=str(include_translation).strip() not in {"0", "false", "False"},
            )
            return jsonify({"material": material}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
