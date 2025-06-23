import 'dart:convert';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../models/project.dart';
import '../widgets/global_sidebar.dart';

class PNTScreen extends StatefulWidget {
  final Project project;
  const PNTScreen({Key? key, required this.project}) : super(key: key);

  @override
  _PNTScreenState createState() => _PNTScreenState();
}

class _PNTScreenState extends State<PNTScreen> {
  final TextEditingController _searchController = TextEditingController();
  List<dynamic> _searchResults = [];
  bool _showSidebar = true;
  bool _isLoading = false;
  Timer? _debounce;

  // 新增分页状态和滚动控制器
  int _currentPage = 1;
  int _perPage = 20;
  List<dynamic> _allResults = [];
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_handleScroll);
    _loadAllData(); // 初始加载全部数据
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadAllData() async {
    setState(() => _isLoading = true);
    final uri = Uri.parse(
      'http://127.0.0.1:5000/pnt/characters_by_str?str=&PNTPath=${widget.project.PNTPath}'
    );
    try {
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _allResults = data['characters'];
          _currentPage = 1; // 重置到第一页
        });
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _handleScroll() {
    // 滚动到80%位置时预加载更多数据
    if (_scrollController.position.pixels >
        _scrollController.position.maxScrollExtent * 0.8) {
      _loadMoreData();
    }
  }

  void _loadMoreData() {
    if (_currentPage * _perPage < _allResults.length) {
      setState(() => _currentPage++);
    }
  }

  List<dynamic> get _visibleResults {
    final end = (_currentPage * _perPage).clamp(0, _allResults.length);
    return _allResults.sublist(0, end);
  }

  Future<void> _performSearch(String query) async {
    if (query.isEmpty) {
      setState(() => _searchResults = []);
      return;
    }

    setState(() => _isLoading = true);
    
    final uri = Uri.parse(
      'http://127.0.0.1:5000/pnt/characters_by_str?str=$query&PNTPath=${widget.project.PNTPath}'
    );

    try {
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _allResults = data['characters'];
          _currentPage = 1; // 搜索后回到第一页
        });
      }
    } catch (e) {
      print('搜索错误: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _updateEntry(Map<String, dynamic> updatedEntry) async {
    final uri = Uri.parse('http://127.0.0.1:5000/pnt');
    try {
      // 获取完整数据
      final currentData = await http.get(Uri.parse(
        'http://127.0.0.1:5000/pnt?PNTPath=${widget.project.PNTPath}'
      ));

      if (currentData.statusCode != 200) throw Exception('数据获取失败');
      
      final fullData = jsonDecode(currentData.body);
      final translations = List.from(fullData['translation_table']);
      
      // 更新对应条目
      final index = translations.indexWhere(
        (e) => e['name'] == updatedEntry['name']);
      if (index != -1) translations[index] = updatedEntry;

      // 保存更新
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          "PNTPath": widget.project.PNTPath,
          "content": jsonEncode({'translation_table': translations}),
        }),
      );

      if (response.statusCode == 200) {
        _performSearch(_searchController.text); // 刷新搜索结果
      }
    } catch (e) {
      print('更新失败: $e');
    }
  }

  void _showEditDialog(Map<String, dynamic> entry) {
    final nameController = TextEditingController(text: entry['name']);
    final transController = TextEditingController(text: entry['translation']);
    final descController = TextEditingController(text: entry['describe']);
    final appearancesController = TextEditingController(
      text: (entry['appearances'] as List).join('\n'));

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('编辑条目 - ${entry['name']}'),
        content: SingleChildScrollView(
          child: Column(
            children: [
              _buildTextField('名称', nameController),
              _buildTextField('译名', transController),
              _buildTextField('描述', descController, maxLines: 3),
              _buildTextField('出现章节（每行一章）', appearancesController, maxLines: 5),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('取消'),
          ),
          ElevatedButton(
            onPressed: () {
              final updated = {
                ...entry,
                'name': nameController.text,
                'translation': transController.text,
                'describe': descController.text,
                'appearances': appearancesController.text.split('\n'),
              };
              _updateEntry(updated);
              Navigator.pop(context);
            },
            child: Text('保存'),
          ),
        ],
      ),
    );
  }

  Widget _buildTextField(String label, TextEditingController controller,
      {int maxLines = 1}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: TextField(
        controller: controller,
        decoration: InputDecoration(
          labelText: label,
          border: OutlineInputBorder(),
        ),
        maxLines: maxLines,
      ),
    );
  }

  Widget _buildPaginationControls() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IconButton(
          icon: Icon(Icons.chevron_left),
          onPressed: _currentPage > 1 
              ? () => setState(() => _currentPage--) 
              : null,
        ),
        Text('第 $_currentPage 页 / 共 ${(_allResults.length / _perPage).ceil()} 页'),
        IconButton(
          icon: Icon(Icons.chevron_right),
          onPressed: _currentPage * _perPage < _allResults.length 
              ? () => setState(() => _currentPage++) 
              : null,
        ),
      ],
    );
  }

  Widget _buildLoadMoreIndicator() {
    final hasMore = _currentPage * _perPage < _allResults.length;
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 16),
      child: Center(
        child: hasMore 
            ? CircularProgressIndicator() 
            : Text('已经到底啦~', style: TextStyle(color: Colors.grey)),
      ),
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
                  title: Text('专有名词管理 - ${widget.project.name}'),
                  actions: [
                    IconButton(
                      icon: Icon(Icons.settings),
                      onPressed: () => setState(() => _showSidebar = !_showSidebar),
                    ),
                  ],
                ),
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: TextField(
                    controller: _searchController,
                    decoration: InputDecoration(
                      hintText: '输入关键词搜索（名称、译名、描述）',
                      prefixIcon: Icon(Icons.search),
                      border: OutlineInputBorder(),
                      suffixIcon: _isLoading
                          ? CircularProgressIndicator()
                          : null,
                    ),
                    onChanged: (value) {
                      _debounce?.cancel();
                      _debounce = Timer(Duration(milliseconds: 500), () {
                        _performSearch(value);
                      });
                    },
                  ),
                ),
                Expanded(
                  child: ListView.builder(
                    controller: _scrollController,
                    itemCount: _visibleResults.length + 1,
                    itemBuilder: (context, index) {
                      if (index == _visibleResults.length) {
                        return _buildLoadMoreIndicator();
                      }
                      final entry = _visibleResults[index];
                      return Card(
                        margin: EdgeInsets.symmetric(
                            horizontal: 16, vertical: 8),
                        child: ListTile(
                          title: Text('${entry['name']} (${entry['translation']})'),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(entry['describe']),
                              SizedBox(height: 8),
                              Wrap(
                                spacing: 4,
                                children: (entry['appearances'] as List)
                                    .map<Chip>((e) => Chip(
                                          label: Text(e),
                                          visualDensity: VisualDensity.compact,
                                        ))
                                    .toList(),
                              ),
                            ],
                          ),
                          trailing: IconButton(
                            icon: Icon(Icons.edit),
                            onPressed: () => _showEditDialog(
                                Map<String, dynamic>.from(entry)),
                          ),
                        ),
                      );
                    },
                  ),
                ),
                _buildPaginationControls(),
                Text('共找到 ${_allResults.length} 条结果', 
                  style: TextStyle(color: Colors.grey)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
