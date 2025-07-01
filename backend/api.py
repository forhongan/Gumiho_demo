import os
import sys
import io
import json

from flask import Flask, jsonify, request, Response
from flask_socketio import SocketIO, emit

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from Config import Config
from Record import Record
from TranslateFile import TranslateFile
from PNT import PNT
from format import LightNovelRobotJpFormat
import uuid
from translate import Translating  # 新增导入
import queue, threading, time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 定义全局变量用于暂存Translating实例
translating_instances = {}

class ProjectsAPI:
    def __init__(self, app):
        self.register_routes(app)
    
    def scan_projects(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        projects = []
        for entry in os.listdir(base_dir):
            if entry.endswith("_project"):
                full_path = os.path.join(base_dir, entry)
                if os.path.isdir(full_path):
                    # 删去 "_project" 后缀
                    project_name = entry[:-8]
                    projects.append({
                        "name": project_name,
                        "configPath": os.path.join(full_path, "config.yml"),
                        "f_recordPath": os.path.join(full_path, "f_record.json"),
                        "p_recordPath": os.path.join(full_path, "p_record.json"),
                        "PNTPath": os.path.join(full_path, "sourcefile", "Proper_nouns_table.json"),
                        "translatefilePath": os.path.join(full_path, "TranslateFile.json")
                    })
        return projects
    
    def register_routes(self, app):
        app.add_url_rule("/projects", view_func=self.get_projects, methods=["GET"])
    
    def get_projects(self):
        return jsonify(self.scan_projects())
    
    def handle_connect(self):
        projects = self.scan_projects()
        emit('projects_update', projects)
    
    def background_thread(self):
        import time
        last_projects = None
        while True:
            socketio.sleep(1)
            projects = self.scan_projects()
            if projects != last_projects:
                last_projects = projects
                socketio.emit('projects_update', projects)

class ConfigAPI:
    def __init__(self, app):
        self.register_routes(app)
    
    def register_routes(self, app):
        app.add_url_rule("/config", view_func=self.get_config, methods=["GET"])
        app.add_url_rule("/config", view_func=self.update_config, methods=["POST"])
    
    def get_config(self):
        config_path = request.args.get("configPath")
        if not config_path or not os.path.exists(config_path):
            return jsonify({"error": "非法的configPath"}), 400
        config_instance = Config(config_path)
        data = config_instance.read_config()
        yaml_buffer = io.StringIO()
        config_instance.yaml.dump(data, yaml_buffer)
        return yaml_buffer.getvalue(), 200

    def update_config(self):
        data = request.get_json()
        print("Received data:", data)
        config_path = data.get("configPath")
        content = data.get("content")
        if not config_path or not os.path.exists(config_path) or content is None:
            print("参数错误：", config_path, content)
            return jsonify({"error": "非法的参数"}), 400
        try:
            config_instance = Config(config_path)
            # 首先读取原始配置文件
            original_config = config_instance.read_config()
            
            # 解析前端发送的配置内容
            if isinstance(content, dict):
                partial_config = content
            else:
                # 如果是YAML字符串，解析为字典
                partial_config = config_instance.yaml.load(io.StringIO(content))
            
            print(f"解析到的部分配置: {partial_config}")
            
            # 递归合并配置
            def merge_configs(original, partial):
                if not isinstance(partial, dict):
                    # 如果不是字典类型，直接返回部分配置的值
                    return partial
                
                result = original.copy() if isinstance(original, dict) else {}
                
                for key, value in partial.items():
                    if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                        # 递归合并嵌套字典
                        result[key] = merge_configs(original[key], value)
                    else:
                        # 对于非字典类型或原配置中不存在的键，输出调试信息
                        if key not in original:
                            print(f"警告: 原配置中不存在键 '{key}'，可能导致配置解析失败")
                        
                        # 仍然更新值，但已提供警告
                        result[key] = value
                
                return result
            
            # 合并配置
            updated_config = merge_configs(original_config, partial_config)
            
            # 写入更新后的完整配置 (会自动处理API密钥到环境变量的保存)
            config_instance.write_config(updated_config)
            
            print(f"配置已成功更新，路径: {config_path}")
            return jsonify({"message": "配置已更新"}), 200
        except Exception as e:
            import traceback
            print("保存配置时发生异常：", str(e))
            print(traceback.format_exc())
            return jsonify({"error": str(e)}), 500

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
        
        """
        根据前端选取的章节的标题,获得该章节的翻译记录
        """
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
        """
        添加新的翻译记录,并放弃旧的翻译记录
        """
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

class TranslateFileAPI:
    def __init__(self, app):
        self.register_routes(app)
    
    def register_routes(self, app):
        # 修改 GET 接口：根据请求参数决定是否调用 get_title_chapters_with_status_list
        app.add_url_rule("/translatefile", view_func=self.get_translatefile, methods=["GET"])
        app.add_url_rule("/translatefile", view_func=self.update_translatefile, methods=["POST"])
        
        app.add_url_rule("/title_list", view_func=self.get_title_list, methods=["GET"])
        app.add_url_rule("/translatefile/paragraph", view_func=self.get_paragraph_by_title, methods=["GET"])
        # 新增句子更新路由
        app.add_url_rule("/translatefile/paragraph", view_func=self.update_sentence, methods=["POST"])
        
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
        """
        获取标题列表,每项包含"title": now_chapter, "status": status
        """
        tf_path = request.args.get("translatefilePath")
        tf_instance = TranslateFile(tf_path)
        self.chapters = tf_instance.get_title_chapters_with_status_list("f_trans_finished")
        return jsonify({"chapters": self.chapters}), 200
    
    def get_paragraph_by_title(self):
        """
        获取指定标题的段落内容
        """
        title = request.args.get("title")
        tf_path = request.args.get("translatefilePath")
        if not title or not tf_path or not os.path.exists(tf_path):
            return jsonify({"error": "非法的参数"}), 400
        try:
            tf_instance = TranslateFile(tf_path)
            paragraphs = tf_instance.get_paragraph_by_title(title)
            print("Debug: paragraphs:", paragraphs)
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
                    chapter["state"] = "f_trans_finished"  # 更新状态
                    updated = True
                    break
            
            if not updated:
                return jsonify({"error": "段落ID不存在"}), 404
                
            tf_instance.write_translatefile(tf_instance.data)
            return jsonify({"message": "段落更新成功"}), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

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
        # 获取选择的段落中出现过的所有角色
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
        # 通过输入的片段,检索出所有包含该片段的角色,为空时返回所有角色
        str = request.args.get("str")
        pnt_path = request.args.get("PNTPath")
        if not pnt_path or not os.path.exists(pnt_path):
            return jsonify({"error": "非法的参数"}), 400
        try:
            pnt_instance = PNT(pnt_path)
            characters = pnt_instance.get_characters_by_str(str)
            return jsonify({"characters": characters}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# 新增全局字典存储SSE通道
sse_channels = {}

class TranslatingAPI:
    def __init__(self, app):
        self.register_routes(app)
    
    def register_routes(self, app):
        app.add_url_rule("/translating/start", view_func=self.translating_start, methods=["POST"])
        app.add_url_rule("/translating/submit_check", view_func=self.translating_submit_check, methods=["POST"])
        # 新增SSE路由
        app.add_url_rule("/translating/stream/<trans_id>", view_func=self.sse_stream, methods=["GET"])
    
    def sse_stream(self, trans_id):
        """SSE事件流处理"""
        def generate():
            channel = sse_channels.get(trans_id)
            if not channel:
                yield "event: error\ndata: {\"message\": \"无效的翻译ID\"}\n\n"
                return
            while True:
                msg = channel.get()
                # print(f"[DEBUG] 将发送SSE消息: {msg}")  # 调试输出
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
        # 创建消息通道
        sse_channels[trans_id] = queue.Queue()
        # 创建Translating实例并传递SSE回调
        translator = Translating(
            project_name, 
            "translating",
            sse_callback=lambda msg: sse_channels[trans_id].put(msg)
        )
        # 启动翻译线程
        threading.Thread(
            target=self.run_translation, 
            args=(translator, trans_id)
        ).start()
        return jsonify({
            "trans_id": trans_id,
            "stream_url": f"/translating/stream/{trans_id}"
        })
    
    def run_translation(self, translator, trans_id):
        """在后台线程中运行翻译"""
        try:
            print("[DEBUG] 开始运行翻译任务")  # 调试输出
            translator.translating_to_result()
            print("[DEBUG] 翻译进度完成，准备发送SSE消息")  # 调试输出
            if translator.Config.data[translator.now_setting].get("human_involvement", False):
                check_data = translator.get_human_check_list()
                translating_instances[trans_id] = translator
                sse_channels[trans_id].put({
                    "type": "result",
                    "need_human_check": True,
                    "check_list": check_data
                })
            else:
                translator.save_f_record()
                translator.record_to_file()
                sse_channels[trans_id].put({
                    "type": "result",
                    "need_human_check": False,
                    "message": "翻译完成并保存"
                })
        except Exception as e:
            sse_channels[trans_id].put({
                "type": "error",
                "message": str(e)
            })
        finally:
            sse_channels[trans_id].put("DONE")
            time.sleep(1)  # 确保消息发送完毕
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

def create_project(project_name, translator_name, file_path, force=False):
    import os, shutil
    from ruamel.yaml import YAML
    yaml_obj = YAML()
    project_folder = f"{project_name}_project"
    if os.path.exists(project_folder) and not force:
        # 提示项目已存在
        return None  # 标识已存在
    if os.path.exists(project_folder) and force:
        shutil.rmtree(project_folder)  # 删除原项目文件夹
    os.makedirs(project_folder, exist_ok=True)
    with open('lnrj_default_config.yml', 'r', encoding='utf-8') as file:
        config_data = yaml_obj.load(file)
    config_data["Translation Project Name"] = project_name
    config_data["book/game/video Name"] = project_name
    config_data["Translater"] = [translator_name]
    config_data["file name"] = os.path.basename(file_path)
    config_data["Original format"] = os.path.splitext(file_path)[1].lower()
    config_data["paragraphed"] = True
    with open(os.path.join(project_folder, 'config.yml'), 'w', encoding='utf-8') as file:
        yaml_obj.dump(config_data, file)
    source_folder = os.path.join(project_folder, 'sourcefile')
    os.makedirs(source_folder, exist_ok=True)
    shutil.copy(file_path, source_folder)
    return project_folder

@app.route("/create_project", methods=["POST"])
def create_project_endpoint():
    data = request.get_json()
    project_name = data.get("project_name")
    translator_name = data.get("translator_name")
    file_path = data.get("file_path")
    force = data.get("force", False)
    if not project_name or not translator_name or not file_path or not os.path.exists(file_path):
        return jsonify({"error": "参数错误或文件不存在"}), 400
    # 检查是否存在项目文件夹
    project_folder = f"{project_name}_project"
    if os.path.exists(project_folder) and not force:
        return jsonify({"warning": f"已存在{project_name}项目，重新创建将会覆盖该项目已生成的全部内容，是否重新初始化项目？"}), 409
    try:
        project_folder = create_project(project_name, translator_name, file_path, force)
        # 调用初始化（保持原有逻辑）
        work1 = LightNovelRobotJpFormat(f"{project_name}_project")
        work1.lurj_project_Initialization()
        return jsonify({"message": f"项目创建成功，文件保存在 {project_folder}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/export_text", methods=["POST"])
def export_text():
    data = request.get_json()
    print("export_text received data:", data)
    tf_path = data.get("translatefilePath")
    if not tf_path:
        print("Error: 缺少translatefilePath参数")
        return jsonify({"error": "缺少translatefilePath参数"}), 400
    export_work = TranslateFile(tf_path)
    start_title = data.get("start_title")
    end_title = data.get("end_title")
    start_id = export_work.get_id_from_chapter_name(start_title)
    end_id = export_work.get_chapter_end_from_id(export_work.get_id_from_chapter_name(end_title))
    print("Debug: start_title:", start_title, "start_id:", start_id)
    print("Debug: end_title:", end_title, "end_id:", end_id)
    output_path = export_work.export_translatefile(start_id, end_id)
    print("Exported file at:", output_path)
    return jsonify({
        "start_title": start_title,
        "end_title": end_title,
        "target_state": data.get("target_state"),
        "output_path": output_path
    }), 200

# 注销原有的/check_list和/submit_check接口

projects_api = ProjectsAPI(app)
config_api = ConfigAPI(app)
frecord_api = FRecordAPI(app)
precord_api = PRecordAPI(app)
translatefile_api = TranslateFileAPI(app)
pnt_api = PNTAPI(app)
translating_api = TranslatingAPI(app)

socketio.on('connect')(projects_api.handle_connect)

if __name__ == '__main__':
    socketio.start_background_task(target=projects_api.background_thread)
    socketio.run(app, debug=False, host="0.0.0.0")

