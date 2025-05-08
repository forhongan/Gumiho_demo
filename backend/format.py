# 这里定义了将不同格式的原文件整理为标准格式的函数
import json
import yaml
import os
import re
from TranslateFile import TranslateFile
# #-------------------待完成-------------------------
#     #设计一些自动检测文章结构的方法,将结构的关键数据写入config传递给主格式化文件
#     #设计与用户交互的方法经由用户提示确定文件格式


#-----------------------目录提取函数-----------------------
def create_table_of_content(directory):
    """
    在指定文件夹中创建 table_of_content.json 文件,初始内容为空目录列表.
    
    参数:
        directory (str): 文件夹路径
    """
    toc_path = os.path.join(directory, "table_of_content.json")
    with open(toc_path, 'w', encoding='utf-8') as f:
        json.dump({"chapters": []}, f, ensure_ascii=False, indent=2)
    return toc_path

def file_update_table_of_content(file_path, json_path):
    """
    从指定文件中提取章节目录并更新指定的 JSON 文件(忽略重复章节）。
    
    参数:
        file_path (str): 包含目录信息的文件路径
        json_path (str): 指向 table_of_content.json 文件的完整路径
    """
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content_str = f.read()
    
    return update_table_of_content(content_str, json_path)

def update_table_of_content(content_str, json_path):
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
    
    # return data

#-----------------------人名，专有名词对提取函数-----------------------
def create_trans_compare_table(directory):
    """
    在指定文件夹中创建 Proper_nouns_table.json 文件，初始内容为空的译名对列表。
    
    参数:
        directory (str): 文件夹路径
    """
    table_path = os.path.join(directory, "Proper_nouns_table.json")
    with open(table_path, 'w', encoding='utf-8') as f:
        json.dump({"translations_table": [],"longterm_describe_table":[]}, f, ensure_ascii=False, indent=2)
    return table_path

def file_update_trans_compare(content_str, file_path, json_path):
    """
    从指定文件中提取译名对并更新指定的 JSON 文件。
    
    参数:
        file_path (str): 包含译名对的文件路径
        json_path (str): 指向 table_of_content.json 文件的完整路径
    """
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content_str = f.read()
    
    return update_trans_compare(content_str, json_path)

def update_trans_compare(content_str, delimiter, json_path):
    """
    从输入字符串中提取译名对并更新指定的 JSON 文件。
    每行包含且仅包含一个原名 和 译名对（通过 delimiter 分割, 忽略空行），
    同时为每个记录创建空的描述字段。如果原名对已存在，则忽略。
    
    参数:
        content_str (str): 包含译名对信息的字符串（每行为一条记录）
        delimiter (str): 分割原名和译名的字符串
        json_path (str): 指向 trans_compare_table.json 文件的完整路径
    """
    lines = [line.strip() for line in content_str.strip().splitlines() if line.strip()]
    
    # 读取已有的译名对
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"translations": []}
    
    # 建立已存在原名的集合，避免重复添加
    existing_origins = {item["原名"] for item in data.get("translations", [])}
    
    for line in lines:
        parts = [part.strip() for part in line.split(delimiter)]
        if len(parts) == 2 and parts[0] and parts[1]:
            if parts[0] not in existing_origins:
                data["translations"].append({
                    "原名": parts[0],
                    "译名": parts[1],
                    "描述": ""
                })
                existing_origins.add(parts[0])
    
    # 写入更新后的译名对数据到 JSON 文件
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return data

#-----------------------手动更新记录更新函数-----------------------
def update_trans_record(json_path, origin, translation, description):
    """
    接受json路径、原名、译名、描述，更新或新建记录:
        - 记录存在且完全相同，返回“相同记录已存在”
        - 若记录存在但译名或描述不同，更新相应字段并返回更新信息
        - 若记录不存在，则添加新记录并返回“新建记录xxx”
    """
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"translations": []}
    
    found = False
    messages = []
    for record in data["translations"]:
        if record["原名"] == origin:
            found = True
            if record["译名"] == translation and record["描述"] == description:
                return "相同记录已存在"
            if record["译名"] != translation:
                record["译名"] = translation
                messages.append(f"更新{origin}译名为{translation}")
            if record["描述"] != description:
                record["描述"] = description
                messages.append(f"更新{origin}描述为{description}")
            break

    if not found:
        data["translations"].append({
            "原名": origin,
            "译名": translation,
            "描述": description
        })
        messages.append(f"新建记录{origin}")
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return "".join(messages)

