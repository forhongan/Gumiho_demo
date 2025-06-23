import 'package:flutter/material.dart';

class PaginatedJsonViewer extends StatefulWidget {
  final List<dynamic> jsonList;
  final int pageSize;
  final Function(List<dynamic> newData)? onChanged; // 可选回调

  const PaginatedJsonViewer({
    Key? key,
    required this.jsonList,
    this.pageSize = 20,
    this.onChanged,
  }) : super(key: key);

  @override
  State<PaginatedJsonViewer> createState() => _PaginatedJsonViewerState();
}

class _PaginatedJsonViewerState extends State<PaginatedJsonViewer> {
  int _currentPage = 0;

  int get totalPages => (widget.jsonList.length / widget.pageSize).ceil();

  List<dynamic> get currentPageItems {
    final start = _currentPage * widget.pageSize;
    final end = (_currentPage + 1) * widget.pageSize;
    return widget.jsonList.sublist(start, end > widget.jsonList.length ? widget.jsonList.length : end);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: ListView.builder(
            itemCount: currentPageItems.length,
            itemBuilder: (context, index) {
              return ListTile(
                title: Text(currentPageItems[index].toString()),
              );
            },
          ),
        ),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Page ${_currentPage + 1} / $totalPages'),
            Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back),
                  onPressed: _currentPage > 0
                      ? () {
                          setState(() {
                            _currentPage--;
                          });
                        }
                      : null,
                ),
                IconButton(
                  icon: const Icon(Icons.arrow_forward),
                  onPressed: _currentPage < totalPages - 1
                      ? () {
                          setState(() {
                            _currentPage++;
                          });
                        }
                      : null,
                ),
              ],
            )
          ],
        )
      ],
    );
  }
}
