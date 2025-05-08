class GumihoConfig {
  // 项目基本设置
  String translationProjectName;
  List<String> translater;
  String type;
  String originalLanguage;
  String targetLanguage;
  bool paragraphed;
  String originalFormat;

  // AI设置
  AISetting defaultAISetting;

  // 翻译任务设置
  bool firstTranslationNeeded;
  bool proofreadingNeeded;

  // 书籍设置
  String name;
  String? bookContentSummary;
  String? writingStyle;
  bool enableBaseInformation;

  // 初译设置
  FirstTranslationSetting firstTranslationSetting;

  GumihoConfig({
    required this.translationProjectName,
    required this.translater,
    required this.type,
    required this.originalLanguage,
    required this.targetLanguage,
    required this.paragraphed,
    required this.originalFormat,
    required this.defaultAISetting,
    required this.firstTranslationNeeded,
    required this.proofreadingNeeded,
    required this.name,
    this.bookContentSummary,
    this.writingStyle,
    required this.enableBaseInformation,
    required this.firstTranslationSetting,
  });

  factory GumihoConfig.fromYaml(Map<String, dynamic> yaml) {
    return GumihoConfig(
      translationProjectName: yaml['Translation Project Name'] ?? '',
      translater: List<String>.from(yaml['Translater'] ?? []),
      type: yaml['type'] ?? '',
      originalLanguage: yaml['original language'] ?? '',
      targetLanguage: yaml['target language'] ?? '',
      paragraphed: yaml['paragraphed'] ?? false,
      originalFormat: yaml['original format'] ?? '',
      defaultAISetting: AISetting.fromMap(yaml['default_ai_setting'] ?? {}),
      firstTranslationNeeded: yaml['first_translation_needed'] ?? false,
      proofreadingNeeded: yaml['Proofreading_needed'] ?? false,
      name: yaml['Name'] ?? '',
      bookContentSummary: yaml['book content summary'],
      writingStyle: yaml['Writing style'],
      enableBaseInformation: yaml['Enable base imformation'] ?? false,
      firstTranslationSetting: FirstTranslationSetting.fromMap(
          yaml['first_translation_setting'] ?? {}),
    );
  }

  Map<String, dynamic> toYaml() {
    return {
      'Translation Project Name': translationProjectName,
      'Translater': translater,
      'type': type,
      'original language': originalLanguage,
      'target language': targetLanguage,
      'paragraphed': paragraphed,
      'original format': originalFormat,
      'default_ai_setting': defaultAISetting.toMap(),
      'first_translation_needed': firstTranslationNeeded,
      'Proofreading_needed': proofreadingNeeded,
      'Name': name,
      if (bookContentSummary != null) 'book content summary': bookContentSummary,
      if (writingStyle != null) 'Writing style': writingStyle,
      'Enable base imformation': enableBaseInformation,
      'first_translation_setting': firstTranslationSetting.toMap(),
    };
  }
}

class AISetting {
  String api;
  String key;
  String modelName;
  bool stream;
  bool jsonOrNot;
  int maxLen;

  AISetting({
    required this.api,
    required this.key,
    required this.modelName,
    required this.stream,
    required this.jsonOrNot,
    required this.maxLen,
  });

  factory AISetting.fromMap(Map<String, dynamic> map) {
    return AISetting(
      api: map['api'] ?? '',
      key: map['key'] ?? '',
      modelName: map['model_name'] ?? '',
      stream: map['stream'] ?? false,
      jsonOrNot: map['json_or_not'] ?? false,
      maxLen: map['max_len'] ?? 0,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'api': api,
      'key': key,
      'model_name': modelName,
      'stream': stream,
      'json_or_not': jsonOrNot,
      'max_len': maxLen,
    };
  }
}

class FirstTranslationSetting {
  // 翻译模式设置
  final bool sentenceBySentenceTranslation;
  final int numberOfTextsPerGroup;
  final bool enableUniformLength;
  final bool enableMaximumLength;
  final bool enableContents;

  // 人工参与设置
  final bool humanInvolvement;
  final HumanCheckSetting humanCheckSetting;

  // 历史文本总结设置
  final AutoTextSummary autoTextSummary;

