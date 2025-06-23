class DefaultJsonModel {
  final Map<String, dynamic> data;

  DefaultJsonModel({required this.data});

  factory DefaultJsonModel.fromJson(Map<String, dynamic> json) {
    return DefaultJsonModel(data: json);
  }

  Map<String, dynamic> toJson() => data;
}
