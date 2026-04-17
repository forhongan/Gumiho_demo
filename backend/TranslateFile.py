import json
import os
import re

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
    
    def check_status(self, start, end, status):
        """
        检查指定id范围内的章节状态是否为指定状态
        """
        start = int(start)  # 转换为整数
        end = int(end)  # 转换为整数
        data = self.read_translatefile()
        for chapter in data["chapters"]:
            if start <= chapter["id"] <= end:
                if chapter.get("state", "") != status:
                    return False
        return True

    def get_chapter_end_from_id(self, id):
        """
        通过起始id(标题句id)获取章节范围，返回章节结束位置的id
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
        通过标题id获取上一章的起始位置id(上一章标题的id)
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
    
    def get_paragraph_by_title(self, title):
        """
        通过章节名获取该章节的内容
        """
        start_id = self.get_id_from_chapter_name(title)
        paragraph_text = []
        start_recording = False
        for chapter in self.data["chapters"]:
            if start_recording:
                if chapter["type"] != 'main_text' and chapter["id"] != start_id:
                    break
                paragraph_text.append(chapter)
            if not start_recording and chapter["id"] == start_id:
                start_recording = True
        return paragraph_text
        
    
    def get_chapter_name_from_id(self, id):
        """
        通过章节id获取章节名
        """
        chapters = self.data["chapters"]
        for chapter in chapters:
            if chapter["id"] == id:
                return chapter["original-text"]
        return None
    
    def get_idx_from_id(self, id):
        """
        通过章节id获取章节在列表中的下标
        """
        chapters = self.data["chapters"]
        for i, chapter in enumerate(chapters):
            if chapter["id"] == id:
                return i
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

    def get_title_chapters_with_status_list(self,target_state="f_trans_finished"):
        """
        获取所有标题章节的列表和状态。

        兼容两类入参：
        - 旧版：传入具体 state（如 f_trans_finished），用于“仅导出已翻译”的语义。
        - 新版：传入 scope：
            - all：返回全部章节，并为每章计算 status（translated/unfinished）
            - translated_only：仅返回已翻译章节

        “已翻译”判定：章节范围内的所有条目 state 均属于已翻译集合。
        """
        chapters = self.data.get("chapters", [])

        translated_states = {
            "f_trans_finished",
            "proofreading_finished",
            "HT_PNTing",
            "HT_PNTed",
        }

        scope = (target_state or "").strip()
        # 兼容旧行为：当传入的是具体 state（例如 f_trans_finished），按“仅已翻译”处理
        if scope not in {"all", "translated_only"}:
            scope = "translated_only"

        # 找到所有标题索引
        title_indices = [
            i for i, ch in enumerate(chapters)
            if isinstance(ch.get("type"), str) and ch.get("type", "").startswith("title")
        ]

        title_chapters = []
        for idx_pos, title_idx in enumerate(title_indices):
            next_title_idx = title_indices[idx_pos + 1] if idx_pos + 1 < len(title_indices) else len(chapters)
            segment = chapters[title_idx:next_title_idx]

            is_translated = True
            for seg_item in segment:
                state = seg_item.get("state")
                if state not in translated_states:
                    is_translated = False
                    break

            status = "translated" if is_translated else "unfinished"
            title_text = chapters[title_idx].get("original-text", "")
            title_id = chapters[title_idx].get("id")
            title_chapters.append({"id": title_id, "title": title_text, "status": status})

        if scope == "translated_only":
            return [c for c in title_chapters if c.get("status") == "translated"]
        return title_chapters

    def export_translatefile(self, start_id, end_id, orig_txt=True):
        """
        导出翻译文件为适合用户阅读的文本(txt格式)。
        接受 start_id 和 end_id（章节的 id，而非列表下标），导出内容包括 title、description，
        以及从 start_id 到 end_id 的 original-text 和 translation-text，
        保留与原文文件相同的空行格式。
        """
        import glob
        
        novel_title = self.data.get("title", "ExportedNovel")
        description = self.data.get("description", "")
        chapters = self.data.get("chapters", [])

        def _safe_filename(name: str) -> str:
            name = (name or "").strip()
            # Windows 文件名非法字符: <>:"/\\|?*
            name = re.sub(r'[<>:"/\\|?*]+', '_', name)
            # 末尾不能是空格或点
            name = name.rstrip(" .")
            return name or "ExportedNovel"
        
        # 根据章节 id 找到在列表中的索引
        start_index = next((i for i, chapter in enumerate(chapters) if chapter["id"] == int(start_id)), None)
        end_index = next((i for i, chapter in enumerate(chapters) if chapter["id"] == int(end_id)), None)
        if start_index is None or end_index is None:
            print("Error: 无效的 start_id 或 end_id")
            return None
        
        # 寻找原文文件
        folder = os.path.dirname(self.translatefile_path)
        source_folder = os.path.join(folder, "sourcefile")
        source_files = glob.glob(os.path.join(source_folder, "*.txt"))
        
        # 保存原文文件的所有非空行及其前面的空行数
        source_lines = []
        source_line_index = 0  # 用于顺序匹配的索引
        
        if source_files:
            source_file = source_files[0]  # 取第一个找到的源文件
            try:
                with open(source_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    
                # 分析原文中的空行
                blank_count = 0
                for line in lines:
                    line = line.strip()
                    if not line:  # 空行
                        blank_count += 1
                    else:  # 非空行
                        source_lines.append({"text": line, "blank_lines": blank_count})
                        blank_count = 0
            except Exception as e:
                print(f"读取源文件时出错: {e}")
        
        selected_chapters = chapters[start_index:end_index+1]
        output_lines = []
        
        # 添加标题和描述
        output_lines.append(novel_title)
        output_lines.append("")
        if description:
            output_lines.append(description)
            output_lines.append("")
        
        # 添加章节内容
        prev_chapter = None
        for chapter in selected_chapters:
            orig = chapter.get("original-text", "")
            trans = chapter.get("translation-text", "")
            
            # 根据原文中的空行添加空行
            if prev_chapter is not None:
                # 获取当前原文前应有的空行数（顺序匹配）
                blank_count = 1  # 默认1个空行
                
                # 从上次匹配位置开始，寻找匹配的原文
                if source_lines:
                    found = False
                    start_search_idx = source_line_index
                    
                    # 在剩余的源文件中查找当前句子
                    for i in range(start_search_idx, len(source_lines)):
                        if source_lines[i]["text"] == orig:
                            blank_count = source_lines[i]["blank_lines"]
                            source_line_index = i + 1  # 更新下次查找的起始位置
                            found = True
                            break
                
                # 如果是标题，确保至少有2个空行
                if chapter.get("type", "").startswith("title"):
                    blank_count = max(blank_count, 2)
                
                # 添加空行
                for _ in range(blank_count):
                    output_lines.append("")
            
            # 添加原文和译文
            if(orig_txt):
                output_lines.append(orig)
            output_lines.append(trans)
            
            prev_chapter = chapter
        
        # 写入文件
        text = "\n".join(output_lines)
        result_dir = os.path.join(folder, "result")
        os.makedirs(result_dir, exist_ok=True)
        output_path = os.path.join(result_dir, f"{_safe_filename(novel_title)}.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return output_path

    def get_texts_in_range(self, start_id, end_id, include_empty=False):
        """
        获取指定id范围内的原文/译文列表
        返回: list[dict] => {"id","original","translation","type","state"}
        include_empty=False 时会跳过原文和译文都为空的条目
        """
        start_id = int(start_id)
        end_id = int(end_id)
        if start_id > end_id:
            start_id, end_id = end_id, start_id

        results = []
        for chapter in self.data.get("chapters", []):
            cid = int(chapter.get("id", -1))
            if start_id <= cid <= end_id:
                original = chapter.get("original-text", "")
                translation = chapter.get("translation-text", "")
                if not include_empty and not (original or translation):
                    continue
                results.append({
                    "id": cid,
                    "original": original,
                    "translation": translation,
                    "type": chapter.get("type", ""),
                    "state": chapter.get("state", "")
                })
        return results
    
    def change_status_in_range(self, start_id, end_id, new_status):
        """
        更改指定id范围内的章节状态为 new_status
        """
        start_id = int(start_id)  # 转换为整数
        end_id = int(end_id)  # 转换为整数
        data = self.read_translatefile()
        for chapter in data["chapters"]:
            if start_id <= chapter["id"] <= end_id:
                chapter["state"] = new_status
        self.write_translatefile(data)
        
if __name__ == "__main__":
    #test
    translatefile_path = "殺されて当然と少女は言った。_project/TranslateFile.json"
    efo = TranslateFile(translatefile_path)
    
    # efo.change_status_in_range(1, 15, "proofreading_finished")
    efo.change_status_in_range(39, 78, "f_trans_unfinished")
    
    # # print(efo.get_chapter_end_from_id(1))
    
    # # 调试输出 title_chapters
    # # title_chapters = efo.get_title_chapters_with_status_list("f_trans_finished")
    # # print("调试输出 title_chapters:", title_chapters)
    # efo.export_translatefile(1, 80)
