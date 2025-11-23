# 添加调试代码
print("Config.py 被执行")
import os
import re
from dotenv import load_dotenv, set_key
from ruamel.yaml import YAML

class Config:
    """
    config.yaml的操作类
    self.config_path: Proper_nouns_table.yml的路径
    self.file_path: 翻译工程文件xxx.yml的路径
    """
    def __init__(self, config_path):  # 修改：增加 config_path 参数
        print(f"Config 类初始化，路径: {config_path}")
        self.config_path = config_path
        self.yaml = YAML()

        self.project_dir = os.path.dirname(config_path)
        self.env_path = os.path.join(self.project_dir, '.env')
        
        # 确保.env文件存在
        if not os.path.exists(self.env_path):
            open(self.env_path, 'a').close()
            print(f"创建了新的.env文件: {self.env_path}")
            
        # 加载环境变量
        load_dotenv(self.env_path)
        
        # 读取配置
        self.data = self.read_config()
        
    def read_config(self):
        """
        读取Config.yml文件
        """
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = self.yaml.load(f)
        return data
    
    def save_api_keys_to_env(self, data):
        """
        将API密钥保存到.env文件
        """
        print(f"正在将API密钥保存到.env文件: {self.env_path}")
        
        # 默认AI设置密钥
        if 'default_ai_setting' in data and 'key' in data['default_ai_setting'] and data['default_ai_setting']['key']:
            key_value = data['default_ai_setting']['key']
            # 检查是否已经是环境变量引用
            if not key_value.startswith('${') and not key_value.endswith('}'):
                set_key(self.env_path, 'DEFAULT_AI_KEY', key_value)
                # 替换为环境变量引用
                data['default_ai_setting']['key'] = '${DEFAULT_AI_KEY}'
                print("已保存默认AI密钥到环境变量")
        
        # 初译设置密钥
        if 'first_translation_setting' in data and 'ai_config' in data['first_translation_setting'] and 'key' in data['first_translation_setting']['ai_config']:
            key_value = data['first_translation_setting']['ai_config']['key']
            if not key_value.startswith('${') and not key_value.endswith('}'):
                set_key(self.env_path, 'FIRST_TRANS_AI_KEY', key_value)
                # 替换为环境变量引用
                data['first_translation_setting']['ai_config']['key'] = '${FIRST_TRANS_AI_KEY}'
                print("已保存初译AI密钥到环境变量")
        
        # 校对设置密钥
        if 'proofreading_setting' in data and 'ai_config' in data['proofreading_setting'] and 'key' in data['proofreading_setting']['ai_config']:
            key_value = data['proofreading_setting']['ai_config']['key']
            if not key_value.startswith('${') and not key_value.endswith('}'):
                set_key(self.env_path, 'PROOF_AI_KEY', key_value)
                # 替换为环境变量引用
                data['proofreading_setting']['ai_config']['key'] = '${PROOF_AI_KEY}'
                print("已保存校对AI密钥到环境变量")
                
        return data
    
    def write_config(self, data):
        """
        写入Config.yml文件
        """
        print(f"正在将配置写入文件: {self.config_path}")
        
        # 提取并保存API密钥到环境变量
        data = self.save_api_keys_to_env(data)
        
        with open(self.config_path, "w", encoding='utf-8') as f:
            self.yaml.dump(data, f)
        print(f"配置已成功写入: {self.config_path}")
    
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
    
    def get_ai_config(self,status=None):
        """
        获取AI相关配置
        根据翻译状态决定使用的AI设置，并从环境变量获取密钥
        status: translating(初译)或proofreading(校对)
        """
        # 尝试从.env文件加载环境变量
        load_dotenv(self.env_path, override=True, verbose=True)
        
        # 验证环境变量是否成功加载
        default_key = os.environ.get('DEFAULT_AI_KEY')
        print(f"DEFAULT_AI_KEY 环境变量{'已加载' if default_key else '未加载'}")
        if default_key:
            print(f"密钥前5个字符: {default_key[:5]}...")
        
        # 读取配置
        config = self.read_config()
        default_ai_config = config.get('default_ai_setting', {}).copy()  # 使用copy避免修改原始数据
        
        # 根据状态选择配置
        if status == 'translating':
            translation_setting = config.get('first_translation_setting', {})
            use_independent = translation_setting.get('enable_independence_ai_config', False)
            
            if use_independent and 'ai_config' in translation_setting:
                ai_config = translation_setting['ai_config'].copy()  # 使用copy避免修改原始数据
                # 从环境变量获取密钥，如果环境变量中没有，则使用配置文件中的值
                env_key = os.environ.get('FIRST_TRANS_AI_KEY')
                if not env_key:
                    env_key = os.environ.get('DEFAULT_AI_KEY')
                    print(f"使用DEFAULT_AI_KEY作为初译密钥: {env_key[:5] if env_key else '未设置'}...")
                
                # 如果环境变量都为空，使用配置文件中的值
                ai_config['key'] = env_key if env_key else ai_config.get('key', default_ai_config.get('key', ''))
                print(f"初译最终使用的API密钥: {ai_config['key'][:5] if ai_config['key'] else '未设置'}...")
                return ai_config
        
        elif status == 'proofreading':
            proofreading_setting = config.get('proofreading_setting', {})
            use_independent = proofreading_setting.get('enable_independence_ai_config', False)
            
            if use_independent and 'ai_config' in proofreading_setting:
                ai_config = proofreading_setting['ai_config'].copy()  # 使用copy避免修改原始数据
                # 从环境变量获取密钥，如果环境变量中没有，则使用配置文件中的值
                env_key = os.environ.get('PROOF_AI_KEY')
                if not env_key:
                    env_key = os.environ.get('DEFAULT_AI_KEY')
                    print(f"使用DEFAULT_AI_KEY作为校对密钥: {env_key[:5] if env_key else '未设置'}...")
                
                ai_config['key'] = env_key if env_key else ai_config.get('key', default_ai_config.get('key', ''))
                print(f"校对最终使用的API密钥: {ai_config['key'][:5] if ai_config['key'] else '未设置'}...")
                return ai_config
        
        # 使用默认配置
        env_key = os.environ.get('DEFAULT_AI_KEY')
        print(f"使用默认API密钥: {env_key[:5] if env_key else '未设置'}...")
        default_ai_config['key'] = env_key if env_key else default_ai_config.get('key', '')
        print(f"默认配置最终使用的API密钥: {default_ai_config['key'][:5] if default_ai_config['key'] else '未设置'}...")
        return default_ai_config
    
    def make_translation_info_tags(self,status='translating'):
        """
        根据配置生成翻译信息标签
        """
        config = self.read_config()
        settings = config.get('first_translation_setting', {})
        
        tags = []
        
        tags.append("--Translated with Gumiho-v0.9.2--九尾狐本地化Ai辅助翻译系统--\n")
        tags.append("   With Ai model:{}\n".format(self.get_ai_config(status).get('model_name', 'unknown')))
        if settings.get('human_involvement', False):
            tags.append("   Human translator/checker:{}\n".format(config.get('Translator', 'unknown')))
        
        return ''.join(tags)
        
        # # 专有名词翻译
        # noun_settings = settings.get('Proper noun translation', {})
        # if noun_settings.get('enable', False):
        #     tags.append("专有名词翻译:启用")
        # else:
        #     tags.append("专有名词翻译:禁用")
        
        # # 自动生成文本总结
        # summary_settings = settings.get('Automatically generated text summary', {})
        # if summary_settings.get('enable', False):
        #     tags.append("文本总结:启用")
        # else:
        #     tags.append("文本总结:禁用")
        
        # return ', '.join(tags)
            
if __name__ == '__main__':
    config_path = '少女所不期望的英雄史诗-Gumiho-v0.92-r1_project/config.yml'
    config = Config(config_path)
    #test
    print(config.make_translation_info_tags())
