import os
import yaml
import json

class Project:
    def __init__(self, project_name):
        self.project_name = project_name
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.project_path = os.path.join(base_path, f"{self.project_name}_project")
        self.config_path = os.path.join(self.project_path, "config.yml")
        self.sourcefile_path = os.path.join(self.project_path, "sourcefile")
        self.f_record_path = os.path.join(self.project_path, "f_record.json")
        self.p_record_path = os.path.join(self.project_path, "p_record.json")
        self.translate_file_path = os.path.join(self.project_path, "TranslateFile.json")
        self.PNT_path = os.path.join(self.project_path, "sourcefile", "Proper_nouns_table.json")
        self.check_project_integrity()
    
    def get_f_record_path(self):
        return self.f_record_path
    
    def get_p_record_path(self):
        return self.p_record_path
    
    def get_config_path(self):
        return self.config_path
    
    def get_sourcefile_path(self):
        return self.sourcefile_path
    
    def get_translate_file_path(self):
        return self.translate_file_path

    def get_pnt_path(self):
        return self.PNT_path
    
    def check_project_integrity(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"找不到配置文件 {self.config_path}")
        if not os.path.exists(self.sourcefile_path):
            raise FileNotFoundError(f"找不到源文件夹 {self.sourcefile_path}")
        if not os.path.exists(self.f_record_path):
            raise FileNotFoundError(f"找不到f_record文件 {self.f_record_path}")
        if not os.path.exists(self.p_record_path):
            raise FileNotFoundError(f"找不到p_record文件 {self.p_record_path}")
        if not os.path.exists(self.PNT_path):
            raise FileNotFoundError(f"找不到专有名词表文件 {self.PNT_path}")
        if not os.path.exists(self.translate_file_path):
            raise FileNotFoundError(f"找不到翻译文件 {self.translate_file_path}")
    
    def load_config_data(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def load_f_record_data(self):
        with open(self.f_record_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def load_p_record_data(self):
        with open(self.p_record_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def load_translate_file_data(self):
        with open(self.translate_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def load_proper_nouns_table_data(self):
        with open(self.PNT_path, "r", encoding="utf-8") as f:
            return json.load(f)



