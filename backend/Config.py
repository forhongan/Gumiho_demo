from ruamel.yaml import YAML
class Config:
    """
    config.yaml的操作类
    self.config_path: Proper_nouns_table.yml的路径
    self.file_path: 翻译工程文件xxx.yml的路径
    """
    def __init__(self, config_path):  # 修改：增加 config_path 参数
        self.config_path = config_path
        self.yaml = YAML()
        self.data = self.read_config()
        
    def read_config(self):
        """
        读取Config.yml文件
        """
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = self.yaml.load(f)
        return data
    
    def write_config(self,data):
        """
        写入Config.yml文件
        """
        with open("config_updated.yml", "w") as f:
            self.yaml.dump(data, f)
    
    def AutoOutputStructureText(self):
        """
        根据配置文件设置自动生成输出结构描述文本
        """
        config = self.read_config()
        settings = config.get('first_translation_setting', {})
        noun_settings = settings.get('Proper noun translation', {})
        auto_dict_settings = settings.get('Automatic Translation Dictionary', {})
        summary_settings = settings.get('Automatically generated text summary', {})
        
        structure = []
        
        # 基本翻译结构
        structure.append("Output structure: |\n    # 翻译结果")
        structure.append("    id：[ID数字]")
        structure.append("    译文：[翻译内容]")
        structure.append("    ...")
        structure.append("    （按顺序处理每个ID对应的内容）")
        
        # 总结部分
        if summary_settings.get('enable', False) and \
        (summary_settings.get('create', False) or summary_settings.get('using', False)):
            structure.append("\n    # 本次总结")
            structure.append("    本次总结：[用1-2句话概括本组内容的核心信息]")
        
        # 专有名词处理
        if noun_settings:
            structure.append("\n    # 新增人物")
            structure.append("    1.")
            structure.append("    name:[原文名称]")
            if auto_dict_settings.get('enable', False):
                structure.append("    translation:[确定的译名]")
                if auto_dict_settings.get('enable_describe', False):
                    structure.append("    describe:[根据文中简要描述该人物，包含性别、特征等]")
            structure.append("    2.")
            structure.append("    ...")
            
            # 原有人物重置
            if auto_dict_settings.get('enable_describe_using', False):
                structure.append("\n    # 对原有人物的重置")
                structure.append("    1.")
                structure.append("    name:[原文名称]")
                structure.append("    describe:[重置后的完整描述，包含新增描述内容]")
                structure.append("    2.")
                structure.append("    ...")
            
            # 其他专有名词
            structure.append("\n    # 其他专有名词（可选）")
            structure.append("    1.")
            structure.append("    name:[原文名称]")
            if auto_dict_settings.get('enable', False):
                structure.append("    translation:[确定的译名]")
                if auto_dict_settings.get('enable_describe', False):
                    structure.append("    describe:[根据文中简要描述该名词，包含性质、特征等]")
            structure.append("    2.")
            structure.append("    ...")
        
        # 人工检查提示
        if settings.get('human_involvement', False) and \
        settings.get('human_check_setting', {}).get('summary_check', False):
            structure.append("\n    # 注意：本次总结需要人工检查确认")
        
        return '\n'.join(structure)

            
if __name__ == '__main__':
    config_path = '少女所不希望的英雄史诗-副本_project/config.yml'
    config = Config(config_path)
