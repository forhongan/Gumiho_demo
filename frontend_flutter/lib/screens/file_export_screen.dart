import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/project.dart';

class FileExportScreen extends StatefulWidget {
  final Project project;  // 新增接收 project
  const FileExportScreen({Key? key, required this.project}) : super(key: key);
  @override
  _FileExportScreenState createState() => _FileExportScreenState();
}

class _FileExportScreenState extends State<FileExportScreen> {
  List<dynamic> chapters = [];
  String targetState = "f_trans_finished";
  String? startChapter;
  String? endChapter;

  @override
  void initState() {
    super.initState();
    fetchChapters();
  }
  
  void fetchChapters() async {
    final url = Uri.parse("http://localhost:5000/translatefile?translatefilePath=${widget.project.translatefilePath}&target_state=$targetState");
    final response = await http.get(url);
    if(response.statusCode == 200) {
      final data = json.decode(response.body);
      // 后端返回的是 {"chapters": [...]}
      setState(() {
        chapters = data["chapters"];
      });
    }
  }
  
  void submitExport() async {
    final url = Uri.parse("http://localhost:5000/export_text");
    final body = {
      "start_title": startChapter,
      "end_title": endChapter,
      "target_state": targetState,
      "translatefilePath": widget.project.translatefilePath, // 新增参数
    };
    final response = await http.post(url,
        headers: {"Content-Type": "application/json"},
        body: json.encode(body));
    if(response.statusCode == 200) {
      debugPrint("导出成功: ${response.body}");
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("导出文本")),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Row(
              children: [
                const Text("目标状态: "),
                DropdownButton<String>(
                  value: targetState,
                  items: const [
                    DropdownMenuItem(value: "f_trans_finished", child: Text("f_trans_finished")),
                    DropdownMenuItem(value: "all", child: Text("all")),
                  ],
                  onChanged: (value) {
                    setState(() {
                      targetState = value!;
                      fetchChapters();
                    });
                  },
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                const Text("起始章节: "),
                DropdownButton<String>(
                  hint: const Text("选择起始章节"),
                  value: startChapter,
                  items: chapters.map<DropdownMenuItem<String>>((ch) {
                    final title = ch["title"];
                    final highlight = (targetState == "all" || ch["status"] == targetState);
                    return DropdownMenuItem(
                      value: title,
                      child: Text(title, style: TextStyle(color: highlight ? Colors.black : Colors.grey)),
                    );
                  }).toList(),
                  onChanged: (value) {
                    setState(() {
                      startChapter = value;
                    });
                  },
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                const Text("结束章节: "),
                DropdownButton<String>(
                  hint: const Text("选择结束章节"),
                  value: endChapter,
                  items: chapters.map<DropdownMenuItem<String>>((ch) {
                    final title = ch["title"];
                    final highlight = (targetState == "all" || ch["status"] == targetState);
                    return DropdownMenuItem(
                      value: title,
                      child: Text(title, style: TextStyle(color: highlight ? Colors.black : Colors.grey)),
                    );
                  }).toList(),
                  onChanged: (value) {
                    setState(() {
                      endChapter = value;
                    });
                  },
                ),
              ],
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () {
                submitExport();
              },
              child: const Text("输出文本"),
            ),
          ],
        ),
      ),
    );
  }
}