  // 专有名词设置
  final bool properNounTranslation;
  final AutoTranslationDictionary autoTranslationDictionary;

  // Prompt设置
  final String basePrompt;
  final String outputStructure;

  FirstTranslationSetting({
    required this.sentenceBySentenceTranslation,
    required this.numberOfTextsPerGroup,
    required this.enableUniformLength,
    required this.enableMaximumLength,
    required this.enableContents,
    required this.humanInvolvement,
    required this.humanCheckSetting,
    required this.autoTextSummary,
    required this.properNounTranslation,
    required this.autoTranslationDictionary,
    required this.basePrompt,
    required this.outputStructure,
  });

  factory FirstTranslationSetting.fromMap(Map<String, dynamic> map) {
    return FirstTranslationSetting(
      sentenceBySentenceTranslation: map['sentence-by-sentence_translation'] ?? false,
      numberOfTextsPerGroup: map['Number of texts per group'] ?? 100,
      enableUniformLength: map['enable uniform length'] ?? false,
      enableMaximumLength: map['enable Maximum length'] ?? false,
      enableContents: map['enable contents'] ?? false,
      humanInvolvement: map['human_involvement'] ?? false,
      humanCheckSetting: HumanCheckSetting.fromMap(map['human_check_setting'] ?? {}),
      autoTextSummary: AutoTextSummary.fromMap(map['Automatically generated text summary'] ?? {}),
      properNounTranslation: map['Proper noun translation'] ?? false,
      autoTranslationDictionary: AutoTranslationDictionary.fromMap(
          map['Automatic Translation Dictionary'] ?? {}),
      basePrompt: map['base_prompt'] ?? '',
      outputStructure: map['Output structure'] ?? '',
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'sentence-by-sentence_translation': sentenceBySentenceTranslation,
      'Number of texts per group': numberOfTextsPerGroup,
      'enable uniform length': enableUniformLength,
      'enable Maximum length': enableMaximumLength,
      'enable contents': enableContents,
      'human_involvement': humanInvolvement,
      'human_check_setting': humanCheckSetting.toMap(),
      'Automatically generated text summary': autoTextSummary.toMap(),
      'Proper noun translation': properNounTranslation,
      'Automatic Translation Dictionary': autoTranslationDictionary.toMap(),
      'base_prompt': basePrompt,
      'Output structure': outputStructure,
    };
  }

  // 新增 copyWith 方法
  FirstTranslationSetting copyWith({
    bool? sentenceBySentenceTranslation,
    int? numberOfTextsPerGroup,
    bool? enableUniformLength,
    bool? enableMaximumLength,
    bool? enableContents,
    bool? humanInvolvement,
    HumanCheckSetting? humanCheckSetting,
    AutoTextSummary? autoTextSummary,
    bool? properNounTranslation,
    AutoTranslationDictionary? autoTranslationDictionary,
    String? basePrompt,
    String? outputStructure,
  }) {
    return FirstTranslationSetting(
      sentenceBySentenceTranslation: sentenceBySentenceTranslation ?? this.sentenceBySentenceTranslation,
      numberOfTextsPerGroup: numberOfTextsPerGroup ?? this.numberOfTextsPerGroup,
      enableUniformLength: enableUniformLength ?? this.enableUniformLength,
      enableMaximumLength: enableMaximumLength ?? this.enableMaximumLength,
      enableContents: enableContents ?? this.enableContents,
      humanInvolvement: humanInvolvement ?? this.humanInvolvement,
      humanCheckSetting: humanCheckSetting ?? this.humanCheckSetting,
      autoTextSummary: autoTextSummary ?? this.autoTextSummary,
      properNounTranslation: properNounTranslation ?? this.properNounTranslation,
      autoTranslationDictionary: autoTranslationDictionary ?? this.autoTranslationDictionary,
      basePrompt: basePrompt ?? this.basePrompt,
      outputStructure: outputStructure ?? this.outputStructure,
    );
  }
}

class HumanCheckSetting {
  final bool summaryCheck;

  HumanCheckSetting({required this.summaryCheck});

  factory HumanCheckSetting.fromMap(Map<String, dynamic> map) {
    return HumanCheckSetting(summaryCheck: map['summary_check'] ?? false);
  }

