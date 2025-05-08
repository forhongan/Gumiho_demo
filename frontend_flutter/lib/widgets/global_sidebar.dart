import 'package:flutter/material.dart';
import '../models/project.dart';
import '../screens/config_screen.dart';
import '../screens/frecord_screen.dart';
import '../screens/translatefile_screen.dart';
import '../screens/PNT_screen.dart';

class GlobalSidebar extends StatelessWidget {
  final Project? project;
  final bool isHomeScreen; // 新增标识位
  final VoidCallback? onClose; // 新增关闭回调参数

  const GlobalSidebar({
    Key? key,
    this.project,
    this.onClose, // 接收关闭回调
    this.isHomeScreen = true, // 修改默认值为 true
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 250, // 调整宽度与主界面保持一致
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.3),
            blurRadius: 10,
            spreadRadius: 2,
          )
        ],
      ),
      child: Column(
        children: [
          // 顶部标题栏
          Container(
            height: 140,
            decoration: BoxDecoration(
              color: Colors.blue.shade800,
              borderRadius: const BorderRadius.only(
                bottomRight: Radius.circular(20),
              ),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Gumiho Demo',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.9),
                        fontSize: 20,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    IconButton(
                      icon: Icon(
                        isHomeScreen ? Icons.close_rounded : Icons.chevron_left_rounded,
                        color: Colors.white.withOpacity(0.9), // 与顶栏文字颜色一致
                      ),
                      onPressed: () {
                        if (onClose != null) {
                          onClose!(); // 优先使用回调关闭
                        } else if (Navigator.canPop(context)) {
                          Navigator.pop(context);
                        }
                      },
                    ),
                  ],
                ),
                const Spacer(),
                if (project != null)
                  Text(
                    project!.name,
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.9),
                      fontSize: 18,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: _buildMenuItems(context),
          ),
        ],
      ),
    );
  }

  Widget _buildMenuItems(BuildContext context) {
    final menuItems = <Widget>[];
    
    // 公共菜单项
    menuItems.addAll([
      _buildMenuItem(
        context,
        title: '工程项目列表',
        icon: Icons.list_alt_rounded,
        onTap: () => Navigator.popUntil(context, (route) => route.isFirst),
      ),
      const Divider(height: 20, indent: 20, endIndent: 20),
    ]);

    // 项目相关菜单项
    if (project != null) {
      menuItems.addAll([
        _buildMenuItem(
          context,
          title: '编辑配置',
          icon: Icons.settings_suggest_rounded,
          onTap: () => _navigateTo(context, ConfigScreen(project: project!)),
        ),
        _buildMenuItem(
          context,
          title: '编辑 F Record',
          icon: Icons.article_rounded,
          onTap: () => _navigateTo(context, FRecordScreen(project: project!)),
        ),
        _buildMenuItem(
          context,
          title: '编辑 PNT',
          icon: Icons.table_chart_rounded,
          onTap: () => _navigateTo(context, PNTScreen(project: project!)),
        ),
        _buildMenuItem(
          context,
          title: '原文译文对照',
          icon: Icons.translate_rounded,
          onTap: () => _navigateTo(context, TranslatefileScreen(project: project!)),
        ),
      ]);
    }

    return ListView(
      padding: const EdgeInsets.only(top: 20),
      physics: const BouncingScrollPhysics(),
      children: menuItems,
    );
  }

  Widget _buildMenuItem(BuildContext context, {
    required String title,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        splashColor: Colors.blue.withOpacity(0.1),
        hoverColor: Colors.blue.withOpacity(0.05),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 24),
          child: Row(
            children: [
              Icon(icon, 
                   color: Colors.blueGrey.shade700, 
                   size: 22),
              const SizedBox(width: 18),
              Text(
                title,
                style: TextStyle(
                  color: Colors.blueGrey.shade800,
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // void _safeClose(BuildContext context) {
  //   // 保留原有安全关闭逻辑作为备用
  //   if (Navigator.canPop(context)) {
  //     Navigator.pop(context);
  //   }
  // }

  void _navigateTo(BuildContext context, Widget screen) {
    if (onClose != null) {
      onClose!();
    }
    
    Navigator.push(
      context,
      PageRouteBuilder(
        pageBuilder: (_, __, ___) => screen,
        transitionsBuilder: (_, animation, __, child) => FadeTransition(opacity: animation, child: child),
        transitionDuration: Duration(milliseconds: 300),
      ),
    );
  }
}
