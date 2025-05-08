#Checked-----------这里指定了与ai交互(调用)的函数
import logging
from openai import OpenAI

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def call_ai(
    config: dict,       # ai基础配置,包括api,key,温度,max_tokens等
    system_prompt: list,       # ai的系统prompt 
    user_prompt: list,   # 来自process_user_input
):
    api_key = config["api_key"]
    base_url = config["base_url"]
    model_name = config["model_name"]
    temperature = config.get("temperature", 0.7)
    stream = config.get("stream", True)
    max_tokens = config.get("max_tokens", 8152)
    timeout= config.get("timeout", 1800)
    system_str = " ".join(system_prompt) if isinstance(system_prompt, list) else str(system_prompt)
    user_str = " ".join(user_prompt) if isinstance(user_prompt, list) else str(user_prompt)
    messages = [
        {"role": "system", "content": system_str},
        {"role": "user", "content": user_str},
    ]
    # 调试：打印消息内容
    # if logger.isEnabledFor(logging.DEBUG):
    #     test_print(messages)
    if base_url == "test":
        
        test_print(messages)
        return{}
    test_print(messages)
    # 调用OpenAI API
    client = OpenAI(api_key=api_key, base_url=base_url, max_retries=0, timeout=timeout)
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            stream=stream,
            max_tokens=max_tokens,
        )
        reasoning_content = ""
        content = ""
        
        if stream:
            print("[AI正在响应]", end="", flush=True)
            for chunk in response:
                delta = chunk.choices[0].delta
                # 处理 reasoning_content
                current_reasoning = getattr(delta, 'reasoning_content', '') or ''
                reasoning_content += current_reasoning
                # 处理 content
                current_content = getattr(delta, 'content', '') or ''
                content += current_content
                # 实时显示
                print(current_reasoning, end="", flush=True)
                print(current_content, end="", flush=True)
            print()  # 换行
        else:
            # 非流式响应处理
            reasoning_content = getattr(response.choices[0].message, 'reasoning_content', '')
            content = getattr(response.choices[0].message, 'content', '')
        
        logger.info("API调用成功")
        return {
            "content": content,
            "reasoning_content": reasoning_content,
        }
    except Exception as e:
        logger.error(f"API调用失败: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }

def test_print(messages):#调试-打印消息内容
    print("即将发送的请求消息内容:")  
    print("\n\033[1;36m=== 调试信息 ===\033[0m")  # 使用颜色和分隔线增强可读性
    for i, msg in enumerate(messages, 1):
        print(f"\033[1;32m消息 {i}:\033[0m")
        print(f"\033[1;33m角色:\033[0m {msg['role']}")
        print("\033[1;33m内容:\033[0m")
        print(msg['content'])  # 直接打印内容本身（非JSON格式）
        print("-" * 50) 

def test_prompt(sys_prompt, user_prompt):#调试-测试用例
    # 测试输入的prompt
    """
    测试函数,输出 ai 的 system prompt 和 user prompt，
    并确保每行分别清晰显示
    """
    print("System Prompt:")
    if isinstance(sys_prompt, list):
        for line in sys_prompt:
            print(line)
    else:
        print(sys_prompt)
        
    print("\nUser Prompt:")
    def print_lines(item):
        if isinstance(item, list):
            for line in item:
                print_lines(line)
        else:
            print(item)
            
    print_lines(user_prompt)
    
if __name__ == "__main__":
    # 测试用例
    test_config = {
        "api_key": "",              # 替换为实际API key
        "base_url": "https://api.deepseek.com",     # API 端点(示例)
        "model_name": "deepseek-reasoner",            # 模型名称示例
        "temperature": 0.7,
        "stream": True,
        "max_tokens": 8152,
    }
    test_system_prompt = ["你是一个有帮助的助手。"]
    test_user_prompt = ["How many Rs are there in the word 'strawberry'?"]
    
    result = call_ai(test_config, test_system_prompt, test_user_prompt)
    print("测试结果:", result)