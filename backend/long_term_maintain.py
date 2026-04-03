import os
import yaml
import json
from ai import Call_Ai
from Config import Config
from TranslateFile import TranslateFile
from Project import Project  # 新增导入父类
from Record import Record
from PNT import PNT

class LongTermSummary(Project):
    """
    用于生成和维护record.json中,以章节到全书为等级的长期总结
    可以通过translating类的部分参数构造,或在外部被直接调用
    self.status: 当前翻译状态,只能是"first translating"或"proofreading"
    self.config_path: 项目配置文件路径
    self.record_path: record.json的路径
    self.file_path: 翻译工程文件xxx.json的路径
    self.book_name: 书名
    self.summary[]: 列表,用于储存用于生成高一级总结的低级总结
    self.higher_summary: 用于储存生成的高一级总结
    self.title{
        "title": 用于储存标题
        "id": 标题对应的id,标明其在翻译工程文件中的位置
        "level": 该标题等级,同时也是表示生成的总结的等级,字符串"title_lv{number}",表示这是{number}级标题,也是生成的后续内容的总结
    }
    record.json的格式如下:
    {
        "Long_term_summary_table":[
            {
            "title": "頭のおかしな少女",
            "type": "title_lv1",
            "start_id":"1",
            "end_id":"",
            "summary": ""
            },
            ...
        ],
        "record": [
            {
            "range": "30",
            "status": "written",
            "translate": {
                "1": "脑袋有点问题的少女",
                "2":...
            },
            ...
            "Summary": "退役士兵加罗持续骚扰具有神秘气质的银发少女克莉榭，在村民默许下逐渐升级的侵犯行为首次遭遇少女明确拒绝，暗示即将发生冲突。",
            },
            ...
        ]
    }
    """
    def __init__(self,project_name, title: dict, status):  # 修改：删除 file_path 参数
        super().__init__(project_name)  # 调用父类构造函数，初始化项目相关成员变量
        self.record_path = self.f_record_path if status == "translating" else self.p_record_path
        self.TranslateFile=TranslateFile(self.translate_file_path)
        self.Record=Record(self.record_path)
        self.status = status
        self.record_path = self.f_record_path if status == "translating" else self.p_record_path
        self.book_name = self.TranslateFile.get_book_name()
        self.summary = []
        self.higher_summary = ""
        self.title = {}
        self.title["title"] = title["title"]
        self.title["id"] = title["id"]
        self.title["level"] = title["level"]
    
    def lts_generate(self):
        """
        生成长期总结
        """
        end_id = self.TranslateFile.get_chapter_end_from_id(self.title["id"])
        self.lts_get_summary_list(self.title["id"],end_id)
        self.lts_generate_summary()
        self.lts_write_record()
        # return self.higher_summary
    
    def lts_get_summary_list(self, start_id, end_id):
        """
        读取record.json中内容,生成self.summary列表
        仅获取 "status" 为 "written" 的记录:
        - "translate"中最小id为开始位置, "range"为结束位置
        - 若记录的开始与结束均在start_id和end_id范围内,则格式化后添加到summary列表中
        """
        self.summary = []  # 清空之前的summary列表
        self.summary = self.Record.get_summary_by_paragraph_title(self.title["title"])

    def lts_generate_summary(self):
        """
        生成高一级总结
        """
        sys_prompt = f"你是一个强大的ai助手,需要根据给出的内容,生成某个段落或整个作品的总结,并严格按照格式要求输出"
        newline = "\n"
        user_prompt = f"""
你需要生成<{self.title['title']}>这一章的内容总结,该段落可能由部分子段落组成,并且这些子段落都已经完成内容总结,我将给出组成这段的子段落的总结,由你来生成整章内容的总结
生成的总结应聚焦于故事情节,不需要包含过多的作品分析.
{newline.join(self.summary)}:
仅返回生成的总结,不要包含任何其他内容
"""
        response=self._lts_call_ai(sys_prompt,user_prompt)
        self.higher_summary = response["content"]
        #test
        with open(os.path.join(os.path.dirname(__file__), "output.txt"), "w", encoding="utf-8") as f:
            f.write(json.dumps(response, ensure_ascii=False, indent=4))
        
    def lts_write_record(self):
        data= self.load_f_record_data() if self.status == "translating" else self.load_p_record_data()
        # 如果"Long_term_summary_table"不存在或不是一个列表，则创建该键并初始化为列表
        if "Long_term_summary_table" not in data or not isinstance(data["Long_term_summary_table"], list):
            data["Long_term_summary_table"] = []
        updated = False
        for entry in data["Long_term_summary_table"]:
            if entry.get("title") == self.title["title"]:
                entry["summary"] = self.higher_summary
                updated = True
                break
        if not updated:
            data["Long_term_summary_table"].append({
                "title": self.title["title"],
                "type": self.title["level"],
                "start_id": self.title["id"],
                "end_id": self.TranslateFile.get_chapter_end_from_id(self.title["id"]),
                "summary": self.higher_summary
            })
        with open(self.record_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
    def _lts_call_ai(self,sys_prompt,user_prompt):
        """
        调用AI生成总结
        """
        # with open(self.config_path, "r", encoding="utf-8") as f:
        #     config_data = yaml.safe_load(f)
        # ai_config=config_data["default_ai_setting"]
        # ai_config["base_url"]=ai_config["api"]
        # ai_config["api_key"]=ai_config["key"]
        self.Config=Config(self.config_path)
        # #test
        # ai_config["base_url"]="test"
        self.lts_test_prompts(sys_prompt,user_prompt)
        # response = call_ai(ai_config,sys_prompt,user_prompt)
        self.Call_Ai = Call_Ai()
        new_config = self.Config.get_ai_config(status=self.status)
        
        # 创建新的AI配置字典
        ai_config = {}
        ai_config["api_key"] = new_config.get("key")
        ai_config["base_url"] = new_config.get("api")
        ai_config["model_name"] = new_config.get("model_name")
        ai_config["temperature"] = new_config.get("temperature", 0.6)
        ai_config["stream"] = new_config.get("stream", False)
        ai_config["max_tokens"] = new_config.get("max_tokens", 8152)
        
        response=self.Call_Ai.call_ai(ai_config,sys_prompt,user_prompt)
        return response
    
    # 新增测试函数，输出系统提示和用户提示
    def lts_test_prompts(self,sys_prompt,user_prompt):
        """
        测试函数,输出 ai 的 system prompt 和 user prompt，
        并确保每行分别清晰显示
        """
        print("System Prompt:")
        if isinstance(sys_prompt, list):
            for line in sys_prompt:
                print(line)
        else:
            print(sys_prompt)
            
        print("\nUser Prompt:")
        def print_lines(item):
            if isinstance(item, list):
                for line in item:
                    print_lines(line)
            else:
                print(item)
                
        print_lines(user_prompt)







class LongTermCharacter(Project):
    """
    用于生成和维护,Proper_nouns_table.json中,重要角色的长期总结
    Proper_nouns_table.json示例:
    {
    "longterm_describe_table": [
        {
        "name": "クリシェ",
        "describes": [
            {
            "id": 1,
            "title":"頭のおかしな少女",
            "describe":""
            }
        ]
        }
    ],
    ...
    }
    """
    def __init__(self,project_name, character_name,title: dict, status):
        super().__init__(project_name)
        self.record_path=self.f_record_path if status == "translating" else self.p_record_path
        self.PNT= PNT(self.PNT_path)
        self.Record=Record(self.record_path)
        self.TranslateFile=TranslateFile(self.translate_file_path)
        self.character_name = character_name
        self.longterm_describe = ""
        self.newlongterm_describe = ""
        self.describes = [] #存储最新章节对该角色的描述的列表
        self.title = {}
        self.title["title"] = title["title"]
        self.title["id"] = title["id"]
        self.title["level"] = title["level"]
        
    def ltc_generate(self):
        """
        生成角色长期描述
        """
        end_id = self.TranslateFile.get_chapter_end_from_id(self.title["id"])
        self.ltc_get_describe_list(self.title["id"],end_id)
        self.ltc_get_longterm_describe()
        self.ltc_generate_summary()
        self.ltc_write_record()
        # return self.higher_summary
    
    def ltc_get_longterm_describe(self):
        """
        获取角色原有长期描述
        """
        data= self.PNT.read_pnt()
        for entry in data["translation_table"]:
            if entry.get("name") == self.character_name:
                self.longterm_describe = entry.get("longterm_describe", "")
                break
    def ltc_get_describe_list(self, start_id, end_id):
        """
        读取中内容,生成self.lastest_chapter_describe列表
        仅获取 "status" 为 "written" 的记录:
        - "translate"中最小id为开始位置, "range"为结束位置
        - 若记录的开始与结束均在start_id和end_id范围内,则格式化后添加到describe列表中
        """
        records = self.Record.data.get("record", [])
        # 遍历每条记录
        for rec in records:
            if rec.get("status") == "written":
                translate_dict = rec.get("translate", {})
                if not translate_dict:
                    continue
                # 获取translate中最小的key作为开始位置,转换成整数
                start = int(min(translate_dict.keys(), key=lambda k: int(k)))
                # 获取结束位置
                end = int(rec.get("range", 0))
                # 如果记录的开始与结束在指定区间内,则添加格式化的字符串到summary列表中
                if start >= int(start_id) and end <= int(end_id):
                    describe_text = ""
                    for item in rec.get("Character changing", []):
                        if isinstance(item, dict) and item.get("name") == self.character_name:
                            describe_text = item.get("describe", "")
                            break
                    formatted = f"范围: {start}-{end}的对该角色的描述为:{describe_text}"
                    if describe_text :self.describes.append(formatted) #如果该章节有对该角色的描述,则添加到列表中

    def ltc_generate_summary(self):
        """
        生成对该角色的新长期描述
        """
        sys_prompt =f"你是一个强大的ai助手,需要根据给出的内容,概括作品中某个角色的特征,并严格按照格式要求输出注意!!! 如果选择更新,则返回的新长期描述必须包含对角色完整的描述,绝对不可以只返回新增内容!如果你认为该角色旧的长期描述已经足以概括角色的主要特质,无需更新,则只返回 '无需更新' !"
        newline = "\n"  # 预先定义换行符
        user_prompt = f"""
你需要生成<{self.character_name}>的人物描述,我将给出对该角色长期以来的描述,和最新章节中,各个段落对该角色的描述,由你来生成该角色的长期描述
#此前对该角色的长期描述是:{self.longterm_describe}{newline}
#最新章节中对该角色的描述有:{newline}{newline.join(self.describes)}:
#你需要生成,对该角色的新长期描述,仅返回生成的新长期描述,不要包含任何其他内容!
#注意!!! 如果选择更新,则返回的新长期描述必须包含对角色完整的描述,绝对不可以只返回新增内容!如果你认为该角色旧的长期描述已经足以概括角色的主要特质,无需更新,则只返回"无需更新"!
"""
        response=self._ltc_call_ai(sys_prompt,user_prompt)

        self.newlongterm_describe = response["content"]
        if self.newlongterm_describe == "无需更新": self.newlongterm_describe = self.longterm_describe
        #test
        with open(os.path.join(os.path.dirname(__file__), "output.txt"), "w", encoding="utf-8") as f:
            f.write(json.dumps(response, ensure_ascii=False, indent=4))
        
    def ltc_write_record(self):
        data = self.PNT.read_pnt()
        # 如果"longterm_describe_table"不存在或不是一个列表，则创建该键并初始化为列表
        if "longterm_describe_table" not in data or not isinstance(data["longterm_describe_table"], list):
            data["longterm_describe_table"] = []
        updated = False
        #更新"translation_table"中对应角色的长期描述
        for entry in data["translation_table"]:
            if entry.get("name") == self.character_name:
                entry["longterm_describe"] = self.newlongterm_describe
                break
        #更新"longterm_describe_table"中对应角色的长期描述
        for entry in data["longterm_describe_table"]:
            if entry.get("name") == self.character_name:
                entry["describes"].append({
                    "id": self.title["id"],
                    "title": self.title["title"],
                    "describe": self.newlongterm_describe
                })
                updated = True
                break
        #如果该角色之前没有长期描述,则创建对应角色的长期描述表
        if not updated:
            data["Long_term_summary_table"].append({
                "title": self.title["title"],
                "name": self.character_name,
                #"translate": GetCharacterTranslate(self.character_name),
                "describe":[{
                    "id": self.title["id"],
                    "title": self.title["title"],
                    "describe": self.newlongterm_describe
                }]
            })
        PNT(self.PNT_path).write_pnt(data)
        
    def _ltc_call_ai(self,sys_prompt,user_prompt):
        """
        调用AI生成总结
        """
        with open(self.config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        ai_config=config_data["default_ai_setting"]
        ai_config["base_url"]=ai_config["api"]
        ai_config["api_key"]=ai_config["key"]
        #test
        self.ltc_test_prompts(sys_prompt,user_prompt)
        response = call_ai(ai_config,sys_prompt,user_prompt)
        return response
    
    # 新增测试函数，输出系统提示和用户提示
    def ltc_test_prompts(self,sys_prompt,user_prompt):
        """
        测试函数,输出 ai 的 system prompt 和 user prompt，
        并确保每行分别清晰显示
        """
        print("System Prompt:")
        if isinstance(sys_prompt, list):
            for line in sys_prompt:
                print(line)
        else:
            print(sys_prompt)
            
        print("\nUser Prompt:")
        def print_lines(item):
            if isinstance(item, list):
                for line in item:
                    print_lines(line)
            else:
                print(item)
                
        print_lines(user_prompt)

    # 新增入口方法，无需创建实例即可调用
    @classmethod
    def generate_character(cls,project_name,character_name, title: dict, status):
        instance = cls(project_name, character_name, title, status)
        instance.ltc_generate()
        #return instance.higher_summary

if __name__ == "__main__":
    #test
    # project_name = "少女所不期望的英雄史诗-Gumiho-v0.92"
    # book_name = "少女所不期望的英雄史诗"
    # title = {"title": "# 少女の日常", "id": 82, "level": "title_lv1"}
    # test1= LongTermSummary(project_name, title,"translating")
    # test1.lts_generate()
    # # character_name = "クリシェ"
    # # LongTermCharacter.generate_character(project_name, character_name,title,"translating")

    project_name = "殺されて当然と少女は言った。"
    book_name = "殺されて当然と少女は言った。"
    title = {"title": "『北条リオ』", "id": 548, "level": "title_lv1"}
    test2= LongTermSummary(project_name, title,"translating")
    test2.lts_generate()






