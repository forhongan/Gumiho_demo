import os

from flask import jsonify
from flask_socketio import emit


class ProjectsAPI:
    def __init__(self, app):
        self.register_routes(app)

    def scan_projects(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # base_dir 当前在 api_routes；项目目录实际在 backend 下
        base_dir = os.path.dirname(base_dir)

        projects = []
        for entry in os.listdir(base_dir):
            if entry.endswith("_project"):
                full_path = os.path.join(base_dir, entry)
                if os.path.isdir(full_path):
                    project_name = entry[:-8]
                    projects.append(
                        {
                            "name": project_name,
                            "configPath": os.path.join(full_path, "config.yml"),
                            "f_recordPath": os.path.join(full_path, "f_record.json"),
                            "p_recordPath": os.path.join(full_path, "p_record.json"),
                            "PNTPath": os.path.join(full_path, "sourcefile", "Proper_nouns_table.json"),
                            "translatefilePath": os.path.join(full_path, "TranslateFile.json"),
                        }
                    )
        return projects

    def register_routes(self, app):
        app.add_url_rule("/projects", view_func=self.get_projects, methods=["GET"])

    def get_projects(self):
        return jsonify(self.scan_projects())

    def handle_connect(self):
        projects = self.scan_projects()
        emit("projects_update", projects)

    def background_thread(self, socketio):
        last_projects = None
        while True:
            socketio.sleep(1)
            projects = self.scan_projects()
            if projects != last_projects:
                last_projects = projects
                socketio.emit("projects_update", projects)
