import io
import os

from flask import jsonify, request

from Config import Config


class ConfigAPI:
    def __init__(self, app, *, current_dir: str):
        self.current_dir = current_dir
        self.register_routes(app)

    def register_routes(self, app):
        app.add_url_rule("/config", view_func=self.get_config, methods=["GET"])
        app.add_url_rule("/config", view_func=self.update_config, methods=["POST"])

    def get_config(self):
        is_global = request.args.get("isGlobalConfig") == "true"
        config_path = os.path.join(self.current_dir, "config.yml") if is_global else request.args.get("configPath")

        if not config_path or not os.path.exists(config_path):
            return jsonify({"error": "非法的配置路径"}), 400

        config_instance = Config(config_path)
        data = config_instance.read_config()
        yaml_buffer = io.StringIO()
        config_instance.yaml.dump(data, yaml_buffer)
        return yaml_buffer.getvalue(), 200

    def update_config(self):
        data = request.get_json()
        print("Received data:", data)

        is_global = data.get("isGlobalConfig") is True
        config_path = os.path.join(self.current_dir, "config.yml") if is_global else data.get("configPath")

        content = data.get("content")
        if not config_path or not os.path.exists(config_path) or content is None:
            print("参数错误：", config_path, content)
            return jsonify({"error": "非法的参数"}), 400

        try:
            config_instance = Config(config_path)
            original_config = config_instance.read_config()

            if isinstance(content, dict):
                partial_config = content
            else:
                partial_config = config_instance.yaml.load(io.StringIO(content))

            print(f"解析到的部分配置: {partial_config}")

            def merge_configs(original, partial):
                if not isinstance(partial, dict):
                    return partial

                result = original.copy() if isinstance(original, dict) else {}

                for key, value in partial.items():
                    if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                        result[key] = merge_configs(original[key], value)
                    else:
                        if key not in original:
                            print(f"警告: 原配置中不存在键 '{key}'，可能导致配置解析失败")

                        result[key] = value

                return result

            updated_config = merge_configs(original_config, partial_config)
            config_instance.write_config(updated_config)

            config_type = "全局" if is_global else "项目"
            print(f"{config_type}配置已成功更新，路径: {config_path}")
            return jsonify({"message": f"{config_type}配置已更新"}), 200

        except Exception as e:
            import traceback

            print("保存配置时发生异常：", str(e))
            print(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
