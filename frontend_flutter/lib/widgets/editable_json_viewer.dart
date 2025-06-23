import 'package:flutter/material.dart';

class EditableJsonViewer extends StatefulWidget {
  final dynamic jsonObj;
  final ValueChanged<dynamic> onChanged;
  const EditableJsonViewer({Key? key, required this.jsonObj, required this.onChanged}) : super(key: key);

  @override
  _EditableJsonViewerState createState() => _EditableJsonViewerState();
}

class _EditableJsonViewerState extends State<EditableJsonViewer> {
  late dynamic _data;

  @override
  void initState() {
    super.initState();
    // 初始化时直接赋值，可根据需求做深拷贝
    _data = widget.jsonObj;
  }

  @override
  Widget build(BuildContext context) {
    if (_data is Map) {
      return _buildMap(_data);
    } else if (_data is List) {
      return _buildList(_data);
    } else {
      return _buildPrimitive(_data);
    }
  }

  Widget _buildMap(Map map) {
    final entries = map.entries.toList();
    if (entries.length <= 10) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: entries.map<Widget>((entry) {
          return ExpansionTile(
            title: Text(entry.key.toString()),
            initiallyExpanded: true,
            children: [
              EditableJsonViewer(
                jsonObj: entry.value,
                onChanged: (newVal) {
                  setState(() {
                    map[entry.key] = newVal;
                    _data = map;
                    widget.onChanged(_data);
                  });
                },
              )
            ],
          );
        }).toList(),
      );
    } else {
      // 前 10 项直接展示，剩余项放在折叠的 ExpansionTile 内（懒加载）
      final initialEntries = entries.take(10).toList();
      final remainingEntries = entries.skip(10).toList();
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ...initialEntries.map((entry) {
            return ExpansionTile(
              title: Text(entry.key.toString()),
              initiallyExpanded: true,
              children: [
                EditableJsonViewer(
                  jsonObj: entry.value,
                  onChanged: (newVal) {
                    setState(() {
                      map[entry.key] = newVal;
                      _data = map;
                      widget.onChanged(_data);
                    });
                  },
                )
              ],
            );
          }).toList(),
          ExpansionTile(
            title: const Text("显示更多..."),
            children: remainingEntries.map((entry) {
              return ExpansionTile(
                title: Text(entry.key.toString()),
                initiallyExpanded: false,
                children: [
                  EditableJsonViewer(
                    jsonObj: entry.value,
                    onChanged: (newVal) {
                      setState(() {
                        map[entry.key] = newVal;
                        _data = map;
                        widget.onChanged(_data);
                      });
                    },
                  )
                ],
              );
            }).toList(),
          ),
        ],
      );
    }
  }

  Widget _buildList(List list) {
    if (list.length <= 10) {
      return ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: list.length,
        separatorBuilder: (context, index) => const Divider(thickness: 2),
        itemBuilder: (context, index) {
          return ListTile(
            title: EditableJsonViewer(
              jsonObj: list[index],
              onChanged: (newVal) {
                setState(() {
                  list[index] = newVal;
                  _data = list;
                  widget.onChanged(_data);
                });
              },
            ),
          );
        },
      );
    } else {
      // 前 10 项直接展示，剩余项折叠到 "显示更多..." 内（懒加载）
      final initialList = list.take(10).toList();
      final remainingList = list.skip(10).toList();
      return Column(
        children: [
          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: initialList.length,
            separatorBuilder: (context, index) => const Divider(thickness: 2),
            itemBuilder: (context, index) {
              return ListTile(
                title: EditableJsonViewer(
                  jsonObj: initialList[index],
                  onChanged: (newVal) {
                    setState(() {
                      list[index] = newVal;
                      _data = list;
                      widget.onChanged(_data);
                    });
                  },
                ),
              );
            },
          ),
          ExpansionTile(
            title: const Text("显示更多..."),
            children: remainingList.asMap().entries.map((entry) {
              int index = entry.key + 10;
              var item = entry.value;
              return ListTile(
                title: EditableJsonViewer(
                  jsonObj: item,
                  onChanged: (newVal) {
                    setState(() {
                      list[index] = newVal;
                      _data = list;
                      widget.onChanged(_data);
                    });
                  },
                ),
              );
            }).toList(),
          ),
        ],
      );
    }
  }

  Widget _buildPrimitive(dynamic value) {
    // 使用 TextEditingController 初始化当前值
    final controller = TextEditingController(text: value?.toString() ?? '');
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(8),
      ),
      child: TextField(
        controller: controller,
        decoration: const InputDecoration(border: InputBorder.none),
        onSubmitted: (newText) {
          // 如有需要，可在此处做类型转换
          dynamic parsedValue = newText;
          setState(() {
            _data = parsedValue;
            widget.onChanged(_data);
          });
        },
      ),
    );
  }
}