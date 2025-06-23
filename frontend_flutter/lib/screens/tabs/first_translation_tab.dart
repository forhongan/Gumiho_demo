import 'package:flutter/material.dart';
import '../../models/config_yml.dart';

class FirstTranslationTab extends StatelessWidget {
  final GumihoConfig config;
  final Function(GumihoConfig) onConfigChanged;

  const FirstTranslationTab({
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
          // 初译设置
          _buildSectionTitle(context, '初译设置'),
          _buildSwitchFieldWithInfo(
            '逐句翻译模式',
            config.firstTranslationSetting.sentenceBySentenceTranslation,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  sentenceBySentenceTranslation: value),
              ));
            },
            infoText: '启用逐句翻译模式，不启用时默认为整合翻译模式',
          ),
          _buildTextFieldWithInfo(
            '每组文本数量',
            config.firstTranslationSetting.numberOfTextsPerGroup.toString(),
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  numberOfTextsPerGroup: int.tryParse(value) ?? 100,
                ),
              ));
            },
            infoText: '启用整合翻译模式时，每组文本的数量',
          ),
          _buildSwitchFieldWithInfo(
            '均匀长度模式',
            config.firstTranslationSetting.enableUniformLength,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  enableUniformLength: value),
              ));
            },
            infoText: '启用后每组文本将会尽可能拓展为AI上下文极限长度（仍会被章节分割截断）',
          ),
          _buildSwitchFieldWithInfo(
            '启用最大长度',
            config.firstTranslationSetting.enableMaximumLength,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  enableMaximumLength: value),
              ));
            },
            infoText: '启用最大长度限制',
          ),
          _buildSwitchFieldWithInfo(
            '启用章节表',
            config.firstTranslationSetting.enableContents,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  enableContents: value),
              ));
            },
            infoText: '存在/启用章节表',
          ),

          // 人工参与设置
          _buildSectionTitle(context, '人工参与设置'),
          _buildSwitchFieldWithInfo(
            '人工参与',
            config.firstTranslationSetting.humanInvolvement,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  humanInvolvement: value),
              ));
            },
            infoText: '是否需要人工参与',
          ),
          _buildSwitchFieldWithInfo(
            '总结检查',
            config.firstTranslationSetting.humanCheckSetting.summaryCheck,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  humanCheckSetting: HumanCheckSetting(summaryCheck: value),
                ),
              ));
            },
            infoText: '是否需要人工检查总结',
          ),

          // 历史文本总结设置
          _buildSectionTitle(context, '历史文本总结'),
          _buildSwitchFieldWithInfo(
            '启用总结',
            config.firstTranslationSetting.autoTextSummary.enable,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  autoTextSummary: config.firstTranslationSetting.autoTextSummary.copyWith(
                    enable: value,
                  ),
                ),
              ));
            },
            infoText: '设置为true时启用自动生成文本总结',
          ),
          _buildSwitchFieldWithInfo(
            '创建总结',
            config.firstTranslationSetting.autoTextSummary.create,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  autoTextSummary: config.firstTranslationSetting.autoTextSummary.copyWith(
                    create: value,
                  ),
                ),
              ));
            },
            infoText: '是否创建总结',
          ),
          _buildSwitchFieldWithInfo(
            '使用总结',
            config.firstTranslationSetting.autoTextSummary.using,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  autoTextSummary: config.firstTranslationSetting.autoTextSummary.copyWith(
                    using: value,
                  ),
                ),
              ));
            },
            infoText: '是否使用总结',
          ),
          _buildTextFieldWithInfo(
            '历史记录数量',
            config.firstTranslationSetting.autoTextSummary.numberOfHistoryGeneratedRecords.toString(),
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  autoTextSummary: config.firstTranslationSetting.autoTextSummary.copyWith(
                    numberOfHistoryGeneratedRecords: int.tryParse(value) ?? 5,
                  ),
                ),
              ));
            },
            infoText: '自动利用的历史记录数量，不启用时默认为零',
          ),
          _buildTextFieldWithInfo(
            '历史文本数量',
            config.firstTranslationSetting.autoTextSummary.numberOfHistoricalTextsUsed.toString(),
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  autoTextSummary: config.firstTranslationSetting.autoTextSummary.copyWith(
                    numberOfHistoricalTextsUsed: int.tryParse(value) ?? 30,
                  ),
                ),
              ));
            },
            infoText: '加入上文的历史文本原文数量，不启用时默认为零',
          ),
          _buildSwitchFieldWithInfo(
            '启用上章总结',
            config.firstTranslationSetting.autoTextSummary.enablePreviousChapterSummary,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  autoTextSummary: config.firstTranslationSetting.autoTextSummary.copyWith(
                    enablePreviousChapterSummary: value,
                  ),
                ),
              ));
            },
            infoText: '是否启用上一章节总结',
          ),
          _buildSwitchFieldWithInfo(
            '启用长期总结',
            config.firstTranslationSetting.autoTextSummary.enableLongtermSummary,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  autoTextSummary: config.firstTranslationSetting.autoTextSummary.copyWith(
                    enableLongtermSummary: value,
                  ),
                ),
              ));
            },
            infoText: '是否启用长期总结',
          ),

          // 专有名词设置
          _buildSectionTitle(context, '专有名词设置'),
          _buildSwitchFieldWithInfo(
            '专有名词翻译',
            config.firstTranslationSetting.properNounTranslation,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  properNounTranslation: value,
                ),
              ));
            },
            infoText: '是否启用专有名词翻译',
          ),
          _buildSwitchFieldWithInfo(
            '自动生成词典',
            config.firstTranslationSetting.autoTranslationDictionary.enable,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  autoTranslationDictionary: config.firstTranslationSetting.autoTranslationDictionary.copyWith(
                    enable: value,
                  ),
                ),
              ));
            },
            infoText: '设置为true时自动生成专有名词对照翻译词典',
          ),
          _buildSwitchFieldWithInfo(
            '生成描述',
            config.firstTranslationSetting.autoTranslationDictionary.enableDescribe,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  autoTranslationDictionary: config.firstTranslationSetting.autoTranslationDictionary.copyWith(
                    enableDescribe: value,
                  ),
                ),
              ));
            },
            infoText: '设置为true时自动生成人名/专有名词的描述',
          ),
          _buildSwitchFieldWithInfo(
            '使用描述',
            config.firstTranslationSetting.autoTranslationDictionary.enableDescribeUsing,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  autoTranslationDictionary: config.firstTranslationSetting.autoTranslationDictionary.copyWith(
                    enableDescribeUsing: value,
                  ),
                ),
              ));
            },
            infoText: '是否使用描述',
          ),
          _buildSwitchFieldWithInfo(
            '启用长期词典',
            config.firstTranslationSetting.autoTranslationDictionary.enableLongterm,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  autoTranslationDictionary: config.firstTranslationSetting.autoTranslationDictionary.copyWith(
                    enableLongterm: value,
                  ),
                ),
              ));
            },
            infoText: '是否启用长期词典',
          ),
          _buildSwitchFieldWithInfo(
            '使用长期词典',
            config.firstTranslationSetting.autoTranslationDictionary.enableLongtermUsing,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  autoTranslationDictionary: config.firstTranslationSetting.autoTranslationDictionary.copyWith(
                    enableLongtermUsing: value,
                  ),
                ),
              ));
            },
            infoText: '是否使用长期词典',
          ),
          
          // Prompt设置
          _buildSectionTitle(context, 'Prompt设置'),
          _buildTextFieldWithInfo(
            '基础提示词',
            config.firstTranslationSetting.basePrompt,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  basePrompt: value,
                ),
              ));
            },
            infoText: '基础提示词设置',
            maxLines: 5,
          ),
          _buildTextFieldWithInfo(
            '输出结构',
            config.firstTranslationSetting.outputStructure,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  outputStructure: value,
                ),
              ));
            },
            infoText: '输出结构设置',
            maxLines: 5,
          ),
          
          const SizedBox(height: 30),
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
      {bool obscureText = false, int? maxLines}) {
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
        maxLines: maxLines,
      ),
    );
  }

  Widget _buildSwitchField(String label, bool value, ValueChanged<bool> onChanged) {
    return SwitchListTile(
      title: Text(label),
      value: value,
      onChanged: onChanged,
    );
  }

  Widget _buildSwitchFieldWithInfo(String label, bool value, ValueChanged<bool> onChanged, {required String infoText}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SwitchListTile(
          title: Text(label),
          value: value,
          onChanged: onChanged,
        ),
        Padding(
          padding: const EdgeInsets.only(left: 16.0, bottom: 8.0),
          child: Text(infoText, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
        ),
      ],
    );
  }

  Widget _buildTextFieldWithInfo(String label, String value, ValueChanged<String> onChanged, 
      {required String infoText, bool obscureText = false, int? maxLines}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          decoration: InputDecoration(
            labelText: label,
            border: const OutlineInputBorder(),
          ),
          controller: TextEditingController(text: value),
          onChanged: onChanged,
          obscureText: obscureText,
          maxLines: maxLines,
        ),
        Padding(
          padding: const EdgeInsets.only(top: 4.0, left: 4.0, bottom: 16.0),
          child: Text(infoText, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
        ),
      ],
    );
  }
}
