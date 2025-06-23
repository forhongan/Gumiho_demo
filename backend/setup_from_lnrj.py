#---------------临时启动入口,从轻小说机翻机器人中导入
#项目的启动程序
import os
import shutil
from ruamel.yaml import YAML
import tkinter as tk
from format import LightNovelRobotJpFormat
from tkinter import filedialog, messagebox

def start_setup(): #获取用户设置
    project_name = project_name_entry.get()
    translator_name = translator_name_entry.get()
    file_path = file_path_entry.get()
    # toc_file = toc_file_entry.get()  # 获取目录文件路径

    if not project_name:
        messagebox.showerror("错误", "作品名是必需的")
        return
    if not translator_name:
        messagebox.showerror("错误", "译者名是必需的")
        return
    if not file_path:
        messagebox.showerror("错误", "未选择文件")
        return
    setup_project(project_name, translator_name, file_path)

def setup_project(project_name, translator_name, file_path):  # 初始化项目对象
    # 确定文件类型
    file_extension = os.path.splitext(file_path)[1].lower()
    original_format = file_extension

    # 创建项目文件夹
    project_folder = f"{project_name}_project"
    os.makedirs(project_folder, exist_ok=True)

    # 修改配置：使用 ruamel.yaml 保留注释结构地加载、修改并写入配置文件
    yaml_obj = YAML()
    with open('lnrj_default_config.yml', 'r', encoding='utf-8') as file:
        config_data = yaml_obj.load(file)
    config_data["Translation Project Name"] = project_name
    config_data["book/game/video Name"] = project_name
    config_data["Translater"] = [translator_name]
    config_data["file name"] =   os.path.basename(file_path)
    config_data["Original format"] = os.path.splitext(file_path)[1].lower()
    config_data["paragraphed"] = True  # 新增段落设置
    with open(os.path.join(project_folder, 'config.yml'), 'w', encoding='utf-8') as file:
        yaml_obj.dump(config_data, file)

    # 创建sourcefile文件夹并复制源文件
    source_folder = os.path.join(project_folder, 'sourcefile')
    os.makedirs(source_folder, exist_ok=True)
    shutil.copy(file_path, source_folder)

    # 注释掉复制目录文件的相关逻辑
    # if toc_file:
    #     try:
    #         with open(toc_file, 'r', encoding='utf-8') as f:
    #             toc_content = f.read()
    #         toc_path = os.path.join(source_folder, 'toc.txt')
    #         with open(toc_path, 'w', encoding='utf-8') as f:
    #             f.write(toc_content)
    #     except Exception as e:
    #         messagebox.showerror("错误", f"复制目录文件失败: {e}")
    #         return

    messagebox.showinfo("成功", f"项目设置完成。文件保存在 {project_folder}")
    
    work1=LightNovelRobotJpFormat(f"{project_name}_project")
    work1.lurj_project_Initialization()
    

def select_file():#展示文件选择界面并记录选择的文件路径
    file_path = filedialog.askopenfilename(title="选择需要翻译的文件")#调用文件对话框，让用户选择文件
    file_path_entry.delete(0, tk.END)#清空输入框
    file_path_entry.insert(0, file_path)#将选择的文件路径插入输入框

# 注释掉选择目录文件的相关函数
# def select_toc_file():
#     toc_path = filedialog.askopenfilename(title="选择目录文本文件", filetypes=[("Text Files", "*.txt")])
#     toc_file_entry.delete(0, tk.END)
#     toc_file_entry.insert(0, toc_path)

def ai_default_config_chance():  # 修改默认配置文件中的ai设置
    yaml_obj = YAML()
    # 修改打开的配置文件名称
    with open('lnrj_default_config.yml', 'r', encoding='utf-8') as file:
        config_data = yaml_obj.load(file)
    # ...existing代码，用config_data进行ai设置的修改...

# def ai_default_config_test():#测试ai连通性,效率
#     call_ai()
#     # --------------------待添加内容--------------------------------

#def restore_default_config():#恢复默认配置文件
#    #待完成

# 创建GUI--------------------待优化--------------------------------
# 创建主窗口
#def create_window():
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

# 注释掉GUI中关于目录文件选择的组件
# tk.Label(root, text="选择目录文件:").grid(row=3, column=0, padx=10, pady=5)
# toc_file_entry = tk.Entry(root)
# toc_file_entry.grid(row=3, column=1, padx=10, pady=5)
# tk.Button(root, text="浏览目录", command=select_toc_file).grid(row=3, column=2, padx=10, pady=5)

# 创建并放置开始按钮
tk.Button(root, text="配置项目", command=start_setup).grid(row=4, column=1, pady=20)

root.mainloop()
    
# if __name__ == "__main__":
#     #create_window()