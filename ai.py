#这里指定了与ai交互(调用)的函数
import logging
from openai import OpenAI

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def call_ai(
    config: dict,       # ai基础配置,包括api,key,温度,max_tokens等
    system_prompt: dict,       # ai的系统prompt 
    user_prompt: dict,   # 来自process_user_input
):
    api_key = config["api_key"]
    base_url = config["base_url"]
    model_name = config["model_name"]
    temperature = config["temperature"]
    stream = config["stream"]
    max_tokens = config["max_tokens"]
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    # 调试：打印消息内容
    if logger.isEnabledFor(logging.DEBUG):
        test_print(messages)
    # 调用OpenAI API
    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            stream=stream,
            max_tokens=max_tokens,
            #response_format={"type": "json_object"}
        )
        full_content = []
        print("[AI正在响应]", end="", flush=True)
        for chunk in response:
            if chunk.choices[0].delta.content:
                chunk_content = chunk.choices[0].delta.content
                full_content.append(chunk_content)
                print(chunk_content, end="", flush=True)  # 实时显示

        print("\n")  # 流式输出结束换行
        logger.info(f"API调用成功")
    
    except Exception as e:
        logger.error(f"API调用失败: {str(e)}")
        return

def test_print(messages):#调试-打印消息内容
    print("即将发送的请求消息内容:")  
    print("\n\033[1;36m=== 调试信息 ===\033[0m")  # 使用颜色和分隔线增强可读性
    for i, msg in enumerate(messages, 1):
        print(f"\033[1;32m消息 {i}:\033[0m")
        print(f"\033[1;33m角色:\033[0m {msg['role']}")
        print("\033[1;33m内容:\033[0m")
        print(msg['content'])  # 直接打印内容本身（非JSON格式）
        print("-" * 50) 