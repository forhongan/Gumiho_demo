import io
import json
import os
import shutil

from typing import Optional

from flask import jsonify, request, Response

from Config import Config
from TranslateFile import TranslateFile
from format import LightNovelRobotJpFormat
from format import create_trans_compare_table, create_f_record, create_p_record, create_table_of_content


def register_config_template(app, *, current_dir: str):
    @app.route("/config_template", methods=["GET"])
    def get_config_template():
        """返回默认配置模板（lnrj_default_config.yml），用于前端创建项目前的预编辑。"""
        template_path = os.path.join(current_dir, "lnrj_default_config.yml")
        if not os.path.exists(template_path):
            return jsonify({"error": "默认配置模板不存在"}), 404
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content, mimetype="text/yaml; charset=utf-8")


def create_project(
    project_name,
    translator_name,
    file_path,
    force=False,
    *,
    current_dir: str,
    init_mode: Optional[str] = None,
    translation_file_path: Optional[str] = None,
    paragraph_aggregation_mode: Optional[bool] = None,
    double_blank_line: Optional[bool] = None,
    merge_to_translatefile: bool = False,
    enable_reading: bool = False,
    config_content=None,
):
    from ruamel.yaml import YAML

    yaml_obj = YAML()
    init_mode = (init_mode or "new").strip().lower()

    project_folder_name = f"{project_name}_project"
    project_folder = os.path.join(current_dir, project_folder_name)

    if os.path.exists(project_folder) and not force:
        return None
    if os.path.exists(project_folder) and force:
        shutil.rmtree(project_folder)

    os.makedirs(project_folder, exist_ok=True)
    source_folder = os.path.join(project_folder, "sourcefile")
    os.makedirs(source_folder, exist_ok=True)

    template_path = os.path.join(current_dir, "lnrj_default_config.yml")
    with open(template_path, "r", encoding="utf-8") as file:
        config_data = yaml_obj.load(file) or {}

    if config_content is not None:
        if isinstance(config_content, dict):
            partial_config = config_content
        else:
            partial_config = yaml_obj.load(io.StringIO(str(config_content)))
            if partial_config is None:
                partial_config = {}

        def merge_configs(original, partial):
            if not isinstance(partial, dict):
                return partial
            result = original.copy() if isinstance(original, dict) else {}
            for key, value in partial.items():
                if key in result and isinstance(result.get(key), dict) and isinstance(value, dict):
                    result[key] = merge_configs(result[key], value)
                else:
                    result[key] = value
            return result

        config_data = merge_configs(config_data, partial_config)

    origin_ext = os.path.splitext(file_path)[1].lower()
    origin_basename = os.path.basename(file_path)
    origin_filename_in_project = f"origin_{origin_basename}" if init_mode == "translated" else origin_basename
    origin_dest_path = os.path.join(source_folder, origin_filename_in_project)
    shutil.copy(file_path, origin_dest_path)

    if init_mode == "translated":
        if not translation_file_path or not os.path.exists(translation_file_path):
            raise FileNotFoundError("已选择从已有译本开始，但译文文件不存在")
        translate_basename = os.path.basename(translation_file_path)
        translate_filename_in_project = f"translate_{translate_basename}"
        translate_dest_path = os.path.join(source_folder, translate_filename_in_project)
        shutil.copy(translation_file_path, translate_dest_path)

    config_data["Translation Project Name"] = project_name
    config_data["book/game/video Name"] = project_name
    config_data["Translator"] = [translator_name]
    config_data["file name"] = origin_filename_in_project
    config_data["original format"] = origin_ext
    config_data["paragraphed"] = True

    if paragraph_aggregation_mode is not None:
        config_data["paragraph aggregation mode"] = bool(paragraph_aggregation_mode)
    if double_blank_line is not None:
        config_data["double blank line"] = bool(double_blank_line)

    reading_cfg = config_data.get("reading_setting")
    if not isinstance(reading_cfg, dict):
        reading_cfg = {}
    reading_cfg["enable"] = bool(enable_reading)
    config_data["reading_setting"] = reading_cfg

    with open(os.path.join(project_folder, "config.yml"), "w", encoding="utf-8") as file:
        yaml_obj.dump(config_data, file)

    create_trans_compare_table(source_folder)
    create_f_record(project_folder)
    create_p_record(project_folder)
    create_table_of_content(source_folder)

    translatefile_path = os.path.join(project_folder, "TranslateFile.json")
    if not os.path.exists(translatefile_path):
        with open(translatefile_path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    if origin_ext == ".txt":
        formatter = LightNovelRobotJpFormat(project_folder)
        formatter.lnrj_create_toc()
        formatter.lnrj_file_update_toc(formatter.original_toc_path)

    if init_mode == "translated" and merge_to_translatefile:
        from merge import Merger

        merger = Merger(project_name)
        merger.merge()

        cfg = Config(os.path.join(project_folder, "config.yml"))
        cfg_data = cfg.read_config()
        rs = cfg_data.get("reading_setting") if isinstance(cfg_data.get("reading_setting"), dict) else {}
        rs["generate_TranslateFile"] = True
        rs["gTF_done"] = True
        cfg_data["reading_setting"] = rs
        cfg.write_config(cfg_data)
    else:
        if origin_ext == ".epub":
            from epub_dispose import EpubDispose

            disposer = EpubDispose(project_folder)
            disposer.epub_format(
                epub_file_path=origin_dest_path,
                destination_file=translatefile_path,
                state="f_trans_unfinished",
            )
        else:
            formatter = LightNovelRobotJpFormat(project_folder)
            formatter.lnrj_format(original_file=origin_dest_path, destination_file=translatefile_path)

    if enable_reading:
        if not (init_mode == "translated" and merge_to_translatefile):
            raise ValueError("当前实现中，reading 需要先 merge 生成 TranslateFile.json（请勾选‘合并到TranslateFile.json’）")
        from reading import Reading

        reader = Reading(project_name)
        reader.reading()

    return project_folder


def register_create_project(app, *, current_dir: str):
    @app.route("/create_project", methods=["POST"])
    def create_project_endpoint():
        data = request.get_json()
        project_name = data.get("project_name")
        translator_name = data.get("translator_name")
        file_path = data.get("file_path")
        force = data.get("force", False)
        init_mode = data.get("init_mode")
        translation_file_path = data.get("translation_file_path")
        paragraph_aggregation_mode = data.get("paragraph_aggregation_mode")
        double_blank_line = data.get("double_blank_line")
        merge_to_translatefile = bool(data.get("merge_to_translatefile", False))
        enable_reading = bool(data.get("enable_reading", False))
        config_content = data.get("config_content")

        if not project_name or not translator_name or not file_path or not os.path.exists(file_path):
            return jsonify({"error": "参数错误或文件不存在"}), 400

        project_folder = os.path.join(current_dir, f"{project_name}_project")
        if os.path.exists(project_folder) and not force:
            return (
                jsonify({"warning": f"已存在{project_name}项目，重新创建将会覆盖该项目已生成的全部内容，是否重新初始化项目？"}),
                409,
            )

        try:
            created_folder = create_project(
                project_name,
                translator_name,
                file_path,
                force,
                current_dir=current_dir,
                init_mode=init_mode,
                translation_file_path=translation_file_path,
                paragraph_aggregation_mode=paragraph_aggregation_mode,
                double_blank_line=double_blank_line,
                merge_to_translatefile=merge_to_translatefile,
                enable_reading=enable_reading,
                config_content=config_content,
            )

            return jsonify({"message": f"项目创建成功，文件保存在 {created_folder}"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
