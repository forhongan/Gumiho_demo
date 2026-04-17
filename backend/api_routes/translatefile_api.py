import json
import os
import glob

from typing import Optional

from flask import current_app, jsonify, request

from Config import Config
from epub_dispose import EpubDispose
from TranslateFile import TranslateFile


class TranslateFileAPI:
    def __init__(self, app):
        self.register_routes(app)

    def register_routes(self, app):
        app.add_url_rule("/translatefile", view_func=self.get_translatefile, methods=["GET"])
        app.add_url_rule("/translatefile", view_func=self.update_translatefile, methods=["POST"])

        app.add_url_rule("/title_list", view_func=self.get_title_list, methods=["GET"])
        app.add_url_rule("/translatefile/paragraph", view_func=self.get_paragraph_by_title, methods=["GET"])
        app.add_url_rule("/translatefile/paragraph", view_func=self.update_sentence, methods=["POST"])

        app.add_url_rule("/export_text", view_func=self.export_text, methods=["POST"])
        app.add_url_rule("/export_capabilities", view_func=self.export_capabilities, methods=["GET"])
        app.add_url_rule("/debug/routes", view_func=self.debug_routes, methods=["GET"])

    def _get_project_dir_from_translatefile(self, tf_path: str) -> str:
        return os.path.dirname(tf_path)

    def _detect_source_from_project(self, project_dir: str):
        """检测项目源文件信息。

        返回 dict（用于调试与能力判断）：
        - source_folder
        - config_path
        - config_file_name_raw
        - config_candidate_path
        - epub_candidates
        - selected_source_path

        选择规则：
        1) 若 config.yml 的 `file name` 能解析到存在的文件，则优先使用它。
        2) 否则从 sourcefile/ 下扫描：优先任意 .epub，其次任意文件。
        """
        source_folder = os.path.join(project_dir, "sourcefile")
        config_path = os.path.join(project_dir, "config.yml")

        debug = {
            "project_dir": project_dir,
            "source_folder": source_folder,
            "config_path": config_path,
            "config_file_name_raw": None,
            "config_candidate_path": None,
            "epub_candidates": [],
            "selected_source_path": None,
        }

        if not os.path.isdir(source_folder):
            return debug

        # 1) config.yml 显式指定
        if os.path.exists(config_path):
            try:
                cfg = Config(config_path)
                cfg_data = cfg.read_config() or {}
                file_name = cfg_data.get("file name")
                debug["config_file_name_raw"] = file_name
                if file_name:
                    candidate = file_name
                    if not os.path.isabs(candidate):
                        candidate = os.path.join(source_folder, candidate)
                    debug["config_candidate_path"] = candidate
                    if os.path.exists(candidate) and os.path.isfile(candidate):
                        debug["selected_source_path"] = candidate
                        # 同时补充 epub candidates
                        try:
                            debug["epub_candidates"] = sorted(
                                [p for p in glob.glob(os.path.join(source_folder, "*.epub")) if os.path.isfile(p)],
                                key=lambda s: s.lower(),
                            )
                        except Exception:
                            debug["epub_candidates"] = []
                        return debug
            except Exception as e:
                debug["config_error"] = str(e)

        # 2) 目录扫描回退：优先 .epub
        try:
            epub_candidates = [p for p in glob.glob(os.path.join(source_folder, "*.epub")) if os.path.isfile(p)]
        except Exception:
            epub_candidates = []
        debug["epub_candidates"] = sorted(epub_candidates, key=lambda s: s.lower())
        if debug["epub_candidates"]:
            debug["selected_source_path"] = debug["epub_candidates"][0]
            return debug

        try:
            all_files = [p for p in glob.glob(os.path.join(source_folder, "*")) if os.path.isfile(p)]
        except Exception:
            all_files = []
        all_files = sorted(all_files, key=lambda s: s.lower())
        debug["source_files"] = all_files[:20]
        debug["selected_source_path"] = all_files[0] if all_files else None
        return debug

    def _print_source_detect_debug(self, *, where: str, translatefile_path: Optional[str], detect: dict):
        """保留函数签名，避免调用方变更；当前不再输出调试日志。"""
        return

    def _get_source_file_path_from_project(self, project_dir: str):
        info = self._detect_source_from_project(project_dir)
        return info.get("selected_source_path")

    def debug_routes(self):
        """列出当前 Flask 已注册的路由，排查 404（例如 /export_capabilities 未注册）。"""
        try:
            rules = []
            for rule in current_app.url_map.iter_rules():
                rules.append({
                    "rule": str(rule),
                    "endpoint": getattr(rule, "endpoint", None),
                    "methods": sorted(list(getattr(rule, "methods", []) or [])),
                })
            return jsonify({"routes": rules}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def get_translatefile(self):
        tf_path = request.args.get("translatefilePath")
        target_state = request.args.get("target_state")
        if not tf_path or not os.path.exists(tf_path):
            return jsonify({"error": "非法的translatefilePath"}), 400
        tf_instance = TranslateFile(tf_path)
        if target_state:
            chapters = tf_instance.get_title_chapters_with_status_list(target_state)
            return jsonify({"chapters": chapters}), 200
        else:
            data = tf_instance.data
            return jsonify(data), 200

    def update_translatefile(self):
        data = request.get_json()
        tf_path = data.get("translatefilePath")
        content = data.get("content")
        if not tf_path or not os.path.exists(tf_path) or content is None:
            return jsonify({"error": "非法的参数"}), 400
        try:
            new_data = json.loads(content)
            tf_instance = TranslateFile(tf_path)
            tf_instance.write_translatefile(new_data)
            return jsonify({"message": "TranslateFile已更新"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def get_title_list(self):
        """获取标题列表,每项包含"title": now_chapter, "status": status"""
        tf_path = request.args.get("translatefilePath")
        tf_instance = TranslateFile(tf_path)
        # 兼容新增已翻译状态：仅返回“已翻译”章节
        self.chapters = tf_instance.get_title_chapters_with_status_list("translated_only")
        return jsonify({"chapters": self.chapters}), 200

    def export_capabilities(self):
        """查询导出能力：是否存在源 epub，从而允许“原样重构（refilled）”。"""
        try:
            tf_path = request.args.get("translatefilePath")
            if not tf_path or not os.path.exists(tf_path):
                return jsonify({"error": "非法的translatefilePath"}), 400

            project_dir = self._get_project_dir_from_translatefile(tf_path)
            detect = self._detect_source_from_project(project_dir)
            source_path = detect.get("selected_source_path")
            epub_candidates = detect.get("epub_candidates") or []

            # 能力判定：只要 sourcefile/ 下存在任意 .epub，即认为可“原样重构”
            has_source_epub = bool(epub_candidates)
            return jsonify(
                {
                    "marker": "GUMIHO_EXPORT_API_2026-04-15",
                    "has_source_epub": has_source_epub,
                }
            ), 200
        except Exception as e:
            return jsonify({"marker": "GUMIHO_EXPORT_API_2026-04-15", "error": str(e), "error_type": type(e).__name__}), 500

    def get_paragraph_by_title(self):
        """获取指定标题的段落内容"""
        title = request.args.get("title")
        tf_path = request.args.get("translatefilePath")
        if not title or not tf_path or not os.path.exists(tf_path):
            return jsonify({"error": "非法的参数"}), 400
        try:
            tf_instance = TranslateFile(tf_path)
            paragraphs = tf_instance.get_paragraph_by_title(title)
            return jsonify({"paragraphs": paragraphs}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def update_sentence(self):
        """更新单句内容"""
        data = request.get_json()
        tf_path = data.get("translatefilePath")
        chapter_id = data.get("id")
        new_translation = data.get("translation_text")

        if not all([tf_path, chapter_id, new_translation]):
            return jsonify({"error": "缺少必要参数"}), 400

        try:
            tf_instance = TranslateFile(tf_path)
            updated = False
            for chapter in tf_instance.data["chapters"]:
                if chapter["id"] == chapter_id:
                    chapter["translation-text"] = new_translation
                    chapter["state"] = "f_trans_finished"
                    updated = True
                    break

            if not updated:
                return jsonify({"error": "段落ID不存在"}), 404

            tf_instance.write_translatefile(tf_instance.data)
            return jsonify({"message": "段落更新成功"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def export_text(self):
        try:
            data = request.get_json(silent=True) or {}

            tf_path = data.get("translatefilePath")
            if not tf_path:
                return jsonify({"marker": "GUMIHO_EXPORT_API_2026-04-15", "error": "缺少translatefilePath参数"}), 400
            if not os.path.exists(tf_path):
                return jsonify({"marker": "GUMIHO_EXPORT_API_2026-04-15", "error": "非法的translatefilePath"}), 400

            export_format = (data.get("export_format") or "txt").lower()
            include_original = bool(data.get("include_original", False))
            epub_rebuild_mode = (data.get("epub_rebuild_mode") or "refilled").lower()  # refilled|rebuild

            export_work = TranslateFile(tf_path)
            start_title = data.get("start_title")
            end_title = data.get("end_title")
            if not start_title or not end_title:
                return jsonify({"marker": "GUMIHO_EXPORT_API_2026-04-15", "error": "缺少起始或结束章节"}), 400

            start_id = export_work.get_id_from_chapter_name(start_title)
            end_id = export_work.get_chapter_end_from_id(export_work.get_id_from_chapter_name(end_title))

            if start_id is None or end_id is None:
                return jsonify({"marker": "GUMIHO_EXPORT_API_2026-04-15", "error": "无法定位起始或结束章节的ID"}), 400

            # 推断导出标签状态：只用于文件命名（初译完成/校对完成）
            novel_status = "f_trans_finished"
            try:
                translated_states = {"proofreading_finished", "HT_PNTing", "HT_PNTed"}
                for ch in export_work.data.get("chapters", []):
                    cid = ch.get("id")
                    if isinstance(cid, int) and int(start_id) <= cid <= int(end_id):
                        if ch.get("state") in translated_states:
                            novel_status = "proofreading_finished"
                            break
            except Exception:
                novel_status = "f_trans_finished"

            output_path = None
            if export_format == "txt":
                output_path = export_work.export_translatefile(start_id, end_id, orig_txt=include_original)
            elif export_format == "epub":
                project_dir = self._get_project_dir_from_translatefile(tf_path)
                disposer = EpubDispose(project_path=project_dir)

                if epub_rebuild_mode == "refilled":
                    detect = self._detect_source_from_project(project_dir)
                    source_path = detect.get("selected_source_path")
                    epub_candidates = detect.get("epub_candidates") or []
                    # 允许原样重构：存在任意 .epub；实际回填使用优先：config 指定 epub，其次第一份 epub
                    if not epub_candidates:
                        return (
                            jsonify(
                                {
                                    "marker": "GUMIHO_EXPORT_API_2026-04-15",
                                    "error": "原样重构仅在 sourcefile/ 下存在 .epub 源文件时可用",
                                }
                            ),
                            400,
                        )

                    # 选择用于回填的 epub
                    if source_path and os.path.splitext(source_path)[1].lower() == ".epub":
                        epub_source = source_path
                    else:
                        epub_source = epub_candidates[0]

                    output_path = disposer.epub_refilled(
                        epub_file_path=epub_source,
                        translated_file_path=tf_path,
                        novel_status=novel_status,
                        with_original_text_or_not=include_original,
                    )
                else:
                    output_path = disposer.normal_epub_rebuild(
                        start_id,
                        end_id,
                        translated_file_path=tf_path,
                        novel_status=novel_status,
                        with_original_text_or_not=include_original,
                    )
            else:
                return jsonify({"marker": "GUMIHO_EXPORT_API_2026-04-15", "error": f"不支持的导出格式: {export_format}"}), 400
            return (
                jsonify(
                    {
                        "marker": "GUMIHO_EXPORT_API_2026-04-15",
                        "start_title": start_title,
                        "end_title": end_title,
                        "export_scope": data.get("export_scope"),
                        "export_format": export_format,
                        "include_original": include_original,
                        "epub_rebuild_mode": epub_rebuild_mode,
                        "output_path": output_path,
                    }
                ),
                200,
            )
        except Exception as e:
            return jsonify({"marker": "GUMIHO_EXPORT_API_2026-04-15", "error": str(e), "error_type": type(e).__name__}), 500
