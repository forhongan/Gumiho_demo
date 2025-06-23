import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:yaml/yaml.dart'; 
import '../models/project.dart';
import '../models/config_yml.dart';
import '../widgets/global_sidebar.dart';
import 'tabs/basic_settings_tab.dart'; // 新增
import 'tabs/ai_settings_tab.dart';    // 新增
import 'tabs/first_translation_tab.dart'; // 新增

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

class _ConfigScreenState extends State<ConfigScreen> with SingleTickerProviderStateMixin {
  late GumihoConfig _config;
  bool _isLoading = true;
  bool _isDirty = false; // 新增：标记配置是否被修改
  bool _showSidebar = true;
  late TabController _tabController; // 新增：Tab控制器

  @override
  void initState() {
    super.initState();
    _loadConfig();
    _tabController = TabController(length: 3, vsync: this); // 初始化Tab控制器
  }

  @override
  void dispose() {
    _tabController.dispose(); // 释放Tab控制器资源
    super.dispose();
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

  // 新增：更新配置的回调方法
  void _updateConfig(GumihoConfig newConfig) {
    setState(() {
      _config = newConfig;
      _isDirty = true;
    });
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

    return WillPopScope(
      onWillPop: _onWillPop,
      child: Scaffold(
        // 保留悬浮保存按钮
        floatingActionButton: FloatingActionButton.extended(
          onPressed: () {
            _saveConfig();
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('配置已保存')),
            );
          },
          icon: const Icon(Icons.save),
          label: const Text('保存'),
          backgroundColor: Colors.green,
        ),
        body: Row(
          children: [
            if (_showSidebar) GlobalSidebar(project: widget.project),
            if (_showSidebar) const VerticalDivider(width: 1),
            Expanded(
              child: Column(
                children: [
                  // 自定义顶栏 - 保留顶栏中的保存按钮
                  Container(
                    height: kToolbarHeight,
                    color: Theme.of(context).primaryColor,
                    child: Row(
                      children: [
                        IconButton(
                          icon: const Icon(Icons.arrow_back_ios),
                          onPressed: () {
                            Navigator.pop(context);
                          },
                          color: Colors.white,
                        ),
                        const SizedBox(width: 8),
                        Text('编辑配置 - ${widget.project.name}', style: const TextStyle(color: Colors.white, fontSize: 20)),
                        const Spacer(),
                        // 保留顶栏中的保存按钮
                        IconButton(
                          icon: const Icon(Icons.save),
                          onPressed: () {
                            _saveConfig();
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('配置已保存')),
                            );
                          },
                          color: Colors.white,
                        ),
                        const SizedBox(width: 16),
                      ],
                    ),
                  ),
                  
                  // 新增：Tab栏
                  Container(
                    color: Colors.grey[200],
                    child: TabBar(
                      controller: _tabController,
                      labelColor: Colors.blue,
                      unselectedLabelColor: Colors.grey,
                      tabs: const [
                        Tab(text: '项目/书籍设置'),
                        Tab(text: 'AI翻译设置'),
                        Tab(text: '初次翻译设置'),
                      ],
                    ),
                  ),
                  
                  // 内容区域
                  Expanded(
                    child: TabBarView(
                      controller: _tabController,
                      children: [
                        // 项目/书籍基本设置
                        BasicSettingsTab(
                          config: _config,
                          onConfigChanged: _updateConfig,
                        ),
                        
                        // AI翻译设置
                        AISettingsTab(
                          config: _config,
                          onConfigChanged: _updateConfig,
                        ),
                        
                        // 初次翻译设置
                        FirstTranslationTab(
                          config: _config,
                          onConfigChanged: _updateConfig,
                        ),
                      ],
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
