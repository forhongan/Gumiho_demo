import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../models/project.dart';
import '../widgets/global_sidebar.dart';
import '../widgets/editable_json_viewer.dart'; // 替换导入

class TranslatefileScreen extends StatefulWidget {
  final Project project;
  const TranslatefileScreen({Key? key, required this.project}) : super(key: key);

  @override
  State<TranslatefileScreen> createState() => _TranslatefileScreenState();
}

class _TranslatefileScreenState extends State<TranslatefileScreen> {
  late TextEditingController _controller;
  bool _showSidebar = true;
  bool _isStructuredView = true;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _loadTranslateFile();
  }

  Future<void> _loadTranslateFile() async {
    final uri = Uri.parse('http://127.0.0.1:5000/translatefile?translatefilePath=${widget.project.translatefilePath}');
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

  Future<void> _saveTranslateFile() async {
    final uri = Uri.parse('http://127.0.0.1:5000/translatefile');
    try {
      final response = await http.post(uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            "translatefilePath": widget.project.translatefilePath,
            "content": _controller.text,
          }));
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('译文配置已保存')),
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
                      Text('编辑译文配置 - ${widget.project.name}', style: const TextStyle(color: Colors.white, fontSize: 20)),
                      const Spacer(),
                      IconButton(
                        icon: Icon(_isStructuredView ? Icons.visibility_off : Icons.visibility),
                        onPressed: () { setState(() { _isStructuredView = !_isStructuredView; }); },
                        color: Colors.white,
                      ),
                    ],
                  ),
                ),
                // 主体内容区域
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: _isStructuredView 
                        ? FutureBuilder(
                            future: Future.value(jsonDecode(_controller.text)),
                            builder: (context, snapshot) {
                              if (snapshot.hasError) {
                                return const Text('JSON解析错误');
                              }
                              if (!snapshot.hasData) {
                                return const CircularProgressIndicator();
                              }
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
                              Text('译文文件路径: ${widget.project.translatefilePath}'),
                              const SizedBox(height: 16),
                              Expanded(
                                child: TextField(
                                  controller: _controller,
                                  maxLines: null,
                                  expands: true,
                                  decoration: const InputDecoration(
                                    border: OutlineInputBorder(),
                                    hintText: '编辑译文配置内容...',
                                  ),
                                ),
                              ),
                              const SizedBox(height: 16),
                              ElevatedButton(
                                onPressed: _saveTranslateFile,
                                child: const Text('保存译文配置'),
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
