import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../models/project.dart';
import '../widgets/global_sidebar.dart';

class TranslatefileScreen extends StatefulWidget {
  final Project project;
  const TranslatefileScreen({Key? key, required this.project}) : super(key: key);

  @override
  State<TranslatefileScreen> createState() => _TranslatefileScreenState();
}

class _TranslatefileScreenState extends State<TranslatefileScreen> {
  late List<dynamic> _titles = [];
  List<dynamic> _currentParagraph = [];
  String? _selectedTitle;
  bool _showSidebar = true;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadTitleList();
  }

  Future<void> _loadTitleList() async {
    final uri = Uri.parse('http://127.0.0.1:5000/title_list?translatefilePath=${widget.project.translatefilePath}');
    try {
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        setState(() {
          _titles = jsonDecode(response.body)['chapters'];
          _selectedTitle = _titles.isNotEmpty ? _titles[0]['title'] : null;
          if (_selectedTitle != null) _loadParagraph(_selectedTitle!);
        });
      }
    } catch (e) {
      print('加载标题列表失败: $e');
    }
  }

  Future<void> _loadParagraph(String title) async {
    setState(() => _isLoading = true);
    try {
      final uri = Uri.parse('http://127.0.0.1:5000/translatefile/paragraph?translatefilePath=${widget.project.translatefilePath}&title=${Uri.encodeComponent(title)}');
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        setState(() {
          _currentParagraph = jsonDecode(response.body)['paragraphs'];
        });
      }
    } catch (e) {
      print('加载段落失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // Future<void> _saveChanges() async {
  //   // 需要实现段落更新逻辑（根据后端接口调整）
  //   // 此处需要与后端确认更新接口的实现方式
  // }

  // 新增保存单个段落的方法
  Future<void> _saveSingleParagraph(int id, String newText) async {
    final uri = Uri.parse('http://127.0.0.1:5000/translatefile/paragraph');
    try {
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          "translatefilePath": widget.project.translatefilePath,
          "id": id,
          "translation_text": newText,
        }),
      );

      final result = jsonDecode(response.body);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['message'] ?? result['error']),
          backgroundColor: response.statusCode == 200 ? Colors.green : Colors.red,
        ),
      );

      if (response.statusCode == 200) {
        _loadParagraph(_selectedTitle!); // 刷新当前段落
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('连接错误: $e')),
      );
    }
  }

  // 新增辅助方法：获取状态对应的颜色
  Color _getStatusColor(String status) {
    switch (status) {
      case 'f_trans_finished':
        return Colors.green;
      case 'unfinished':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  // 新增辅助方法：获取状态文字描述
  String _getStatusText(String status) {
    switch (status) {
      case 'f_trans_finished':
        return '翻译完成';
      case 'unfinished':
        return '未完成';
      default:
        return '未知状态';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          if (_showSidebar) GlobalSidebar(project: widget.project),
          if (_showSidebar) const VerticalDivider(width: 1),
          Expanded(
            child: Column(
              children: [
                // 修改后的顶栏（仅保留基本操作）
                Container(
                  height: kToolbarHeight,
                  color: Theme.of(context).primaryColor,
                  child: Row(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.arrow_back_ios),
                        onPressed: () => Navigator.pop(context),
                        color: Colors.white,
                      ),
                      const Expanded(
                        child: Center(
                          child: Text(
                            '原文译文对照',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.refresh),
                        onPressed: _loadTitleList,
                        color: Colors.white,
                      ),
                    ],
                  ),
                ),
                // 新增标题选择区域
                if (_titles.isNotEmpty)
                  Container(
                    margin: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(8),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.1),
                          blurRadius: 6,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // 新增提示文本
                          const Padding(
                            padding: EdgeInsets.only(top: 8, bottom: 8),
                            child: Text(
                              '选择章节',
                              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                          ),
                          DropdownButtonHideUnderline(
                            child: DropdownButton<String>(
                              isExpanded: true,
                              value: _selectedTitle,
                              icon: const Icon(Icons.keyboard_arrow_down),
                              style: TextStyle(
                                color: Theme.of(context).primaryColor,
                                fontSize: 16,
                              ),
                              items: _titles.map<DropdownMenuItem<String>>((title) {
                                return DropdownMenuItem<String>(
                                  value: title['title'],
                                  child: Row(
                                    children: [
                                      Icon(
                                        Icons.text_snippet,
                                        color: _getStatusColor(title['status']),
                                        size: 18,
                                      ),
                                      const SizedBox(width: 8),
                                      Text(
                                        title['title'],
                                        style: TextStyle(
                                          color: Colors.grey[800],
                                          fontWeight: title['status'] == 'f_trans_finished'
                                              ? FontWeight.bold
                                              : FontWeight.normal,
                                        ),
                                      ),
                                    ],
                                  ),
                                );
                              }).toList(),
                              onChanged: (value) {
                                setState(() => _selectedTitle = value);
                                if (value != null) _loadParagraph(value);
                              },
                              hint: const Text('请选择章节'),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                // 内容区域保持原有样式
                Expanded(
                  child: _isLoading
                      ? const Center(child: CircularProgressIndicator())
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _currentParagraph.length,
                          itemBuilder: (context, index) {
                            final item = _currentParagraph[index];
                            final controller = TextEditingController(text: item['translation-text']);
                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              child: Padding(
                                padding: const EdgeInsets.all(12),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    // 原文显示
                                    Text(
                                      '原文: ${item['original-text']}',
                                      style: TextStyle(
                                        color: Colors.grey[700],
                                        fontSize: 14,
                                      ),
                                    ),
                                    const SizedBox(height: 8),
                                    // 译文编辑区域
                                    TextField(
                                      controller: controller,
                                      decoration: InputDecoration(
                                        labelText: '译文',
                                        border: const OutlineInputBorder(),
                                        suffixIcon: IconButton(
                                          icon: const Icon(Icons.save, color: Colors.blue),
                                          onPressed: () => _saveSingleParagraph(item['id'], controller.text),
                                        ),
                                      ),
                                      maxLines: 3,
                                      minLines: 1,
                                      style: const TextStyle(fontSize: 14),
                                    ),
                                    // 状态显示
                                    if (item['state'] != null)
                                      Padding(
                                        padding: const EdgeInsets.only(top: 8),
                                        child: Text(
                                          '状态: ${_getStatusText(item['state'])}',
                                          style: TextStyle(
                                            color: _getStatusColor(item['state']),
                                            fontSize: 12,
                                          ),
                                        ),
                                      ),
                                  ],
                                ),
                              ),
                            );
                          },
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
