import os

from .projects import ProjectsAPI
from .config_api import ConfigAPI
from .records_api import FRecordAPI, PRecordAPI
from .translatefile_api import TranslateFileAPI
from .pnt_api import PNTAPI
from .knowledge_awak_api import KnowledgeAwakAPI
from .translating_api import TranslatingAPI
from .create_project_api import register_config_template, register_create_project


def register_all(app, socketio, *, current_dir: str):
    """统一注册所有路由与 socket 事件。

    返回值：用于主入口启动后台任务所需的对象。
    """

    projects_api = ProjectsAPI(app)
    socketio.on("connect")(projects_api.handle_connect)

    ConfigAPI(app, current_dir=current_dir)
    FRecordAPI(app)
    PRecordAPI(app)
    TranslateFileAPI(app)
    PNTAPI(app)
    KnowledgeAwakAPI(app)
    TranslatingAPI(app)

    register_config_template(app, current_dir=current_dir)
    register_create_project(app, current_dir=current_dir)

    return {
        "projects_api": projects_api,
    }
