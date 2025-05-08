import 'package:flutter/material.dart';
import '../models/project.dart';
import 'config_screen.dart';
import 'frecord_screen.dart';
import 'PNT_screen.dart';
import 'translatefile_screen.dart';
import '../widgets/global_sidebar.dart';
import 'file_export_screen.dart';  // 新增导入
import 'translating_screen.dart';
// import 'home_screen.dart'; // 新增导入，用于返回主界面

class SelectScreen extends StatefulWidget {
  final Project project;
  final bool embed;
  
  const SelectScreen({
    Key? key,
    required this.project,
    this.embed = false, // 默认全屏模式
  }) : super(key: key);
  
  @override
  _SelectScreenState createState() => _SelectScreenState();
}

class _SelectScreenState extends State<SelectScreen> {
  bool _showSidebar = true;

  // 修改 _buildContent 方法
  Widget _buildContent(BuildContext context) {
    final buttonStyle = ElevatedButton.styleFrom(
      foregroundColor: Colors.white,
      backgroundColor: Theme.of(context).primaryColor,
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      elevation: 4,
      shadowColor: Colors.black26,
    );
  
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.project.name,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: Theme.of(context).primaryColorDark,
                  ),
            ),
            const Divider(height: 32, thickness: 1),
            _buildMenuButton(
              context,
              icon: Icons.settings,
              label: '翻译设置',
              onPressed: () => _navigateTo(ConfigScreen(project: widget.project)),
              style: buttonStyle,
            ),
            _buildMenuButton(
              context,
              icon: Icons.history,
              label: '初译记录文件',
              onPressed: () => _navigateTo(FRecordScreen(project: widget.project)),
              style: buttonStyle,
            ),
            _buildMenuButton(
              context,
              icon: Icons.list_alt,
              label: '专有名词列表',
              onPressed: () => _navigateTo(PNTScreen(project: widget.project)),
              style: buttonStyle,
            ),
            _buildMenuButton(
              context,
              icon: Icons.compare,
              label: '查看原文译文对照',
              onPressed: () => _navigateTo(TranslatefileScreen(project: widget.project)),
              style: buttonStyle,
            ),
            _buildMenuButton(
              context,
              icon: Icons.download,
              label: '导出翻译后文本',
              onPressed: () => _navigateTo(FileExportScreen(project: widget.project)),
              style: buttonStyle,
            ),
            _buildMenuButton(
              context,
              icon: Icons.translate,
              label: '进入翻译页面',
              onPressed: () => _navigateTo(TranslatingScreen(project: widget.project)),
              style: buttonStyle,
            ),
          ],
        ),
      ),
    );
  }

  // 新增辅助方法：生成带图标按钮
  Widget _buildMenuButton(
    BuildContext context, {
    required IconData icon,
    required String label,
    required VoidCallback onPressed,
    required ButtonStyle style,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: ElevatedButton.icon(
        icon: Icon(icon, size: 24),
        label: Padding(
          padding: const EdgeInsets.symmetric(vertical: 12.0),
          child: Text(
            label,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w500,
                ),
          ),
        ),
        onPressed: onPressed,
        style: style.copyWith(
          backgroundColor: MaterialStateProperty.all(Colors.white),
          foregroundColor: MaterialStateProperty.all(Theme.of(context).primaryColor),
          overlayColor: MaterialStateProperty.all(Theme.of(context).primaryColor.withOpacity(0.1)),
        ),
      ),
    );
  }

  // 新增导航方法
  void _navigateTo(Widget screen) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => screen),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (widget.embed) {
      // 嵌入模式：自定义顶栏返回按钮逻辑
      return Row(
        children: [
          if (_showSidebar)
            GlobalSidebar(
              project: widget.project,
              onClose: () => setState(() => _showSidebar = false),
              isHomeScreen: false,
            ),
          if (_showSidebar)
            const VerticalDivider(width: 1),
          Expanded(
            child: Column(
              children: [
                Container(
                  height: kToolbarHeight,
                  color: Theme.of(context).primaryColor,
                  child: Row(
                    children: [
                      IconButton(
                        icon: Icon(_showSidebar ? Icons.arrow_back_ios : Icons.arrow_back),
                        onPressed: () {
                          Navigator.popUntil(context, (route) => route.isFirst);
                        },
                        color: Colors.white,
                      ),
                      const SizedBox(width: 8),
                      Text(widget.project.name, style: const TextStyle(color: Colors.white, fontSize: 20)),
                    ],
                  ),
                ),
                Expanded(child: _buildContent(context)),
              ],
            ),
          ),
        ],
      );
    }

    // 全屏模式：自定义顶栏返回按钮逻辑
    return Scaffold(
      body: Row(
        children: [
          if (_showSidebar)
            GlobalSidebar(
              project: widget.project,
              onClose: () => setState(() => _showSidebar = false),
              isHomeScreen: false,
            ),
          if (_showSidebar)
            const VerticalDivider(width: 1),
          Expanded(
            child: Column(
              children: [
                Container(
                  height: kToolbarHeight,
                  color: Theme.of(context).primaryColor,
                  child: Row(
                    children: [
                      IconButton(
                        icon: Icon(_showSidebar ? Icons.arrow_back_ios : Icons.arrow_back),
                        onPressed: () {
                          Navigator.popUntil(context, (route) => route.isFirst);
                        },
                        color: Colors.white,
                      ),
                      const SizedBox(width: 8),
                      Text('选择编辑 - ${widget.project.name}', style: const TextStyle(color: Colors.white, fontSize: 20)),
                    ],
                  ),
                ),
                Expanded(child: _buildContent(context)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
