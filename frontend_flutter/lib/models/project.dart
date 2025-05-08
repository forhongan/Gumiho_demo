class Project {
  final String name;
  final String configPath; // 后端 config.yml 路径
  final String f_recordPath;
  final String p_recordPath;
  final String PNTPath;
  final String translatefilePath;
  
  const Project({
    required this.name,
    required this.configPath,
    required this.f_recordPath,
    required this.p_recordPath,
    required this.PNTPath,
    required this.translatefilePath,
  });
  
  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      name: json['name'],
      configPath: json['configPath'],
      f_recordPath: json['f_recordPath'],
      p_recordPath: json['p_recordPath'],
      PNTPath: json['PNTPath'],
      translatefilePath: json['translatefilePath'],
    );
  }
}
