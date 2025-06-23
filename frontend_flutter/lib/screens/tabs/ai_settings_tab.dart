import 'package:flutter/material.dart';
import '../../models/config_yml.dart';

class AISettingsTab extends StatelessWidget {
  final GumihoConfig config;
  final Function(GumihoConfig) onConfigChanged;

  const AISettingsTab({
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
          // 默认AI设置
          _buildSectionTitle(context, '默认AI设置'),
          _buildTextField('API地址', config.defaultAISetting.api, (value) {
            onConfigChanged(config.copyWith(
              defaultAISetting: config.defaultAISetting.copyWith(api: value),
            ));
          }),
          _buildTextField('API密钥', config.defaultAISetting.key, (value) {
            onConfigChanged(config.copyWith(
              defaultAISetting: config.defaultAISetting.copyWith(key: value),
            ));
          }, obscureText: true),
          _buildTextField('模型名称', config.defaultAISetting.modelName, (value) {
            onConfigChanged(config.copyWith(
              defaultAISetting: config.defaultAISetting.copyWith(modelName: value),
            ));
          }),
          _buildSwitchField('流式传输', config.defaultAISetting.stream, (value) {
            onConfigChanged(config.copyWith(
              defaultAISetting: config.defaultAISetting.copyWith(stream: value),
            ));
          }),
          _buildSwitchField('JSON格式', config.defaultAISetting.jsonOrNot, (value) {
            onConfigChanged(config.copyWith(
              defaultAISetting: config.defaultAISetting.copyWith(jsonOrNot: value),
            ));
          }),
          _buildTextField('最大长度', config.defaultAISetting.maxLen.toString(), (value) {
            onConfigChanged(config.copyWith(
              defaultAISetting: config.defaultAISetting.copyWith(maxLen: int.tryParse(value) ?? 0),
            ));
          }),

          // 初译AI独立配置
          _buildSectionTitle(context, '初译AI独立配置'),
          _buildSwitchFieldWithInfo(
            '启用独立AI配置',
            config.firstTranslationSetting.enableIndependenceAIConfig,
            (value) {
              onConfigChanged(config.copyWith(
                firstTranslationSetting: config.firstTranslationSetting.copyWith(
                  enableIndependenceAIConfig: value,
                ),
              ));
            },
            infoText: '启用后将使用下方配置而非默认AI配置进行初译',
          ),

          // 当启用独立AI配置时显示详细设置
          if (config.firstTranslationSetting.enableIndependenceAIConfig) ...[
            Padding(
              padding: const EdgeInsets.only(left: 16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildTextField('API地址', 
                    config.firstTranslationSetting.aiConfig?.api ?? '', 
                    (value) {
                      final currentConfig = config.firstTranslationSetting.aiConfig ?? AISetting(
                        api: '', key: '', modelName: '', stream: false, jsonOrNot: false, maxLen: 0,
                      );
                      onConfigChanged(config.copyWith(
                        firstTranslationSetting: config.firstTranslationSetting.copyWith(
                          aiConfig: currentConfig.copyWith(api: value),
                        ),
                      ));
                    }
                  ),
                  _buildTextField('API密钥', 
                    config.firstTranslationSetting.aiConfig?.key ?? '', 
                    (value) {
                      final currentConfig = config.firstTranslationSetting.aiConfig ?? AISetting(
                        api: '', key: '', modelName: '', stream: false, jsonOrNot: false, maxLen: 0,
                      );
                      onConfigChanged(config.copyWith(
                        firstTranslationSetting: config.firstTranslationSetting.copyWith(
                          aiConfig: currentConfig.copyWith(key: value),
                        ),
                      ));
                    },
                    obscureText: true
                  ),
                  _buildTextField('模型名称', 
                    config.firstTranslationSetting.aiConfig?.modelName ?? '', 
                    (value) {
                      final currentConfig = config.firstTranslationSetting.aiConfig ?? AISetting(
                        api: '', key: '', modelName: '', stream: false, jsonOrNot: false, maxLen: 0,
                      );
                      onConfigChanged(config.copyWith(
                        firstTranslationSetting: config.firstTranslationSetting.copyWith(
                          aiConfig: currentConfig.copyWith(modelName: value),
                        ),
                      ));
                    }
                  ),
                  _buildSwitchField('流式传输', 
                    config.firstTranslationSetting.aiConfig?.stream ?? false, 
                    (value) {
                      final currentConfig = config.firstTranslationSetting.aiConfig ?? AISetting(
                        api: '', key: '', modelName: '', stream: false, jsonOrNot: false, maxLen: 0,
                      );
                      onConfigChanged(config.copyWith(
                        firstTranslationSetting: config.firstTranslationSetting.copyWith(
                          aiConfig: currentConfig.copyWith(stream: value),
                        ),
                      ));
                    }
                  ),
                  _buildSwitchField('JSON格式', 
                    config.firstTranslationSetting.aiConfig?.jsonOrNot ?? false, 
                    (value) {
                      final currentConfig = config.firstTranslationSetting.aiConfig ?? AISetting(
                        api: '', key: '', modelName: '', stream: false, jsonOrNot: false, maxLen: 0,
                      );
                      onConfigChanged(config.copyWith(
                        firstTranslationSetting: config.firstTranslationSetting.copyWith(
                          aiConfig: currentConfig.copyWith(jsonOrNot: value),
                        ),
                      ));
                    }
                  ),
                  _buildTextField('最大长度', 
                    (config.firstTranslationSetting.aiConfig?.maxLen ?? 0).toString(), 
                    (value) {
                      final currentConfig = config.firstTranslationSetting.aiConfig ?? AISetting(
                        api: '', key: '', modelName: '', stream: false, jsonOrNot: false, maxLen: 0,
                      );
                      onConfigChanged(config.copyWith(
                        firstTranslationSetting: config.firstTranslationSetting.copyWith(
                          aiConfig: currentConfig.copyWith(maxLen: int.tryParse(value) ?? 0),
                        ),
                      ));
                    }
                  ),
                ],
              ),
            ),
          ],
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
}