  Map<String, dynamic> toMap() {
    return {'summary_check': summaryCheck};
  }
}

class AutoTextSummary {
  final bool enable;
  final bool create;
  final bool using;
  final int numberOfHistoryGeneratedRecords;
  final int numberOfHistoricalTextsUsed;
  final bool enablePreviousChapterSummary;
  final bool enableLongtermSummary;

  AutoTextSummary({
    required this.enable,
    required this.create,
    required this.using,
    required this.numberOfHistoryGeneratedRecords,
    required this.numberOfHistoricalTextsUsed,
    required this.enablePreviousChapterSummary,
    required this.enableLongtermSummary,
  });

  factory AutoTextSummary.fromMap(Map<String, dynamic> map) {
    return AutoTextSummary(
      enable: map['enable'] ?? false,
      create: map['create'] ?? false,
      using: map['using'] ?? false,
      numberOfHistoryGeneratedRecords: map['Number of history generated records'] ?? 5,
      numberOfHistoricalTextsUsed: map['Number of historical texts used'] ?? 30,
      enablePreviousChapterSummary: map['enable previous chapter summary'] ?? false,
      enableLongtermSummary: map['enable longterm summary'] ?? false,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'enable': enable,
      'create': create,
      'using': using,
      'Number of history generated records': numberOfHistoryGeneratedRecords,
      'Number of historical texts used': numberOfHistoricalTextsUsed,
      'enable previous chapter summary': enablePreviousChapterSummary,
      'enable longterm summary': enableLongtermSummary,
    };
  }
  
  // 新增 copyWith 方法
  AutoTextSummary copyWith({
    bool? enable,
    bool? create,
    bool? using,
    int? numberOfHistoryGeneratedRecords,
    int? numberOfHistoricalTextsUsed,
    bool? enablePreviousChapterSummary,
    bool? enableLongtermSummary,
  }) {
    return AutoTextSummary(
      enable: enable ?? this.enable,
      create: create ?? this.create,
      using: using ?? this.using,
      numberOfHistoryGeneratedRecords: numberOfHistoryGeneratedRecords ?? this.numberOfHistoryGeneratedRecords,
      numberOfHistoricalTextsUsed: numberOfHistoricalTextsUsed ?? this.numberOfHistoricalTextsUsed,
      enablePreviousChapterSummary: enablePreviousChapterSummary ?? this.enablePreviousChapterSummary,
      enableLongtermSummary: enableLongtermSummary ?? this.enableLongtermSummary,
    );
  }
}

class AutoTranslationDictionary {
  final bool enable;
  final bool enableDescribe;
  final bool enableDescribeUsing;
  final bool enableLongterm;
  final bool enableLongtermUsing;

  AutoTranslationDictionary({
    required this.enable,
    required this.enableDescribe,
    required this.enableDescribeUsing,
    required this.enableLongterm,
    required this.enableLongtermUsing,
  });

  factory AutoTranslationDictionary.fromMap(Map<String, dynamic> map) {
    return AutoTranslationDictionary(
      enable: map['enable'] ?? false,
      enableDescribe: map['enable_describe'] ?? false,
      enableDescribeUsing: map['enable_describe_using'] ?? false,
      enableLongterm: map['enable_longterm'] ?? false,
      enableLongtermUsing: map['enable_longterm_using'] ?? false,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'enable': enable,
      'enable_describe': enableDescribe,
      'enable_describe_using': enableDescribeUsing,
      'enable_longterm': enableLongterm,
      'enable_longterm_using': enableLongtermUsing,
    };
  }
  
  // 新增 copyWith 方法
  AutoTranslationDictionary copyWith({
    bool? enable,
    bool? enableDescribe,
    bool? enableDescribeUsing,
    bool? enableLongterm,
    bool? enableLongtermUsing,
  }) {
    return AutoTranslationDictionary(
      enable: enable ?? this.enable,
      enableDescribe: enableDescribe ?? this.enableDescribe,
      enableDescribeUsing: enableDescribeUsing ?? this.enableDescribeUsing,
      enableLongterm: enableLongterm ?? this.enableLongterm,
      enableLongtermUsing: enableLongtermUsing ?? this.enableLongtermUsing,
    );
  }
}