import 'package:flutter/material.dart';
import '../../models/config_yml.dart';

class BasicSettingsTab extends StatelessWidget {
  final GumihoConfig config;
  final Function(GumihoConfig) onConfigChanged;

  const BasicSettingsTab({
    Key? key,
    required this.config,
    required this.onConfigChanged,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 项目基本设置
          _buildSectionTitle(context, '项目基本设置'),
          _buildTextField('项目名称', config.translationProjectName, (value) {
            onConfigChanged(config.copyWith(translationProjectName: value));
          }),
          _buildMultiSelectField(context, '翻译人员', config.translater, (updatedList) {
            onConfigChanged(config.copyWith(translater: updatedList));
          }),
          _buildTextField('类型', config.type, (value) {
            onConfigChanged(config.copyWith(type: value));
          }),
          _buildTextField('原文语言', config.originalLanguage, (value) {
            onConfigChanged(config.copyWith(originalLanguage: value));
          }),
          _buildTextField('目标语言', config.targetLanguage, (value) {
            onConfigChanged(config.copyWith(targetLanguage: value));
          }),
          _buildSwitchField('存在段落', config.paragraphed, (value) {
            onConfigChanged(config.copyWith(paragraphed: value));
          }),
          _buildTextField('源文件格式', config.originalFormat, (value) {
            onConfigChanged(config.copyWith(originalFormat: value));
          }),

          // 书籍基本设置
          _buildSectionTitle(context, '书籍基本设置'),
          _buildTextField('书籍名称', config.name, (value) {
            onConfigChanged(config.copyWith(name: value));
          }),
          _buildTextField('内容简介', config.bookContentSummary ?? '', (value) {
            onConfigChanged(config.copyWith(bookContentSummary: value));
          }),
          _buildTextField('写作风格', config.writingStyle ?? '', (value) {
            onConfigChanged(config.copyWith(writingStyle: value));
          }),
          _buildSwitchField('启用基本信息', config.enableBaseInformation, (value) {
            onConfigChanged(config.copyWith(enableBaseInformation: value));
          }),

          // 翻译任务设置
          _buildSectionTitle(context, '翻译任务设置'),
          _buildSwitchField('需要初译', config.firstTranslationNeeded, (value) {
            onConfigChanged(config.copyWith(firstTranslationNeeded: value));
          }),
          _buildSwitchField('需要校对', config.proofreadingNeeded, (value) {
            onConfigChanged(config.copyWith(proofreadingNeeded: value));
          }),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Text(title, style: Theme.of(context).textTheme.titleLarge),
    );
  }

  Widget _buildTextField(String label, String value, ValueChanged<String> onChanged,
      {bool obscureText = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: TextField(
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
        ),
        controller: TextEditingController(text: value),
        onChanged: onChanged,
        obscureText: obscureText,
      ),
    );
  }

  Widget _buildMultiSelectField(BuildContext context, String label, List<String> values, Function(List<String>) onChanged) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.titleSmall),
        ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: values.length + 1, // +1 for the add button
          itemBuilder: (context, index) {
            if (index == values.length) {
              return IconButton(
                icon: const Icon(Icons.add),
                onPressed: () {
                  final newList = List<String>.from(values);
                  newList.add('');
                  onChanged(newList);
                },
              );
            }
            
            return Row(
              children: [
                Expanded(
                  child: TextField(
                    decoration: InputDecoration(
                      labelText: '翻译人员 ${index + 1}',
                      border: const OutlineInputBorder(),
                    ),
                    controller: TextEditingController(text: values[index]),
                    onChanged: (newValue) {
                      final newList = List<String>.from(values);
                      newList[index] = newValue;
                      onChanged(newList);
                    },
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.delete),
                  onPressed: () {
                    final newList = List<String>.from(values);
                    newList.removeAt(index);
                    onChanged(newList);
                  },
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildSwitchField(String label, bool value, ValueChanged<bool> onChanged) {
    return SwitchListTile(
      title: Text(label),
      value: value,
      onChanged: onChanged,
    );
  }
}
