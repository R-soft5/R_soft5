import os
import json
import http.client
import sys
from datetime import datetime


def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"')
    return env_vars


# 工具函数1：列出目录下的文件信息
def list_files(directory):
    """列出某个目录下有哪些文件（包括文件的基本属性、大小等信息）"""
    try:
        files = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                stat = os.stat(item_path)
                files.append({
                    'name': item,
                    'type': 'file',
                    'size': stat.st_size,
                    'mtime': stat.st_mtime
                })
            elif os.path.isdir(item_path):
                files.append({
                    'name': item,
                    'type': 'directory'
                })
        return json.dumps(files, ensure_ascii=False, indent=2)
    except Exception as e:
        return f'Error: {str(e)}'


# 工具函数2：修改文件名字
def rename_file(directory, old_name, new_name):
    """修改某个目录下某个文件的名字"""
    try:
        old_path = os.path.join(directory, old_name)
        new_path = os.path.join(directory, new_name)
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            return f'Successfully renamed {old_name} to {new_name}'
        else:
            return f'Error: File {old_name} not found'
    except Exception as e:
        return f'Error: {str(e)}'


# 工具函数3：删除文件
def delete_file(directory, filename):
    """删除某个目录下的某个文件"""
    try:
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return f'Successfully deleted {filename}'
        else:
            return f'Error: File {filename} not found'
    except Exception as e:
        return f'Error: {str(e)}'


