# 这里定义了将不同格式的原文件整理为标准格式的函数
import json
import os
import re
#-------------------待完成-------------------------
    #设计一些自动检测文章结构的方法,将结构的关键数据写入config传递给主格式化文件
    #设计与用户交互的方法经由用户提示确定文件格式
def automatic_structure_detection(file_path):
    
    directory_import(dir_text,config)
    
    noun_dictionary_import(noun_dic_text,config)
    
    convert_novel_to_json(file_path,config)

#-------------------待完成-------------------------
#定义从文本取得外部目录的方式,保存到path指向的.json文件中
def directory_import(dir_text,path):
    
#-------------------待完成-------------------------
#定义从文本中取得专有名词名词词典的方式,保存到config中
def noun_dictionary_import(noun_dic_text,config):

#-------------------待完成-------------------------
#检查本次待译内容(含记录,概括中的内容中是否包含专有名词字典中的内容,返回包含的字典对)
def check_noun_in_content(content,config):

#-------------------待完成-------------------------
# 将类markdown格式的文本转换为JSON文件    
def convert_novel_to_json(file_path,config):
    #-------------------待重写-------------------------
    #需要适配更多样的格式
    """
    将特定格式的轻小说文本转换为JSON文件
    
    参数:
        file_path (str): 输入的.txt文件路径
        
    返回:
        str: 生成的JSON文件路径
    """
    # 读取并预处理文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    chapters = []
    current_chapter = None
    i = 0

    while i < len(lines):
        line = lines[i]
        
        if line.startswith('#'):
            # 解析章节标题
            if i+1 < len(lines) and lines[i+1].startswith('#'):
                # 双行标题结构
                jp_title = line[1:].strip()
                cn_title = lines[i+1][1:].strip()
                current_chapter = {
                    'original_title': jp_title,
                    'translated_title': cn_title,
                    'content': [],
                    'chapter_summary': ''
                }
                chapters.append(current_chapter)
                i += 2  # 跳过两行标题
            else:
                # 单行标题结构（非常规情况）用于处理高级目录下没有正文的情况
                current_chapter = {
                    'original_title': line[1:].strip(),
                    'translated_title': '',
                    'content': []
                }
                chapters.append(current_chapter)
                i += 1
            
            # 收集后续内容
            content_lines = []
            while i < len(lines) and not lines[i].startswith('#'):
                content_lines.append(lines[i])
                i += 1
            
            # 处理双语内容对
            for j in range(0, len(content_lines), 2):
                if j+1 < len(content_lines):
                    current_chapter['content'].append({
                        'original text': content_lines[j],
                        'translated text': content_lines[j+1]
                    })
        else:
            # 跳过非章节内容
            i += 1

    # 构建输出路径
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join(os.path.dirname(file_path), f"{base_name}.json")
    output_path2 = os.path.join(os.path.dirname(file_path), f"{base_name}_校对工程.json")
    # 写入JSON文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({'chapters': chapters}, f, ensure_ascii=False, indent=2)
    with open(output_path2, 'w', encoding='utf-8') as f:
        json.dump({'chapters': chapters}, f, ensure_ascii=False, indent=2)
    
    return output_path2

class NovelDirectoryHandler:
    def create_directory(self, directory):
        """
        在指定文件夹中创建 table_of_content.json 文件,初始内容为空目录列表.
        
        参数:
            directory (str): 文件夹路径
        """
        toc_path = os.path.join(directory, "table_of_content.json")
        with open(toc_path, 'w', encoding='utf-8') as f:
            json.dump({"chapters": []}, f, ensure_ascii=False, indent=2)
        return toc_path

    def update_directory(self, content_str, json_path):
        """
        从输入字符串中提取章节目录并更新指定的 JSON 文件(忽略重复章节）。
        章节通过回车或空行进行分隔.
        
        参数:
            content_str (str): 包含目录信息的字符串
            json_path (str): 指向 table_of_content.json 文件的完整路径
        """
        # 使用正则表达式分割字符串,以匹配单个换行及空行情况
        chapters_extracted = [chap.strip() for chap in re.split(r'\n\s*\n|\r?\n', content_str) if chap.strip()]
        
        # 读取已有的目录
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"chapters": []}
        
        # 更新目录列表, 如果章节标题已存在则忽略
        existing_chapters = set(data.get("chapters", []))
        for chap in chapters_extracted:
            if chap not in existing_chapters:
                data["chapters"].append(chap)
                existing_chapters.add(chap)
        
        # 写入更新后的数据到 JSON 文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return data