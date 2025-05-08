import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:file_picker/file_picker.dart';

class CreateNProjectScreen extends StatefulWidget {
  @override
  _CreateNProjectScreenState createState() => _CreateNProjectScreenState();
}

class _CreateNProjectScreenState extends State<CreateNProjectScreen> {
  final TextEditingController _projectController = TextEditingController();
  final TextEditingController _translatorController = TextEditingController();
  String _filePath = '';

  Future<void> _pickFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles();
    if (result != null) {
      setState(() {
        _filePath = result.files.single.path ?? '';
      });
    }
  }

  Future<void> _createProject({bool force = false}) async {
    final url = Uri.parse("http://127.0.0.1:5000/create_project");
    final payload = {
      "project_name": _projectController.text,
      "translator_name": _translatorController.text,
      "file_path": _filePath,
      "force": force,
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
      appBar: AppBar(title: Text("创建新项目")),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(
              controller: _projectController,
              decoration: InputDecoration(labelText: "作品名"),
            ),
            TextField(
              controller: _translatorController,
              decoration: InputDecoration(labelText: "译者名"),
            ),
            Row(
              children: [
                Expanded(
                  child: Text(_filePath.isEmpty ? "未选择文件" : _filePath),
                ),
                ElevatedButton(
                  onPressed: _pickFile,
                  child: Text("选择文件"),
                )
              ],
            ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: _createProject,
              child: Text("创建项目"),
            ),
          ],
        ),
      ),
    );
  }
}
