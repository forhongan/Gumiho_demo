import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../models/project.dart';
import '../widgets/global_sidebar.dart';

class KnowledgeAwakScreen extends StatefulWidget {
  final Project project;
  const KnowledgeAwakScreen({Key? key, required this.project}) : super(key: key);

  @override
  State<KnowledgeAwakScreen> createState() => _KnowledgeAwakScreenState();
}

class _KnowledgeAwakScreenState extends State<KnowledgeAwakScreen> {
  static const String _baseUrl = 'http://127.0.0.1:5000';

  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  Timer? _debounce;
  bool _showSidebar = true;
  bool _isLoading = false;

  // Pagination
  int _currentPage = 1;
  final int _perPage = 20;

  List<dynamic> _allCards = [];

  // chapter list for AI generation
  bool _chaptersLoading = false;
  List<dynamic> _chapters = [];

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_handleScroll);
    _loadAllCards();
    _loadChapters();
  }

  InputDecoration _inputDecoration(
    BuildContext context, {
    String? label,
    String? hint,
    Widget? prefixIcon,
    Widget? suffixIcon,
  }) {
    final scheme = Theme.of(context).colorScheme;
    return InputDecoration(
      labelText: label,
      hintText: hint,
      prefixIcon: prefixIcon,
      suffixIcon: suffixIcon,
      filled: true,
      fillColor: scheme.surfaceVariant.withOpacity(0.35),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: scheme.outlineVariant),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: scheme.primary, width: 1.5),
      ),
      isDense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
    );
  }

  ButtonStyle _primaryButtonStyle(BuildContext context) {
    return ElevatedButton.styleFrom(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    );
  }

  ButtonStyle _secondaryButtonStyle(BuildContext context) {
    return OutlinedButton.styleFrom(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    );
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _handleScroll() {
    if (_scrollController.position.pixels >
        _scrollController.position.maxScrollExtent * 0.8) {
      _loadMore();
    }
  }

  void _loadMore() {
    if (_currentPage * _perPage < _allCards.length) {
      setState(() => _currentPage++);
    }
  }

  List<dynamic> get _visibleCards {
    final end = (_currentPage * _perPage).clamp(0, _allCards.length);
    return _allCards.sublist(0, end);
  }

  Future<void> _loadAllCards() async {
    await _performSearch('');
  }

  Future<void> _performSearch(String query) async {
    setState(() => _isLoading = true);

    final uri = Uri.parse(
      '$_baseUrl/ka/cards?q=${Uri.encodeQueryComponent(query)}&PNTPath=${Uri.encodeQueryComponent(widget.project.PNTPath)}',
    );

    try {
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _allCards = (data['cards'] as List?) ?? [];
          _currentPage = 1;
        });
      } else {
        _showSnack('加载失败：${response.body}');
      }
    } catch (e) {
      _showSnack('加载失败：$e');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _loadChapters() async {
    setState(() => _chaptersLoading = true);

    final uri = Uri.parse(
      '$_baseUrl/title_list?translatefilePath=${Uri.encodeQueryComponent(widget.project.translatefilePath)}',
    );

    try {
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _chapters = (data['chapters'] as List?) ?? [];
        });
      }
    } catch (_) {
      // 章节列表只用于 AI 辅助生成，失败不阻塞主流程
    } finally {
      if (mounted) setState(() => _chaptersLoading = false);
    }
  }

  Future<void> _upsertCard({String? id, required String expr, required String content, required bool enabled, Map<String, dynamic>? meta}) async {
    final uri = Uri.parse('$_baseUrl/ka/card');
    try {
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'PNTPath': widget.project.PNTPath,
          'card': {
            'id': id,
            'keyword_expr': expr,
            'knowledge_content': content,
            'enabled': enabled,
            if (meta != null) 'meta': meta,
          }
        }),
      );

      if (response.statusCode == 200) {
        await _performSearch(_searchController.text);
      } else {
        _showSnack('保存失败：${response.body}');
      }
    } catch (e) {
      _showSnack('保存失败：$e');
    }
  }

  Future<void> _deleteCard(String id) async {
    final uri = Uri.parse('$_baseUrl/ka/card/delete');
    try {
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'PNTPath': widget.project.PNTPath,
          'id': id,
        }),
      );

      if (response.statusCode == 200) {
        await _performSearch(_searchController.text);
      } else {
        _showSnack('删除失败：${response.body}');
      }
    } catch (e) {
      _showSnack('删除失败：$e');
    }
  }

  void _showSnack(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg)),
    );
  }

  void _insertToken(TextEditingController controller, String token) {
    final value = controller.value;
    final selection = value.selection;

    final text = value.text;
    final start = selection.isValid ? selection.start : text.length;
    final end = selection.isValid ? selection.end : text.length;

    final before = text.substring(0, start);
    final after = text.substring(end);

    String insert = token;
    // 给操作符左右补空格，减少拼接歧义
    if (token == 'AND' || token == 'OR' || token == 'NOT') {
      insert = ' $token ';
    }

    final newText = before + insert + after;
    final caret = (before + insert).length;

    controller.value = TextEditingValue(
      text: newText,
      selection: TextSelection.collapsed(offset: caret),
    );
  }

  Future<void> _showEditDialog({Map<String, dynamic>? card}) async {
    final isCreating = card == null;
    final id = isCreating ? null : (card['id']?.toString());

    final exprController = TextEditingController(text: (card?['keyword_expr'] ?? '').toString());
    final contentController = TextEditingController(text: (card?['knowledge_content'] ?? '').toString());
    bool enabled = (card?['enabled'] ?? true) == true;

    await showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              insetPadding: const EdgeInsets.all(16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              title: Text(isCreating ? '新增知识唤醒卡片' : '编辑知识唤醒卡片 - $id'),
              content: SizedBox(
                width: math.min(MediaQuery.of(context).size.width * 0.92, 760.0),
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: exprController,
                              decoration: _inputDecoration(
                                context,
                                label: '触发表达式（keyword_expr）',
                                hint: '示例：("王都" OR "帝都") AND NOT "误译"',
                              ),
                              minLines: 2,
                              maxLines: 4,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          OutlinedButton(
                            onPressed: () => _insertToken(exprController, 'AND'),
                            style: _secondaryButtonStyle(context),
                            child: const Text('AND'),
                          ),
                          OutlinedButton(
                            onPressed: () => _insertToken(exprController, 'OR'),
                            style: _secondaryButtonStyle(context),
                            child: const Text('OR'),
                          ),
                          OutlinedButton(
                            onPressed: () => _insertToken(exprController, 'NOT'),
                            style: _secondaryButtonStyle(context),
                            child: const Text('NOT'),
                          ),
                          OutlinedButton(
                            onPressed: () => _insertToken(exprController, '('),
                            style: _secondaryButtonStyle(context),
                            child: const Text('('),
                          ),
                          OutlinedButton(
                            onPressed: () => _insertToken(exprController, ')'),
                            style: _secondaryButtonStyle(context),
                            child: const Text(')'),
                          ),
                          OutlinedButton(
                            onPressed: () => _insertToken(exprController, '"关键词"'),
                            style: _secondaryButtonStyle(context),
                            child: const Text('"关键词"'),
                          ),
                          TextButton.icon(
                            onPressed: () async {
                              final generated = await _showAIGenerateDialog();
                              if (generated == null) return;
                              setDialogState(() {
                                final gExpr = (generated['keyword_expr'] ?? '').toString();
                                final gContent = (generated['knowledge_content'] ?? '').toString();
                                if (gExpr.isNotEmpty) exprController.text = gExpr;
                                if (gContent.isNotEmpty) contentController.text = gContent;
                              });
                            },
                            icon: const Icon(Icons.auto_awesome),
                            label: const Text('AI 辅助生成'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: contentController,
                        decoration: _inputDecoration(
                          context,
                          label: '触发后附带的知识内容（knowledge_content）',
                          hint: '写给模型看的补充设定/术语规范/一致性约束（尽量精炼）',
                        ),
                        minLines: 6,
                        maxLines: 12,
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Switch(
                            value: enabled,
                            onChanged: (v) => setDialogState(() => enabled = v),
                          ),
                          const SizedBox(width: 8),
                          const Text('启用该卡片'),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              actions: [
                if (!isCreating)
                  TextButton(
                    onPressed: () async {
                      final ok = await showDialog<bool>(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: const Text('确认删除？'),
                          content: const Text('删除后将无法恢复。'),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.pop(context, false),
                              child: const Text('取消'),
                            ),
                            ElevatedButton(
                              onPressed: () => Navigator.pop(context, true),
                              child: const Text('删除'),
                            ),
                          ],
                        ),
                      );
                      if (ok == true && id != null) {
                        await _deleteCard(id);
                        if (mounted) Navigator.pop(context);
                      }
                    },
                    child: const Text('删除'),
                  ),
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('取消'),
                ),
                ElevatedButton(
                  style: _primaryButtonStyle(context),
                  onPressed: () async {
                    await _upsertCard(
                      id: id,
                      expr: exprController.text.trim(),
                      content: contentController.text.trim(),
                      enabled: enabled,
                    );
                    if (mounted) Navigator.pop(context);
                  },
                  child: const Text('保存'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<Map<String, dynamic>?> _showAIGenerateDialog() async {
    final requirementController = TextEditingController();
    final keywordHintController = TextEditingController();

    final originalController = TextEditingController();
    final translatedController = TextEditingController();

    final startIdController = TextEditingController();
    final endIdController = TextEditingController();

    String? startTitle;
    String? endTitle;

    String status = 'translating';

    Future<Map<String, dynamic>?> callBuildText() async {
      final uri = Uri.parse('$_baseUrl/ka/build_ai_knowledge');
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'projectName': widget.project.name,
          'original_text': originalController.text,
          'translated_text': translatedController.text,
          'requirement': requirementController.text,
          'keyword_hint': keywordHintController.text.isEmpty ? null : keywordHintController.text,
          'status': status,
        }),
      );
      if (response.statusCode != 200) {
        throw Exception(response.body);
      }
      final data = jsonDecode(response.body);
      return (data['result'] as Map?)?.cast<String, dynamic>();
    }

    Future<Map<String, dynamic>?> callBuildRange() async {
      final uri = Uri.parse('$_baseUrl/ka/build_ai_knowledge_from_range');
      final startId = int.tryParse(startIdController.text.trim());
      final endId = int.tryParse(endIdController.text.trim());
      if (startId == null || endId == null) {
        throw Exception('start_id/end_id 需要是整数');
      }
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'projectName': widget.project.name,
          'start_id': startId,
          'end_id': endId,
          'requirement': requirementController.text,
          'keyword_hint': keywordHintController.text.isEmpty ? null : keywordHintController.text,
          'status': status,
        }),
      );
      if (response.statusCode != 200) {
        throw Exception(response.body);
      }
      final data = jsonDecode(response.body);
      return (data['result'] as Map?)?.cast<String, dynamic>();
    }

    Future<Map<String, dynamic>?> callBuildChapters() async {
      if ((startTitle ?? '').isEmpty || (endTitle ?? '').isEmpty) {
        throw Exception('请选择起止章节');
      }
      final uri = Uri.parse('$_baseUrl/ka/build_ai_knowledge_from_chapters');
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'projectName': widget.project.name,
          'start_title': startTitle,
          'end_title': endTitle,
          'requirement': requirementController.text,
          'keyword_hint': keywordHintController.text.isEmpty ? null : keywordHintController.text,
          'status': status,
        }),
      );
      if (response.statusCode != 200) {
        throw Exception(response.body);
      }
      final data = jsonDecode(response.body);
      return (data['result'] as Map?)?.cast<String, dynamic>();
    }

    return showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) {
        final size = MediaQuery.of(context).size;
        final double dialogMaxWidth = math.min(size.width * 0.94, 900.0).toDouble();
        final double dialogMaxHeight = math.min(size.height * 0.86, 760.0).toDouble();
        final double tabHeight = math
          .min(360.0, math.max(240.0, dialogMaxHeight * 0.48))
          .toDouble();

        return DefaultTabController(
          length: 3,
          child: StatefulBuilder(
            builder: (context, setDialogState) {
              return AlertDialog(
                insetPadding: const EdgeInsets.all(16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                title: const Text('AI 辅助生成知识卡片'),
                content: SizedBox(
                  width: dialogMaxWidth,
                  child: ConstrainedBox(
                    constraints: BoxConstraints(maxHeight: dialogMaxHeight),
                    child: SingleChildScrollView(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          TextField(
                            controller: requirementController,
                            decoration: _inputDecoration(
                              context,
                              label: '生成要求（必填）',
                              hint: '例如：统一译名、世界观设定、术语规范',
                            ),
                            minLines: 2,
                            maxLines: 4,
                          ),
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              Expanded(
                                child: TextField(
                                  controller: keywordHintController,
                                  decoration: _inputDecoration(
                                    context,
                                    label: 'keyword_hint（可选）',
                                    hint: '若你已确定触发条件，可在此提示',
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
                                decoration: BoxDecoration(
                                  color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.35),
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
                                ),
                                child: DropdownButtonHideUnderline(
                                  child: DropdownButton<String>(
                                    value: status,
                                    items: const [
                                      DropdownMenuItem(value: 'translating', child: Text('translating')),
                                      DropdownMenuItem(value: 'proofreading', child: Text('proofreading')),
                                    ],
                                    onChanged: (v) {
                                      if (v == null) return;
                                      setDialogState(() => status = v);
                                    },
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          const TabBar(
                            tabs: [
                              Tab(text: '原文/译文'),
                              Tab(text: 'ID 范围'),
                              Tab(text: '章节范围'),
                            ],
                          ),
                          SizedBox(
                            height: tabHeight,
                            child: TabBarView(
                              children: [
                                // 原文/译文
                                SingleChildScrollView(
                                  padding: const EdgeInsets.only(top: 10),
                                  child: Column(
                                    children: [
                                      TextField(
                                        controller: originalController,
                                        decoration: _inputDecoration(
                                          context,
                                          label: '原文（可空）',
                                        ),
                                        minLines: 4,
                                        maxLines: 8,
                                      ),
                                      const SizedBox(height: 10),
                                      TextField(
                                        controller: translatedController,
                                        decoration: _inputDecoration(
                                          context,
                                          label: '译文（可空）',
                                        ),
                                        minLines: 4,
                                        maxLines: 8,
                                      ),
                                    ],
                                  ),
                                ),
                                // ID 范围
                                SingleChildScrollView(
                                  padding: const EdgeInsets.only(top: 10),
                                  child: Row(
                                    children: [
                                      Expanded(
                                        child: TextField(
                                          controller: startIdController,
                                          decoration: _inputDecoration(
                                            context,
                                            label: 'start_id',
                                            hint: '例如：120',
                                          ),
                                          keyboardType: TextInputType.number,
                                        ),
                                      ),
                                      const SizedBox(width: 10),
                                      Expanded(
                                        child: TextField(
                                          controller: endIdController,
                                          decoration: _inputDecoration(
                                            context,
                                            label: 'end_id',
                                            hint: '例如：220',
                                          ),
                                          keyboardType: TextInputType.number,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                // 章节范围
                                SingleChildScrollView(
                                  padding: const EdgeInsets.only(top: 10),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          TextButton.icon(
                                            onPressed: _chaptersLoading
                                                ? null
                                                : () async {
                                                    await _loadChapters();
                                                    setDialogState(() {});
                                                  },
                                            icon: const Icon(Icons.refresh),
                                            label: const Text('刷新章节列表'),
                                          ),
                                          if (_chaptersLoading)
                                            const Padding(
                                              padding: EdgeInsets.only(left: 8.0),
                                              child: SizedBox(
                                                width: 18,
                                                height: 18,
                                                child: CircularProgressIndicator(strokeWidth: 2),
                                              ),
                                            ),
                                        ],
                                      ),
                                      const SizedBox(height: 6),
                                      DropdownButtonFormField<String>(
                                        value: startTitle,
                                        decoration: _inputDecoration(
                                          context,
                                          label: '起始章节',
                                        ),
                                        items: _chapters
                                            .map((c) => (c is Map ? c['title'] : null))
                                            .where((t) => t != null)
                                            .map<DropdownMenuItem<String>>(
                                              (t) => DropdownMenuItem<String>(
                                                value: t.toString(),
                                                child: Text(t.toString(), overflow: TextOverflow.ellipsis),
                                              ),
                                            )
                                            .toList(),
                                        onChanged: (v) => setDialogState(() => startTitle = v),
                                      ),
                                      const SizedBox(height: 10),
                                      DropdownButtonFormField<String>(
                                        value: endTitle,
                                        decoration: _inputDecoration(
                                          context,
                                          label: '结束章节',
                                        ),
                                        items: _chapters
                                            .map((c) => (c is Map ? c['title'] : null))
                                            .where((t) => t != null)
                                            .map<DropdownMenuItem<String>>(
                                              (t) => DropdownMenuItem<String>(
                                                value: t.toString(),
                                                child: Text(t.toString(), overflow: TextOverflow.ellipsis),
                                              ),
                                            )
                                            .toList(),
                                        onChanged: (v) => setDialogState(() => endTitle = v),
                                      ),
                                      const SizedBox(height: 8),
                                      const Text(
                                        '说明：将按章节标题解析范围，并让后端自动换算 end_id。',
                                        style: TextStyle(color: Colors.grey),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('取消'),
                  ),
                  ElevatedButton.icon(
                    style: _primaryButtonStyle(context),
                    onPressed: () async {
                      final req = requirementController.text.trim();
                      if (req.isEmpty) {
                        _showSnack('请先填写生成要求');
                        return;
                      }

                      try {
                        final tabIndex = DefaultTabController.of(context).index;
                        Map<String, dynamic>? result;
                        if (tabIndex == 0) {
                          result = await callBuildText();
                        } else if (tabIndex == 1) {
                          result = await callBuildRange();
                        } else {
                          result = await callBuildChapters();
                        }
                        Navigator.pop(context, result);
                      } catch (e) {
                        _showSnack('生成失败：$e');
                      }
                    },
                    icon: const Icon(Icons.auto_awesome),
                    label: const Text('生成并应用'),
                  )
                ],
              );
            },
          ),
        );
      },
    );
  }

  Widget _buildPaginationControls() {
    final totalPages = (_allCards.length / _perPage).ceil().clamp(1, 1 << 30);
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IconButton(
          icon: const Icon(Icons.chevron_left),
          onPressed: _currentPage > 1 ? () => setState(() => _currentPage--) : null,
        ),
        Text('第 $_currentPage 页 / 共 $totalPages 页'),
        IconButton(
          icon: const Icon(Icons.chevron_right),
          onPressed: _currentPage * _perPage < _allCards.length ? () => setState(() => _currentPage++) : null,
        ),
      ],
    );
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
                AppBar(
                  title: Text('知识卡片库（实验性） - ${widget.project.name}'),
                  actions: [
                    IconButton(
                      icon: const Icon(Icons.settings),
                      onPressed: () => setState(() => _showSidebar = !_showSidebar),
                    ),
                    IconButton(
                      icon: const Icon(Icons.refresh),
                      onPressed: _isLoading ? null : () => _performSearch(_searchController.text),
                    ),
                  ],
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                  child: Row(
                    children: [
                      ElevatedButton.icon(
                        onPressed: () => _showEditDialog(card: null),
                        icon: const Icon(Icons.add),
                        label: const Text('新增知识唤醒卡片'),
                        style: _primaryButtonStyle(context),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextField(
                          controller: _searchController,
                          decoration: _inputDecoration(
                            context,
                            hint: '搜索（id / 表达式 / 内容）',
                            prefixIcon: const Icon(Icons.search),
                            suffixIcon: _isLoading
                                ? const Padding(
                                    padding: EdgeInsets.all(12),
                                    child: SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(strokeWidth: 2),
                                    ),
                                  )
                                : (_searchController.text.isNotEmpty
                                    ? IconButton(
                                        icon: const Icon(Icons.clear),
                                        onPressed: () {
                                          _searchController.clear();
                                          _performSearch('');
                                          setState(() {});
                                        },
                                      )
                                    : null),
                          ),
                          onChanged: (value) {
                            _debounce?.cancel();
                            _debounce = Timer(const Duration(milliseconds: 450), () {
                              _performSearch(value);
                            });
                          },
                        ),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: ListView.builder(
                    controller: _scrollController,
                    itemCount: _visibleCards.length + 1,
                    itemBuilder: (context, index) {
                      if (index == _visibleCards.length) {
                        final hasMore = _currentPage * _perPage < _allCards.length;
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          child: Center(
                            child: hasMore
                                ? const CircularProgressIndicator()
                                : const Text('已经到底啦~', style: TextStyle(color: Colors.grey)),
                          ),
                        );
                      }

                      final card = _visibleCards[index];
                      if (card is! Map) {
                        return const SizedBox.shrink();
                      }
                      final map = card.cast<String, dynamic>();
                      final id = (map['id'] ?? '').toString();
                      final enabled = (map['enabled'] ?? true) == true;
                      final expr = (map['keyword_expr'] ?? '').toString();
                      final content = (map['knowledge_content'] ?? '').toString();

                      String contentPreview = content.trim();
                      if (contentPreview.length > 120) {
                        contentPreview = contentPreview.substring(0, 120) + '…';
                      }

                      return Card(
                        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        elevation: 2,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        child: ListTile(
                          title: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  '[$id] ${enabled ? "启用" : "禁用"}',
                                  style: const TextStyle(fontWeight: FontWeight.w600),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Icon(
                                enabled ? Icons.check_circle : Icons.block,
                                size: 18,
                                color: enabled ? Colors.green : Colors.grey,
                              ),
                            ],
                          ),
                          subtitle: Padding(
                            padding: const EdgeInsets.only(top: 8),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                if (expr.trim().isNotEmpty) ...[
                                  Text('表达式：$expr', maxLines: 2, overflow: TextOverflow.ellipsis),
                                  const SizedBox(height: 6),
                                ],
                                if (contentPreview.isNotEmpty)
                                  Text('内容：$contentPreview', maxLines: 3, overflow: TextOverflow.ellipsis),
                              ],
                            ),
                          ),
                          trailing: const Icon(Icons.edit),
                          onTap: () => _showEditDialog(card: map),
                        ),
                      );
                    },
                  ),
                ),
                _buildPaginationControls(),
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text('共找到 ${_allCards.length} 条卡片', style: const TextStyle(color: Colors.grey)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
