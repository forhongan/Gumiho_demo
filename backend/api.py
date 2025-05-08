import os
import io
import json
from flask import Flask, jsonify, request, Response
from flask_socketio import SocketIO, emit
from Config import Config
from Record import Record
from TranslateFile import TranslateFile
from PNT import PNT
from format import LightNovelRobotJpFormat
import uuid
from translate import Translating  # 新增导入

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
            if isinstance(content, dict):
                new_data = content
            else:
                new_data = config_instance.yaml.load(io.StringIO(content))
            config_instance.write_config(new_data)
            print("配置已成功更新：", config_path)
            return jsonify({"message": "配置已更新"}), 200
        except Exception as e:
            print("保存配置时发生异常：", str(e))
            return jsonify({"error": str(e)}), 500

class FRecordAPI:
    def __init__(self, app):
        self.register_routes(app)
    
    def register_routes(self, app):
        app.add_url_rule("/f_record", view_func=self.get_f_record, methods=["GET"])
        app.add_url_rule("/f_record", view_func=self.update_f_record, methods=["POST"])
        
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

class PNTAPI:
    def __init__(self, app):
        self.register_routes(app)
    
    def register_routes(self, app):
        app.add_url_rule("/pnt", view_func=self.get_pnt, methods=["GET"])
        app.add_url_rule("/pnt", view_func=self.update_pnt, methods=["POST"])
        
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

class TranslatingAPI:
    def __init__(self, app):
        self.register_routes(app)
    
    def register_routes(self, app):
        app.add_url_rule("/translating/start", view_func=self.translating_start, methods=["POST"])
        app.add_url_rule("/translating/submit_check", view_func=self.translating_submit_check, methods=["POST"])
    
    def translating_start(self):
        data = request.get_json()
        project_name = data.get("project_name")
        if not project_name:
            return jsonify({"error": "缺少project_name参数"}), 400
        # 创建Translating实例，状态固定为"translating"
        translator = Translating(project_name, "translating")
        # 调用部分流程，准备校对数据
        translator.translating_to_result() # 执行一次翻译并将翻译内容保存至result
        if translator.Config.data[translator.now_setting].get("human_involvement", False):
            # 获取人工检查数据
            check_data = translator.get_human_check_list()
            # # 临时设置调试用的 check_data 值
            # check_data = {
            #     "new_record": {
            #         "range": 155,
            #         "title": "# 死亡フラグ",
            #         "type": "translating",
            #         "status": "written",
            #         "translate": {
            #             "140": "是的，猫咪确实在那里。",
            #             "141": "那只猫确确实实就在那里。",
            #             "142": "猫咪出现了。就在我面前。",
            #             "143": "近得离谱，几乎要贴到我的脸上。",
            #             "144": "「……啊？」",
            #             "145": "先理清一下状况。",
            #             "146": "原本在车道中央的猫。",
            #             "147": "卡车原本也行驶在同一条车道的正中央。",
            #             "148": "而现在这只猫却出现在我眼前——这意味着？",
            #             "149": "「呜哇......啊......？」",
            #             "150": "在理解事态之前...意识已被黑暗吞噬。",
            #             "151": "唯一值得安慰的是，并不痛苦。",
            #             "152": "虽然这根本算不上什么安慰。",
            #             "153": "在最后的意识碎片中如此想着。",
            #             "154": "「呃啊！？」",
            #             "155": "一切都结束了。"
            #         },
            #         "New Character": [],
            #         "Character changing": [],
            #         "New proper noun": [],
            #         "Summary": "通过高速切换的时空错位描写，展现主角在死亡瞬间的认知失调与黑色幽默，最终以意识消散完成死亡flag的闭环，为异世界转生铺垫冲击性开场。",
            #         "timestamp": "2025-04-25T22:36:33.219933"
            #     },
            #     "original_text": [
            #         "そう、猫はいた。",
            #         "猫は確かにそこにいた。",
            #         "ねこはいました。私の前に。",
            #         "私の目の前も目の前、顔のすぐ近くに。",
            #         "「……え？」",
            #         "ちょっと整理しよう。",
            #         "猫は車道の真ん中にいた。",
            #         "トラックも、同じ道の真ん中を走っていた。",
            #         "そして、その猫が今、私の目の前にいる……ということは？",
            #         "「うわ……あ……？」",
            #         "──何があったかを理解する間も無く……意識が闇に飲み込まれる。",
            #         "苦しくなかったのは、せめてもの救いか。",
            #         "いや救いようはないけどな。",
            #         "そんなことを思いつつ。",
            #         "「ぅぐぁっ？」",
            #         "全てが、終わった。"
            #     ]
            # }
            trans_id = uuid.uuid4().hex
            translating_instances[trans_id] = translator
            print("DEBUG: checklist is:")            # 打印调试信息
            print(json.dumps(check_data, indent=4, ensure_ascii=False))
            return jsonify({"need_human_check": True, "check_list": check_data, "trans_id": trans_id})
        else:
            translator.save_f_record()
            translator.record_to_file()
            return jsonify({"need_human_check": False, "message": "翻译完成并保存"})

        
    def translating_submit_check(self):
        data = request.get_json()
        trans_id = data.get("trans_id")
        checked_record = data.get("new_record")
        if not trans_id or trans_id not in translating_instances:
            return jsonify({"error": "无效的trans_id"}), 400
        translator = translating_instances.pop(trans_id)
        # 更新翻译结果中的"translate"部分为人工修改过的数据
        # if "translate" in translator.response:
        #     translator.response["translate"] = checked_record
        # else:
        #     translator.response.update({"translate": checked_record})
        # 更新本次翻译的record
        translator.new_record = checked_record
        translator.save_f_record()
        translator.record_to_file()
        return jsonify({"message": "校对结果已提交并保存"}), 200

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
    socketio.run(app, debug=True, host="0.0.0.0")
