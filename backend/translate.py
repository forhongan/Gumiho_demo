import os
import json
import datetime
from Project import Project  
from Config import Config
from ai import call_ai
from Record import Record  
from TranslateFile import TranslateFile
from long_term_maintain import LongTermSummary
from PNT import PNT
from ai import Call_Ai
import math
import re
from knowledge_awak import match_knowledge_cards_for_text, format_triggered_knowledge_for_prompt

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
    def __init__(self, project_name, status,sse_callback=None):  # 修改参数名为 project_name
        super().__init__(project_name)  # 调用 Project 的构造器进行项目完整性检查及初始化
        self.project_name = project_name
        self.status = status  # 状态: translating, proofreading
        self.now_setting = "first_translation_setting" if status == "translating" else "proofreading_setting"
        self.sse_callback = sse_callback
        
        self.Call_Ai=Call_Ai(sse_callback=sse_callback)
        self.Config=Config(self.config_path)
        self.TranslateFile=TranslateFile(self.translate_file_path)
        # 统一使用单一记录文件，废止 p_record 机制
        self.record_path = self.f_record_path
        self.Record = Record(self.record_path)
        self.PNT=PNT(self.PNT_path)
        self.Config.data=self.Config.read_config()
        
        
        self.translatefile_data = self.TranslateFile.read_translatefile()
        self.paragraphed = self.Config.data.get("paragraphed")
    
    #执行一次翻译/校对
    def translating(self):
        if self.status == "translating":
            #执行一次翻译到获取翻译结果
            self.translating_to_result()
        else:
            #执行一次校对到获取校对结果
            self.proofreading_to_result()
        
        self.save_f_record() # p_record 已废止，统一使用 f_record

            
        # 将记录文件中的翻译结果写入工程文件和专有名词表
        self.record_to_file()

        # 如果是初译且启用了章节长期总结，且本次处理为该章节的最后一段且已完成翻译，则调用长期总结生成
        try:
            cfg_summary = self.Config.data[self.now_setting].get("Automatically generated text summary", {})
            enable_lts = bool(cfg_summary.get("enable longterm summary", False))
        except Exception:
            enable_lts = False

        if self.status == "translating" and enable_lts and self.paragraph_title:
            title = self.paragraph_title
            title_id = self.TranslateFile.get_id_from_chapter_name(title)
            chapter_end_id = self.TranslateFile.get_chapter_end_from_id(title_id)
            if chapter_end_id is not None and self.end == chapter_end_id:
                self.call_lts_generated_summary()
        
        if self.status == "translating" and self.Config.data.get("first_translation_setting", {}).get("Proofread now", False):
            # 在初译完成后立即将本段提交至校对阶段
            self.status = "proofreading"
            self.is_proofread_now_model=True # 标记为即时校对模式
            self.proofreading_to_result()
            self.save_f_record() # p_record 已废止，统一使用 f_record
            self.record_to_file()

        return
    
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

        # 知识唤醒：匹配并缓存本次触发的知识卡片（实验性）
        self.triggered_knowledge_cards = []
        try:
            ka_enabled = bool(self.Config.data.get(self.now_setting, {}).get("knowledge_awakening_enabled", False))
        except Exception:
            ka_enabled = False
        if ka_enabled:
            try:
                # 触发文本：以本次原文 + 上下文总结为主，避免引入过多噪声
                trigger_texts = []
                trigger_texts.extend(self.original_text or [])
                trigger_texts.extend(self.summary_list or [])
                self.triggered_knowledge_cards = match_knowledge_cards_for_text(
                    project_name=self.project_name,
                    text_or_list=trigger_texts,
                    case_sensitive=False,
                    limit=8,
                    sse_callback=self.sse_callback,
                )
            except Exception:
                self.triggered_knowledge_cards = []
        
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
        self.new_record= self.Record.recording(self.response, self.paragraph_title, self.start, self.end, self.status)

        #test
        with open(os.path.join(self.project_path, "output.txt"), "w", encoding="utf-8") as f:
            f.write(json.dumps(self.new_record, ensure_ascii=False, indent=4))
    
    def proofreading_to_result(self):
        """执行一次校对到获取校对结果
        支持两种调用场景：
        1) 在初译流程中复用已计算的 start/end/original_text/translated_text 等（如果这些属性已存在则不重复计算）
        2) 独立以 status="proofreading" 创建对象时自行计算范围
        同时支持配置项：lightweight_proofreading_mode 与 same_as_first_translation_text
        """
        # 如果范围未设置/为空，则计算范围
        if getattr(self, "start", None) is None:
            self.scope_definition()
            # 若仍未找到待处理范围则直接返回
            if getattr(self, "start", None) is None:
                return
        else:
            # 即时校对模式，沿用原范围，但从更新了的TranslateFile文件获取新的译文内容
            self.translatefile_data = self.TranslateFile.read_translatefile()
            start_idx = self.TranslateFile.get_idx_from_id(self.start)
            if start_idx is None:
                self.translated_text = []
                print("DEBUG: Warning: Start ID not found in translate file during proofreading.")
                return
            else:
                if self.TranslateFile.check_status(self.start, self.end, "f_trans_finished") == False:
                    # 存在未完成初译的章节，终止校对
                    print("DEBUG: Warning: Some chapters in the specified range are not marked as 'f_trans_finished' during proofreading.")
                    return
                current_group, _ = self._collect_current_group(
                    chapters=self.translatefile_data.get("chapters", []),
                    start_index=start_idx,
                    req_state="f_trans_finished",
                    max_len=self.Config.data.get(self.now_setting, {}).get("Number of texts per group", 60)
                )
                self.translated_text = [c.get("translation-text", "") for c in current_group] if current_group else []

        # 决定文本处理配置来源（是否沿用初译的文本处理设置）
        try:
            use_first_text_setting = bool(self.Config.data.get("proofreading_setting", {}).get("same_as_first_translation_text", False))
        except Exception:
            use_first_text_setting = False
        text_setting = "first_translation_setting" if use_first_text_setting else "proofreading_setting"

        # 临时切换 now_setting 以复用 first_translation_setting 的文本处理逻辑（name_table_get/summary_get/user_prompt_make 依赖 now_setting）
        orig_now = getattr(self, "now_setting", None)
        self.now_setting = text_setting

        # 获取人名/专有名词表（如果配置开启）
        try:
            if self.Config.data.get(self.now_setting, {}).get("Automatic Translation Dictionary", {}).get("enable", False):
                self.name_table_get()
        except Exception:
            pass

        # 获取上文总结（如果配置开启）
        self.summary_list = []
        try:
            if self.Config.data.get(self.now_setting, {}).get("Automatically generated text summary", {}).get("using", False):
                self.summary_get()
        except Exception:
            self.summary_list = []

        # 构建系统提示（基于 status）
        self.sys_prompt_make()

        # 根据是否为轻量化校对模式决定 user_prompt 的构建方式
        lightweight = bool(self.Config.data.get("proofreading_setting", {}).get("lightweight_proofreading_mode", False))

        if lightweight:
            # 仅提供译文，突出流畅性校对要求
            base_prompt = self.Config.data.get("proofreading_setting", {}).get("proofreading_prompt", "")
            prompt_lines = [base_prompt.strip()] if base_prompt else []
            prompt_lines.append("\n## 本次需要校对的译文：")
            for idx, trans in enumerate(self.translated_text):
                prompt_lines.append(f"ID：{self.start + idx}")
                prompt_lines.append(f"译文：{trans}")

            # 添加输出结构与检查表（保证校对AI按期望格式返回）
            prompt_lines.append("\n#请严格按照以下格式输出:")
            prompt_lines.append(self.Config.data.get("proofreading_setting", {}).get("Output structure", ""))
            prompt_lines.append("\n#其他注意点:")
            prompt_lines.append(self.Config.data.get("proofreading_setting", {}).get("Checklist", ""))

            final_prompt = "\n".join([line.strip() for line in prompt_lines if line and line.strip()])
            self.user_prompt = [final_prompt]
        else:
            # 使用通用构建逻辑（user_prompt_make 已会在非 translating 状态下包含原文与当前译文）
            self.user_prompt_make()

        # 恢复 now_setting 为原值（避免影响外部流程的状态）
        self.now_setting = orig_now

        # 构建AI配置：支持使用初译阶段的 ai 设置（with_same_setting_as_first_translation）
        try:
            use_first_ai_setting = bool(self.Config.data.get("proofreading_setting", {}).get("with_same_setting_as_first_translation", False))
        except Exception:
            use_first_ai_setting = False

        if use_first_ai_setting:
            # 从 first_translation_setting 获取 ai 配置
            new_config = self.Config.get_ai_config(status="translating")
            ai_config = {}
            ai_config["api_key"] = new_config.get("key")
            ai_config["base_url"] = new_config.get("api")
            ai_config["model_name"] = new_config.get("model_name")
            ai_config["temperature"] = new_config.get("temperature", 0.3)
            ai_config["stream"] = new_config.get("stream", False)
            ai_config["json_or_not"] = new_config.get("json_or_not", False)
            ai_config["max_tokens"] = new_config.get("max_tokens", 8152)
            self.ai_config = ai_config
        else:
            # 默认行为：基于当前对象的 status 获取 ai 配置
            self.ai_config_make()

        # 调用AI
        self.ai_translating()

        # 处理AI返回结果生成 new_record（与翻译流程保持一致的记录格式）
        self.new_record = self.Record.recording(self.response, self.paragraph_title, self.start, self.end, self.status)

        # 调试输出：将 new_record 写入输出文件
        try:
            with open(os.path.join(self.project_path, "output.txt"), "w", encoding="utf-8") as f:
                f.write(json.dumps(self.new_record, ensure_ascii=False, indent=4))
        except Exception:
            pass

    def scope_definition(self):
        # 初始化配置和结果变量,计算翻译范围,将范围内的内容载入到文本列表中
        config_key = "first_translation_setting" if self.status == "translating" or self.Config.data.get("proofreading_setting", {}).get("same_as_first_translation_text", False) else "proofreading_setting"
        max_len = self.Config.data.get(config_key, {}).get("Number of texts per group", 60)
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
        # test
        print("Debug: start =", self.start)
        print("Debug: end =", self.end)
        
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
        # 先扫描可用的连续条目（受状态和段落分隔影响）
        available = []
        for chap in chapters[start_index:]:
            if chap.get("state") != req_state:
                break
            # 若启用了段落分组，遇到非正文且已有内容则停止（保持与原逻辑一致）
            if self.paragraphed and available and chap.get("type") != "main_text":
                break
            available.append(chap)

        if not available:
            return [], None

        available_count = len(available)

        # 如果启用了 uniform split mode，并且可用条目超过 max_len，则尽量均匀拆分
        uniform_mode = False
        try:
            uniform_mode = bool(self.Config.data.get(self.now_setting, {}).get("uniform split mode", False))
        except Exception:
            uniform_mode = False

        if uniform_mode and available_count > max_len:
            # 需要的组数（使得每组不超过 max_len）
            groups_needed = math.ceil(available_count / max_len)
            # 将 available_count 尽量均匀分配到 groups_needed 组中，当前组取其中一组的大小（向上取整）
            group_size = math.ceil(available_count / groups_needed)
            # 仍然保证不超过 max_len
            group_size = min(group_size, max_len)
            current_group = available[:group_size]
        else:
            # 原有行为：直接取不超过 max_len 的前缀
            current_group = available[:max_len]

        current_end_id = current_group[-1]["id"] if current_group else None
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
        data = self.PNT.read_pnt()
        self.name_list = []
        for item in data.get("translation_table", []):
            name = item.get("name", "")
            translation = item.get("translation", "")
            #如果原名在原文中出现,则将对应人物/专有名词信息加入name_list
            if any(name in txt for txt in self.original_text if txt):
                # 将本章章节名加入该条目的appearances（避免重复），表示该角色在本章中出现
                if self.paragraph_title:
                    appearances = item.get("appearances", [])
                    if self.paragraph_title not in appearances:
                        appearances.append(self.paragraph_title)
                        item["appearances"] = appearances
                        
                #拼接描述
                if self.Config.data[self.now_setting]["Automatic Translation Dictionary"]["enable_describe_using"]:
                    # 如果存在"固定描述",添加固定描述到描述前
                    locked = item.get("locked_describe", "")
                    describe = f"<<{locked}>>" if locked else ""
                    # 添加描述主体，同时处理长度限制配置
                    base_desc_orig = item.get("describe", "") or ""
                    adt_cfg = self.Config.data[self.now_setting]["Automatic Translation Dictionary"]
                    enable_len_limit = bool(adt_cfg.get("enable_describe_length_limit", False))
                    limit = int(adt_cfg.get("describe_length_limit", 0)) if enable_len_limit else 0 #为0表示不启用
                    # 若超过两倍限制则截断多余部分并以省略号替代（基于原始主体，不包括locked_describe与长期描述）
                    base_desc = base_desc_orig
                    if limit and len(base_desc_orig) > 2 * limit:
                        base_desc = base_desc_orig[:2 * limit] + "……"
                    # 将主体加入describe
                    describe += base_desc
                    # 若启用描述长度限制且原始主体超过阈值,在末尾加入警告（长度计算不包括被<<>>包裹的locked_describe和长期描述）
                    if limit and len(base_desc_orig) > limit:
                        describe += f"[警告：该角色描述长度已超限，长度限制为{limit}个字(不包括被<<>>包裹的部分），请在更新该人物描述时进行适当总结以浓缩描述文本长度到{limit}个字内]"
                    
                    # 【未使用】如果存在长期描述,获取角色到上一章为止的长期描述（长期描述不计入长度判断）
                    if adt_cfg.get("enable_longterm_using", False):
                        ltd = self.PNT.get_longterm_describe(name,self.TranslateFile.get_previous_chapter_start_from_id(self.start))
                        if ltd:
                            describe +=f"\n此外,本角色的长期描述(来自从开头为止的此前章的角色描述概述)为: {ltd}"
                    

                if self.Config.data[self.now_setting]["Automatic Translation Dictionary"]["enable_describe_using"]:
                    self.name_list.append(f"原名:{name}  译名:{translation}  描述:{describe}")
                else :
                    self.name_list.append(f"原名:{name}  译名:{translation}")
        
        self.PNT.write_pnt(data)

    def summary_get(self):
        """
        #获取上文总结列表
        """
        max_summary_num = self.Config.data[self.now_setting]["Automatically generated text summary"]["Number of history generated records"]
        records = self.Record.read_record().get("record", [])
        filtered = [rec for rec in records if int(rec.get("range", 0)) <= int(self.start) and rec.get("Summary", "").strip()]
        sorted_filtered = sorted(filtered, key=lambda x: int(x.get("range", 0)), reverse=True)
        selected = sorted_filtered[:max_summary_num]
        summary_num = len(selected)
        
        message = ""
        #如果启用了长期总结并启用将其加入到本章请求中，则加入
        if self.Config.data[self.now_setting]["Automatically generated text summary"]["enable previous chapter summary"]:
            title_id= self.TranslateFile.get_id_from_chapter_name(self.paragraph_title) if self.paragraph_title else None
            previous_title_id = self.TranslateFile.get_previous_chapter_start_from_id(title_id) if title_id is not None else None
            longterm_summary = self.Record.get_longterm_summary(previous_title_id)
            print("Debug: previous_title_id =", previous_title_id)
            if longterm_summary:
                message = f"上一章<{self.TranslateFile.get_chapter_name_from_id(previous_title_id)}>的内容的概括为：\n"
                message += longterm_summary
        
        if summary_num == 0:
            self.summary_list = []
        else:
            if summary_num == 1:
                message += "\n上一组翻译内容的概括为："
            else:
                message += f"\n前{summary_num}组的翻译内容的总结依次为："
            self.summary_list = [message] + [rec.get("Summary", "").strip() for rec in reversed(selected)]

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
            prompt_lines.append(f"# 你需要执行{self.Config.data['type']}:<{self.Config.data['Name']}>的翻译工作")
        ## 添加概述
        
        ## 添加当前段落标题（如有）
        if self.paragraphed and self.paragraph_title:
            prompt_lines.append(f"## 当前翻译内容来自章节：<{self.paragraph_title}>")

        # =============== 核心内容区 ===============
        # 添加上文翻译内容
        if self.past_text and self.Config.data[self.now_setting]["Automatically generated text summary"]["Number of historical texts used"]>0:
            prompt_lines.append("\n## 最近上文的翻译结果是：")
            for past in self.past_text:
                prompt_lines.append(f"- {past}")
        # 添加原文内容
        prompt_lines.append("\n## 本次需要处理的原文内容：")
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
            prompt_lines.append("\n## 上下文总结：")
            prompt_lines.extend([f"- {summary}" for summary in self.summary_list])
        
        # 添加专有名词列表
        if self.Config.data[self.now_setting]["Automatic Translation Dictionary"]["enable"]:
            prompt_lines.append("\n## 已确定的人物/专有名词翻译：\n")#注:无论有没有表中有没有内容,均有必要添加该行,否则容易引起ai误解
            if len(self.name_list) > 0:
                prompt_lines.extend([f"- {name}" for name in self.name_list])

        # 添加知识唤醒（实验性）：仅当启用且确实匹配到知识卡片时写入
        try:
            ka_enabled = bool(self.Config.data.get(self.now_setting, {}).get("knowledge_awakening_enabled", False))
        except Exception:
            ka_enabled = False
        if ka_enabled:
            cards = getattr(self, "triggered_knowledge_cards", []) or []
            prompt_lines.extend(format_triggered_knowledge_for_prompt(cards))
        
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

        new_config = self.Config.get_ai_config(status=self.status)
        
        # 创建新的AI配置字典
        ai_config = {}
        ai_config["api_key"] = new_config.get("key")
        ai_config["base_url"] = new_config.get("api")
        ai_config["model_name"] = new_config.get("model_name")
        ai_config["temperature"] = new_config.get("temperature", 0.3)
        ai_config["stream"] = new_config.get("stream", False)
        ai_config["json_or_not"] = new_config.get("json_or_not", False)
        ai_config["max_tokens"] = new_config.get("max_tokens", 8152)

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
                if rec.get("type") == "translating":
                    for tid, ttext in rec.get("translate", {}).items():
                        chapter_id = int(tid)
                        for chapter in self.translatefile_data.get("chapters", []):
                            if chapter.get("id") == chapter_id:
                                chapter["translation-text"] = ttext
                                chapter["state"] = "f_trans_finished"
                                updated = True
                                break
                elif rec.get("type") == "proofreading":
                    for tid, ttext in rec.get("translate", {}).items():
                        chapter_id = int(tid)
                        for chapter in self.translatefile_data.get("chapters", []):
                            if chapter.get("id") == chapter_id and ttext != chapter.get("translation-text", ""):
                                chapter["abandoned_translation_text"] = chapter.get("translation-text", "")
                                chapter["translation-text"] = ttext
                                updated = True
                                break

                    # 对校对记录，统一将记录范围内（rec['start'] 或 self.start 到 rec['range']）的章节标记为已完成
                    rec_start = rec.get("start", 1)
                    rec_end = rec.get("range")
                    for chapter in self.translatefile_data.get("chapters", []):
                        cid = chapter.get("id")
                        if isinstance(cid, int) and rec_start <= cid <= rec_end:
                            if chapter.get("state") != "proofreading_finished":
                                chapter["state"] = "proofreading_finished"
                                updated = True

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
                        describe = item.get("describe", "")
                        # 删除describe中所有被<< >>包裹的内容（支持跨行），并去除首尾多余空白
                        clean_describe = re.sub(r'<<.*?>>', '', describe, flags=re.S).strip()
                        if entry:
                            # 若已存在则不重复追加appearances列表
                            entry["describe"] = clean_describe
                            appearances = entry.get("appearances", [])
                            if f"{title}" not in appearances and title:
                                appearances.append(f"{title}")
                            entry["appearances"] = appearances
                        else:
                            new_entry = {
                                "name": item.get("name"),
                                "type": "Character" if key == "New Character" else "Proper noun",
                                "translation": item.get("translation"),
                                "describe": clean_describe,
                                "appearances": [f"{title}"]
                            }
                            table.append(new_entry)
                # 处理Character changing中的描述更新
                for item in rec.get("Character changing", []):
                    entry = find_entry(item.get("name"))
                    if entry and not entry.get("locked", False):
                        describe = item.get("describe", "")
                        # 删除describe中所有被<< >>包裹的内容（支持跨行），并去除首尾多余空白
                        clean_describe = re.sub(r'<<.*?>>', '', describe, flags=re.S).strip()
                        entry["describe"] = clean_describe

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
        # 统一使用单一记录文件（废止 p_record）
        record_file = self.record_path
        
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
    
    def test_prompts(self):
        """
        测试函数,输出prompt内容
        """
        print("System Prompt:")
        for line in self.sys_prompt:
            print(line)
        print("\nUser Prompt:")
        for line in self.user_prompt:
            print(line)
    
    def call_lts_generated_summary(self):
        """
        调用LongTermSummary类,生成本章长期总结,一般在章节翻译完毕时调用
        """
        title_id=self.TranslateFile.get_id_from_chapter_name(self.paragraph_title)
        end_id=self.TranslateFile.get_chapter_end_from_id(title_id)
        if title_id is not None and end_id-title_id>1: #防止章节过短/为独立的高级标题导致长期总结无意义
            print(f"Debug: 调用长期总结生成章节<{self.paragraph_title}>的长期总结, title_id={title_id}, end_id={end_id}")
            LongT=LongTermSummary(self.project_name, {"title":self.paragraph_title,"id":title_id,"level":"title_lv1"},self.status)
            LongT.lts_generate()
        # return self.LongT

    def ai_translating(self):
        """
        #调用ai
        """
        #test
        self.test_prompts()
        
        ptest=False
        # ptest=True
        if ptest==True:
            input("测试模式,按回车继续读取output.txt作为返回结果")
            with open(os.path.join(self.project_path, "output.txt"), "r", encoding="utf-8") as f:
                self.response = json.load(f)
        else:
            # self.response=call_ai(self.ai_config,self.sys_prompt,self.user_prompt)
            self.response=self.Call_Ai.call_ai(self.ai_config,self.sys_prompt,self.user_prompt)
        #test
        # with open(os.path.join(self.project_path, "output.txt"), "w", encoding="utf-8") as f:
        #     f.write(json.dumps(self.response, ensure_ascii=False, indent=4))
    
if __name__ == "__main__":
    # project_name = "少女所不期望的英雄史诗"
    # project_name = "少女所不期望的英雄史诗-Gumiho-v0.92-r1"
    # project_name = "鲜血王女-屠戮殆尽-kiki"
    # # project_name = "温暖的异世界转生~等级感和，携带物品!我是最强幼女~"
    # project_name = "殺されて当然と少女は言った。"
    project_name = "鲜血王女-屠戮殆尽-proo-test-kiki"
    status = "translating"
    # status = "proofreading"
    
    for i in range(1):
        now_translating = Translating(project_name, status)
        # print(now_translating.project_path)
        # print(now_translating.config_path)
        # print(now_translating.translate_file_path)
        
        now_translating.translating()
        
        # now_translating.ai_config_make()
        # now_translating.scope_definition()
        # print(f"start:{now_translating.start}")
        
        # print(json.dumps(now_translating.get_human_check_list(), indent=4, ensure_ascii=False))
        # now_translating.ai_translating()
        # #now_translating.response={}
        # now_translating.save_f_record()
        # now_translating.record_to_file()
