import json
import os

class TranslateFile:
    """
    #工程文件操作类
    #translatefile_path: 工程文件路径
    #工程文件的类似格式如下:
    {  
        "title": "...", // 文集或书籍标题（可选）  
        "author": "...", // 作者（可选）
        "translator": "...", // 译者（可选）
        "description": "...", // 描述（可选）
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
                "id": 400, // 段落编号  
                "original-text": "第二章 沉没", // 原文  
                "translation-text": "", // 译文 
                "type": "title_lv1" ,//一级标题
                "state": "f_trans_unfinished" //f_trans_unfinished, f_trans_finished,p_finished,checked,re_trans_needed
            },
        ]
    }  
    """
    def __init__(self,translatefile_path):
        self.translatefile_path = translatefile_path
        self.data = self.read_translatefile()

    def read_translatefile(self):
        """
        读取工程文件
        """
        with open(self.translatefile_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    
    def write_translatefile(self,data):    
        """
        写入工程文件
        """
        with open(self.translatefile_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    #检查id是否为标题，标题的"type"以 "title" 开头
    def check_id_is_title(self, id):
        id = int(id)  # 转换为整数
        data = self.read_translatefile()
        for chapter in data["chapters"]:
            if chapter["id"] == id:
                return chapter.get("type", "").startswith("title")
        return False
    
    def get_chapter_end_from_id(self, id):
        """
        通过id获取章节范围，返回章节结束位置的id
        如果id不是标题则报错返回空值
        """
        id = int(id)  # 转换为整数
        if not self.check_id_is_title(id):
            print(f"Error: id {id} 对应的章节不是标题")
            return None
        chapters = self.data["chapters"]
        current_type = None
        found = False
        for i, chapter in enumerate(chapters):
            if chapter["id"] == id:
                current_type = chapter["type"]
                found = True
                continue
            if found and chapter["type"] == current_type:
                return chapter["id"] - 1
        return chapters[-1]["id"]

    def get_previous_chapter_start_from_id(self, id):
        """
        通过章节id获取上一章节的起始位置id
        如果id不是标题则报错返回空值
        """
        id = int(id)  # 转换为整数
        if not self.check_id_is_title(id):
            print(f"Error: id {id} 对应的章节不是标题")
            return None
        chapters = self.data["chapters"]
        # 首先找到当前章节在列表中的下标
        current_index = None
        for i, chapter in enumerate(chapters):
            if chapter["id"] == id:
                current_index = i
                break
        if current_index is None:
            return None
        current_type = chapters[current_index]["type"]
        # 倒序遍历当前章节之前的所有章节
        for i in range(current_index - 1, -1, -1):
            # 找到与当前章节类型相同的章节即认为是上一章节的起始
            if chapters[i]["type"] == current_type:
                return chapters[i]["id"]
        # 如果未找到，则返回第一章节的 id
        return chapters[0]["id"]
    
    def get_id_from_chapter_name(self, chapter_name):
        """
        通过章节名获取章节id
        """
        chapters = self.data["chapters"]
        for chapter in chapters:
            if chapter["original-text"] == chapter_name:
                return chapter["id"]
        return None
    
    def get_chapter_name_from_id(self, id):
        """
        通过章节id获取章节名
        """
        chapters = self.data["chapters"]
        for chapter in chapters:
            if chapter["id"] == id:
                return chapter["original-text"]
        return None
    
    def get_book_name(self):
        """
        获取书名
        """
        return self.data.get("title", "")
    
    def get_title_chapter_list(self):
        """
        获取所有标题章节的列表
        """
        chapters = self.data["chapters"]
        title_chapters = []
        for chapter in chapters:
            if chapter["type"].startswith("title"):
                title_chapters.append(chapter["original-text"])
        return title_chapters

    def get_title_chapters_with_status_list(self,target_state):
        """
        获取所有标题章节的列表和状态
        """
        chapters = self.data["chapters"]
        title_chapters = []
        now_chapter = None
        status= target_state
        for chapter in chapters:
            if chapter["state"] != target_state:
                status = "unfinished"
            if chapter["type"].startswith("title"):
                if now_chapter is not None:
                    title_chapters.append({"title":now_chapter,"status":status})
                
                now_chapter = chapter["original-text"]
                status= target_state
        if now_chapter is not None:
            title_chapters.append({"title": now_chapter, "status": status})
        
        return title_chapters

    def export_translatefile(self, start_id, end_id):
        """
        导出翻译文件为适合用户阅读的文本。
        接受 start_id 和 end_id（章节的 id，而非列表下标），导出内容包括 title、description，
        以及从 start_id 到 end_id 的 original-text 和 translation-text，格式参考原实现。
        """
        import os
        novel_title = self.data.get("title", "ExportedNovel")
        description = self.data.get("description", "")
        chapters = self.data.get("chapters", [])
        
        # 根据章节 id 找到在列表中的索引
        start_index = next((i for i, chapter in enumerate(chapters) if chapter["id"] == int(start_id)), None)
        end_index = next((i for i, chapter in enumerate(chapters) if chapter["id"] == int(end_id)), None)
        if start_index is None or end_index is None:
            print("Error: 无效的 start_id 或 end_id")
            return None
        
        selected_chapters = chapters[start_index:end_index+1]
        lines = []
        # 添加标题和描述
        lines.append(novel_title)
        lines.append("")
        if description:
            lines.append(description)
            lines.append("")
        # 添加章节内容
        for chapter in selected_chapters:
            orig = chapter.get("original-text", "")
            trans = chapter.get("translation-text", "")
            lines.append(orig)
            lines.append(trans)
            if chapter.get("type", "").startswith("title"):
                lines.append("")
                lines.append("")
            else:
                lines.append("")
        text = "\n".join(lines)
        folder = os.path.dirname(self.translatefile_path)
        output_path = os.path.join(folder, f"{novel_title}.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return output_path
        
if __name__ == "__main__":
    #test
    translatefile_path = "对反派千金发动百合攻势后，她却当真了，还把我收为宠物_project/TranslateFile.json"
    efo = TranslateFile(translatefile_path)
    
    # print(efo.get_chapter_end_from_id(1))
    
    # 调试输出 title_chapters
    # title_chapters = efo.get_title_chapters_with_status_list("f_trans_finished")
    # print("调试输出 title_chapters:", title_chapters)
    efo.export_translatefile(1, 80)
