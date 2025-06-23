import 'package:flutter/material.dart';
import 'package:socket_io_client/socket_io_client.dart' as IO;
import '../models/project.dart';
import 'select_screen.dart';
import '../widgets/global_sidebar.dart';
import 'create_nproject_screen.dart'; // 新增导入
import 'package:flutter_svg/flutter_svg.dart';
import 'package:shimmer/shimmer.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);
  
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  IO.Socket? socket;
  List<Project> _projects = [];
  bool _showSidebar = true;
  bool _isLoading = true; // 新增加载状态

  @override
  void initState() {
    super.initState();
    socket = IO.io('http://127.0.0.1:5000', <String, dynamic>{
      'transports': ['websocket'],
      'autoConnect': true,
    });
    socket!.onConnect((_) {
      print('WebSocket connected');
    });
    socket!.on('projects_update', (data) {
      List<Project> projectsFromSocket = [];
      if (data is List) {
        projectsFromSocket = data.map((proj) => Project.fromJson(proj)).toList();
      }
      setState(() {
        _projects = projectsFromSocket;
        _isLoading = false; // 加载完成
      });
    });
  }
  
  @override
  void dispose() {
    socket?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // 移除系统 AppBar
      body: Row(
        children: [
          if (_showSidebar)
            GlobalSidebar(
              onClose: () => setState(() => _showSidebar = false), // 新增关闭回调
              project: null, // 根据实际情况传递项目
            ),
          if (_showSidebar)
            const VerticalDivider(width: 1),
          Expanded(
            child: Column(
              children: [
                // 修改顶部工具栏：增加阴影及左右间距
                Container(
                  height: kToolbarHeight + 8,
                  decoration: BoxDecoration(
                    color: Theme.of(context).primaryColor,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black12,
                        blurRadius: 8,
                        offset: Offset(0, 2)
                      )
                    ]
                  ),
                  child: Row(
                    children: [
                      SizedBox(width: 16),
                      IconButton(
                        icon: Icon(_showSidebar ? Icons.arrow_back_ios : Icons.menu),
                        onPressed: () { setState(() { _showSidebar = !_showSidebar; }); },
                        color: Colors.white,
                      ),
                      const SizedBox(width: 8),
                      const Text(
                        '工程项目列表',
                        style: TextStyle(
                          color: Colors.white, 
                          fontSize: 20,
                          fontWeight: FontWeight.w500
                        )
                      ),
                      Spacer(),
                      ElevatedButton.icon(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => CreateNProjectScreen()),
                          );
                        },
                        icon: Icon(Icons.add, size: 20),
                        label: Text("创建新项目"),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: Theme.of(context).primaryColor,
                          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                          ),
                        ),
                      ),
                      SizedBox(width: 20),
                    ],
                  ),
                ),
                Expanded(
                  child: _isLoading 
                    ? _buildSkeletonLoader()
                    : _projects.isEmpty
                        ? _buildEmptyState()
                        : _buildProjectList(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildProjectList() {
    return ListView.builder(
      itemCount: _projects.length,
      itemBuilder: (context, index) {
        final project = _projects[index];
        return Padding(
          padding: EdgeInsets.symmetric(vertical: 4, horizontal: 8),
          child: Card(
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            child: InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: () => _navigateToProject(project),
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Stack(
                  children: [
                    Row(
                      children: [
                        Icon(Icons.folder, color: Colors.amber[700], size: 32),
                        SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                project.name,
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w600
                                )
                              ),
                            ],
                          ),
                        ),
                        Icon(Icons.chevron_right, color: Colors.grey[400]),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
  
  Widget _buildSkeletonLoader() {
    return ListView.builder(
      itemCount: 5,
      itemBuilder: (_, index) => Padding(
        padding: EdgeInsets.all(8),
        child: Shimmer.fromColors(
          baseColor: Colors.grey[200]!,
          highlightColor: Colors.grey[100]!,
          child: Container(
            height: 80,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12)
            ),
          ),
        ),
      ),
    );
  }
  
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SvgPicture.asset(
            'assets/empty-state.svg',
            width: 200,
            color: Colors.grey[400],
          ),
          SizedBox(height: 20),
          Text(
            '暂无项目',
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey[600]
            )
          ),
          SizedBox(height: 8),
          Text(
            '点击下方按钮创建第一个项目',
            style: TextStyle(
              color: Colors.grey[500]
            )
          ),
        ],
      ),
    );
  }
  
  void _navigateToProject(Project project) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => SelectScreen(
          project: project,
          embed: false,
        ),
      ),
    );
  }
  
}
