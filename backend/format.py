# 这里定义了将不同格式的原文件整理为标准格式的函数
import json
import yaml
import os
import re
from TranslateFile import TranslateFile
from Config import Config
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
        json.dump({"translation_table": [],"longterm_describe_table":[]}, f, ensure_ascii=False, indent=2)
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



# 对接"轻小说机翻机器人"网站的的自动结构化类
class LightNovelRobotJpFormat:
    """
        将来自"轻小说机翻机器人"的轻小说文本转换为标准格式JSON文件
        
        参数:
            project_path (str): 项目文件夹路径
            name (str): 原文件名
            original_file_path (str): 原文件路径
            toc_path (str): 目录文件路径
            destination_path (str): 目的文件路径
    """
    def __init__(self,project_path):
        config_path=os.path.join(project_path, "config.yml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        self.project_path = project_path
        self.name = config_data["file name"]
        self.paragraph_aggregation_mode = config_data["paragraph aggregation mode"] if "paragraph aggregation mode" in config_data else False
        self.double_blank_line = config_data["double blank line"] if "double blank line" in config_data else False
        self.original_file_path = os.path.join(project_path, "sourcefile", self.name)
        self.original_toc_path = os.path.join(project_path, "sourcefile", "toc.txt")
        self.toc_path = os.path.join(project_path, "sourcefile", "table_of_content.json")
        # self.toc_path = create_table_of_content(project_path) if config_data["paragraphed"] else None
        self.destination_path = os.path.join(project_path, "TranslateFile.json")
        
    def lurj_project_Initialization(self):
        """
        初始化项目文件夹，创建必要的文件和目录。
        """
        # 创建目录文件
        self.lnrj_create_toc()
        self.lnrj_file_update_toc(self.original_toc_path)
        # 创建名词字典
        create_trans_compare_table(self.project_path+"/sourcefile")
        # 创建翻译记录文件
        create_f_record(self.project_path)
        create_p_record(self.project_path)
        # 创建翻译文件
        self.lnrj_format()  # 使用默认的 self.original_file_path
        print(f"项目初始化完成，文件保存在 {self.project_path}")
        
    def lnrj_format(self, original_file=None, toc_file=None, destination_file=None):
        
        original_file = original_file if original_file else self.original_file_path
        toc_file = toc_file if toc_file else self.toc_path
        destination_file = destination_file if destination_file else self.destination_path
        
        # 读取目录文件，获取章节标题集合
        with open(toc_file, 'r', encoding='utf-8') as f:
            dir_data = json.load(f)
        chapters_set = set(dir_data.get("chapters", []))
        
        # 读取原文件，保留空行（用于段落聚合）
        with open(original_file, 'r', encoding='utf-8') as f:
            # 将仅包含空格的行也视作空行（转换为空字符串），保留其他行的原始内容（去除末尾换行符）
            raw_lines = [line.rstrip('\n') if line.rstrip('\n').strip() != '' else '' for line in f]
        
        if self.paragraph_aggregation_mode:
            # 段落聚合模式，将空行而不是换行视为分割
            paragraphs = []
            cur = []
            closers = ('」', '”', '』')
            openers = ('「', '“', '『')
            empty_count = 0

            for idx, line in enumerate(raw_lines):
                if line.strip() == '':
                    empty_count += 1
                    # 若未启用双空行模式，单个空行为段结束
                    if not self.double_blank_line:
                        if cur:
                            paragraphs.append(''.join(l.strip() for l in cur))
                            cur = []
                        empty_count = 0
                    else:
                        # 启用双空行模式时，只有遇到两个及以上连续空行才视为段结束
                        if empty_count >= 2:
                            if cur:
                                paragraphs.append(''.join(l.strip() for l in cur))
                                cur = []
                            empty_count = 0
                    continue

                # 非空行
                empty_count = 0
                # 先检测是否为标题行（去除行首的 '#' 和空格后与 chapters_set 比对）
                stripped = line.strip()
                clean_for_title = stripped.lstrip('# ').strip()
                if clean_for_title in chapters_set:
                    # 若当前已在收集段落，先将其作为独立段落压出
                    if cur:
                        paragraphs.append(''.join(l.strip() for l in cur))
                        cur = []
                    # 将标题行作为独立段落（保留原始的 '#' 形式）
                    paragraphs.append(stripped)
                    continue

                cur.append(line)
                # lookahead 查找下一个非空行（若存在）
                next_line = ''
                j = idx + 1
                while j < len(raw_lines):
                    if raw_lines[j].strip() != '':
                        next_line = raw_lines[j]
                        break
                    j += 1

                # 如果当前行以闭合引号结尾，且下一行以开引号开头，则也视为段结束（此规则不受双空行模式限制）
                if cur and line.strip().endswith(closers) and next_line.lstrip().startswith(openers):
                    paragraphs.append(''.join(l.strip() for l in cur))
                    cur = []

            if cur:
                paragraphs.append(''.join(l.strip() for l in cur))

            # 最终的“行”列表由段落组成（忽略完全为空的段）
            lines = [p for p in paragraphs if p]
        else:
            # 非段落聚合模式按非空行切分
            lines = [line.strip() for line in raw_lines if line.strip()]
        
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
        从 self.original_file_path 中提取以 '#' 开头的行作为章节标题.
        """
        project_path = project_path if project_path else self.project_path
        toc_path = os.path.join(project_path, "sourcefile", "toc.txt")
        
        chapters = []
        if os.path.exists(self.original_file_path):
            with open(self.original_file_path, 'r', encoding='utf-8') as f:
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
        original_file_path = original_file_path if original_file_path else self.original_file_path
        translated_file_path = translated_file_path if translated_file_path else self.destination_path

        self.TranslateFile=TranslateFile(self.translated_file_path)
        
        # 读取原文
        with open(original_file_path, 'r', encoding='utf-8') as f:
            original_lines = [line.rstrip('\n') for line in f]

        # 读取翻译数据
        with open(translated_file_path, 'r', encoding='utf-8') as f:
            translated_data = json.load(f)

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
    
    def lnrj_normal_txt_rebuild(self, start_idx, end_chapter_idx, translated_file_path=None, novel_status="f_trans_finished", with_original_text_or_not=False):
        """
        将翻译后的JSON文件重新构建为普通文本文件，按章节单元(type)输出。
        规则：标题与描述（若存在），标题与描述之间以一个空行分隔
        参数:
            start_idx, end_chapter_idx: 以章节 id 为范围（包含端点）
            translated_file_path: 翻译 JSON 路径，默认为 self.destination_path
            novel_status: 状态字符串，用于文件名
            with_original_text_or_not: bool，若 True 则在译文上方保留原文
        返回：写入的文件路径。
        """
        translated_file_path = translated_file_path if translated_file_path else self.destination_path

        # 读取翻译 JSON
        if not os.path.exists(translated_file_path):
            raise FileNotFoundError(f"翻译文件未找到: {translated_file_path}")
        with open(translated_file_path, 'r', encoding='utf-8') as f:
            translated_data = json.load(f)

        title = translated_data.get("title", "")
        description = translated_data.get("description", "")
        chapters = translated_data.get("chapters", [])

        # 验证索引
        try:
            s = int(start_idx)
            e = int(end_chapter_idx)
        except Exception:
            raise ValueError("start_idx 和 end_chapter_idx 必须为整数")
        if s > e:
            raise ValueError("start_idx 不能大于 end_chapter_idx")

        # 过滤并按 id 排序出指定 id 范围内的章节（按 id 字段匹配）
        selected = sorted([c for c in chapters if isinstance(c.get("id"), int) and s <= c.get("id") <= e], key=lambda x: x.get("id"))
        if not selected:
            raise ValueError("未找到指定范围的章节")

        output = []
        # 写入翻译信息标签
        get_tag_by_config = Config(config_path=os.path.join(self.project_path, "config.yml"))
        tag = get_tag_by_config.make_translation_info_tags(status='translating')
        if tag:
            output.append(f"{tag}\n\n")
            
        # 写入文件头：标题与描述（若存在），标题与描述之间以一个空行分隔
        if title:
            output.append(title.strip() + '\n')
            output.append('\n')
        if description:
            for line in description.splitlines():
                output.append(line.rstrip() + '\n')
            output.append('\n')

        # Helper: 在闭合符与开启符相邻的情况下插入换行，修复特定情况 '....』『.....','....」『.....','....』「.....'
        # 这是为了修复旧版本生成TranslateFile时出现的错误的补救措施
        def _repair_adjacent_quotes(text):
            if not text:
                return text
            s = str(text)
            # 仅修复三种具体组合，顺序无关，但使用 replace 保证不会误伤其他组合
            s = s.replace('』『', '』\n『')
            s = s.replace('」『', '」\n『')
            s = s.replace('』「', '』\n「')
            return s

        # 逐单元写入：根据 type 区分 title 与 main_text
        for chap in selected:
            chap_type = chap.get("type", "") or ""
            orig = chap.get("original-text", "")
            trans = chap.get("translation-text", "")

            # 标题单元：前空三行，后空一行
            if isinstance(chap_type, str) and chap_type.startswith("title"):
                # 三个空行作为分隔
                output.append('\n' * 3)

                # 如果需要保留原文，先写原文
                if with_original_text_or_not and orig:
                    orig_processed = _repair_adjacent_quotes(orig)
                    for line in str(orig_processed).splitlines():
                        output.append(line.rstrip() + '\n')

                # 写译文（若无译文则写原文）
                write_src = trans if trans else orig
                write_src_processed = _repair_adjacent_quotes(write_src)
                if write_src_processed:
                    for line in str(write_src_processed).splitlines():
                        output.append(line.rstrip() + '\n')
                else:
                    output.append('\n')

                # 标题后空一行
                output.append('\n')

            else:
                # 普通段落：可选保留原文在上方
                if with_original_text_or_not and orig:
                    orig_processed = _repair_adjacent_quotes(orig)
                    for line in str(orig_processed).splitlines():
                        output.append(line.rstrip() + '\n\n')
                # 写译文（若无译文则写原文或空行）
                write_src = trans if trans else orig
                write_src_processed = _repair_adjacent_quotes(write_src)
                if write_src_processed:
                    for line in str(write_src_processed).splitlines():
                        output.append(line.rstrip() + '\n\n')
                else:
                    output.append('\n\n')

        # 生成文件名并保存（与 lnrj_refilled_novel 保持一致的命名格式）
        base_name = f'Gumiho-{title.strip()} ({s})-({e})-'
        status = "初译完成" if novel_status == "f_trans_finished" else "校对完成"
        file_name = base_name + status + '.txt'

        if self.project_path:
            save_dir = os.path.join(self.project_path, 'result')
            os.makedirs(save_dir, exist_ok=True)
        else:
            save_dir = os.path.dirname(translated_file_path)

        save_path = os.path.join(save_dir, file_name)
        with open(save_path, 'w', encoding='utf-8') as f:
            f.writelines(output)

        return save_path
    
    def lnrj_normal_epub_rebuild(self, start_idx, end_chapter_idx, translated_file_path=None, novel_status="f_trans_finished", with_original_text_or_not=False):
        """
        将翻译后的JSON文件重新构建为EPUB格式电子书，包含章节结构和目录。
        规则：
        - type为title_lv1的为章节标题
        - 连续两个title_lv1时，前一个视为更高级标题(卷标题)
        - 每个标题后到下一个标题前的main_text为该章正文段落
        
        参数:
            start_idx, end_chapter_idx: 以章节 id 为范围（包含端点）
            translated_file_path: 翻译 JSON 路径，默认为 self.destination_path
            novel_status: 状态字符串，用于文件名
            with_original_text_or_not: bool，若 True 则在译文上方保留原文
        返回：写入的文件路径。
        """
        try:
            from ebooklib import epub
        except ImportError:
            raise ImportError("请先安装 ebooklib: pip install ebooklib")
        
        translated_file_path = translated_file_path if translated_file_path else self.destination_path

        # 读取翻译 JSON
        if not os.path.exists(translated_file_path):
            raise FileNotFoundError(f"翻译文件未找到: {translated_file_path}")
        with open(translated_file_path, 'r', encoding='utf-8') as f:
            translated_data = json.load(f)

        title = translated_data.get("title", "")
        description = translated_data.get("description", "")
        chapters = translated_data.get("chapters", [])

        # 验证索引
        try:
            s = int(start_idx)
            e = int(end_chapter_idx)
        except Exception:
            raise ValueError("start_idx 和 end_chapter_idx 必须为整数")
        if s > e:
            raise ValueError("start_idx 不能大于 end_chapter_idx")

        # 过滤并按 id 排序出指定 id 范围内的章节
        selected = sorted([c for c in chapters if isinstance(c.get("id"), int) and s <= c.get("id") <= e], key=lambda x: x.get("id"))
        if not selected:
            raise ValueError("未找到指定范围的章节")

        # 创建 EPUB 书籍对象
        book = epub.EpubBook()
        
        # 设置元数据
        book.set_identifier(f'gumiho_{title}_{s}_{e}')
        book.set_title(title)
        book.set_language('zh-CN')
        book.add_author('Gumiho Translation')
        
        # Helper: 修复相邻引号的换行问题
        def _repair_adjacent_quotes(text):
            if not text:
                return text
            s = str(text)
            s = s.replace('』『', '』\n『')
            s = s.replace('」『', '」\n『')
            s = s.replace('』「', '』\n「')
            return s

        # Helper: 将文本转换为HTML段落
        def _text_to_html_paragraphs(text):
            if not text:
                return ""
            lines = str(text).splitlines()
            return ''.join(f'<p>{line}</p>' for line in lines if line.strip())

        # 创建封面页（包含标题和描述）
        intro_content = f'<h1>{title}</h1>'
        if description:
            intro_content += _text_to_html_paragraphs(description)
        
        # 获取翻译信息标签
        get_tag_by_config = Config(config_path=os.path.join(self.project_path, "config.yml"))
        tag = get_tag_by_config.make_translation_info_tags(status='translating')
        if tag:
            intro_content += f'<p style="margin-top: 2em; font-style: italic;">{tag}</p>'
        
        intro_chapter = epub.EpubHtml(title='简介', file_name='intro.xhtml', lang='zh-CN')
        intro_chapter.content = intro_content
        book.add_item(intro_chapter)

        # 解析章节结构
        epub_chapters = []
        toc_entries = []
        spine_entries = ['nav', intro_chapter]
        
        i = 0
        chapter_counter = 0
        volume_counter = 0
        
        while i < len(selected):
            item = selected[i]
            item_type = item.get("type", "")
            
            # 如果是标题
            if isinstance(item_type, str) and item_type.startswith("title"):
                # 检查下一个元素是否也是标题（判断是否为卷标题）
                is_volume_title = False
                if i + 1 < len(selected):
                    next_item = selected[i + 1]
                    next_type = next_item.get("type", "")
                    if isinstance(next_type, str) and next_type.startswith("title"):
                        is_volume_title = True
                
                if is_volume_title:
                    # 这是卷标题，暂存但不立即创建章节
                    volume_counter += 1
                    volume_title = item.get("translation-text") or item.get("original-text", "")
                    volume_title = _repair_adjacent_quotes(volume_title)
                    volume_toc_entry = []
                    i += 1
                    continue
                
                # 这是章节标题
                chapter_counter += 1
                chapter_title = item.get("translation-text") or item.get("original-text", "")
                chapter_title = _repair_adjacent_quotes(chapter_title)
                
                # 收集该章节的所有正文段落
                content_parts = []
                
                # 如果需要显示原文标题
                if with_original_text_or_not:
                    orig_title = item.get("original-text", "")
                    if orig_title:
                        orig_title = _repair_adjacent_quotes(orig_title)
                        content_parts.append(f'<p style="color: gray;">{orig_title}</p>')
                
                i += 1
                
                # 收集正文段落
                while i < len(selected):
                    para_item = selected[i]
                    para_type = para_item.get("type", "")
                    
                    # 遇到下一个标题则停止
                    if isinstance(para_type, str) and para_type.startswith("title"):
                        break
                    
                    # 处理正文段落
                    orig_text = para_item.get("original-text", "")
                    trans_text = para_item.get("translation-text", "")
                    
                    if with_original_text_or_not and orig_text:
                        orig_text = _repair_adjacent_quotes(orig_text)
                        content_parts.append(f'<p style="color: gray;">{orig_text}</p>')
                    
                    text_to_write = trans_text if trans_text else orig_text
                    text_to_write = _repair_adjacent_quotes(text_to_write)
                    if text_to_write:
                        content_parts.append(f'<p>{text_to_write}</p>')
                    
                    i += 1
                
                # 创建章节HTML
                chapter_html = f'<h2>{chapter_title}</h2>' + ''.join(content_parts)
                chapter_file = epub.EpubHtml(
                    title=chapter_title,
                    file_name=f'chapter_{chapter_counter}.xhtml',
                    lang='zh-CN'
                )
                chapter_file.content = chapter_html
                book.add_item(chapter_file)
                epub_chapters.append(chapter_file)
                spine_entries.append(chapter_file)
                
                # 添加到目录
                if volume_counter > 0 and 'volume_toc_entry' in locals():
                    volume_toc_entry.append(chapter_file)
                else:
                    toc_entries.append(chapter_file)
            else:
                # 跳过非标题的孤立段落
                i += 1
        
        # 如果有卷结构，需要重新组织目录
        if volume_counter > 0:
            # 这里需要更复杂的逻辑来处理卷和章节的层级关系
            # 简化处理：如果检测到卷结构，将所有章节按顺序添加
            book.toc = epub_chapters
        else:
            book.toc = toc_entries

        # 添加必需的 NCX 和 Nav 文件
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # 设置书脊（阅读顺序）
        book.spine = spine_entries

        # 生成文件名
        base_name = f'Gumiho-{title.strip()} ({s})-({e})-'
        status = "初译完成" if novel_status == "f_trans_finished" else "校对完成"
        file_name = base_name + status + '.epub'

        if self.project_path:
            save_dir = os.path.join(self.project_path, 'result')
            os.makedirs(save_dir, exist_ok=True)
        else:
            save_dir = os.path.dirname(translated_file_path)

        save_path = os.path.join(save_dir, file_name)
        
        # 写入 EPUB 文件
        epub.write_epub(save_path, book, {})
        
        return save_path


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
    
    
    # work1=LightNovelRobotJpFormat("少女所不期望的英雄史诗-Gumiho-v0.92_project")
    # start_idx=1
    # end_chapter_idx=6377
    # work1.lnrj_normal_txt_rebuild(start_idx, end_chapter_idx, translated_file_path=None, novel_status="f_trans_finished")
    
    # work2=LightNovelRobotJpFormat("少女所不期望的英雄史诗-Gumiho-v0.92-r1_project")
    # # work2.lurj_project_Initialization()
    # start_idx=1
    # end_chapter_idx=5574
    # work2.lnrj_normal_txt_rebuild(start_idx, end_chapter_idx, translated_file_path=None, novel_status="f_trans_finished")
    
    work3=LightNovelRobotJpFormat("鲜血王女-屠戮殆尽-kiki_project")
    # work3.lurj_project_Initialization()
    start_idx=1
    end_chapter_idx=19491
    work3.lnrj_normal_txt_rebuild(start_idx, end_chapter_idx, translated_file_path=None, novel_status="proofreading_finished")
    work3.lnrj_normal_epub_rebuild(start_idx, end_chapter_idx, translated_file_path=None, novel_status="proofreading_finished", with_original_text_or_not=False)
    
    
    # work4=LightNovelRobotJpFormat("温暖的异世界转生~等级感和，携带物品!我是最强幼女~_project")
    # # work4.lurj_project_Initialization()
    # # work4.lnrj_file_update_toc(work4.original_toc_path)
    # # work4.lnrj_format()
    # start_idx=1
    # end_chapter_idx=6718
    # work4.lnrj_normal_txt_rebuild(start_idx, end_chapter_idx, translated_file_path=None, novel_status="proofreading_finished")
    # work4.lnrj_normal_epub_rebuild(start_idx, end_chapter_idx, translated_file_path=None, novel_status="proofreading_finished", with_original_text_or_not=False)
