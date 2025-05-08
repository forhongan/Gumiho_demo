# 主程序入口/项目创建

# setup.py 创建项目
- start_setup：获取用户输入数据并调用 setup_project 进行项目初始化
- setup_project：创建项目文件夹、处理默认配置文件并复制源文件到目标目录
- select_file：弹出文件选择对话框，供用户选择文件
- ai_default_config_chance：修改默认配置文件中的 AI 设置（待实现）

# Format.py 初始化项目初始化各主要数据文件
## Project工作区初始化
- create_table_of_content：在指定目录创建初始空目录 JSON 文件
- file_update_table_of_content：从文件中提取章节，并更新目录 JSON 文件
- update_table_of_content：根据输入文本更新目录 JSON 文件内容
- create_trans_compare_table：在指定目录创建初始空译名对 JSON 文件
- file_update_trans_compare：从文件中提取译名对并更新 JSON 文件
- update_trans_compare：根据文本更新译名对 JSON 文件
- update_trans_record：更新或新增译名记录，并返回状态提示
- create_f_record：创建初始空字典记录文件 f_record.json
- create_p_record：创建初始空字典记录文件 p_record.json
- build_Gumiho_imformation：从配置文件生成 Gumiho 系统翻译信息文本
## 将原文文本格式化为TranslateFile.json翻译工程文件
### class light_novel_robot嵌入式工作流-对接"轻小说机翻机器人网站"实验性
- auto_format_jp_format.__init__：初始化轻小说机器人格式化对象，读取配置文件及路径
- light_novel_robot_jp_format.lnrj_format：转换轻小说文本为标准 JSON 格式
- light_novel_robot_jp_format.lnrj_create_toc：创建初始目录文件 table_of_content.json
- light_novel_robot_jp_format.lnrj_update_toc：更新目录 JSON 文件，根据文本提取新章节
- light_novel_robot_jp_format.lnrj_file_update_toc：从指定文件中提取章节目录并更新目录 JSON 文件
- light_novel_robot_jp_format.lnrj_refilled_novel：回填翻译文本到原文件中并生成新文本文件
### auto_format.py-实验性
- auto_format: 使用ai自动分析文章格式并完成初始化
### epub_format
- epub_format: 将国际通行电子书格式.epub的小说转化为TranslateFile.json翻译工程文件
