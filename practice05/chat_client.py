import os
import json
import http.client
import sys
import subprocess


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


# 工具函数：查询文档仓库（使用本地模型）
def anythingllm_query(message):
    """查询文档仓库（使用本地模型）"""
    try:
        # 从环境变量获取配置
        env_vars = load_env()
        base_url = env_vars.get('BASE_URL', 'http://localhost:11434/v1')
        model = env_vars.get('MODEL', 'llama3')
        api_key = env_vars.get('API_KEY', 'your-api-key-here')
        
        # 构建查询提示，模拟文档仓库查询
        query_prompt = f"""你是一个文档仓库助手，请根据你的知识库回答以下问题：
        
问题：{message}

请提供详细的回答。"""
        
        # 解析 base_url
        if base_url.startswith('http://'):
            host = base_url[7:].split('/')[0]
            path = '/' + '/'.join(base_url[7:].split('/')[1:]) if len(base_url[7:].split('/')) > 1 else ''
            conn = http.client.HTTPConnection(host)
        elif base_url.startswith('https://'):
            host = base_url[8:].split('/')[0]
            path = '/' + '/'.join(base_url[8:].split('/')[1:]) if len(base_url[8:].split('/')) > 1 else ''
            conn = http.client.HTTPSConnection(host)
        else:
            return 'Error: Invalid BASE_URL format'
        
        # 构建消息
        messages = [
            {"role": "system", "content": "你是一个文档仓库助手，专门回答用户关于文档仓库中的信息查询。请使用中文回答。"},
            {"role": "user", "content": query_prompt}
        ]
        
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
        conn.request('POST', f'{path}/chat/completions', json.dumps(data, ensure_ascii=False), headers)
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


# 工具映射
tools = {
    'anythingllm_query': anythingllm_query
}


# 系统提示词
system_prompt = """
你是一个AI助手，能够使用以下工具来帮助用户查询文档仓库：

工具列表：
1. anythingllm_query(message): 查询 AnythingLLM 文档仓库
   - 参数：message (字符串) - 查询消息
   - 返回：文档仓库中的相关信息

使用工具的格式：
```json
{
  "tool_call": {
    "name": "工具名称",
    "parameters": {
      "参数1": "值1"
    }
  }
}
```

当你需要使用工具时，请以JSON格式输出工具调用请求。
当收到工具执行结果后，请根据结果向用户提供总结和下一步建议。

特别注意：
- 当用户提到"文档仓库"、"文件仓库"、"仓库"等关键词时，请使用anythingllm_query工具查询文档仓库
- 对于其他请求，如果不需要工具调用，可以直接回答用户
- 所有回复必须使用中文，不要包含任何英文
- 不要在回复中添加任何额外的提示信息或思考过程

请严格按照上述格式输出，不要添加任何额外的文本。
"""


def call_llm_stream(prompt, history, env_vars):
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
            messages.append({"role": "assistant", "content": json.dumps(msg["tool_call"])})
        if "tool_result" in msg:
            messages.append({"role": "tool", "content": msg["tool_result"]})
    messages.append({"role": "user", "content": prompt})
    
    # 构建请求数据
    data = {
        'model': model,
        'messages': messages,
        'max_tokens': 500,
        'temperature': 0.7,
        'stream': True
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # 发送请求
    try:
        conn.request('POST', f'{path}/chat/completions', json.dumps(data), headers)
        response = conn.getresponse()
        
        # 处理流式响应
        full_response = []
        for line in response:
            line = line.decode('utf-8').strip()
            if line.startswith('data: '):
                data_part = line[6:]
                if data_part == '[DONE]':
                    break
                try:
                    chunk = json.loads(data_part)
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        if 'content' in delta:
                            content = delta['content']
                            full_response.append(content)
                            print(content, end='', flush=True)
                except json.JSONDecodeError:
                    pass
        conn.close()
        
        print()  # 换行
        return ''.join(full_response)
    except Exception as e:
        print(f'Error: {str(e)}')
        conn.close()
        return f'Error: {str(e)}'


def process_tool_call(tool_call_json):
    """处理工具调用请求"""
    try:
        tool_call = json.loads(tool_call_json)
        if 'tool_call' in tool_call:
            tool_name = tool_call['tool_call']['name']
            parameters = tool_call['tool_call']['parameters']
            
            if tool_name in tools:
                if tool_name == 'anythingllm_query':
                    return tools[tool_name](parameters['message'])
            else:
                return f'Error: Tool {tool_name} not found'
        else:
            return 'Error: Invalid tool call format'
    except Exception as e:
        return f'Error: {str(e)}'


def main():
    env_vars = load_env()
    if not env_vars:
        print('No .env file found. Please copy env.example to .env and fill in the values.')
        return
    
    history = []
    print('=== LLM Chat Client with AnythingLLM Integration ===')
    print('Type your message and press Enter to chat.')
    print('Mention "文档仓库", "文件仓库", or "仓库" to query document repository.')
    print('Press Ctrl+C to exit.')
    print('====================================================')
    
    try:
        while True:
            try:
                user_input = input('\nYou: ')
                if not user_input.strip():
                    continue
                
                print('Assistant: ', end='', flush=True)
                response = call_llm_stream(user_input, history, env_vars)
                
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
                
                # 限制历史记录长度，避免上下文过长
                if len(history) > 5:
                    history = history[-5:]
                    
            except EOFError:
                # 处理Ctrl+D输入
                break
    except KeyboardInterrupt:
        # 处理Ctrl+C退出
        print('\nExiting chat client...')


if __name__ == '__main__':
    main()
