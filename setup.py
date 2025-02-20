#项目的启动程序
import os
import shutil
import yaml
import tkinter as tk
from tkinter import filedialog, messagebox

def start_setup(): #获取用户设置
    project_name = project_name_entry.get()
    translator_name = translator_name_entry.get()
    file_path = file_path_entry.get()

    if not project_name:
        messagebox.showerror("错误", "作品名是必需的")
        return
    if not translator_name:
        messagebox.showerror("错误", "译者名是必需的")
        return
    if not file_path:
        messagebox.showerror("错误", "未选择文件")
        return
    # ......
    # --------------------待添加内容--------------------------------
    setup_project(project_name, translator_name, file_path)

def setup_project(project_name, translator_name, file_path):#初始化项目对象
    # 确定文件类型
    file_extension = os.path.splitext(file_path)[1].lower()
    original_format = file_extension

    # 创建项目文件夹
    project_folder = f"{project_name}_project"
    os.makedirs(project_folder, exist_ok=True)

    # 以纯文本读取默认配置文件以保留注释
    with open('default_config.yml', 'r', encoding='utf-8') as file:
        config_content = file.read()
        config = yaml.safe_load(config_content)

    # 修改配置文件内容
    new_config_content = config_content.replace(
        'Translation Project Name: default', f'Translation Project Name: {project_name}'
    ).replace(
        'Translater:\n  - "Gumiho System"', f'Translater:\n  - "{translator_name}"'
    ).replace(
        'Original format:', f'Original format: {original_format}'
    )

    # 保存新的配置文件到项目文件夹
    with open(os.path.join(project_folder, 'config.yml'), 'w', encoding='utf-8') as file:
        file.write(new_config_content)

    # 创建sourcefile文件夹并复制源文件
    source_folder = os.path.join(project_folder, 'sourcefile')
    os.makedirs(source_folder, exist_ok=True)
    shutil.copy(file_path, source_folder)

    messagebox.showinfo("成功", f"项目设置完成。文件保存在 {project_folder}")


def select_file():#展示文件选择界面并记录选择的文件路径
    file_path = filedialog.askopenfilename(title="选择需要翻译的文件")#调用文件对话框，让用户选择文件
    file_path_entry.delete(0, tk.END)#清空输入框
    file_path_entry.insert(0, file_path)#将选择的文件路径插入输入框

def ai_default_config_chance():#修改默认配置文件中的ai设置
    with open('default_config.yml', 'r', encoding='utf-8') as file:
        config_content = file.read()
        config = yaml.safe_load(config_content)
    # --------------------待添加内容--------------------------------

# def ai_default_config_test():#测试ai连通性,效率
#     call_ai()
#     # --------------------待添加内容--------------------------------

#def restore_default_config():#恢复默认配置文件
#    #待完成

# 创建GUI--------------------待优化--------------------------------
# 创建主窗口
root = tk.Tk()
root.title("翻译项目设置")

# 创建并放置标签和输入框
tk.Label(root, text="作品名:").grid(row=0, column=0, padx=10, pady=5)
project_name_entry = tk.Entry(root)
project_name_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="译者名:").grid(row=1, column=0, padx=10, pady=5)
translator_name_entry = tk.Entry(root)
translator_name_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="选择文件:").grid(row=2, column=0, padx=10, pady=5)
file_path_entry = tk.Entry(root)
file_path_entry.grid(row=2, column=1, padx=10, pady=5)
tk.Button(root, text="浏览", command=select_file).grid(row=2, column=2, padx=10, pady=5)

# 创建并放置开始按钮
tk.Button(root, text="配置项目", command=start_setup).grid(row=3, column=1, pady=20)

root.mainloop()
