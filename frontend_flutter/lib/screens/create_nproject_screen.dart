import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:file_picker/file_picker.dart';
import 'config_screen.dart';

class CreateNProjectScreen extends StatefulWidget {
  @override
  _CreateNProjectScreenState createState() => _CreateNProjectScreenState();
}

class _CreateNProjectScreenState extends State<CreateNProjectScreen> {
  final TextEditingController _projectController = TextEditingController();
  final TextEditingController _translatorController = TextEditingController();
  String _originFilePath = '';

  bool _initFromExistingTranslation = false;
  String _translationFilePath = '';

  bool _paragraphAggregationMode = false;
  bool _doubleBlankLine = false;

  bool _mergeToTranslateFile = true;
  bool _enableReading = false;

  Map<String, dynamic>? _draftConfigContent;

  Future<void> _pickOriginFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['txt', 'epub'],
    );
    if (result != null) {
      setState(() {
        _originFilePath = result.files.single.path ?? '';
      });
    }
  }

  Future<void> _pickTranslationFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['txt', 'epub'],
    );
    if (result != null) {
      setState(() {
        _translationFilePath = result.files.single.path ?? '';
      });
    }
  }

  Future<void> _editConfigBeforeCreate() async {
    final uri = Uri.parse('http://127.0.0.1:5000/config_template');
    try {
      final resp = await http.get(uri);
      if (resp.statusCode != 200) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('获取默认配置模板失败')));
        return;
      }

      final result = await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ConfigScreen(
            initialYamlContent: resp.body,
          ),
        ),
      );

      if (result is Map) {
        setState(() {
          _draftConfigContent = Map<String, dynamic>.from(result);
        });
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('已应用预编辑配置')));
      }
    } catch (e) {
      print('DEBUG: _editConfigBeforeCreate error: $e');
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('打开配置编辑失败')));
    }
  }

  Future<void> _createProject({bool force = false}) async {
    final url = Uri.parse("http://127.0.0.1:5000/create_project");

    if (_projectController.text.trim().isEmpty ||
        _translatorController.text.trim().isEmpty ||
        _originFilePath.trim().isEmpty) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('请填写作品名/译者名并选择原文文件')));
      return;
    }
    if (_initFromExistingTranslation && _translationFilePath.trim().isEmpty) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('请选择译文文件路径')));
      return;
    }

    final payload = {
      "project_name": _projectController.text,
      "translator_name": _translatorController.text,
      "file_path": _originFilePath,
      "force": force,

      // 新增参数
      "init_mode": _initFromExistingTranslation ? "translated" : "new",
      if (_initFromExistingTranslation)
        "translation_file_path": _translationFilePath,
      "paragraph_aggregation_mode": _paragraphAggregationMode,
      "double_blank_line": _doubleBlankLine,
      "merge_to_translatefile": _initFromExistingTranslation ? _mergeToTranslateFile : false,
      "enable_reading": (_initFromExistingTranslation && _mergeToTranslateFile)
          ? _enableReading
          : false,
      if (_draftConfigContent != null) "config_content": _draftConfigContent,
    };
    final response = await http.post(url,
        headers: {"Content-Type": "application/json"},
        body: json.encode(payload));
    if (response.statusCode == 200) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text("项目创建成功")));
    } else if (response.statusCode == 409) {
      // 弹出确认对话框
      bool? confirm = await showDialog<bool>(
        context: context,
        builder: (context) {
          return AlertDialog(
            title: Text("确认"),
            content: Text(json.decode(response.body)["warning"]),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: Text("取消"),
              ),
              TextButton(
                onPressed: () => Navigator.of(context).pop(true),
                child: Text("确定"),
              ),
            ],
          );
        },
      );
      if (confirm == true) {
        // 用户选择重新初始化
        _createProject(force: true);
      }
    } else {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text("项目创建失败")));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("创建新项目", style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.blue[800],
        elevation: 5,
      ),
      body: Padding(
        padding: EdgeInsets.symmetric(horizontal: 24.0, vertical: 32.0),
        child: SingleChildScrollView(
          child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildInputField(
              controller: _projectController,
              label: "作品名",
              icon: Icons.book,
            ),
            SizedBox(height: 24),
            _buildInputField(
              controller: _translatorController,
              label: "译者名",
              icon: Icons.person,
            ),
            SizedBox(height: 24),

            _buildSwitchTile(
              title: '从已有译本开始',
              value: _initFromExistingTranslation,
              onChanged: (v) {
                setState(() {
                  _initFromExistingTranslation = v;
                  if (!v) {
                    _translationFilePath = '';
                    _enableReading = false;
                    _mergeToTranslateFile = true;
                  }
                });
              },
            ),

            SizedBox(height: 16),
            _buildFilePicker(
              label: '原文文件（txt/epub）',
              filePath: _originFilePath,
              onPick: _pickOriginFile,
            ),

            if (_initFromExistingTranslation) ...[
              SizedBox(height: 16),
              _buildFilePicker(
                label: '译文文件（txt/epub）',
                filePath: _translationFilePath,
                onPick: _pickTranslationFile,
              ),
              SizedBox(height: 16),
              _buildSwitchTile(
                title: '合并并写入 TranslateFile.json',
                value: _mergeToTranslateFile,
                onChanged: (v) {
                  setState(() {
                    _mergeToTranslateFile = v;
                    if (!v) _enableReading = false;
                  });
                },
              ),
              _buildSwitchTile(
                title: '启用 reading（生成专有名词表）',
                value: _enableReading,
                onChanged: _mergeToTranslateFile
                    ? (v) => setState(() => _enableReading = v)
                    : null,
              ),
            ],

            SizedBox(height: 16),
            _buildSectionTitle('文件解析模式（txt 生效）'),
            _buildSwitchTile(
              title: '启用行聚合（空行分段）',
              value: _paragraphAggregationMode,
              onChanged: (v) {
                setState(() {
                  _paragraphAggregationMode = v;
                  if (!v) _doubleBlankLine = false;
                });
              },
            ),
            _buildSwitchTile(
              title: '双空行分段',
              value: _doubleBlankLine,
              onChanged: _paragraphAggregationMode
                  ? (v) => setState(() => _doubleBlankLine = v)
                  : null,
            ),

            SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: _editConfigBeforeCreate,
              icon: Icon(Icons.edit, color: Colors.blue[800]),
              label: Text(
                _draftConfigContent == null ? '预编辑配置' : '已预编辑配置（点击重新编辑）',
                style: TextStyle(color: Colors.blue[800]),
              ),
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: Colors.blue[800]!, width: 1.5),
                padding: EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),

            SizedBox(height: 40),
            ElevatedButton(
              onPressed: _createProject,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue[800],
                padding: EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 3,
              ),
              child: Text(
                "创建项目",
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: Colors.white,
                ),
              ),
            ),
          ],
          ),
        ),
      ),
    );
  }

  Widget _buildInputField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
  }) {
    return TextField(
      controller: controller,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: Colors.blue[800]),
        filled: true,
        fillColor: Colors.grey[50],
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: Colors.blue[800]!, width: 2),
        ),
        contentPadding: EdgeInsets.symmetric(vertical: 16, horizontal: 20),
        labelStyle: TextStyle(color: Colors.grey[600]),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Text(
        title,
        style: TextStyle(
          fontWeight: FontWeight.w600,
          color: Colors.grey[800],
        ),
      ),
    );
  }

  Widget _buildSwitchTile({
    required String title,
    required bool value,
    required ValueChanged<bool>? onChanged,
  }) {
    return SwitchListTile(
      contentPadding: EdgeInsets.zero,
      title: Text(title),
      value: value,
      onChanged: onChanged,
    );
  }

  Widget _buildFilePicker({
    required String label,
    required String filePath,
    required VoidCallback onPick,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.blue[800]!, width: 1.5),
      ),
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          Expanded(
            child: Text(
              filePath.isEmpty ? "$label：未选择" : filePath,
              style: TextStyle(
                color: filePath.isEmpty ? Colors.grey : Colors.blue[900],
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),
          SizedBox(width: 12),
          ElevatedButton.icon(
            icon: Icon(Icons.attach_file, size: 20),
            label: Text("选择文件"),
            onPressed: onPick,
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue[50],
              foregroundColor: Colors.blue[800],
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
              padding: EdgeInsets.symmetric(vertical: 12, horizontal: 16),
            ),
          ),
        ],
      ),
    );
  }
}
