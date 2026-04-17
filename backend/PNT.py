import json
import re
from datetime import datetime

class PNT:
    """
    Proper_nouns_table.json的操作类
    self.PNT_path: Proper_nouns_table.json的路径
    self.file_path: 翻译工程文件xxx.json的路径
    """
    def __init__(self, pnt_path):  # 修改：增加 config_path 参数
        self.PNT_path = pnt_path
        self.data = self.read_pnt()
    
    def get_longterm_describe(self, original_name, id):
        """
        获取到id指向的章节为止的,角色名为original_name的角色的长期描述
        """
        for character in self.data.get("longterm_describe_table", []):
            if character["name"] == original_name:
                for describe in character["describes"]:
                    if describe["id"] == id:
                        return describe["describe"]
        return None
    
    def read_pnt(self):
        """
        读取Proper_nouns_table.json文件
        """
        with open(self.PNT_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def write_pnt(self,data):
        """
        写入Proper_nouns_table.json文件
        """
        with open(self.PNT_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # -------------------- Knowledge awaken cards (experimental) --------------------
    def _ensure_knowledge_awaken_table(self, data: dict):
        if not isinstance(data, dict):
            data = {}
        table = data.get("knowledge_awaken_table")
        if not isinstance(table, list):
            table = []
            data["knowledge_awaken_table"] = table
        return data, table

    def _next_knowledge_awaken_id(self, table):
        max_num = 0
        for item in table or []:
            raw = str((item or {}).get("id", ""))
            m = re.match(r"ka_(\d+)", raw)
            if m:
                try:
                    max_num = max(max_num, int(m.group(1)))
                except Exception:
                    pass
        return f"ka_{max_num + 1:04d}"

    def list_knowledge_awaken_cards(self):
        data = self.read_pnt()
        _, table = self._ensure_knowledge_awaken_table(data)
        return table

    def search_knowledge_awaken_cards(self, query: str):
        query = (query or "").strip()
        cards = self.list_knowledge_awaken_cards()
        if not query:
            return cards
        q = query.lower()
        results = []
        for c in cards:
            try:
                if q in str(c.get("id", "")).lower() or q in str(c.get("keyword_expr", "")).lower() or q in str(c.get("knowledge_content", "")).lower():
                    results.append(c)
            except Exception:
                continue
        return results

    def upsert_knowledge_awaken_card(self, *, card_id=None, keyword_expr="", knowledge_content="", enabled=True, meta=None):
        """新增或更新一张知识唤醒卡片。

        - card_id=None 时创建新卡片并自动分配 id
        - card_id!=None 时按 id 更新；找不到则创建一张并使用该 id
        """
        data = self.read_pnt()
        data, table = self._ensure_knowledge_awaken_table(data)

        entry = None
        if card_id:
            for item in table:
                if str(item.get("id")) == str(card_id):
                    entry = item
                    break

        creating = entry is None
        if creating:
            entry = {
                "id": str(card_id) if card_id else self._next_knowledge_awaken_id(table),
                "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            }
            table.append(entry)

        entry["keyword_expr"] = keyword_expr or ""
        entry["knowledge_content"] = knowledge_content or ""
        entry["enabled"] = bool(enabled)
        entry["updated_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        if meta is not None:
            entry["meta"] = meta

        data["knowledge_awaken_table"] = table
        self.write_pnt(data)
        return entry

    def delete_knowledge_awaken_card(self, card_id):
        data = self.read_pnt()
        data, table = self._ensure_knowledge_awaken_table(data)
        before = len(table)
        table = [c for c in table if str((c or {}).get("id")) != str(card_id)]
        data["knowledge_awaken_table"] = table
        if len(table) != before:
            self.write_pnt(data)
            return True
        return False
    
    def get_character_translate(self,original_name):
        """
        获取角色译名
        """
        pass
    
    def get_characters_in_one_chapter(self, title):
        """
        获取章节名为title的章节中的所有角色表
        """
        characters = []
        # 遍历translation_table中的每个角色条目
        for entry in self.data.get('translation_table', []):
            # 获取该角色的appearances列表，默认为空列表以防键不存在
            appearances = entry.get('appearances', [])
            # 如果title在appearances列表中，则添加该角色到结果
            if title in appearances:
                characters.append(entry)
        return characters
    
    def get_characters_by_str(self, str):
        """通过输入的片段,检索出所有包含该片段的角色,为空时返回全部"""
        characters = []
        if str=="":
            return self.data.get('translation_table', [])
        # 遍历translation_table中的每个角色条目
        for entry in self.data.get('translation_table', []):
            # # 获取该角色的appearances列表，默认为空列表以防键不存在
            # appearances = entry.get('appearances', [])
            if str in entry["name"] or str in entry["translation"] or str in entry["describe"]:
                characters.append(entry)
        return characters