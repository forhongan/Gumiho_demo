import os, json, datetime
from datetime import timedelta

def update_timestamps():
    # 目标文件路径
    target_file = "test/f_record.json"
    if not os.path.exists(target_file):
        print("目标文件不存在！")
        return
    
    with open(target_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 确保存在记录数组
    if "record" not in data:
        print("记录键(record)不存在！")
        return

    records = data["record"]
    # 按照 range 值从大到小排序（range值越大，完成时间越近）
    records_sorted = sorted(records, key=lambda r: int(r.get("range", "0")), reverse=True)
    
    now = datetime.datetime.now()
    for i, record in enumerate(records_sorted):
        ts = (now - timedelta(minutes=10 * i)).isoformat()
        # 在每条记录中添加时间戳
        record["timestamp"] = ts

    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
if __name__ == "__main__":
    update_timestamps()
