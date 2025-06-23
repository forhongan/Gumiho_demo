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
      appBar: AppBar(
        title: Text("创建新项目", style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.blue[800],
        elevation: 5,
      ),
      body: Padding(
        padding: EdgeInsets.symmetric(horizontal: 24.0, vertical: 32.0),
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
            SizedBox(height: 32),
            _buildFilePicker(),
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

  Widget _buildFilePicker() {
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
              _filePath.isEmpty ? "未选择文件" : _filePath,
              style: TextStyle(
                color: _filePath.isEmpty ? Colors.grey : Colors.blue[900],
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),
          SizedBox(width: 12),
          ElevatedButton.icon(
            icon: Icon(Icons.attach_file, size: 20),
            label: Text("选择文件"),
            onPressed: _pickFile,
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
