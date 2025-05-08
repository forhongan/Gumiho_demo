import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:yaml/yaml.dart'; // 添加 YAML 导入
import '../models/project.dart';
import '../models/config_yml.dart';
import '../widgets/global_sidebar.dart';  
// 新增默认配置实例
final GumihoConfig defaultConfig = GumihoConfig(
  translationProjectName: 'Default Project',
  translater: <String>[],
  type: 'default',
  originalLanguage: 'en',
  targetLanguage: 'en',
  paragraphed: false,
  originalFormat: '.txt',
  defaultAISetting: AISetting(
    api: '',
    key: '',
    modelName: 'default',
    stream: false,
    jsonOrNot: false,
    maxLen: 0,
  ),
  firstTranslationNeeded: false,
  proofreadingNeeded: false,
  name: 'Default Name',
  bookContentSummary: '',
  writingStyle: '',
  enableBaseInformation: false,
  firstTranslationSetting: FirstTranslationSetting(
    sentenceBySentenceTranslation: false,
    numberOfTextsPerGroup: 0,
    enableUniformLength: false,
    enableMaximumLength: false,
    enableContents: false,
    humanInvolvement: false,
    humanCheckSetting: HumanCheckSetting(summaryCheck: false),
    autoTextSummary: AutoTextSummary(
      enable: false,
      create: false,
      using: false,
      numberOfHistoryGeneratedRecords: 0,
      numberOfHistoricalTextsUsed: 0,
      enablePreviousChapterSummary: false,
      enableLongtermSummary: false,
    ),
    properNounTranslation: false,
    autoTranslationDictionary: AutoTranslationDictionary(
      enable: false,
      enableDescribe: false,
      enableDescribeUsing: false,
      enableLongterm: false,
      enableLongtermUsing: false,
    ),
    basePrompt: '',
    outputStructure: '',
  ),
);

class ConfigScreen extends StatefulWidget {
  final Project project;
  const ConfigScreen({Key? key, required this.project}) : super(key: key);

  @override
  State<ConfigScreen> createState() => _ConfigScreenState();
}

class _ConfigScreenState extends State<ConfigScreen> {
  late GumihoConfig _config;
  bool _isLoading = true;
  bool _isDirty = false; // 新增：标记配置是否被修改
  bool _showSidebar = true;

  @override
  void initState() {
    super.initState();
    _loadConfig();
  }

  Future<void> _loadConfig() async {
    final uri = Uri.parse('http://127.0.0.1:5000/config?configPath=${widget.project.configPath}');
    print("DEBUG: Sending GET request to $uri");
    try {
      final response = await http.get(uri);
      print("DEBUG: Received response with status ${response.statusCode}");
      if (response.statusCode == 200) {
        try {
          final rawYaml = loadYaml(response.body); // 获取 YamlMap
          // 将 YamlMap 转换为 Map<String, dynamic>
          final Map<String, dynamic> yamlMap = jsonDecode(jsonEncode(rawYaml));
          print("DEBUG: YAML parsed successfully: $yamlMap");
          setState(() {
            _config = GumihoConfig.fromYaml(yamlMap);
            _isLoading = false;
          });
        } catch (yamlError) {
          print("DEBUG: Error parsing YAML: $yamlError");
          setState(() {
            _config = defaultConfig;
            _isLoading = false;
          });
        }
      } else {
        print("DEBUG: Non-200 status code. Body: ${response.body}");
        setState(() {
          _config = defaultConfig;
          _isLoading = false;
        });
      }
    } catch (e) {
      print("DEBUG: Exception during HTTP GET: $e");
      setState(() {
        _config = defaultConfig;
        _isLoading = false;
      });
    }
  }

