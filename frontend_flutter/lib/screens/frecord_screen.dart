import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../models/project.dart';
import '../widgets/global_sidebar.dart';
import '../widgets/editable_json_viewer.dart'; // 替换导入

// 用于编辑 f_record.json，仿照 config_screen.dart 实现
class FRecordScreen extends StatefulWidget {
  final Project project;
  const FRecordScreen({Key? key, required this.project}) : super(key: key);

  @override
  State<FRecordScreen> createState() => _FRecordScreenState();
}

class _FRecordScreenState extends State<FRecordScreen> {
  late TextEditingController _controller;
  bool _showSidebar = true;
  bool _isStructuredView = true; // 新增变量

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _loadFRecord();
  }

  Future<void> _loadFRecord() async {
    final uri = Uri.parse('http://127.0.0.1:5000/f_record?recordPath=${widget.project.f_recordPath}');
    try {
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        setState(() {
          _controller.text = const JsonEncoder.withIndent('  ')
              .convert(jsonDecode(response.body));
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

  Future<void> _saveFRecord() async {
    final uri = Uri.parse('http://127.0.0.1:5000/f_record');
    try {
      final response = await http.post(uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            "recordPath": widget.project.f_recordPath,
            "content": _controller.text,
          }));
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('f_record已保存')),
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
      body: Row(
        children: [
          if (_showSidebar) GlobalSidebar(project: widget.project),
          if (_showSidebar)
            const VerticalDivider(width: 1),
          Expanded(
            child: Column(
              children: [
                // 修改顶栏，增加切换按钮
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
                      Text('编辑F Record - ${widget.project.name}', style: const TextStyle(color: Colors.white, fontSize: 20)),
                      const Spacer(),
                      IconButton(
                        icon: Icon(_isStructuredView ? Icons.visibility_off : Icons.visibility),
                        onPressed: () { setState(() { _isStructuredView = !_isStructuredView; }); },
                        color: Colors.white,
                      ),
                    ],
                  ),
                ),
                // 修改主体内容区域
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: _isStructuredView
                        ? FutureBuilder(
                            future: Future.value(jsonDecode(_controller.text)),
                            builder: (context, snapshot) {
                              if (snapshot.hasError) return const Text('JSON解析错误');
                              if (!snapshot.hasData) return const CircularProgressIndicator();
                              return SingleChildScrollView(
                                child: EditableJsonViewer(
                                  jsonObj: snapshot.data,
                                  onChanged: (newData) {
                                    setState(() {
                                      _controller.text = const JsonEncoder.withIndent('  ').convert(newData);
                                    });
                                  },
                                ),
                              );
                            },
                          )
                        : Column(
                            children: [
                              Text('f_record文件路径: ${widget.project.f_recordPath}'),
                              const SizedBox(height: 16),
                              Expanded(
                                child: TextField(
                                  controller: _controller,
                                  maxLines: null,
                                  expands: true,
                                  decoration: const InputDecoration(
                                    border: OutlineInputBorder(),
                                    hintText: '编辑 f_record 内容...',
                                  ),
                                ),
                              ),
                              const SizedBox(height: 16),
                              ElevatedButton(
                                onPressed: _saveFRecord,
                                child: const Text('保存f_record'),
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
    );
  }
}
