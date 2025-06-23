import json
import re

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