  Future<void> _saveConfig() async {
    final uri = Uri.parse('http://127.0.0.1:5000/config');
    try {
      print("DEBUG: Saving config. configPath: ${widget.project.configPath}");
      // 直接传递 YAML 字符串，不对 _config.toYaml() 进行二次编码
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          "configPath": widget.project.configPath,
          "content": _config.toYaml(),
        }),
      );
      print("DEBUG: Save response status: ${response.statusCode}");
      setState(() {
        _isDirty = false;
      });
    } catch (e) {
      print("DEBUG: Exception in _saveConfig: $e");
      // ...错误处理代码...
    }
  }

  // 新增：处理返回操作时未保存的提示
  Future<bool> _onWillPop() async {
    if (!_isDirty) return true;
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('保存配置'),
        content: const Text('配置已修改，是否保存？'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop(false); // 取消保存，直接返回
            },
            child: const Text('否'),
          ),
          TextButton(
            onPressed: () {
              _saveConfig();
              Navigator.of(context).pop(true); // 保存后返回
            },
            child: const Text('是'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop(null); // 取消返回
            },
            child: const Text('取消'),
          ),
        ],
      ),
    );
    return result ?? false;
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const CircularProgressIndicator();

    return WillPopScope( // 新增：返回时检测未保存修改
      onWillPop: _onWillPop,
      child: Scaffold(
        body: Row(
          children: [
            if (_showSidebar) GlobalSidebar(project: widget.project), // 修改为传入 project
            if (_showSidebar)
              const VerticalDivider(width: 1),
            Expanded(
              child: Column(
                children: [
                  // 自定义顶栏
                  Container(
                    height: kToolbarHeight,
                    color: Theme.of(context).primaryColor,
                    child: Row(
                      children: [
                        IconButton(
                          icon: Icon(Icons.arrow_back_ios),
                          onPressed: () {
                            Navigator.pop(context);
                          },
                          color: Colors.white,
                        ),
                        const SizedBox(width: 8),
                        Text('编辑配置 - ${widget.project.name}', style: const TextStyle(color: Colors.white, fontSize: 20)),
                        // ...existing顶栏操作按钮可移至侧边栏区域...
                      ],
                    ),
                  ),
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // 项目基本设置
                          _buildSectionTitle('项目基本设置'),
                          _buildTextField('项目名称', _config.translationProjectName, (value) {
                            setState(() {
                              _config.translationProjectName = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildMultiSelectField('翻译人员', _config.translater),
                          _buildTextField('类型', _config.type, (value) {
                            setState(() {
                              _config.type = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildTextField('原文语言', _config.originalLanguage, (value) {
                            setState(() {
                              _config.originalLanguage = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildTextField('目标语言', _config.targetLanguage, (value) {
                            setState(() {
                              _config.targetLanguage = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildSwitchField('存在段落', _config.paragraphed, (value) {
                            setState(() {
                              _config.paragraphed = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildTextField('源文件格式', _config.originalFormat, (value) {
                            setState(() {
                              _config.originalFormat = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),

                          // AI设置
                          _buildSectionTitle('AI设置'),
                          _buildTextField('API地址', _config.defaultAISetting.api, (value) {
                            setState(() {
                              _config.defaultAISetting.api = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildTextField('API密钥', _config.defaultAISetting.key, (value) {
                            setState(() {
                              _config.defaultAISetting.key = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }, obscureText: true),
                          _buildTextField('模型名称', _config.defaultAISetting.modelName, (value) {
                            setState(() {
                              _config.defaultAISetting.modelName = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildSwitchField('流式传输', _config.defaultAISetting.stream, (value) {
                            setState(() {
                              _config.defaultAISetting.stream = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildSwitchField('JSON格式', _config.defaultAISetting.jsonOrNot, (value) {
                            setState(() {
                              _config.defaultAISetting.jsonOrNot = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildTextField('最大长度', _config.defaultAISetting.maxLen.toString(), (value) {
                            setState(() {
                              _config.defaultAISetting.maxLen = int.tryParse(value) ?? 0;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),

                          // 书籍基本设置
                          _buildSectionTitle('书籍基本设置'),
                          _buildTextField('书籍名称', _config.name, (value) {
                            setState(() {
                              _config.name = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildTextField('内容简介', _config.bookContentSummary ?? '', (value) {
                            setState(() {
                              _config.bookContentSummary = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildTextField('写作风格', _config.writingStyle ?? '', (value) {
                            setState(() {
                              _config.writingStyle = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildSwitchField('启用基本信息', _config.enableBaseInformation, (value) {
                            setState(() {
                              _config.enableBaseInformation = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),

                          // 翻译任务设置
                          _buildSectionTitle('翻译任务设置'),
                          _buildSwitchField('需要初译', _config.firstTranslationNeeded, (value) {
                            setState(() {
                              _config.firstTranslationNeeded = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                          _buildSwitchField('需要校对', _config.proofreadingNeeded, (value) {
                            setState(() {
                              _config.proofreadingNeeded = value;
                              _isDirty = true; // 修改后标记_dirty
                            });
                          }),
                            // 初译设置
                          _buildSectionTitle('初译设置'),
                          _buildSwitchFieldWithInfo(
                            '逐句翻译模式',
                            _config.firstTranslationSetting.sentenceBySentenceTranslation,
                            (value) => setState(() {
                              _config.firstTranslationSetting = _config.firstTranslationSetting.copyWith(sentenceBySentenceTranslation: value);
                              _isDirty = true; // 修改后标记_dirty
                            }),
                            infoText: '启用逐句翻译模式，不启用时默认为整合翻译模式',
                          ),
                          _buildTextFieldWithInfo(
                            '每组文本数量',
                            _config.firstTranslationSetting.numberOfTextsPerGroup.toString(),
                            (value) => setState(() {
                              _config.firstTranslationSetting = _config.firstTranslationSetting.copyWith(
                                numberOfTextsPerGroup: int.tryParse(value) ?? 100,
                              );
                              _isDirty = true; // 修改后标记_dirty
                            }),
                            infoText: '启用整合翻译模式时，每组文本的数量',
                          ),
                          _buildSwitchFieldWithInfo(
                            '均匀长度模式',
                            _config.firstTranslationSetting.enableUniformLength,
                            (value) => setState(() {
                              _config.firstTranslationSetting = _config.firstTranslationSetting.copyWith(enableUniformLength: value);
                              _isDirty = true; // 修改后标记_dirty
                            }),
                            infoText: '启用后每组文本的数量将会保持为不超过设定数量的尽可能相等的长度',
                          ),
                          _buildSwitchFieldWithInfo(
                            '最大长度模式',
                            _config.firstTranslationSetting.enableMaximumLength,
                            (value) => setState(() {
                              _config.firstTranslationSetting = _config.firstTranslationSetting.copyWith(enableMaximumLength: value);
                              _isDirty = true; // 修改后标记_dirty
                            }),
                            infoText: '启用后每组文本将会尽可能拓展为AI上下文极限长度（仍会被章节分割截断）',
                          ),
                          _buildSwitchFieldWithInfo(
                            '启用章节表',
                            _config.firstTranslationSetting.enableContents,
                            (value) => setState(() {
                              _config.firstTranslationSetting = _config.firstTranslationSetting.copyWith(enableContents: value);
                              _isDirty = true; // 修改后标记_dirty
                            }),
                            infoText: '存在/启用章节表',
                          ),

                          // 人工参与设置
                          _buildSectionTitle('人工参与设置'),
                          _buildSwitchFieldWithInfo(
                            '人工参与',
                            _config.firstTranslationSetting.humanInvolvement,
                            (value) => setState(() {
                              _config.firstTranslationSetting = _config.firstTranslationSetting.copyWith(humanInvolvement: value);
                              _isDirty = true; // 修改后标记_dirty
                            }),
                            infoText: '是否需要人工参与',
                          ),
                          _buildSwitchFieldWithInfo(
                            '总结检查',
                            _config.firstTranslationSetting.humanCheckSetting.summaryCheck,
                            (value) => setState(() {
                              // 若 HumanCheckSetting 需要修改，也需添加 copyWith（此处假设不可变则重新创建实例）
                              _config.firstTranslationSetting = _config.firstTranslationSetting.copyWith(
                                humanCheckSetting: HumanCheckSetting(summaryCheck: value),
                              );
                              _isDirty = true; // 修改后标记_dirty
                            }),
                            infoText: '是否需要人工检查总结',
                          ),

                          // 历史文本总结设置
                          _buildSectionTitle('历史文本总结'),
                          _buildSwitchFieldWithInfo(
                            '启用总结',
                            _config.firstTranslationSetting.autoTextSummary.enable,
                            (value) => setState(() {
                              _config.firstTranslationSetting = _config.firstTranslationSetting.copyWith(
                                autoTextSummary: _config.firstTranslationSetting.autoTextSummary.copyWith(enable: value),
                              );
                              _isDirty = true; // 修改后标记_dirty
                            }),
                            infoText: '设置为true时启用自动生成文本总结',
                          ),
                          _buildTextFieldWithInfo(
                            '历史记录数量',
                            _config.firstTranslationSetting.autoTextSummary.numberOfHistoryGeneratedRecords.toString(),
                            (value) => setState(() {
                              _config.firstTranslationSetting = _config.firstTranslationSetting.copyWith(
                                autoTextSummary: _config.firstTranslationSetting.autoTextSummary.copyWith(
                                  numberOfHistoryGeneratedRecords: int.tryParse(value) ?? 5,
                                ),
                              );
                              _isDirty = true; // 修改后标记_dirty
                            }),
                            infoText: '自动利用的历史记录数量，不启用时默认为零',
                          ),
                          _buildTextFieldWithInfo(
                            '历史文本数量',
                            _config.firstTranslationSetting.autoTextSummary.numberOfHistoricalTextsUsed.toString(),
                            (value) => setState(() {
                              _config.firstTranslationSetting = _config.firstTranslationSetting.copyWith(
                                autoTextSummary: _config.firstTranslationSetting.autoTextSummary.copyWith(
                                  numberOfHistoricalTextsUsed: int.tryParse(value) ?? 30,
                                ),
                              );
                              _isDirty = true; // 修改后标记_dirty
                            }),
                            infoText: '加入上文的历史文本原文数量，不启用时默认为零',
                          ),

                          // 专有名词设置
                          _buildSectionTitle('专有名词设置'),
                          _buildSwitchFieldWithInfo(
                            '自动生成词典',
                            _config.firstTranslationSetting.autoTranslationDictionary.enable,
                            (value) => setState(() {
                              _config.firstTranslationSetting = _config.firstTranslationSetting.copyWith(
                                autoTranslationDictionary: _config.firstTranslationSetting.autoTranslationDictionary.copyWith(enable: value),
                              );
                              _isDirty = true; // 修改后标记_dirty
                            }),
                            infoText: '设置为true时自动生成专有名词对照翻译词典',
                          ),
                          _buildSwitchFieldWithInfo(
                            '生成描述',
                            _config.firstTranslationSetting.autoTranslationDictionary.enableDescribe,
                            (value) => setState(() {
                              _config.firstTranslationSetting = _config.firstTranslationSetting.copyWith(
                                autoTranslationDictionary: _config.firstTranslationSetting.autoTranslationDictionary.copyWith(enableDescribe: value),
                              );
                              _isDirty = true; // 修改后标记_dirty
                            }),
                            infoText: '设置为true时自动生成人名/专有名词的描述',
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Text(title, style: Theme.of(context).textTheme.titleLarge), // 使用 titleLarge 替换 headline6
    );
  }

  Widget _buildTextField(String label, String value, ValueChanged<String> onChanged,
      {bool obscureText = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: TextField(
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
        ),
        controller: TextEditingController(text: value),
        onChanged: onChanged,
        obscureText: obscureText,
      ),
    );
  }

  Widget _buildMultiSelectField(String label, List<String> values) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.titleSmall), // 使用 titleSmall 替换 subtitle1
        ...values.map((value) => _buildTextField('', value, (newValue) {
              // 更新逻辑
            })),
        IconButton(
          icon: const Icon(Icons.add),
          onPressed: () => setState(() => values.add('')),
        ),
      ],
    );
  }

  // 添加新方法：构建开关控件
  Widget _buildSwitchField(String label, bool value, ValueChanged<bool> onChanged) {
    return SwitchListTile(
      title: Text(label),
      value: value,
      onChanged: onChanged,
    );
  }

  // 修改：将caption改为bodySmall
  Widget _buildSwitchFieldWithInfo(String label, bool value, ValueChanged<bool> onChanged, {required String infoText}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SwitchListTile(
          title: Text(label),
          value: value,
          onChanged: onChanged,
        ),
        Padding(
          padding: const EdgeInsets.only(left: 16.0, bottom: 8.0),
          child: Text(infoText, style: Theme.of(context).textTheme.bodySmall),
        ),
      ],
    );
  }

  // 同样修改_buildTextFieldWithInfo中caption
  Widget _buildTextFieldWithInfo(String label, String value, ValueChanged<String> onChanged, {required String infoText, bool obscureText = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          decoration: InputDecoration(
            labelText: label,
            border: const OutlineInputBorder(),
          ),
          controller: TextEditingController(text: value),
          onChanged: onChanged,
          obscureText: obscureText,
        ),
        Padding(
          padding: const EdgeInsets.only(top: 4.0, left: 4.0, bottom: 16.0),
          child: Text(infoText, style: Theme.of(context).textTheme.bodySmall),
        ),
      ],
    );
  }
}
