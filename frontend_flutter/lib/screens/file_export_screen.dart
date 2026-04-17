import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import '../models/project.dart';
import '../widgets/global_sidebar.dart';

class FileExportScreen extends StatefulWidget {
  final Project project; // 新增接收 project
  const FileExportScreen({Key? key, required this.project}) : super(key: key);
  @override
  _FileExportScreenState createState() => _FileExportScreenState();
}

class _FileExportScreenState extends State<FileExportScreen> {
  List<dynamic> chapters = [];
  String exportScope = "translated_only"; // all | translated_only
  String? startChapter;
  String? endChapter;

  String exportFormat = "txt"; // txt | epub
  bool includeOriginal = false;
  String epubRebuildMode = "refilled"; // refilled | rebuild
  bool hasSourceEpub = false;

  bool _showSidebar = true;
  bool _isLoadingChapters = false;
  bool _isExporting = false;
  String? _lastOutputPath;

  Future<void> _openLastOutputDirectory() async {
    final outputPath = _lastOutputPath;
    if (outputPath == null || outputPath.trim().isEmpty) return;

    final dirPath = File(outputPath).parent.path;
    try {
      if (Platform.isWindows) {
        await Process.run('explorer', [dirPath]);
      } else if (Platform.isMacOS) {
        await Process.run('open', [dirPath]);
      } else if (Platform.isLinux) {
        await Process.run('xdg-open', [dirPath]);
      } else {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('当前平台不支持打开目录')),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('打开目录失败: $e')),
      );
    }
  }

  @override
  void initState() {
    super.initState();
    fetchChapters();
    fetchExportCapabilities();
  }

  Uri _buildUri(String path, Map<String, String> query) {
    final base = Uri.parse('http://127.0.0.1:5000$path');
    return base.replace(queryParameters: query);
  }

  Future<void> fetchExportCapabilities() async {
    final uri = _buildUri('/export_capabilities', {
      'translatefilePath': widget.project.translatefilePath,
    });
    try {
      if (kDebugMode) {
        debugPrint('[EXPORT][capabilities] GET $uri');
      }
      final response = await http.get(uri);
      if (kDebugMode) {
        final preview = utf8.decode(response.bodyBytes, allowMalformed: true);
        debugPrint(
          '[EXPORT][capabilities] status=${response.statusCode} bodyPreview=${preview.length > 200 ? preview.substring(0, 200) : preview}',
        );
        debugPrint(
          '[EXPORT][capabilities] content-type=${response.headers['content-type']} x-gumiho-marker=${response.headers['x-gumiho-marker']}',
        );
      }
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          hasSourceEpub = data['has_source_epub'] == true;
          if (!hasSourceEpub && epubRebuildMode == 'refilled') {
            epubRebuildMode = 'rebuild';
          }
        });
      }
    } catch (_) {
      // 静默失败：不阻塞页面
    }
  }

  Future<void> fetchChapters() async {
    setState(() => _isLoadingChapters = true);
    final uri = _buildUri('/translatefile', {
      'translatefilePath': widget.project.translatefilePath,
      'target_state': exportScope,
    });

    try {
      if (kDebugMode) {
        debugPrint('[EXPORT][chapters] GET $uri');
      }
      final response = await http.get(uri);
      if (kDebugMode) {
        final preview = utf8.decode(response.bodyBytes, allowMalformed: true);
        debugPrint(
          '[EXPORT][chapters] status=${response.statusCode} bodyPreview=${preview.length > 200 ? preview.substring(0, 200) : preview}',
        );
        debugPrint(
          '[EXPORT][chapters] content-type=${response.headers['content-type']} x-gumiho-marker=${response.headers['x-gumiho-marker']}',
        );
      }
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final newChapters = (data['chapters'] as List<dynamic>? ?? []);

        setState(() {
          chapters = newChapters;

          final titles = newChapters.map((c) => c['title'] as String).toList();
          if (titles.isEmpty) {
            startChapter = null;
            endChapter = null;
          } else {
            // 尽量保留用户选择，否则默认首尾
            if (startChapter == null || !titles.contains(startChapter)) {
              startChapter = titles.first;
            }
            if (endChapter == null || !titles.contains(endChapter)) {
              endChapter = titles.last;
            }
          }
        });
      } else {
        setState(() {
          chapters = [];
          startChapter = null;
          endChapter = null;
        });
      }
    } finally {
      if (mounted) setState(() => _isLoadingChapters = false);
    }
  }

  Future<void> submitExport() async {
    if (startChapter == null || endChapter == null) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('请选择起始与结束章节')));
      return;
    }

    final titles = chapters.map((c) => c['title'] as String).toList();
    final startIndex = titles.indexOf(startChapter!);
    final endIndex = titles.indexOf(endChapter!);
    if (startIndex == -1 || endIndex == -1 || startIndex > endIndex) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('章节范围不合法：起始章节需在结束章节之前')));
      return;
    }

    if (exportFormat == 'epub' &&
        epubRebuildMode == 'refilled' &&
        !hasSourceEpub) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('未检测到源 EPUB，无法使用“原样重构”')));
      return;
    }

    setState(() => _isExporting = true);
    final uri = _buildUri('/export_text', {});
    final body = {
      'start_title': startChapter,
      'end_title': endChapter,
      'export_scope': exportScope,
      'export_format': exportFormat,
      'include_original': includeOriginal,
      'epub_rebuild_mode': epubRebuildMode,
      'translatefilePath': widget.project.translatefilePath,
    };

    try {
      if (kDebugMode) {
        debugPrint('[EXPORT][submit] POST $uri body=${json.encode(body)}');
      }
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode(body),
      );

      if (kDebugMode) {
        final preview = utf8.decode(response.bodyBytes, allowMalformed: true);
        debugPrint(
          '[EXPORT][submit] status=${response.statusCode} bodyPreview=${preview.length > 200 ? preview.substring(0, 200) : preview}',
        );
        debugPrint(
          '[EXPORT][submit] content-type=${response.headers['content-type']} x-gumiho-marker=${response.headers['x-gumiho-marker']}',
        );
      }

      // 后端如果抛异常，Flask 可能会返回 HTML；这里要兜底，避免 FormatException。
      final rawBody = utf8.decode(response.bodyBytes, allowMalformed: true);
      dynamic result;
      try {
        result = json.decode(rawBody);
      } catch (_) {
        final preview = rawBody.length > 200 ? rawBody.substring(0, 200) : rawBody;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              '导出失败：服务器返回非JSON（HTTP ${response.statusCode}）\n$preview',
            ),
          ),
        );
        return;
      }

      if (response.statusCode == 200) {
        setState(() => _lastOutputPath = result['output_path'] as String?);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('导出成功：${result['output_path']}')),
        );
      } else {
        final errMsg = (result is Map)
            ? (result['error']?.toString() ?? '导出失败')
            : '导出失败（HTTP ${response.statusCode}）';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(errMsg)),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('连接错误: $e')));
    } finally {
      if (mounted) setState(() => _isExporting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    final chapterItems =
        chapters.map<DropdownMenuItem<String>>((ch) {
          final title = ch['title'] as String;
          final status = (ch['status'] as String?) ?? 'unfinished';
          final isTranslated = status == 'translated';
          return DropdownMenuItem(
            value: title,
            child: Text(
              title,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color:
                    exportScope == 'all' && !isTranslated
                        ? Colors.grey
                        : Colors.black,
              ),
            ),
          );
        }).toList();

    Widget buildForm() {
      return SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              Card(
                elevation: 2,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '导出设置',
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        value: exportScope,
                        decoration: const InputDecoration(
                          labelText: '导出范围',
                          border: OutlineInputBorder(),
                        ),
                        items: const [
                          DropdownMenuItem(value: 'all', child: Text('全部文本')),
                          DropdownMenuItem(
                            value: 'translated_only',
                            child: Text('仅导出已翻译'),
                          ),
                        ],
                        onChanged: (value) {
                          if (value == null) return;
                          setState(() => exportScope = value);
                          fetchChapters();
                        },
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        value: exportFormat,
                        decoration: const InputDecoration(
                          labelText: '输出格式',
                          border: OutlineInputBorder(),
                        ),
                        items: const [
                          DropdownMenuItem(value: 'txt', child: Text('TXT')),
                          DropdownMenuItem(value: 'epub', child: Text('EPUB')),
                        ],
                        onChanged: (value) {
                          if (value == null) return;
                          setState(() => exportFormat = value);
                          if (value == 'epub') {
                            fetchExportCapabilities();
                          }
                        },
                      ),
                      const SizedBox(height: 8),
                      CheckboxListTile(
                        contentPadding: EdgeInsets.zero,
                        value: includeOriginal,
                        onChanged:
                            (v) => setState(() => includeOriginal = v ?? false),
                        title: const Text('保留原文（原文 + 译文）'),
                      ),
                      if (exportFormat == 'epub') ...[
                        const SizedBox(height: 8),
                        Text(
                          'EPUB 重构模式',
                          style: theme.textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        RadioListTile<String>(
                          value: 'refilled',
                          groupValue: epubRebuildMode,
                          onChanged:
                              hasSourceEpub
                                  ? (v) => setState(
                                    () => epubRebuildMode = v ?? 'refilled',
                                  )
                                  : null,
                          title: const Text('原样重构（保留原 EPUB 结构）'),
                          subtitle:
                              hasSourceEpub
                                  ? null
                                  : const Text('需要存在源 EPUB 文件'),
                        ),
                        RadioListTile<String>(
                          value: 'rebuild',
                          groupValue: epubRebuildMode,
                          onChanged:
                              (v) => setState(
                                () => epubRebuildMode = v ?? 'rebuild',
                              ),
                          title: const Text('全新重构（不保留原结构）'),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Card(
                elevation: 2,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '章节范围',
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          IconButton(
                            tooltip: '刷新章节列表',
                            onPressed: fetchChapters,
                            icon: const Icon(Icons.refresh),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (_isLoadingChapters)
                        const LinearProgressIndicator(minHeight: 2)
                      else
                        const SizedBox(height: 2),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        value: startChapter,
                        isExpanded: true,
                        decoration: const InputDecoration(
                          labelText: '起始章节',
                          border: OutlineInputBorder(),
                        ),
                        items: chapterItems,
                        onChanged:
                            (value) => setState(() => startChapter = value),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        value: endChapter,
                        isExpanded: true,
                        decoration: const InputDecoration(
                          labelText: '结束章节',
                          border: OutlineInputBorder(),
                        ),
                        items: chapterItems,
                        onChanged:
                            (value) => setState(() => endChapter = value),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _isExporting ? null : submitExport,
                  icon:
                      _isExporting
                          ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                          : const Icon(Icons.download),
                  label: Text(_isExporting ? '导出中…' : '开始导出'),
                ),
              ),
              if (_lastOutputPath != null) ...[
                const SizedBox(height: 12),
                Card(
                  color: theme.colorScheme.surface,
                  child: ListTile(
                    leading: const Icon(Icons.check_circle_outline),
                    title: const Text('最近一次导出路径'),
                    subtitle: Row(
                      children: [
                        Expanded(
                          child: Text(
                            _lastOutputPath!,
                            maxLines: 3,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 8),
                        OutlinedButton.icon(
                          onPressed: _openLastOutputDirectory,
                          icon: const Icon(Icons.folder_open),
                          label: const Text('打开目录'),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      );
    }

    return Scaffold(
      body: Row(
        children: [
          if (_showSidebar)
            GlobalSidebar(
              project: widget.project,
              onClose: () => setState(() => _showSidebar = false),
              isHomeScreen: false,
            ),
          if (_showSidebar) const VerticalDivider(width: 1),
          Expanded(
            child: Column(
              children: [
                Container(
                  height: kToolbarHeight,
                  color: theme.primaryColor,
                  child: Row(
                    children: [
                      IconButton(
                        icon: Icon(
                          _showSidebar
                              ? Icons.arrow_back_ios
                              : Icons.arrow_back,
                        ),
                        onPressed: () => Navigator.pop(context),
                        color: Colors.white,
                      ),
                      const Expanded(
                        child: Center(
                          child: Text(
                            '导出文本/电子书',
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
                        onPressed: () {
                          fetchChapters();
                          fetchExportCapabilities();
                        },
                        color: Colors.white,
                      ),
                    ],
                  ),
                ),
                Expanded(child: buildForm()),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
