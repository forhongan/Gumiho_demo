"""Flask 路由模块拆分包。

注意：这里刻意命名为 api_routes，而不是 api，避免与顶层 api.py 同名造成 import 混淆。
"""

from .register_all import register_all  # noqa: F401
