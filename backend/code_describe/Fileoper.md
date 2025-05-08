# 数据文件处理类,每个类都处理且仅处理对应的数据保存文件的记录,更新
# 主要数据文件包括:
  - `config.yml`: 配置文件,用于储存此次翻译project的各种设置
  - `TranslatFile.json`: 翻译工程文件,用于储存原文,译文
  - `f/p_record.json`: 记录文件,保存了格式化后的ai每次的响应数据,包括每部分的新增人物,人物修改,内容概括
  - `Proper_nouns_table.json`: 专有名词表,保留了人物及专有名词的对照翻译,描述和出现位置

## TranslateFile.py
**类：TranslateFile**  
- 成员变量:
  - `translatefile_path`: 工程文件路径  
  - `data`: 工程文件数据  
- 函数说明:
  - `__init__`: 初始化对象并读取工程文件  
  - `read_translatefile`: 读取翻译工程文件（JSON格式）  
  - `write_translatefile`: 写入翻译工程文件  
  - `check_id_is_title`: 检查指定id对应的章节是否为标题  
  - `get_chapter_end_from_id`: 获取指定章节范围的结束id  
  - `get_previous_chapter_start_from_id`: 获取上一章节的起始id  
  - `get_book_name`: 返回书名

## Record.py
**类：Record**  
- 成员变量:
  - `record_path`: 记录文件路径  
  - `data`: 记录文件数据  
- 函数说明:
  - `__init__`: 初始化对象并读取记录文件  
  - `read_record`: 读取记录文件（JSON格式）  
  - `write_record`: 写入记录文件  
  - `update_record`: 更新记录文件，处理翻译、角色变动和总结信息  
  - 类方法 `update_record`: 快速调用实例方式更新记录

## Project.py
**类：Project**  
- 成员变量:
  - `project_name`: 工程名称  
  - `project_path`: 工程目录路径  
  - `config_path`: 配置文件路径  
  - `sourcefile_path`: 源文件文件夹路径  
  - `f_record_path`: 第一阶段记录文件路径  
  - `p_record_path`: 校对记录文件路径  
  - `translate_file_path`: 翻译文件路径  
  - `PNT_path`: 专有名词表文件路径  
- 函数说明:
  - 多个 getter：获取各类文件和文件夹路径  
  - `check_project_integrity`: 检查关键文件是否存在  
  - `load_config_data`: 读取配置数据  
  - `load_f_record_data`: 读取第一阶段记录数据  
  - `load_p_record_data`: 读取校对记录数据  
  - `load_translate_file_data`: 读取翻译文件数据  
  - `load_proper_nouns_table_data`: 读取专有名词表数据

## PNT.py
**类：PNT**  
- 成员变量:
  - `PNT_path`: 专有名词表文件路径  
  - `data`: 专有名词表数据  
- 函数说明:
  - `__init__`: 初始化对象并读取专有名词表  
  - `get_longterm_describe`: 根据章节id获取角色的长期描述  
  - `read_pnt`: 读取专有名词表（JSON格式）  
  - `write_pnt`: 写入专有名词表  
  - `get_character_translate`: 获取角色译名（功能未实现）

## Config.py
**类：Config**  
- 成员变量:
  - `config_path`: 配置文件路径  
  - `yaml`: ruamel.yaml 实例，用于处理YAML文件  
  - `data`: 配置数据  
- 函数说明:
  - `__init__`: 初始化对象并读取配置文件  
  - `read_config`: 读取配置文件数据  
  - `write_config`: 写入更新后的配置数据  
  - `AutoOutputStructureText`: 根据配置生成输出结构描述文本


