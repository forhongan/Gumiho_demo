import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'checking_screen.dart';
import '../models/project.dart';
import 'package:eventsource/eventsource.dart';

class TranslatingScreen extends StatefulWidget {
  final Project project;
  const TranslatingScreen({Key? key, required this.project}) : super(key: key);

  @override
  _TranslatingScreenState createState() => _TranslatingScreenState();
}

class _TranslatingScreenState extends State<TranslatingScreen> with SingleTickerProviderStateMixin {
  EventSource? _sse;
  String _aiResponse = "";
  bool _isLoading = false;
  bool _showCompletion = false; // 新增：翻译完成状态
  bool _translationCompleted = false; // 新增：区分完成和显示状态
  late AnimationController _animationController; // 新增：动画控制器
  String _savedTransId = "";       // 新增：保存transId
  dynamic _savedCheckData;         // 新增：保存checkData
  int _autoTranslateCount = 10; // 默认自动翻译次数
  bool _autoModeRunning = false; // 是否正在自动执行
  int _currentAutoCount = 0;    // 当前自动执行次数

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );
  }

  Future<void> startTranslating() async {
    // 重置所有状态
    _resetState(); // 调用完整重置方法
    
    setState(() {
      _isLoading = true;
    });
    _animationController.forward(); // 启动动画

    try {
      final response = await http.post(
        Uri.parse('http://127.0.0.1:5000/translating/start'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"project_name": widget.project.name}),
      );
      
      final data = jsonDecode(response.body);
      final transId = data['trans_id'];
      setState(() => _savedTransId = transId); // 立即保存transId到状态
      final streamUrl = data['stream_url'];
      
      _sse = await EventSource.connect(Uri.parse('http://127.0.0.1:5000$streamUrl'));

      _sse!.listen((Event event) {
        final data = jsonDecode(event.data!);
        setState(() {
          if (event.event == 'progress') {
            _aiResponse += data['content'];
          } else if (event.event == 'result') {
            _translationCompleted = true; // 标记翻译完成
            _showCompletion = true; // 显示完成提示
            _savedCheckData = data['check_list'];  // 保存checkData到状态
            _isLoading = false; // 添加：加载状态重置
            _sse?.client.close(); // 修改：使用正确的关闭方法
            // 添加：自动模式处理
            if (_autoModeRunning) {
              WidgetsBinding.instance.addPostFrameCallback((_) {
                _submitWithoutCheck();
              });
            }
          } else if (event.event == 'error') {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(data['message']))
            );
            _isLoading = false; // 错误时重置加载状态
            _sse?.client.close(); // 修改：使用正确的关闭方法
          }
        });
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _aiResponse = "错误: ${e.toString()}";
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("翻译失败: ${e.toString()}"))
      );
      if (_autoModeRunning) {
        setState(() {
          _autoModeRunning = false;
        });
      }
    }
  }

  // 完整状态重置方法
  void _resetState() {
    _sse?.client.close(); // 修改：使用正确的关闭方法
    _sse = null;
    
    setState(() {
      _isLoading = false;
      _showCompletion = false;
      _translationCompleted = false;
      _aiResponse = ""; // 重置翻译内容
      _savedTransId = ""; // 重置transId
      _savedCheckData = null; // 重置检查数据
    });
    _animationController.reset();
  }

  void _navigateToCheckPage() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => TranslationCheckPage(
        transId: _savedTransId,
        checkData: _savedCheckData,
      )),
    ).then((_) => _resetState());
  }

  // 新增：信任提交逻辑方法
  Future<void> _submitWithoutCheck() async {
    try {
      final response = await http.post(
        Uri.parse('http://127.0.0.1:5000/translating/submit_check'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          'trans_id': _savedTransId,
          'new_record': {
            ..._savedCheckData['new_record'],
            'status': 'accept',
          },
        }),
      );
      if (response.statusCode == 200) {
        // ✅ 提交成功后先重置状态
        _resetState();
        
        // 再判断是否继续翻译
        if (_autoModeRunning && _currentAutoCount < _autoTranslateCount) {
          _currentAutoCount++;
          Future.delayed(const Duration(milliseconds: 500), () {
            startTranslating(); // 开始下一轮
          });
        } else {
          setState(() {
            _autoModeRunning = false;
          });
        }
      } else {
        // 提交失败也要重置状态
        _resetState();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('提交失败: ${response.body}'))
        );
        setState(() {
          _autoModeRunning = false;
        });
      }
    } catch (e) {
      // 异常情况下也要重置状态
      _resetState();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('提交错误: ${e.toString()}'))
      );
      setState(() {
        _autoModeRunning = false;
      });
    }
  }

  // 新增方法 _submitAndTrust
  Future<void> _submitAndTrust() async {
    try {
      final response = await http.post(
        Uri.parse('http://127.0.0.1:5000/translating/submit_check'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          'trans_id': _savedTransId,
          'new_record': {
            ..._savedCheckData['new_record'],
            'status': 'accept',
          },
        }),
      );

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('已信任提交当前翻译'))
        );
        _resetState(); // 重置但不自动开始下一次翻译
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('提交失败: ${response.body}'))
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('提交错误: ${e.toString()}'))
      );
    }
  }

  // 添加自动执行的方法
  void _startAutoTranslation() {
    setState(() {
      _autoModeRunning = true;
      _currentAutoCount = 0;
    });

    startTranslating(); // 启动第一轮翻译
  }

  @override
  void dispose() {
    _animationController.dispose(); // 释放动画资源
    _sse?.client.close(); // 修改：使用正确的关闭方法
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('翻译项目：${widget.project.name}'),
        centerTitle: true,
        elevation: 4,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(bottom: Radius.circular(16)),
        ),
      ),
      body: Column(
        children: [
          if (_isLoading) LinearProgressIndicator(
            minHeight: 4,
            backgroundColor: Colors.blue[100],
            valueColor: const AlwaysStoppedAnimation<Color>(Colors.blueAccent),
          ),
          Expanded(
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 300),
              child: _aiResponse.isEmpty
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.translate, size: 80, color: Colors.blueGrey),
                        SizedBox(height: 20),
                        Text("准备翻译项目内容",
                          style: TextStyle(fontSize: 18, color: Colors.blueGrey),
                        ),
                      ],
                    ),
                  )
                : SingleChildScrollView(
                    padding: const EdgeInsets.all(16),
                    child: Container(
                      decoration: BoxDecoration(
                        color: Colors.grey[50],
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.blueGrey.shade100),
                      ),
                      padding: const EdgeInsets.all(16),
                      child: Text(
                        _aiResponse,
                        style: const TextStyle(fontSize: 16, height: 1.6),
                      ),
                    ),
                  ),
            ),
          ),
          _buildAutoTranslationControls(),
          if (_showCompletion) _buildCompletionSection(),
          const SizedBox(height: 20),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 40.0, vertical: 20),
            child: ScaleTransition(
              scale: Tween(begin: 0.95, end: 1.0).animate(
                CurvedAnimation(
                  parent: _animationController,
                  curve: Curves.easeInOut,
                ),
              ),
              child: ElevatedButton(
                onPressed: _isLoading 
                  ? null 
                  : _translationCompleted 
                      ? _submitWithoutCheck 
                      : startTranslating,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blueAccent,
                  foregroundColor: Colors.white,
                  minimumSize: const Size(double.infinity, 56),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(28),
                  ),
                  elevation: 6,
                  shadowColor: Colors.blueAccent.withOpacity(0.4),
                ),
                child: _isLoading
                  ? const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            strokeWidth: 2.5,
                            color: Colors.white,
                          ),
                        ),
                        SizedBox(width: 12),
                        Text("翻译中...", style: TextStyle(fontSize: 18))
                      ],
                    )
                  : Text(
                      _translationCompleted 
                        ? "信任翻译，提交并启动下一次翻译" 
                        : "开始翻译",
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)
                    ),
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildCompletionSection() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.check_circle, 
            size: 56, 
            color: Colors.green,
          ),
          const SizedBox(height: 16),
          const Text("翻译完成!", 
            style: TextStyle(
              fontSize: 22, 
              fontWeight: FontWeight.bold,
              color: Colors.green
            ),
          ),
          const SizedBox(height: 24),
          Column(
            children: [
              ElevatedButton.icon(
                onPressed: _navigateToCheckPage, // 使用保存的数据跳转
                icon: const Icon(Icons.visibility),
                label: const Text("查看翻译结果", style: TextStyle(fontSize: 16)),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 14),
                  backgroundColor: Colors.blueAccent,
                ),
              ),
              const SizedBox(height: 12),
              ElevatedButton.icon(
                onPressed: _submitAndTrust, // 使用新信任提交方法(不自动开始下一次翻译)
                icon: const Icon(Icons.verified_user),
                label: const Text("信任并提交翻译", style: TextStyle(fontSize: 16)),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 14),
                  backgroundColor: Colors.green,
                ),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: _resetState,
                child: const Text("重新翻译", style: TextStyle(color: Colors.blueGrey)),
              )
            ],
          )
        ],
      ),
    );
  }

  Widget _buildAutoTranslationControls() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40.0, vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          Expanded(
            child: Text(
              "自动启用x次翻译并直接提交",
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[700],
              ),
            ),
          ),
          const SizedBox(width: 10),
          Container(
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey[300]!),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  icon: const Icon(Icons.remove, size: 18),
                  onPressed: _autoModeRunning
                      ? null
                      : () {
                          if (_autoTranslateCount > 1) {
                            setState(() {
                              _autoTranslateCount--;
                            });
                          }
                        },
                  padding: const EdgeInsets.all(4),
                  constraints: const BoxConstraints(),
                ),
                SizedBox(
                  width: 40,
                  child: TextField(
                    textAlign: TextAlign.center,
                    controller: TextEditingController(text: _autoTranslateCount.toString()),
                    keyboardType: TextInputType.number,
                    enabled: !_autoModeRunning,
                    onChanged: (value) {
                      final count = int.tryParse(value);
                      if (count != null && count > 0) {
                        setState(() {
                          _autoTranslateCount = count;
                        });
                      }
                    },
                    decoration: const InputDecoration(
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.zero,
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.add, size: 18),
                  onPressed: _autoModeRunning
                      ? null
                      : () {
                          setState(() {
                            _autoTranslateCount++;
                          });
                        },
                  padding: const EdgeInsets.all(4),
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
          ),
          const SizedBox(width: 10),
          ElevatedButton(
            onPressed: _autoModeRunning || _isLoading || (_translationCompleted && !_autoModeRunning)
                ? null
                : _startAutoTranslation,
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blueGrey,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            ),
            child: _autoModeRunning
                ? Text("$_currentAutoCount/$_autoTranslateCount")
                : const Text("启动"),
          ),
        ],
      ),
    );
  }
}
