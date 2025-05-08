# 核心逻辑:翻译进行类
# 类：Translating

**概述：**  
Translating 类为翻译系统的主进程类，负责组织翻译流程。该类除调用 AI 接口 call_ai 外，其余所有数据操作均通过 Fileoper文件操作模块中的各个类执行。同时，Translating 类提供了回滚功能，用于撤销可能出现错误的翻译进度，确保数据的正确性与一致性。

## 成员变量
- `project_name`：项目名称（继承自 Project，来自 Project.py）
- `status`：当前状态（"translating" 或 "proofreading"）
- `now_setting`：当前使用的设置名称，根据状态选择（配置字段来自 Config.py）
- `Config`：配置管理实例（来自 Config.py，使用 read_config）
- `TranslateFile`：工程文件操作实例（来自 Fileoper 中 TranslateFile.py，使用 read/write_translatefile）
- `Record`：记录文件操作实例（来自 Record.py，使用 read/write_record）
- `PNT`：专有名词表操作实例（来自 Fileoper 中 PNT.py，使用 read_pnt / write_pnt）
- `translatefile_data`：工程文件数据（JSON 格式）
- `original_text`、`translated_text`、`past_text`：文本数据列表
- `start`、`end`：当前翻译范围的起始与结束 ID
- `paragraph_title`：当前段落标题
- `name_list`：人名/专有名词列表
- `summary_list`：上文总结列表
- `sys_prompt`、`user_prompt`：系统提示和用户提示列表
- `output_structure`：输出格式要求
- `check_list`：校对检查项
- `ai_config`：AI 配置字典
- `response`：AI 翻译接口返回结果

## 成员函数及调用的外部函数/类

- `__init__(project_name, status)`  
  初始化对象，调用：  
  - `Project.__init__`（来自 Project.py）  
  - `Config.read_config`（来自 Config.py）  
  - `TranslateFile.read_translatefile`（来自 Fileoper 的 TranslateFile.py）  
  - 初始化 Record（Record.py）和 PNT（PNT.py）实例  

- `translating()`  
  主流程函数，依次调用：  
  - `scope_definition()`（解析翻译范围）  
  - `name_table_get()`（构造人名/专有名词列表，调用 Project.load_proper_nouns_table_data 与 PNT.get_longterm_describe）  
  - `summary_get()`（生成上文总结，依赖 Record.get_longterm_summary，来自 Record.py/TranslateFile.py）  
  - `sys_prompt_make()`（构建系统提示）  
  - `user_prompt_make()`（构建用户提示）  
  - `ai_config_make()`（生成 AI 配置）  
  - `ai_translating()`（调用 AI 接口，调用 ai.call_ai 来自 ai.py）  
  - 保存记录：`save_f_record()` 或 `save_p_record()`（调用 Record.write_record，来自 Record.py）  
  - `record_to_file()`（更新工程文件及专有名词表，调用 TranslateFile.write_translatefile 与 PNT.write_pnt）

- `scope_definition()`  
  计算翻译范围，依次调用：  
  - `_find_start_index()`  
  - `_detect_paragraph_title()`  
  - `_collect_current_group()`  
  - `_build_past_text()` （构建历史翻译文本）

- `_find_start_index(chapters, req_state)`  
  遍历章节列表，查找符合要求的起始索引。

- `_detect_paragraph_title(chapters, start_index)`  
  向前查找，检测并返回段落标题及其索引。

- `_collect_current_group(chapters, start_index, req_state, max_len)`  
  收集当前处理组中的文本内容和终止 ID。

- `_build_past_text(chapters, start_index, max_len, paragraphed, paragraph_title_index)`  
  构建历史翻译文本列表。

- `name_table_get()`  
  获取人名/专有名词表，调用：  
  - `Project.load_proper_nouns_table_data()`（来自 Project.py）  
  - `PNT.get_longterm_describe()`（来自 PNT.py）

- `summary_get()`  
  获取上文总结列表，调用：  
  - `Record.data.get`  
  - `Record.get_longterm_summary()`（来自 Record.py/TranslateFile.py）

- `sys_prompt_make()`  
  构建系统提示，依据不同状态调用不同的配置数据（来自 Config.py）。

- `user_prompt_make()`  
  构建用户提示，整合项目基本信息、上文、原文及校对要求（配置来自 Config.py）。

- `ai_config_make()`  
  生成调用 AI 接口所需要的参数配置。

- `save_f_record()` / `save_p_record()`  
  保存翻译或校对记录，调用 `Record.write_record()`（来自 Record.py）。

- `record_to_file()`  
  将记录文件中的翻译写入工程文件并更新专有名词表，调用：  
  - `TranslateFile.write_translatefile()`（来自 Fileoper 的 TranslateFile.py）  
  - `PNT.write_pnt()`（来自 Fileoper 的 PNT.py）  
  - `Record.write_record()`（来自 Record.py）

- `rollback(timestamp)`  
  回滚操作，将指定时间戳之后的记录撤销，调用：  
  - `Record.read_record()` 与 `Record.write_record()`（来自 Record.py）  
  - `TranslateFile.write_translatefile()`（来自 TranslateFile.py）

- `test_original_text()`  
  测试函数，打印原文列表。

- `test_name_list()`  
  测试函数，打印人名/专有名词列表。

- `ai_translating()`  
  发起 AI 翻译请求，调用：  
  - `call_ai()`（来自 ai.py）  

- `human_check()`  
  用于人工对翻译过程进行检查与修正，当前未实现具体逻辑。
