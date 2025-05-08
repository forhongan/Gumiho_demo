import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../models/project.dart';

class EditScreen extends StatefulWidget {
  final Project project;
  const EditScreen({Key? key, required this.project}) : super(key: key);

  @override
  State<EditScreen> createState() => _EditScreenState();
}

class _EditScreenState extends State<EditScreen> {
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _loadConfig();
  }

  Future<void> _loadConfig() async {
    // 请求后端接口加载配置内容，传入完整的 configPath
    final uri = Uri.parse('http://127.0.0.1:5000/config?configPath=${widget.project.configPath}');
    try {
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        setState(() {
          _controller.text = response.body;
        });
      } else {
        setState(() {
          _controller.text = '# 无法加载配置';
        });
      }
    } catch (e) {
      setState(() {
        _controller.text = '# 错误：$e';
      });
    }
  }

  Future<void> _saveConfig() async {
    // 将修改后的配置提交给后端
    final uri = Uri.parse('http://127.0.0.1:5000/config');
    try {
      final response = await http.post(uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            "configPath": widget.project.configPath,
            "content": _controller.text,
          }));
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('配置已保存')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('保存失败')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('错误：$e')),
      );
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('编辑项目 - ${widget.project.name}'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text('配置文件路径: ${widget.project.configPath}'),
            const SizedBox(height: 16),
            Expanded(
              child: TextField(
                controller: _controller,
                maxLines: null,
                expands: true,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: '编辑配置内容...',
                ),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _saveConfig,
              child: const Text('保存配置'),
            ),
          ],
        ),
      ),
    );
  }
}