def create_f_record(directory):
    """
    在指定文件夹中创建 f_record.json 文件,初始内容为空字典。
    
    参数:
        directory (str): 文件夹路径
    返回:
        str: f_record.json 文件的完整路径
    """
    f_record_path = os.path.join(directory, "f_record.json")
    with open(f_record_path, 'w', encoding='utf-8') as f:
        json.dump({"Long_term_summary_table":[], "record":[] }, f, ensure_ascii=False, indent=2)
    return f_record_path


def create_p_record(directory):
    """
    在指定文件夹中创建 p_record.json 文件,初始内容为空字典。
    
    参数:
        directory (str): 文件夹路径
    返回:
        str: p_record.json 文件的完整路径
    """
    p_record_path = os.path.join(directory, "p_record.json")
    with open(p_record_path, 'w', encoding='utf-8') as f:
        json.dump({"Long_term_summary_table":[], "record":[] }, f, ensure_ascii=False, indent=2)
    return p_record_path

#-----------------------翻译工程文件初始化函数-----------------------
def create_translatefile(directory):
    """
    在指定文件夹中创建 TranslateFile.json 文件,初始内容为空字典。
    
    参数:
        directory (str): 文件夹路径
    返回:
        str: TranslateFile.json 文件的完整路径
    """
    translatefile_path = os.path.join(directory, "TranslateFile.json")
    with open(translatefile_path, 'w', encoding='utf-8') as f:
        json.dump({}, f, ensure_ascii=False, indent=2)
    return translatefile_path

