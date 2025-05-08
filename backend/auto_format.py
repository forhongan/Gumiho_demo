# Coding-----------自动结构化组件---------------
# 调用ai自动生成代码结构化无法用预设行为结构化的文档
import re
import json
import yaml
import ast
import logging
from typing import Dict, List
from textwrap import dedent
from ai import call_ai


class SecurityError(Exception):
    pass

class InvalidCodeError(Exception):
    pass

class NovelParserGenerator:
    def __init__(self, config_path):
        self.config_path=config_path
        self.safety_checker = CodeSafetyChecker()
        self.logger = logging.getLogger(__name__)

    def generate_parser(self, sample_text: str, json_example: str) -> callable:
        """生成解析函数的入口方法"""
        # 1. 提取前4000字作为样本
        text_sample = sample_text[:4000]
        result_example=json_example[:2000]
        # 2. 构造prompt
        prompt = self._build_prompt(text_sample,result_example)
        
        # 3. 调用AI生成代码
        generated_code = self._get_ai_response(prompt)
        
        # 4. 安全检查和代码解析
        return self._compile_safe_function(generated_code)

    def _build_prompt(self, text_sample: str,result_sample) -> str:
        """构造用于生成解析代码的prompt"""
        return dedent(f"""
        你是一个专业的文本处理代码生成器，需要根据输入样本分析文本结构，生成Python解析函数。
        要求：
        函数必须命名为 parse_novel，接收text参数，返回格式化后的小说内容
        你将获取某本小说的最多前2k字文本,你需要根据样本数据分析小说的章节结构
        分析完毕后,你需要针对性设计一个python函数parse_novel,将小说文件处理成结构化的json文件
        parse_novel函数的生成内容,要求的结构化json格式类似于:
        {result_sample}
        你生成的处理函数仅需针对性处理这本小说,无需考虑在其他情况下的通用性
        输入样本示例：
        {text_sample[:1000]}...（截断）
        
        请直接输出最终的Python代码，不需要解释。
        """)

    def _get_ai_response(self, prompt: str) -> str:
        """调用大模型API"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config_data = yaml.safe_load(f)
        if "default_ai_setting" not in self.config_data:
            raise KeyError("配置文件中缺少 'default_ai_setting' 键")
        ai_config = {}
        ai_config["api_key"] = self.config_data["default_ai_setting"]["key"]
        ai_config["base_url"] = self.config_data["default_ai_setting"]["api"]
        ai_config["model_name"] = self.config_data["default_ai_setting"]["model_name"]
        ai_config["max_tokens"] = self.config_data["default_ai_setting"]["max_tokens"]
        response = call_ai(ai_config, [], prompt)
        # 根据返回结果判断不同情况
        if isinstance(response, dict):
            if "choices" in response:
                return response["choices"][0]["message"]["content"]
            elif "content" in response:
                return response["content"]
        raise KeyError(f"返回结果格式异常: {response}")

    def _compile_safe_function(self, code: str) -> callable:
        """将生成的代码编译为安全可执行的函数"""
        # 提取函数部分
        func_code = self._extract_function(code)
        
        # 安全检查
        if not self.safety_checker.is_safe(func_code):
            raise SecurityError("检测到不安全代码")
        
        # 动态编译
        namespace = {}
        exec(func_code, {"re": re}, namespace)
        return namespace["parse_novel"]

    def _extract_function(self, code: str) -> str:
        """从生成的代码中提取函数定义部分"""
        # 去除Markdown代码块标记
        lines = code.splitlines()
        if lines and lines[0].startswith("```"):
            lines = [line for line in lines if not line.startswith("```")]
            code = "\n".join(lines)
        tree = ast.parse(code)
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        
        if not functions or functions[0].name != "parse_novel":
            raise InvalidCodeError("未找到有效的parse_novel函数")
        
        return ast.unparse(functions[0])


class CodeSafetyChecker:
    """代码安全检查器"""
    UNSAFE_NODES = {
        ast.Import, ast.ImportFrom, ast.Call, 
        ast.Attribute, ast.BinOp, ast.Lambda
    }
    
    ALLOWED_IMPORTS = {"re"}

    def is_safe(self, code: str) -> bool:
        try:
            tree = ast.parse(code)
        except:
            return False
        
        for node in ast.walk(tree):
            if isinstance(node, self.UNSAFE_NODES):
                # 检查函数调用
                if isinstance(node, ast.Call):
                    if not self._is_call_allowed(node):
                        return False
                # 检查模块导入
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.ALLOWED_IMPORTS:
                            return False
                # 其他安全检查...
        return True

    def _is_call_allowed(self, node: ast.Call) -> bool:
        # 允许re模块的方法调用
        if isinstance(node.func, ast.Attribute):
            module = node.func.value.id
            if module in self.ALLOWED_IMPORTS:
                return True
        return False


# 使用示例
def auto_format_run(raw_text_path,json_sample):

    # 实例化生成器
    generator = NovelParserGenerator("default_config.yml")
    
    # 原始文本
    raw_text = open(raw_text_path, "r", encoding="utf-8").read()
    
    
    try:
        # 生成解析函数
        parser = generator.generate_parser(raw_text,json_sample)
        
        # 执行解析
        chapters = parser(raw_text)
        
        # 构建最终结构
        result = {
            "chapters": chapters,
            #"meta": {...}  # 可以额外添加元数据
        }
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        # 调用新函数保存结果至JSON文件
        write_result(result, "test_result.json")
    # except SecurityError as e:
    #     print("安全检测失败：", e)
    # except InvalidCodeError as e:
    #     print("代码生成失败：", e)
    except Exception as e:
        print("代码执行失败：", e)

# 新增函数：将result保存为JSON文件
def write_result(result: dict, output_path: str):
    """
    保存result为JSON文件
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    
    raw_text_path = "(NEW)jp.少女所不期望的英雄史诗.txt"

    json_sample ="""
    "chapters": [  
        {
            "id": 1, // 段落编号  
            "original-text": "第一章 启航", // 原文  
            "translation-text": "", // 译文 
            "type": "title_lv1" ,//一级标题
            "state": "f_trans_unfinished" //f_trans_unfinished, f_trans_finished,p_finished,checked,re_trans_needed
        },
        {
            "id": 2, // 段落编号  
            "original-text": "船要扬帆起航了", // 原文  
            "translation-text": "", // 译文 
            "type": "main_text" ,
            "state": "f_trans_unfinished"
        },
        {
            "id": 3, // 段落编号  
            "original-text": "王明在甲板上看着港口里的...", // 原文  
            "translation-text": "", // 译文 
            "type": "main_text" ,
            "state": "f_trans_unfinished"
        }
        ...
        {
            "id": 40, // 段落编号  
            "original-text": "第二章 沉没", // 原文  
            "translation-text": "", // 译文 
            "type": "title_lv1" ,//一级标题
            "state": "f_trans_unfinished" //f_trans_unfinished, f_trans_finished,p_finished,checked,re_trans_needed
        },
    ]
    //每个数据都需要编号为一个id,正文的"type"为main_text",标题的"type"为"type": "title_lvx",如果没有多级标题,则默认均为"title_lv1"
    """
    
    auto_format_run(raw_text_path,json_sample)