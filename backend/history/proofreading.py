import os
import yaml

class proofreading:
    """
    #校对类
    #start: 起始位置id, end: 结束位置id, length: 校对长度 length= end-start,最小为1
    int start
    int end
    int length
    #status: 校对状态, 0:未校对, 1:校对中, 2:校对完成
    int status
    #text: 需校对文本
    string list text
    #ai_config: ai设置
    dict config(
        "model_name": "xxx",
        "temperature": 0.7,
        "json_or_not": false,
    )
    #ai_prompt: ai提示
    string list sys_prompt
    string list user_prompt
    #proofreading_config: 校对设置
    dict proofreading_config(
        ...
    )
    
    """
    def __init__(self,project_path,):
        config_path = os.path.join(project_path, "config.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        self.config = config_data.get("ai_config", {})
        self.proofreading_config = config_data.get("proofreading_config", {})
        # max_length =
        # self.length=
        self.proofreading = True

    def save_record(self):
        """
        #保存校对记录
        """
        pass


def proofreading_main():
    now_proofreading = proofreading()
    now_proofreading.to_ai()
    now_proofreading.save_record()
