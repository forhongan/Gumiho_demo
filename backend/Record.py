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
        # 更新翻译状态
        new_data = self.data
        new_data["record"].append(new_record)
        # self.write_record(records)
        self.write_record(new_data)
    
    def recording(self, new_data, title, end, status,data_status="unwritten"):
        """ 根据读入数据,组织出新增的记录,返回新记录"""
        # try:
        #     records = self.read_record()
        # except (FileNotFoundError, json.JSONDecodeError):
        #     records = {"record": []}
        # records = self.data
        new_record = {
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
        content_block = re.search(
            r"# 翻译结果[：:]?[）)]?\s*\n(.+?)(?=\n# 本次总结)", 
            new_data["content"], 
            re.DOTALL
        )
        if content_block:
            translations = re.findall(
                r"id[：:]\s*(\d+)\s+译文[：:]\s*(.*?)(?=\n\n|$)", 
                content_block.group(1), 
                re.DOTALL
            )
            for tid, text in translations:
                new_record["translate"][tid] = text.strip()
        characters_block = re.search(
            r"# 新增人物[：:]?[）)]?\s*(.+?)(?=\n#|$)", 
            new_data["content"], 
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
            new_data["content"], 
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
            new_data["content"],
            re.DOTALL
        )
        if summary_block:
            new_record["Summary"] = summary_block.group(1).strip()
        terms_block = re.search(
            r"# 其他认为有必要添加的专有名词[：:]?[）)]?\s*(.+?)(?=\n#|$)", 
            new_data["content"], 
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
        for record in records.get("record", []):
            if record.get("timestamp") == record_time:
                record= rewrited_record
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
        for record in data.get("Long_term_summary_table", []):
            if record.get("start_id") == start_id:
                return record.get("summary", "")
        return ""