def build_Gumiho_imformation(config_path,status):
    """
    从config文件中读取信息，组成Gumiho-翻译信息
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    return f"""BY Gumiho-translate-system
&Deepseek-R1-full
checker: {config_data["Translater"]}
"""



# 对接"轻小说机翻机器人"网站的的自动结构化类
class LightNovelRobotJpFormat:
    """
        将来自"轻小说机翻机器人"的轻小说文本转换为标准格式JSON文件
        
        参数:
            project_path (str): 项目文件夹路径
            name (str): 原文件名
            orininal_file_path (str): 原文件路径
            toc_path (str): 目录文件路径
            destination_path (str): 目的文件路径
    """
    def __init__(self,project_path):
        config_path=os.path.join(project_path, "config.yml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        self.project_path = project_path
        self.name = config_data["file name"]
        self.orininal_file_path = os.path.join(project_path, "sourcefile", self.name)
        self.orininal_toc_path = os.path.join(project_path, "sourcefile", "toc.txt")
        self.toc_path = os.path.join(project_path, "sourcefile", "table_of_content.json")
        # self.toc_path = create_table_of_content(project_path) if config_data["paragraphed"] else None
        self.destination_path = os.path.join(project_path, "TranslateFile.json")
        
    def lurj_project_Initialization(self):
        """
        初始化项目文件夹，创建必要的文件和目录。
        """
        # 创建目录文件
        self.lnrj_create_toc()
        self.lnrj_file_update_toc(self.orininal_toc_path)
        # 创建名词字典
        create_trans_compare_table(self.project_path+"/sourcefile")
        # 创建翻译记录文件
        create_f_record(self.project_path)
        create_p_record(self.project_path)
        # 创建翻译文件
        self.lnrj_format()  # 使用默认的 self.orininal_file_path
        print(f"项目初始化完成，文件保存在 {self.project_path}")
        
    def lnrj_format(self, original_file=None, toc_file=None, destination_file=None):
        
        original_file = original_file if original_file else self.orininal_file_path
        toc_file = toc_file if toc_file else self.toc_path
        destination_file = destination_file if destination_file else self.destination_path
        
        # 读取目录文件，获取章节标题集合
        with open(toc_file, 'r', encoding='utf-8') as f:
            dir_data = json.load(f)
        chapters_set = set(dir_data.get("chapters", []))
        
        # 读取原文件，忽略空行
        with open(original_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            raise ValueError("原文件为空")
        
        # 第一行为title
        title = lines[0]
        # 收集描述：从第二行开始，仅移除每行行首的'#'和空格后再判断是否匹配章节标题
        description_lines = []
        i = 1
        while i < len(lines):
            # 仅移除 '#' 和空格
            line_clean = lines[i].lstrip('# ').strip()
            if line_clean in chapters_set:
                break
            description_lines.append(lines[i])
            i += 1
        description = "\n".join(description_lines)
        
        # 从第一个匹配的章节标题开始，将剩余行依序生成章节对象
        chapters_list = []
        chapter_id = 1
        for j in range(i, len(lines)):
            line = lines[j]
            # 清理行首的 '#' 和空格再进行匹配
            clean_line = line.lstrip('# ').strip()
            type_field = "title_lv1" if clean_line in chapters_set else "main_text"
            chapters_list.append({
                "id": chapter_id,
                "original-text": line,
                "translation-text": "",
                "type": type_field,
                "state": "f_trans_unfinished"
            })
            chapter_id += 1

        output_json = {
            "title": title,
            "description": description,
            "chapters": chapters_list
        }
        
        # 写入目的文件
        with open(destination_file, 'w', encoding='utf-8') as f:
            json.dump(output_json, f, ensure_ascii=False, indent=2)
        
        # return destination_file

    def lnrj_create_toc(self, project_path=None):
        """
        在指定文件夹中创建 toc.txt 文件, 
        从 self.orininal_file_path 中提取以 '#' 开头的行作为章节标题.
        """
        project_path = project_path if project_path else self.project_path
        toc_path = os.path.join(project_path, "sourcefile", "toc.txt")
        
        chapters = []
        if os.path.exists(self.orininal_file_path):
            with open(self.orininal_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        title = stripped.lstrip("#").strip()
                        if title:
                            chapters.append(title)
        # 将章节标题按换行写入 toc.txt
        with open(toc_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(chapters))
    
    def lnrj_update_toc(self, content_str, toc_path=None):
        toc_path = toc_path if toc_path else self.toc_path
        # 原有规则已注释掉:
        # chapters_extracted = [chap.strip() for chap in re.split(r'\n\s*\n|\r?\n', content_str) if chap.strip()]
        # processed_chapters = [re.sub(r'^[\s!"#$%&\'()*+,\-./:;<=>?@\[\]^_`{|}~]+', '', chap) for chap in chapters_extracted]
        
        # 采用简单规则：每个独立非空行视作一个标题
        chapters_extracted = [line.strip() for line in content_str.splitlines() if line.strip()]
        
        # 读取已有目录数据
        if os.path.exists(toc_path):
            with open(toc_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"chapters": []}
        
        existing_chapters = set(data.get("chapters", []))
        for chap in chapters_extracted:
            if chap not in existing_chapters:
                data["chapters"].append(chap)
                existing_chapters.add(chap)
        
        with open(toc_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # return data

    def lnrj_file_update_toc(self, file_path, toc_path=None):
        """
        从指定文件中提取章节目录并更新指定的 JSON 文件（忽略重复章节）。
        """
        toc_path = toc_path if toc_path else self.toc_path
        with open(file_path, 'r', encoding='utf-8') as f:
            content_str = f.read()
        self.lnrj_update_toc(content_str, toc_path)
        
    def lnrj_refilled_novel(self, start_idx, end_chapter_idx, original_file_path=None, translated_file_path=None, original_save=False, novel_status="f_trans_finished"):

        # 处理文件路径
        original_file_path = original_file_path if original_file_path else self.orininal_file_path
        translated_file_path = translated_file_path if translated_file_path else self.destination_path

        self.TranslateFile=TranslateFile(self.translated_file_path)
        
        # 读取原文
        with open(original_file_path, 'r', encoding='utf-8') as f:
            original_lines = [line.rstrip('\n') for line in f]

        # 读取翻译数据
        with open(translated_file_path, 'r', encoding='utf-8') as f:
            translated_data = json.load(f)
        
        # # 收集所有章节标题
        # chapter_titles = set()
        # for item in translated_data["chapters"]:
        #     if item["type"].startswith("title"):
        #         chapter_titles.add(item["original-text"].strip())

        # # 定位章节范围
        # # 步骤1：找到所有章节起始行
        # chapter_start_lines = []
        # for i, line in enumerate(original_lines):
        #     if line.strip() in chapter_titles:
        #         chapter_start_lines.append(i)
        
        # # 步骤2：定位起始和结束章节
        # try:
        #     start_idx = next(i for i in chapter_start_lines if original_lines[i].strip() == start_chapter.strip())
        #     end_chapter_idx = next(i for i in chapter_start_lines if original_lines[i].strip() == end_chapter.strip())
        # except StopIteration:
        #     raise ValueError("章节定位失败")

        # # 步骤3：确定结束位置
        # end_idx = len(original_lines) - 1  # 默认文件结尾
        # current_chapter_index = chapter_start_lines.index(end_chapter_idx)
        # if current_chapter_index + 1 < len(chapter_start_lines):
        #     end_idx = chapter_start_lines[current_chapter_index + 1] - 1

        end_idx= self.TranslateFile.get_chapter_end_from_id(end_chapter_idx)
        # 提取处理范围内的内容（保留原始空行）
        output = [line + '\n' for line in original_lines[start_idx:end_idx+1]]
        
        # 创建翻译字典（注意处理换行符）
        trans_dict = {}
        for item in translated_data["chapters"]:
            orig = item["original-text"].strip()
            trans = item["translation-text"]
            trans_dict[orig] = trans

        # 执行回填操作
        i = 0
        while i < len(output):
            raw_line = output[i].rstrip('\n').strip()
            if not raw_line:  # 跳过空行
                i += 1
                continue
                
            if raw_line in trans_dict:
                # 获取翻译文本
                translated = trans_dict[raw_line] + '\n'
                
                if original_save:
                    # 插入到下一行（覆盖空行或插入新行）
                    if i+1 < len(output) and output[i+1].strip() == '':
                        output[i+1] = translated
                    else:
                        output.insert(i+1, translated)
                    i += 2
                else:
                    # 替换当前行并删除后续空行
                    output[i] = translated
                    if i+1 < len(output) and output[i+1].strip() == '':
                        del output[i+1]
                    i += 1
            else:
                print(f"警告：未找到翻译 - {raw_line}")
                i += 1

        # 生成文件名
        base_name = f'Gumiho-{translated_data["title"].strip()} ({start_idx})-({end_idx})-'
        status = "初译完成" if novel_status == "f_trans_finished" else "校对完成"
        file_name = base_name + status + '.txt'

        # 确定保存路径
        if self.project_path:
            save_dir = os.path.join(self.project_path, 'result')
            os.makedirs(save_dir, exist_ok=True)
        else:
            save_dir = os.path.dirname(original_file_path)
        
        # 写入文件
        save_path = os.path.join(save_dir, file_name)
        with open(save_path, 'w', encoding='utf-8') as f:
            f.writelines(output)


if __name__ == "__main__":
    # 测试目录提取函数
    # toc_path = create_table_of_content("Example_project\\sourcefile")
    # print(f"创建目录文件: {toc_path}")
    # data = file_update_table_of_content("Example_project\\sourcefile\\toc.txt", toc_path)
    # print(f"更新目录文件: {data}")
    
    # 测试译名对提取函数
    # table_path =
    #create_f_record("少女所不希望的英雄史诗_project")
    #create_p_record("少女所不希望的英雄史诗_project")
    work1=LightNovelRobotJpFormat("对反派千金发动百合攻势后，她却当真了，还把我收为宠物_project")
    work1.lurj_project_Initialization()
    # work1.lnrj_create_toc()
    # work1.lnrj_file_update_toc("Example_project/sourcefile/toc.txt")
    # work1.lnrj_format()
    # work1.lnrj_refilled_novel("頭のおかしな少女","旅立ちと屋敷","少女所不希望的英雄史诗_project/sourcefile/(NEW)jp.少女所不期望的英雄史诗.txt","少女所不希望的英雄史诗_project/(NEW)jp.少女所不期望的英雄史诗.json")