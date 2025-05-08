import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class TranslationCheckPage extends StatefulWidget {
  final String transId;
  final Map<String, dynamic> checkData;
  
  const TranslationCheckPage({
    Key? key,
    required this.transId,
    required this.checkData,
  }) : super(key: key);

  @override
  _TranslationCheckPageState createState() => _TranslationCheckPageState();
}

class _TranslationCheckPageState extends State<TranslationCheckPage> {
  late Map<String, dynamic> newRecord;
  late List<String> originalText;
  String _selectedStatus = 'accept';
  TextEditingController _remakeTipController = TextEditingController();
  List<String> _missingFields = []; // 记录缺失字段

  @override
  void initState() {
    super.initState();
    
    // 安全初始化数据
    try {
      newRecord = Map.from(widget.checkData['new_record'] ?? {});
      originalText = List.from(widget.checkData['original_text'] ?? []);
      
      // 字段存在性检查
      _checkRequiredFields();
    } catch (e) {
      _showErrorAlert('数据解析错误: $e');
    }
  }

  void _checkRequiredFields() {
    _missingFields = [];
    final requiredFields = ['title', 'translate'];
    
    for (var field in requiredFields) {
      if (!newRecord.containsKey(field)) {
        _missingFields.add(field);
      }
    }
    
    if (_missingFields.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('警告：缺失关键字段 ${_missingFields.join(', ')}'),
            backgroundColor: Colors.orange,
          )
        );
      });
    }
  }
  
  Widget _buildHeader() {
    return Card(
      child: ListTile(
        title: Text(newRecord['title'] ?? '未命名章节'),
        subtitle: Text("段落范围: ${newRecord['range']}"),
        trailing: Chip(
          label: Text(newRecord['type'] ?? '未知类型'),
          backgroundColor: Colors.blue[100],
        ),
      ),
    );
  }

  Widget _buildTranslationComparison() {
    List<String> sortedKeys = (newRecord['translate'] as Map<String, dynamic>)
        .keys
        .toList()
      ..sort((a, b) => int.parse(a).compareTo(int.parse(b)));

    return ExpansionTile(
      title: Text('原文译文对照表'),
      children: [
        Table(
          columnWidths: const {
            0: FixedColumnWidth(60),
            1: FlexColumnWidth(),
            2: FlexColumnWidth(),
          },
          border: TableBorder.all(color: Colors.grey),
          children: [
            TableRow(
              decoration: BoxDecoration(color: Colors.grey[100]),
              children: [
                _buildHeaderCell('序号'),
                _buildHeaderCell('原文'),
                _buildHeaderCell('译文（可编辑）'),
              ],
            ),
            for (int i = 0; i < sortedKeys.length; i++)
              TableRow(
                children: [
                  Padding(
                    padding: EdgeInsets.all(8),
                    child: Text(sortedKeys[i]),
                  ),
                  Padding(
                    padding: EdgeInsets.all(8),
                    child: Text(i < originalText.length ? originalText[i] : "[警告: 原文缺失]"),
                  ),
                  Padding(
                    padding: EdgeInsets.all(8),
                    child: TextField(
                      controller: TextEditingController(
                        text: (newRecord['translate'] as Map<String, dynamic>)[sortedKeys[i]] ?? '',
                      ),
                      onChanged: (value) =>
                          (newRecord['translate'] as Map<String, dynamic>)[sortedKeys[i]] = value,
                      maxLines: 2,
                    ),
                  ),
                ],
              ),
          ],
        ),
      ],
    );
  }

  Widget _buildHeaderCell(String text) {
    return Padding(
      padding: EdgeInsets.all(8),
      child: Text(text, style: TextStyle(fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildEntityEditor(String title, String listKey) {
    final items = List.from(newRecord[listKey] ?? []);
    final isChanging = listKey == 'Character changing';

    return Visibility(
      visible: items.isNotEmpty || listKey == 'Character changing',
      child: ExpansionTile(
        title: Text('$title (${items.length})'),
        children: [
          ...items.map((item) {
            final index = items.indexOf(item);
            return Padding(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                children: [
                  if (!isChanging) 
                    _buildEditableField('译名', item['translation'], (value) =>
                      newRecord[listKey][index]['translation'] = value),
                  _buildEditableField('名称', item['name'], (value) =>
                    newRecord[listKey][index]['name'] = value),
                  _buildEditableField('描述', item['describe'], (value) =>
                    newRecord[listKey][index]['describe'] = value),
                  Divider(),
                ],
              ),
            );
          }),
          ElevatedButton.icon(
            icon: Icon(Icons.add),
            label: Text('新增条目'),
            onPressed: () => setState(() {
              newRecord.putIfAbsent(listKey, () => []);
              newRecord[listKey].add({
                if (!isChanging) 'translation': '',
                'name': '',
                'describe': ''
              });
            }),
          ),
        ],
      ),
    );
  }

  void _showErrorAlert(String message) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('数据异常'),
        content: Text(message),
        actions: [
          TextButton(
            child: Text('关闭'),
            onPressed: () => Navigator.pop(ctx),
          ),
        ],
      ),
    );
  }

  Widget _buildEditableField(String label, String value, Function(String) onChanged) {
    return TextFormField(
      initialValue: value,
      decoration: InputDecoration(labelText: label),
      onChanged: onChanged,
    );
  }

  Widget _buildStatusSelector() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        DropdownButtonFormField<String>(
          value: _selectedStatus,
          items: const [
            DropdownMenuItem(
              value: 'accept', child: Text('接受翻译内容')),
            DropdownMenuItem(
              value: 'refuse', child: Text('拒绝翻译内容')),
            DropdownMenuItem(
              value: 'remake', child: Text('新增建议/要求后重试')),
          ],
          onChanged: (value) => setState(() => _selectedStatus = value!),
          decoration: InputDecoration(
            labelText: '处理结果',
            border: OutlineInputBorder(),
          ),
        ),
        if (_selectedStatus == 'remake')
          Padding(
            padding: EdgeInsets.only(top: 16),
            child: TextField(
              controller: _remakeTipController,
              decoration: InputDecoration(
                labelText: '重译要求',
                hintText: '请输入具体的修改建议...',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
          ),
      ],
    );
  }

  Future<void> _submitData() async {
    // 更新状态和附加信息
    newRecord['status'] = _selectedStatus;
    if (_selectedStatus == 'remake') {
      newRecord['Remake tip'] = _remakeTipController.text;
    }

    final response = await http.post(
      Uri.parse('http://127.0.0.1:5000/translating/submit_check'),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        'trans_id': widget.transId,
        'new_record': newRecord,
      }),
    );

    if (response.statusCode == 200) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('提交成功！'))
      );
      Navigator.pop(context);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('提交失败: ${response.body}'))
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('翻译校对系统')),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            _buildHeader(),
            _buildTranslationComparison(),
            _buildEntityEditor('新增人物', 'New Character'),
            _buildEntityEditor('修正人物', 'Character changing'),
            _buildEntityEditor('新增专名', 'New proper noun'),
            Padding(
              padding: EdgeInsets.all(16),
              child: _buildStatusSelector(),
            ),
            ElevatedButton.icon(
              icon: Icon(Icons.send),
              label: Text('提交终审'),
              style: ElevatedButton.styleFrom(
                minimumSize: Size(double.infinity, 50)),
              onPressed: _submitData,
            ),
          ],
        ),
      ),
    );
  }
}