# 工具函数4：新建文件并写入内容
def create_file(directory, filename, content):
    """在某个目录下新建1个文件，并且写入内容"""
    try:
        file_path = os.path.join(directory, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f'Successfully created file {filename}'
    except Exception as e:
        return f'Error: {str(e)}'


# 工具函数5：读取文件内容
def read_file(directory, filename):
    """读取某个目录下的某个文件的内容"""
    try:
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        else:
            return f'Error: File {filename} not found'
    except Exception as e:
        return f'Error: {str(e)}'


# 工具函数6：访问网页并返回内容
def fetch_webpage(url):
    """访问网页并返回网页内容"""
    try:
        if url.startswith('http://'):
            host = url[7:].split('/')[0]
            path = '/' + '/'.join(url[7:].split('/')[1:]) if len(url[7:].split('/')) > 1 else ''
            conn = http.client.HTTPConnection(host)
        elif url.startswith('https://'):
            host = url[8:].split('/')[0]
            path = '/' + '/'.join(url[8:].split('/')[1:]) if len(url[8:].split('/')) > 1 else ''
            conn = http.client.HTTPSConnection(host)
        else:
            return 'Error: Invalid URL format. URL must start with http:// or https://'
        
        conn.request('GET', path)
        response = conn.getresponse()
        content = response.read().decode('utf-8', errors='ignore')
        conn.close()
        
        # 限制返回内容长度，避免过长
        if len(content) > 5000:
            return content[:5000] + '\n[Content truncated]'
        return content
    except Exception as e:
        return f'Error: {str(e)}'


# 工具函数7：查找聊天历史
def search_chat_history(query):
    """查找聊天历史记录"""
    try:
        # 从项目根目录读取log.txt
        log_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log.txt')
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # 构建搜索请求
            search_prompt = f"根据以下聊天历史记录，回答用户的问题：\n\n{log_content}\n\n用户问题：{query}"
            return search_prompt
        else:
            return f'Error: Chat history log file not found at {log_file_path}'
    except Exception as e:
        return f'Error: {str(e)}'


# 工具映射
tools = {
    'list_files': list_files,
    'rename_file': rename_file,
    'delete_file': delete_file,
    'create_file': create_file,
    'read_file': read_file,
    'fetch_webpage': fetch_webpage,
    'search_chat_history': search_chat_history
}


# 系统提示词
system_prompt = """
你是一个AI助手，能够使用以下工具来帮助用户完成文件操作、网络访问和聊天历史查询任务：

工具列表：
1. list_files(directory): 列出某个目录下有哪些文件（包括文件的基本属性、大小等信息）
   - 参数：directory (字符串) - 目录路径
   - 返回：JSON格式的文件列表

2. rename_file(directory, old_name, new_name): 修改某个目录下某个文件的名字
   - 参数：
     - directory (字符串) - 目录路径
     - old_name (字符串) - 旧文件名
     - new_name (字符串) - 新文件名
   - 返回：操作结果信息

3. delete_file(directory, filename): 删除某个目录下的某个文件
   - 参数：
     - directory (字符串) - 目录路径
     - filename (字符串) - 要删除的文件名
   - 返回：操作结果信息

4. create_file(directory, filename, content): 在某个目录下新建1个文件，并且写入内容
   - 参数：
     - directory (字符串) - 目录路径
     - filename (字符串) - 新文件名
     - content (字符串) - 要写入的内容
   - 返回：操作结果信息

5. read_file(directory, filename): 读取某个目录下的某个文件的内容
   - 参数：
     - directory (字符串) - 目录路径
     - filename (字符串) - 要读取的文件名
   - 返回：文件内容

6. fetch_webpage(url): 访问网页并返回网页内容
   - 参数：url (字符串) - 网页URL，必须以http://或https://开头
   - 返回：网页内容（如果内容过长会被截断）

7. search_chat_history(query): 查找聊天历史记录
   - 参数：query (字符串) - 搜索查询
   - 返回：包含聊天历史和查询的搜索提示

使用工具的格式：
```json
{
  "tool_call": {
    "name": "工具名称",
    "parameters": {
      "参数1": "值1",
      "参数2": "值2"
    }
  }
}
```

当你需要使用工具时，请以JSON格式输出工具调用请求。
当收到工具执行结果后，请根据结果向用户提供总结和下一步建议。

特别注意：
- 当用户发送的信息以"/search"开头，或表达了"查找聊天历史"的意思，或你认为应该查找聊天历史时，请使用search_chat_history工具
- 对于其他请求，请根据具体情况选择合适的工具
- 所有回复必须使用中文，不要包含任何英文
- 不要在回复中添加任何额外的提示信息或思考过程

请严格按照上述格式输出，不要添加任何额外的文本。
"""


def call_llm(prompt, history, env_vars):
    base_url = env_vars.get('BASE_URL', 'http://localhost:11434/v1')
    model = env_vars.get('MODEL', 'llama3')
    api_key = env_vars.get('API_KEY', 'your-api-key-here')
    
    # 解析base_url
    if base_url.startswith('http://'):
        host = base_url[7:].split('/')[0]
        path = '/' + '/'.join(base_url[7:].split('/')[1:]) if len(base_url[7:].split('/')) > 1 else ''
        conn = http.client.HTTPConnection(host)
    elif base_url.startswith('https://'):
        host = base_url[8:].split('/')[0]
        path = '/' + '/'.join(base_url[8:].split('/')[1:]) if len(base_url[8:].split('/')) > 1 else ''
        conn = http.client.HTTPSConnection(host)
    else:
        raise ValueError('Invalid BASE_URL format')
    
    # 构建消息历史
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    for msg in history:
        messages.append({"role": "user", "content": msg["user"]})
        if "assistant" in msg:
            messages.append({"role": "assistant", "content": msg["assistant"]})
        if "tool_call" in msg:
            messages.append({"role": "assistant", "content": json.dumps(msg["tool_call"]), "tool_calls": [msg["tool_call"]]})
        if "tool_result" in msg:
            messages.append({"role": "tool", "content": msg["tool_result"], "tool_call_id": "tool_1"})
    messages.append({"role": "user", "content": prompt})
    
    # 构建请求数据
    data = {
        'model': model,
        'messages': messages,
        'max_tokens': 1000,
        'temperature': 0.7
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # 发送请求
    try:
        conn.request('POST', f'{path}/chat/completions', json.dumps(data), headers)
        response = conn.getresponse()
        result = response.read().decode('utf-8')
        conn.close()
        
        # 解析响应
        response_data = json.loads(result)
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return f'Error: {response_data.get("error", {}).get("message", "Unknown error")}'
    except Exception as e:
        return f'Error: {str(e)}'


def process_tool_call(tool_call_json):
    """处理工具调用请求"""
    try:
        tool_call = json.loads(tool_call_json)
        if 'tool_call' in tool_call:
            tool_name = tool_call['tool_call']['name']
            parameters = tool_call['tool_call']['parameters']
            
            if tool_name in tools:
                if tool_name == 'list_files':
                    return tools[tool_name](parameters['directory'])
                elif tool_name == 'rename_file':
                    return tools[tool_name](parameters['directory'], parameters['old_name'], parameters['new_name'])
                elif tool_name == 'delete_file':
                    return tools[tool_name](parameters['directory'], parameters['filename'])
                elif tool_name == 'create_file':
                    return tools[tool_name](parameters['directory'], parameters['filename'], parameters['content'])
                elif tool_name == 'read_file':
                    return tools[tool_name](parameters['directory'], parameters['filename'])
                elif tool_name == 'fetch_webpage':
                    return tools[tool_name](parameters['url'])
                elif tool_name == 'search_chat_history':
                    return tools[tool_name](parameters['query'])
            else:
                return f'Error: Tool {tool_name} not found'
        else:
            return 'Error: Invalid tool call format'
    except Exception as e:
        return f'Error: {str(e)}'


def summarize_chat_history(history, env_vars):
    """总结聊天历史记录"""
    # 准备要总结的内容
    summary_prompt = "请总结以下聊天历史，对前70%的内容进行压缩，保留最后30%的内容原文：\n\n"
    
    # 计算分割点
    split_point = int(len(history) * 0.7)
    summary_part = history[:split_point]
    keep_part = history[split_point:]
    
    # 构建总结部分的文本
    for msg in summary_part:
        if "user" in msg:
            summary_prompt += f"用户: {msg['user']}\n"
        if "assistant" in msg:
            summary_prompt += f"助手: {msg['assistant']}\n"
    
    # 构建保留部分的文本
    summary_prompt += "\n保留原文部分：\n"
    for msg in keep_part:
        if "user" in msg:
            summary_prompt += f"用户: {msg['user']}\n"
        if "assistant" in msg:
            summary_prompt += f"助手: {msg['assistant']}\n"
    
    # 调用LLM进行总结
    summary = call_llm(summary_prompt, [], env_vars)
    
    # 返回总结结果
    return summary


def extract_key_info(history):
    """提取关键信息"""
    # 构建提取提示
    extract_prompt = "请从以下聊天历史中提取关键信息，按照5W规则（谁Who、做了什么事What、什么时候When、在何处Where、为什么要做这个事Why）提取多条关键信息：\n\n"
    
    for msg in history:
        if "user" in msg:
            extract_prompt += f"用户: {msg['user']}\n"
        if "assistant" in msg:
            extract_prompt += f"助手: {msg['assistant']}\n"
    
    # 这里应该调用LLM进行提取，但为了简化，我们直接返回提示
    return extract_prompt


def save_key_info(key_info):
    """保存关键信息到log.txt文件"""
    # 保存到项目根目录
    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log.txt')
    
    # 追加写入关键信息
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        f.write(key_info)
        f.write("\n")
    
    return f"关键信息已保存到 {log_file}"


def calculate_history_length(history):
    """计算聊天历史的长度"""
    length = 0
    for msg in history:
        if "user" in msg:
            length += len(msg["user"])
        if "assistant" in msg:
            length += len(msg["assistant"])
    return length


def main():
    env_vars = load_env()
    if not env_vars:
        print('No .env file found. Please copy env.example to .env and fill in the values.')
        return
    
    history = []
    chat_count = 0
    print('=== LLM Tool Client with Chat History Management ===')
    print('You can ask me to perform file operations, fetch webpages, or search chat history.')
    print('Use "/search" to search chat history.')
    print('Press Ctrl+C to exit.')
    print('====================================')
    
    try:
        while True:
            try:
                user_input = input('\nYou: ')
                if not user_input.strip():
                    continue
                
                chat_count += 1
                
                # 检查是否需要总结聊天历史
                if len(history) > 5 or calculate_history_length(history) > 3000:
                    print('\nAssistant: 正在总结聊天历史...')
                    summary = summarize_chat_history(history, env_vars)
                    print(f'总结结果: {summary}')
                    # 用总结替换历史记录
                    history = [{"user": "聊天历史总结", "assistant": summary}]
                
                # 检查是否需要提取关键信息
                if chat_count % 5 == 0:
                    print('\nAssistant: 正在提取关键信息...')
                    key_info = extract_key_info(history)
                    save_result = save_key_info(key_info)
                    print(save_result)
                
                # 正常处理用户输入
                print('Assistant: ', end='', flush=True)
                response = call_llm(user_input, history, env_vars)
                print(response)
                
                # 检查是否包含工具调用
                if response.strip().startswith('{') and 'tool_call' in response:
                    # 处理工具调用
                    tool_result = process_tool_call(response)
                    print('Tool Result: ', tool_result)
                    
                    # 添加到历史记录
                    history.append({"user": user_input, "tool_call": json.loads(response), "tool_result": tool_result})
                else:
                    # 添加到历史记录
                    history.append({"user": user_input, "assistant": response})
                
            except EOFError:
                # 处理Ctrl+D输入
                break
    except KeyboardInterrupt:
        # 处理Ctrl+C退出
        print('\nExiting tool client...')


if __name__ == '__main__':
    main()
