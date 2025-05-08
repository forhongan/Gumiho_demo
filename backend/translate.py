#ReBuilding----------------翻译操作类,定义了以一次翻译进程为单位的翻译过程的主要方法
#!!!!!!!!!!!!!需要将部分方法分拆纾解
import os
import json
import datetime
from Project import Project  
from Config import Config
from ai import call_ai
from Record import Record  
from TranslateFile import TranslateFile
from PNT import PNT
class Translating(Project):
    """
    #翻译进行类
    #project_path: 项目工程文件夹路径
    #file_path: 待翻译的结构化文本数据库(json)路径
    #start: 起始位置id, end: 结束位置id, length: 校对长度 length= end-start,最小为1
    int start
    int end
    int length
    #status: 状态
    string status
    string now_setting
    #text: 需翻译文本
    string list original_text
    string list translated_text
    #past_text: 已翻译文本
    string list past_text
    #name_list: 人名/专有名词列表
    string list name_list
    #summary_list: 上文总结
    string list summary_list
    #output_structure: 输出结构
    string output_structure
    #check_list: 校对列表
    string check_list
    #ai_config: ai设置
    dict config(
        "model_name": "xxx",
        "temperature": 0.7,
        "json_or_not": false,
    )
    #ai_prompt: ai提示
    string list sys_prompt
    string list user_prompt
    #translating_config: 校对设置
    dict translating_config(
        ...
    )
    
    """
    def __init__(self, project_name, status):  # 修改参数名为 project_name
        super().__init__(project_name)  # 调用 Project 的构造器进行项目完整性检查及初始化
        self.status = status  # 状态: translating, proofreading
        self.now_setting = "first_translation_setting" if status == "translating" else "proofreading_setting"

        self.Config=Config(self.config_path)
        self.TranslateFile=TranslateFile(self.translate_file_path)
        self.record_path = self.f_record_path if status == "translating" else self.p_record_path
        self.Record=Record(self.record_path)
        self.PNT=PNT(self.PNT_path)
        self.Config.data=self.Config.read_config()
        
        
        self.translatefile_data = self.TranslateFile.read_translatefile()
        self.paragraphed = self.Config.data.get("paragraphed")
    
    #执行一次翻译
    def translating(self):
        #执行一次翻译到获取翻译结果
        self.translating_to_result()
        
        #保存结果至记录文件
        if self.status == "translating" : 
            self.save_f_record() 
        else: 
            self.save_p_record()
            
        # 将记录文件中的翻译结果写入工程文件和专有名词表
        self.record_to_file()
    
    def translating_to_result(self):
        """执行一次翻译到获取翻译结果"""
        #计算翻译范围,将范围内的内容载入到文本列表中
        self.scope_definition()
        
        #获取人名/专有名词表
        if self.Config.data[self.now_setting]["Automatic Translation Dictionary"]["enable"]:
            self.name_table_get()
        
        #获取上文总结
        self.summary_list=[]
        if(self.Config.data[self.now_setting]["Automatically generated text summary"]["using"]): 
            self.summary_get()
        
        #构建系统提示
        self.sys_prompt_make()
        
        #构建用户提示
        self.output_structure=self.Config.data[self.now_setting]["json_structure"] if self.Config.data[self.now_setting]["ai_config"]["json_or_not"] else self.Config.data[self.now_setting]["Output structure"]
        self.check_list=self.Config.data[self.now_setting]["Checklist"]
        self.user_prompt_make()
        
        #构建ai配置
        self.ai_config_make()
        
        #调用ai
        self.ai_translating()
        
        #处理ai返回结果生成new_record
        self.new_record= self.Record.recording(self.response, self.paragraph_title, self.end, self.status)
    

    def scope_definition(self):
        # 初始化配置和结果变量,计算翻译范围,将范围内的内容载入到文本列表中
        config_key = "first_translation_setting" if self.status == "translating" else "proofreading_setting"
        config = self.Config.data.get(config_key, {})
        max_len = config.get("Number of texts per group", 5)
        req_state = "f_trans_unfinished" if self.status == "translating" else "f_trans_finished"
        self.original_text = []
        self.translated_text = []
        self.past_text = []
        self.start = None
        self.end = None
        self.paragraph_title = None

        chapters = self.translatefile_data.get("chapters", [])
        if not chapters:
            return

        start_index = self._find_start_index(chapters, req_state)
        if start_index is None:
            return

        self.paragraph_title, paragraph_title_index = self._detect_paragraph_title(chapters, start_index)
        current_group, current_end_id = self._collect_current_group(chapters, start_index , req_state, max_len)
        if not current_group:
            return

        self.start = current_group[0]["id"]
        self.end = current_end_id
        self.original_text = [c["original-text"] for c in current_group]
        self.translated_text = [c["translation-text"] for c in current_group]
        self.past_text = self._build_past_text(chapters, start_index, max_len, self.paragraphed, paragraph_title_index)

    def _find_start_index(self, chapters, req_state):
        # 查找首个符合条件的章节索引
        for idx, chap in enumerate(chapters):
            if chap.get("state") == req_state:
                return idx
        return None

    def _detect_paragraph_title(self, chapters, start_index):
        # 检测当前句前的段落标题及其索引
        paragraph_title = None
        paragraph_title_index = None
        if self.paragraphed:
            for idx in range(start_index, -1, -1):
                if chapters[idx].get("type") != "main_text":
                    paragraph_title = chapters[idx].get("original-text")
                    paragraph_title_index = idx
                    break
        return paragraph_title, paragraph_title_index

    def _collect_current_group(self, chapters, start_index, req_state, max_len):
        # 收集当前处理组中的句并返回当前组及终止ID
        current_group = []
        current_end_id = None
        for chap in chapters[start_index:]:
            if chap.get("state") != req_state:
                break
            if self.paragraphed and current_group and chap.get("type") != "main_text":
                break
            if len(current_group) >= max_len:
                break
            current_group.append(chap)
            current_end_id = chap["id"]
        return current_group, current_end_id

    def _build_past_text(self, chapters, start_index, max_len, paragraphed, paragraph_title_index):
        # 构建之前翻译内容的列表
        past_window = []
        for idx in range(start_index-1, max(-1, start_index-max_len-1), -1):
            if (trans := chapters[idx].get("translation-text")):
                past_window.append(trans)
            if len(past_window) >= max_len:
                break
        past_window = past_window[::-1]
        if paragraphed and paragraph_title_index is not None:
            has_cross_paragraph = any(
                idx < paragraph_title_index 
                for idx in range(max(0, start_index-len(past_window)), start_index)
            )
            if has_cross_paragraph and paragraph_title_index > 0:
                prev_para_trans = None
                for idx in range(paragraph_title_index-1, -1, -1):
                    if (trans := chapters[idx].get("translation-text")):
                        prev_para_trans = trans
                        break
                if prev_para_trans:
                    past_window = [prev_para_trans] + past_window
                    past_window = past_window[:max_len]
        return [t for t in past_window if t]

    def name_table_get(self):
        """
        #获取人名/专有名词表表，并将符合条件的条目以格式“原名:...  译名:...  描述:...”加入name_list
        """
        data = self.load_proper_nouns_table_data()  # 调用Project方法
        self.name_list = []
        for item in data.get("translation_table", []):
            name = item.get("name", "")
            translation = item.get("translation", "")
            #如果原名在原文中出现,则将对应人物/专有名词信息加入name_list
            if any(name in txt for txt in self.original_text if txt):
                #拼接描述
                if self.Config.data[self.now_setting]["Automatic Translation Dictionary"]["enable_describe_using"]:
                    # 如果存在"固定描述",添加固定描述到描述前
                    describe=f"[固定描述:{item.get("locked_describe", "")}]" if item.get("locked_describe", False) else ""
                    # 添加描述
                    describe += item.get("describe", "")
                    # 如果存在长期描述,获取角色到上一章为止的长期描述
                    if self.Config.data[self.now_setting]["Automatic Translation Dictionary"]["enable_longterm_using"]:
                        ltd = self.PNT.get_longterm_describe(name,self.TranslateFile.get_previous_chapter_start_from_id(self.start))
                        if ltd:
                            describe +=f"\n此外,本角色的长期描述(来自从开头为止的此前章的角色描述概述)为: {ltd}"
                        
                    
                if self.Config.data[self.now_setting]["Automatic Translation Dictionary"]["enable_describe_using"]:
                    self.name_list.append(f"原名:{name}  译名:{translation}  描述:{describe}")
                else :
                    self.name_list.append(f"原名:{name}  译名:{translation}")

    def summary_get(self):
        """
        #获取上文总结列表
        """
        max_summary_num = self.Config.data[self.now_setting]["Automatically generated text summary"]["Number of history generated records"]
        records = self.Record.data.get("record", [])
        filtered = [rec for rec in records if int(rec.get("range", 0)) <= int(self.start) and rec.get("Summary", "").strip()]
        sorted_filtered = sorted(filtered, key=lambda x: int(x.get("range", 0)), reverse=True)
        selected = sorted_filtered[:max_summary_num]
        summary_num = len(selected)
        if summary_num == 0:
            self.summary_list = []
        else:
            if summary_num == 1:
                message = "上一组翻译内容的概括为："
            else:
                message = f"最新的{summary_num}组翻译内容的总结依次为："
            self.summary_list = [message] + [rec.get("Summary", "").strip() for rec in selected]
        
        if self.Config.data[self.now_setting]["Automatically generated text summary"]["enable previous chapter summary"]:
            longterm_summary = self.Record.get_longterm_summary(self.TranslateFile.get_previous_chapter_start_from_id(self.start))
            if longterm_summary:
                message = f"上一章的翻译内容的概括为：\n"
                message += longterm_summary

        print("Debug: self.summary_list =", self.summary_list)

    def sys_prompt_make(self):
        """
        #构成初次翻译时每次请求的系统prompt
        """
        if self.status == "translating":
            prompt_content = self.Config.data["first_translation_setting"]["base_prompt"]
        else:
            prompt_content = self.Config.data["proofreading_setting"]["proofreading_prompt"]
        self.sys_prompt = prompt_content.splitlines() 
    
    def user_prompt_make(self):
        """
        # 构建用户提示,指导AI完成翻译/校对任务
        # 返回:拼接好的用户提示字符串
        """
        # =============== 基础信息准备 ===============
        prompt_lines = []
        # 添加项目基本信息标题
        if self.Config.data.get("type","")not in {"", "default"} and self.Config.data.get("Name","") not in {"", "default"}:
            prompt_lines.append(f"# 你需要执行{self.Config.data["type"]}:<{self.Config.data["Name"]}>的翻译工作")
        ## 添加概述
        
        ## 添加当前段落标题（如有）
        if self.paragraphed and self.paragraph_title:
            prompt_lines.append(f"## 当前翻译内容来自段落：{self.paragraph_title}")
        
        # =============== 核心内容区 ===============
        # 添加上文翻译内容
        if self.past_text and self.Config.data[self.now_setting]["Automatically generated text summary"]["Number of historical texts used"]>0:
            prompt_lines.append("\n## 上文已翻译内容：")
            for past in self.past_text:
                prompt_lines.append(f"- {past}")
        # 添加原文内容
        prompt_lines.append("\n## 需要处理的原文内容：")
        for idx, (original, translated) in enumerate(zip(self.original_text, self.translated_text)):
            prompt_lines.append(f"\n### ID：{self.start + idx}")  # 自动生成连续ID
            
            # 翻译时仅展示原文，校对时同时展示现有译文
            if self.status == "translating":
                prompt_lines.append(f"原文：{original}")
            else:
                prompt_lines.append(f"原文：{original}")
                prompt_lines.append(f"当前译文：{translated}（请校对修改）")
        
        # =============== 上下文信息区 ===============
        # 添加上文总结（如有）
        if len(self.summary_list) > 0 and self.Config.data[self.now_setting]["Automatically generated text summary"]["using"]:
            prompt_lines.append("\n## 上下文总结（按时间从近到远排序）：")
            prompt_lines.extend([f"- {summary}" for summary in self.summary_list])
        
        # 添加专有名词列表
        if self.Config.data[self.now_setting]["Automatic Translation Dictionary"]["enable"]:
            prompt_lines.append("\n## 已确定的人物/专有名词翻译：\n")#注:无论有没有表中有没有内容,均有必要添加该行,否则容易引起ai误解
            if len(self.name_list) > 0:
                prompt_lines.extend([f"- {name}" for name in self.name_list])
        
        # =============== 输出格式要求 ===============
        prompt_lines.append(f"\n#请严格按照以下格式输出:\n{self.output_structure}")
        prompt_lines.append(f"\n#其他注意点:\n{self.check_list}")
        
        # =============== 格式优化处理 ===============
        # 去除空行并合并为单个字符串
        final_prompt = "\n".join([line.strip() for line in prompt_lines if line.strip()])
        #final_prompt = prompt_lines
        # 根据配置决定是否添加格式强调
        # if not self.Config.data["ai_config"]["json_or_not"]:
        #     final_prompt += "\n\n注意：请使用纯文本格式，不要用Markdown或代码块！"
        
        self.user_prompt = [final_prompt]
    
    def ai_config_make(self):
        ai_config = {}
        ai_config["api_key"] = self.Config.data[self.now_setting]["ai_config"]["key"]
        ai_config["base_url"] = self.Config.data[self.now_setting]["ai_config"]["api"]
        ai_config["model_name"] = self.Config.data[self.now_setting]["ai_config"]["model_name"]
        ai_config["temperature"] = self.Config.data[self.now_setting]["ai_config"].get("temperature", 0.7)
        ai_config["stream"] = self.Config.data[self.now_setting]["ai_config"].get("stream", False)
        ai_config["max_tokens"] = self.Config.data[self.now_setting]["ai_config"].get("max_tokens", 8152)
        #test:
        # ai_config["base_url"] = "test"
        # 将生成的ai_config保存为实例变量
        self.ai_config = ai_config
    
    def save_f_record(self):
        self.Record.update_record(self.new_record)
        # self.Record.update_record(self.response, self.paragraph_title, self.end, self.status)
        
    def save_p_record(self):
        self.Record.update_record(self.new_record)
        # self.Record.update_record(self.response, self.paragraph_title, self.end, self.status)
    
    def get_human_check_list(self):
        # 人工检查
        check_data = {
            "new_record": self.new_record,
            "original_text": self.get_original_text(),
            # "summary_list": self.get_summary_list()
        }
        print("Debug: 人工检查列表:\n")
        print(json.dumps(check_data, indent=4, ensure_ascii=False))
        return check_data

    def get_original_text(self):
        # 获取原文
        return self.original_text
    
    def get_summary_list(self):
        # 获取上文总结
        return self.summary_list
    
    def get_newest_record(self):
        # return self.Record.get_newest_record()
        return self.new_record
    
    def record_to_file(self):
        """
        # 将记录文件中的翻译结果写入工程文件和专有名词表
        """
        # 加载record文件
        records=self.Record.read_record()
        updated = False
        # 更新工程文件章节内容
        for rec in records.get("record", []):
            if rec.get("status") not in ["written", "abandoned"]:
                for tid, ttext in rec.get("translate", {}).items():
                    chapter_id = int(tid)
                    for chapter in self.translatefile_data.get("chapters", []):
                        if chapter.get("id") == chapter_id:
                            chapter["translation-text"] = ttext
                            chapter["state"] = "f_trans_finished" if self.status == "translating" else "proofreading_finished"
                            break
                

        # 将更新后的工程文件写回
        self.TranslateFile.write_translatefile(self.translatefile_data)

        # 更新Proper_nouns_table
        #data = self.load_proper_nouns_table_data()  # 调用Project方法
        data=self.PNT.read_pnt()
        table = data.get("translation_table", [])

        def find_entry(name):
            for entry in table:
                if entry.get("name") == name or entry.get("translation") == name:
                    return entry
            return None

        for rec in records.get("record", []):
            if rec.get("status") not in ["written", "abandoned"]:
                title = rec.get("title", "")
                # 处理New Character和New proper noun
                for key in ["New Character", "New proper noun"]:
                    for item in rec.get(key, []):
                        entry = find_entry(item.get("name"))
                        if entry:
                            # 若已存在则不重复追加appearances列表
                            entry["describe"] = item.get("describe")
                            appearances = entry.get("appearances", [])
                            if f"{title}" not in appearances and title:
                                appearances.append(f"{title}")
                            entry["appearances"] = appearances
                        else:
                            new_entry = {
                                "name": item.get("name"),
                                "type": "Character" if key == "New Character" else "Proper noun",
                                "translation": item.get("translation"),
                                "describe": item.get("describe"),
                                "appearances": [f"{title}"]
                            }
                            table.append(new_entry)
                # 处理Character changing中的描述更新
                for item in rec.get("Character changing", []):
                    entry = find_entry(item.get("name"))
                    if entry and not entry.get("locked", False):
                        entry["describe"] = item.get("describe")

                # 更新处理状态
                rec["status"] = "written"
            
        data["translation_table"] = table
        self.PNT.write_pnt(data)

        # 将更新后的record文件写回
        self.Record.write_record(records)

        return updated

    def rollback(self, timestamp):
        """
        # 回滚操作
        # timestamp: 回滚时间戳
        # 将所有时间晚于等于timestamp的内容回滚
        # 注意,重写不会包括名词表中名词出现章节表的回滚,因为该数据被认为是客观且不会错误的,其余内容都会回滚
        """
        # 确定记录文件路径
        record_file = self.f_record_path if self.status == "translating" else self.p_record_path  # 修改：使用 Project 方法
        
        # 读取记录文件
        records=self.Record.read_record()
        
        abandoned_ids = set()
        input_time = datetime.datetime.fromisoformat(timestamp)
        
        # 处理所有记录状态
        for record in records["record"]:
            # 第一步：所有未被废弃的状态重置为reusing
            if record["status"] not in "abandoned":
                record["status"] = "reusing"
            
            # 第二步：标记需要废弃的记录
            record_time = datetime.datetime.fromisoformat(record["timestamp"])
            if record_time >= input_time:
                record["status"] = "abandoned"
                # 收集被废弃的翻译ID
                abandoned_ids.update(record.get("translate", {}).keys())
        
        #写回记录文件
        self.Record.write_record(records)
            
        # 转换ID为整数类型
        abandoned_ids = {int(id_str) for id_str in abandoned_ids}
        
        # 处理工程文件状态
        self.translatefile_data=self.TranslateFile.read_translatefile()
        
        # 更新章节状态
        for chapter in self.translatefile_data["chapters"]:
            if chapter["id"] in abandoned_ids:
                chapter["state"] = "f_trans_unfinished"
        
        # 保存工程文件修改
        self.TranslateFile.write_translatefile(self.translatefile_data)
        
        # 执行记录文件覆盖
        self.record_to_file()
        
        # 分析回滚结果
        need_retranslate = []
        auto_rolled_back = []
        
        for chapter in self.translatefile_data["chapters"]:
            if chapter["id"] in abandoned_ids:
                if chapter["state"] == "f_trans_unfinished":
                    need_retranslate.append(chapter["id"])
                else:
                    auto_rolled_back.append(chapter["id"])
        
        # 输出结果报告
        if need_retranslate:
            print(f"需要重新翻译的段落ID: {sorted(need_retranslate)}")
        if auto_rolled_back:
            print(f"已自动回滚的段落ID: {sorted(auto_rolled_back)}")
        
    def test_original_text(self):
        """
        测试函数,输出原文内容
        """
        print("Original Text:")
        for line in self.original_text:
            print(line)
            
    def test_name_list(self):
        """
        测试函数,输出原文内容
        """
        print("self.name_list:")
        for line in self.name_list:
            print(line)
    
    def ai_translating(self):
        """
        #调用ai
        """
        #test
        #test_prompts(self.sys_prompt,self.user_prompt)
        ptest=False
        if ptest==True:
            with open(os.path.join(self.project_path, "output.txt"), "r", encoding="utf-8") as f:
                self.response = json.load(f)
        else:
            self.response=call_ai(self.ai_config,self.sys_prompt,self.user_prompt)
        
        #test
        with open(os.path.join(self.project_path, "output.txt"), "w", encoding="utf-8") as f:
            f.write(json.dumps(self.response, ensure_ascii=False, indent=4))
    
if __name__ == "__main__":
    project_name = "对反派千金发动百合攻势后，她却当真了，还把我收为宠物"
    status = "translating"
    
    for i in range(1):
        now_translating = Translating(project_name, status)
        # print(now_translating.project_path)
        # print(now_translating.config_path)
        # print(now_translating.translate_file_path)
        
        # now_translating.translating()
        now_translating.scope_definition()
        print(f"start:{now_translating.start}")
        
        # print(json.dumps(now_translating.get_human_check_list(), indent=4, ensure_ascii=False))
        # now_translating.ai_translating()
        # #now_translating.response={}
        # now_translating.save_f_record()
        # now_translating.record_to_file()
