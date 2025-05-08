#这里设计了有关初次翻译过程的主要函数
#函数参数仅用作提示
#如果过于复杂,可以将函数分解为更小的函数
import logging #推荐使用logging模块记录日志,规范化调试

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#根据设置内容和翻译记录文件,与用户交互(可选)的内容,将初次翻译请求的关键参数传递给初次翻译请求构成函数,该函数是为了分解构成函数的功能,使得构成函数更加简洁
def f_sys_make_drive(config,p_record):#config
    # ...
    return sys_parameter
#构成初次翻译时每次请求的系统prompt,config:配置文件中的first_trans_json: |和其他数据
def f_sys_make(sys_parameter): 
    
    # ...
    return sys_prompt


#根据设置内容和翻译记录文件,与用户交互(可选)的内容,将初次翻译请求的关键参数传递给初次翻译请求构成函数,该函数是为了分解构成函数的功能,使得构成函数更加简洁
def f_user_make_drive(config,p_record):#config
        # ...
    return user_parameter
#构成初次翻译时每次请求的用户prompt,config:配置文件中指定一次翻译的文本数量等设定
def f_user_make(user_parameter): 
    # ...
    return user_prompt

#根据设定中的内容,将不同的ai返回值标准化为record中的内容
def ai_replication_format(replication,config)
    # ...
    #将本条record记录回record.json
def user_check():#定义初译阶段用户检查函数
    def renew_record():#将用户检查后的内容更新到翻译工程文件中

#定义初次翻译的主函数,检查目前的翻译进度,继续翻译
//
    #打开配置文件提取配置(从config.yaml中提取)...
    #推荐的方式是将需要的设置项提取到一个字典中,然后传递给不同的构成函数
    config1=
    config2=
    config3=
    # ...
    
    sys_prompt=f_sys_make(f_sys_make_drive(config1,p_record))
    user_prompt=f_user_make(f_user_make_drive(config2,p_record))
    
    ai_config={
        "api_key": "your-api-key",
        # ...
    }
    replication=call_ai(sys_prompt,user_prompt,ai_config)
    ai_replication_format(replication,config3)
    user_check()
    #保存内容到record.json
    # 检查ai返回的内容
    # 用户检查 user_check(),检查后修正后内容到record.json