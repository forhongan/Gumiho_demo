import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../models/project.dart';

// 用于编辑 p_record.json，仿照 config_screen.dart 实现
class PRecordScreen extends StatefulWidget {
  final Project project;
  const PRecordScreen({Key? key, required this.project}) : super(key: key);

  @override
  State<PRecordScreen> createState() => _PRecordScreenState();
}

class _PRecordScreenState extends State<PRecordScreen> {
  late TextEditingController _controller;
  
  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _loadPRecord();
  }

  Future<void> _loadPRecord() async {
    final uri = Uri.parse('http://127.0.0.1:5000/p_record?recordPath=${widget.project.p_recordPath}');
    try {
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        setState(() {
          _controller.text = jsonEncode(json.decode(response.body), toEncodable: (object) => object.toString());
        });
      } else {
        setState(() {
          _controller.text = '{ "error": "加载失败" }';
        });
      }
    } catch (e) {
      setState(() {
        _controller.text = '{ "error": "$e" }';
      });
    }
  }

  Future<void> _savePRecord() async {
    final uri = Uri.parse('http://127.0.0.1:5000/p_record');
    try {
      final response = await http.post(uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            "recordPath": widget.project.p_recordPath,
            "content": _controller.text,
          }));
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('p_record已保存')),
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
      appBar: AppBar(title: Text('编辑P Record - ${widget.project.name}')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text('p_record文件路径: ${widget.project.p_recordPath}'),
            const SizedBox(height: 16),
            Expanded(
              child: TextField(
                controller: _controller,
                maxLines: null,
                expands: true,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: '编辑 p_record 内容...',
                ),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _savePRecord,
              child: const Text('保存p_record'),
            ),
          ],
        ),
      ),
    );
  }
}
