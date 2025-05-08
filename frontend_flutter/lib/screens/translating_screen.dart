import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'checking_screen.dart';
import '../models/project.dart';

class TranslatingScreen extends StatelessWidget {
  final Project project;
  const TranslatingScreen({Key? key, required this.project}) : super(key: key);

  Future<void> startTranslating(BuildContext context) async {
    // 显示加载对话框
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 20),
            Text("AI正在翻译 ${project.name}...", 
              style: Theme.of(context).textTheme.bodyLarge),
          ],
        ),
      ),
    );

    try {
      final response = await http.post(
        Uri.parse('http://127.0.0.1:5000/translating/start'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"project_name": project.name}),
      );
      
      final data = jsonDecode(response.body);
      Navigator.pop(context); // 关闭加载对话框

      if (data['need_human_check'] == true) {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => TranslationCheckPage(
            transId: data['trans_id'],
            checkData: data['check_list'],
          )),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(data['message'] ?? '翻译完成'),
            backgroundColor: Colors.green,
          )
        );
      }
    } catch (e) {
      Navigator.pop(context); // 关闭加载对话框
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("翻译失败: ${e.toString()}"),
          backgroundColor: Colors.red,
        )
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('翻译项目：${project.name}'),
        centerTitle: true,
        elevation: 4,
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Colors.blue.shade100,
              Colors.white,
              Colors.green.shade100
            ],
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Card(
                elevation: 8,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                child: InkWell(
                  onTap: () => startTranslating(context),
                  borderRadius: BorderRadius.circular(20),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 40,
                      vertical: 25
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.translate, 
                          size: 50, 
                          color: Theme.of(context).primaryColor),
                        const SizedBox(height: 20),
                        Text(
                          "开始翻译",
                          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Colors.blueGrey.shade800
                          ),
                        ),
                        const SizedBox(height: 10),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 30),
              Text(
                "点击按钮启动AI翻译引擎",
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey.shade700,
                  fontStyle: FontStyle.italic
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
