
#以前用于生成用户profile的代码，建议别看

def filled(group_file_path):
    group_number = int(group_file_path.split('_')[-1].split('.')[0])
    
    # 如果 group_number 等于 1，则直接结束函数
    if group_number == 1:
        print("group_number 为 1，跳过 filled 函数。")
        return
    
    result_file_path = group_file_path.replace(f'group_{group_number}.yaml', f'group_{group_number-1}_result.json')
    
    with open(result_file_path, 'r', encoding='utf-8') as result_file:
        result_data = json.load(result_file)
    
    translation_content = result_data.get("翻译结果", [])
    translation_text = '\n'.join(['  ' + line for item in translation_content for line in item["machineTrans"].split('\n')])
    
    with open(group_file_path, 'r', encoding='utf-8') as group_file:
        group_content = group_file.read()
    
    insert_position = group_content.find('上1组的译文为:')
    if insert_position != -1:
        print("找到了插入位置。")
        insert_position += len('上1组的译文为:\n')
        new_group_content = group_content[:insert_position] + translation_text + group_content[insert_position:]
        
        # 删除插入后译文中的重复行
        lines = new_group_content.split('\n')
        seen = set()
        unique_lines = []
        for line in lines:
            if line not in seen:
                unique_lines.append(line)
                seen.add(line)
        new_group_content = '\n'.join(unique_lines)
        
        with open(group_file_path, 'w', encoding='utf-8') as group_file:
            group_file.write(new_group_content)
    else:
        print("未找到插入位置。")
    
    # 读取 translatesetting.yml 中的配置
    with open(os.path.join(os.path.dirname(group_file_path), '../translatesetting.yml'), 'r', encoding='utf-8') as setting_file:
        settings = yaml.safe_load(setting_file)
    
    if settings['Automatically generated text summary']['enable']:
        N = settings['Automatically generated text summary']['Number of history generated records']
        summaries = []
        
        for i in range(max(1, group_number - N), group_number):
            previous_result_file_path = group_file_path.replace(f'group_{group_number}.yaml', f'group_{i}_result.json')
            if os.path.exists(previous_result_file_path):
                with open(previous_result_file_path, 'r', encoding='utf-8') as previous_result_file:
                    previous_result_data = json.load(previous_result_file)
                
                summary_content = previous_result_data.get("本次翻译内容总结", "")
                if summary_content:
                    summaries.append(f"  第{i}段的总结为:\n  {summary_content}")
                    print(f"找到第{i}段的总结: {summary_content}")
        
        if summaries:
            summaries_content = '\n'.join(summaries)
            with open(group_file_path, 'r', encoding='utf-8') as group_file:
                group_content = group_file.read()
            
            summary_insert_position = group_content.find('此外,我们将上')
            if summary_insert_position != -1:
                print("找到了总结插入位置。")
                summary_insert_position += len('此外,我们将上 N 段的文本进行了总结,总结如下:\n')
                new_group_content = group_content[:summary_insert_position] + summaries_content + group_content[summary_insert_position:]
                
                with open(group_file_path, 'w', encoding='utf-8') as group_file:
                    group_file.write(new_group_content + '\n')
            else:
                print("未找到总结插入位置。")
