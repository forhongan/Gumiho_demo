# Record 类,翻译日志记录文件的及其相关操作
import json
import re

class Record:
    """
    用于更新和处理记录文件
    self.status: 当前翻译状态,只能是"first translating"或"proofreading"
    self.config_path: 项目配置文件路径
    self.record_path: record.json的路径
    self.file_path: 翻译工程文件xxx.json的路径
    """
    def __init__(self, record_path):  # 修改：增加 config_path 参数
        self.record_path = record_path
        self.data = self.read_record()
    
    def read_record(self):
        # 读取record.json文件
        with open(self.record_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def write_record(self, data):
        # 写入record.json文件
        with open(self.record_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.data = data  # 更新当前数据
    
    def update_record(self, new_record):
        # 在写入前重新读取文件以避免使用过期的内存数据（防止覆盖其它进程/实例写入的 Long_term_summary_table）
        try:
            current = self.read_record()
        except Exception:
            current = {"record": []}
        # 确保有 record 列表
        if "record" not in current or not isinstance(current["record"], list):
            current["record"] = []
        current["record"].append(new_record)
        self.write_record(current)
    
    def recording(self, new_data, title, start, end, status,data_status="unwritten"):
        """ 根据读入数据,组织出新增的记录,返回新记录"""
        # try:
        #     records = self.read_record()
        # except (FileNotFoundError, json.JSONDecodeError):
        #     records = {"record": []}
        # records = self.data
        new_record = {
            "start": start,
            "range": end,
            "title": f"{title}",
            "type": f"{status}",
            "status": f"{data_status}",
            "translate": {},
            "New Character": [],
            "Character changing": [],
            "New proper noun": [],
            "Summary": "",
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }

        content = new_data.get("content", "")

        # 先尝试把 AI 返回内容解析为 JSON（支持宽松的键名：中英双写）
        parsed_json = None
        try:
            # 优先尝试整段内容作为纯 JSON 解析
            parsed_json = json.loads(content)
        except Exception:
            # 如果解析失败，尝试从被包裹的文本中提取 JSON 子串并解析
            def _extract_json_from_text(s):
                candidates = []
                for opening, closing in (("{", "}"), ("[", "]")):
                    start = 0
                    while True:
                        idx = s.find(opening, start)
                        if idx == -1:
                            break
                        in_string = False
                        escape = False
                        depth = 0
                        for j in range(idx, len(s)):
                            ch = s[j]
                            if ch == '\\' and in_string:
                                escape = not escape
                                continue
                            if ch == '"' and not escape:
                                in_string = not in_string
                            if in_string:
                                escape = False
                                continue
                            if ch == opening:
                                depth += 1
                            elif ch == closing:
                                depth -= 1
                                if depth == 0:
                                    candidates.append(s[idx:j+1])
                                    break
                            escape = False
                        start = idx + 1
                return candidates

            for cand in _extract_json_from_text(content):
                try:
                    parsed_json = json.loads(cand)
                    break
                except Exception:
                    parsed_json = None
                    continue
        if isinstance(parsed_json, (dict, list)):
            # 规范化为 dict（如果是 list，尝试取第一个元素或视作 translations 列表）
            data = parsed_json
            if isinstance(parsed_json, list):
                if parsed_json and isinstance(parsed_json[0], dict):
                    data = parsed_json[0]
                else:
                    data = {"translations": parsed_json}

            # 解析翻译条目（支持多种键名）
            translations = data.get("translations") or data.get("翻译结果") or data.get("translate") or data.get("results")
            if isinstance(translations, list):
                for item in translations:
                    if not isinstance(item, dict):
                        continue
                    tid = item.get("id") or item.get("ID") or item.get("编号") or item.get("序号")
                    text = item.get("translation") or item.get("译文") or item.get("text") or item.get("翻译")
                    if tid is not None:
                        new_record["translate"][str(tid)] = (text or "").strip()

            # 解析总结
            new_record["Summary"] = (data.get("summary") or data.get("本次总结") or "").strip()

            # 解析新增人物
            nc = data.get("new_characters") or data.get("New Character") or data.get("新增人物")
            if isinstance(nc, list):
                for c in nc:
                    if not isinstance(c, dict):
                        continue
                    name = c.get("name") or c.get("原文名称") or c.get("name")
                    trans = c.get("translation") or c.get("译名") or c.get("translation")
                    desc = c.get("describe") or c.get("describe") or c.get("描述")
                    new_record["New Character"].append({
                        "name": (name or "").strip(),
                        "translation": (trans or "").strip(),
                        "describe": (desc or "").strip()
                    })

            # 解析人物修改
            cc = data.get("character_changes") or data.get("Character changing") or data.get("对原有人物的修改")
            if isinstance(cc, list):
                for ch in cc:
                    if not isinstance(ch, dict):
                        continue
                    name = ch.get("name") or ch.get("原文名称") or ch.get("name")
                    desc = ch.get("describe") or ch.get("describe") or ch.get("描述")
                    new_record["Character changing"].append({
                        "name": (name or "").strip(),
                        "describe": (desc or "").strip()
                    })

            # 解析专有名词
            terms = data.get("new_proper_nouns") or data.get("New proper noun") or data.get("其他专有名词") or data.get("其他认为有必要添加的专有名词")
            if isinstance(terms, list):
                for t in terms:
                    if not isinstance(t, dict):
                        continue
                    name = t.get("name") or t.get("原文名称")
                    trans = t.get("translation") or t.get("译名")
                    desc = t.get("describe") or t.get("描述")
                    new_record["New proper noun"].append({
                        "name": (name or "").strip(),
                        "translation": (trans or "").strip(),
                        "describe": (desc or "").strip()
                    })

        else:
            # 非 JSON 回退到原有的基于正则的解析逻辑
            # 根据 status 决定匹配的结果标题：proofreading 模式下使用 "# 校对结果"，否则使用 "# 翻译结果"
            result_header = "# 校对结果" if status == "proofreading" else "# 翻译结果"
            pattern = rf"{re.escape(result_header)}[：:]?[）)]?\s*\n(.+?)(?=\n# 本次总结|\Z)"
            content_block = re.search(
                pattern, 
                content, 
                re.DOTALL
            )
            if content_block:
                # 修改正则表达式以匹配id和译文之间可能有换行的情况
                translations = re.findall(
                    r"id[\s\n]*[：:]\s*(\d+)[\s\n]*译文[\s\n]*[：:][\s\n]*([^\n]*)", 
                    content_block.group(1)
                )
                for tid, text in translations:
                    new_record["translate"][tid] = text.strip()
            characters_block = re.search(
                r"# 新增人物[：:]?[）)]?\s*(.+?)(?=\n#|$)", 
                content, 
                re.DOTALL
            )
            if characters_block and "（无新增人物）" not in characters_block.group(1):
                characters = re.findall(
                    r"name[：:][（(]?(.*?)[）)]?\s+translation[：:][（(]?(.*?)[）)]?\s+describe[：:][（(]?(.*?)(?=\n\d\.|$)", 
                    characters_block.group(1), 
                    re.DOTALL
                )
                for char in characters:
                    new_record["New Character"].append({
                        "name": char[0].strip(),
                        "translation": char[1].strip(),
                        "describe": char[2].strip()
                    })
            character_change_block = re.search(
                r"# 对原有人物的修改[：:]?[）)]?\s*(.+?)(?=\n#|$)", 
                content, 
                re.DOTALL
            )
            if character_change_block:
                changes = re.findall(
                    r"name[：:][（(]?(.*?)[）)]?\s+describe[：:][（(]?(.*?)(?=\n\d\.|$)", 
                    character_change_block.group(1), 
                    re.DOTALL
                )
                for change in changes:
                    new_record["Character changing"].append({
                        "name": change[0].strip(),
                        "describe": change[1].strip()
                    })
            summary_block = re.search(
                r"#\s*本次总结(?:[：:])?(?:\s*\n\s*本次总结(?:[：:])?)?\s*(.*?)(?=\n#|$)",
                content,
                re.DOTALL
            )
            if summary_block:
                new_record["Summary"] = summary_block.group(1).strip()
            terms_block = re.search(
                r"# 其他认为有必要添加的专有名词[：:]?[）)]?\s*(.+?)(?=\n#|$)", 
                content, 
                re.DOTALL
            )
            if terms_block:
                terms = re.findall(
                    r"name[：:][（(]?(.*?)[）)]?\s+translation[：:][（(]?(.*?)[）)]?\s+describe[：:][（(]?(.*?)(?=\n\d\.|$)", 
                    terms_block.group(1), 
                    re.DOTALL
                )
                for term in terms:
                    new_record["New proper noun"].append({
                        "name": term[0].strip(),
                        "translation": term[1].strip(),
                        "describe": term[2].strip()
                    })
        # records["record"].append(new_record)
        # self.write_record(records)
        return new_record
    
    def rewrite_one_record(self, record_time, rewrited_record):
        # 根据输入的更新的record内容,重写一条记录
        records = self.read_record()
        for idx, record in enumerate(records.get("record", [])):
            if record.get("timestamp") == record_time:
                # 将列表中对应索引的元素替换为新的记录
                records["record"][idx] = rewrited_record
                break
        self.write_record(records)
        
    def get_newest_record(self):
        # 获取最新的记录
        records = self.read_record()
        if records.get("record"):
            return records["record"][-1]
        return None
    
    def get_longterm_summary(self, start_id):
        data = self.read_record()
        print("Debug: get_longterm_summary called with start_id =", start_id)
        for record in data.get("Long_term_summary_table", []):
            if record.get("start_id") == start_id:
                print("Debug: Found longterm summary for start_id", start_id)
                print("Debug: Summary content:", record.get("summary", ""))
                return record.get("summary", "")
        return ""
    
    def get_summary_by_paragraph_title(self,title):
        # 根据段落标题获取对应的该段的总结
        summaries = []
        for record in self.data.get("record", []):
            if record.get("title") == title and record.get("status")=="written" and record.get("Summary","").strip()!="":
                summaries.append(record.get("Summary", ""))
        return summaries
    
    def get_records_by_paragraph_title(self, title):
        # 根据段落标题获取对应的该段的记录
        records = []
        for record in self.data.get("record", []):
            if record.get("title") == title:
                records.append(record)
        return records







