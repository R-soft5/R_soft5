import os
import json
import http.client
import sys

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
    messages = []
    # 添加系统消息，要求使用全中文回答，包括思考过程
    messages.append({"role": "system", "content": "请使用中文简体回答用户的问题，包括思考过程在内的所有内容都必须使用中文，不要包含任何英文，包括但不限于'Thinking Process'等英文标记。"})
    for msg in history:
        messages.append({"role": "user", "content": msg["user"]})
        messages.append({"role": "assistant", "content": msg["assistant"]})
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
                            # 替换英文标记为中文
                            content = content.replace('Thinking Process:', '思考过程：')
                            # 过滤掉英文内容，只保留中文
                            content = ''.join([c for c in content if ord(c) > 127 or c in '，。！？；：""（）【】'])
                            full_response.append(content)
                            print(content, end='', flush=True)
                        elif 'reasoning_content' in delta:
                            # 处理包含 reasoning_content 字段的响应
                            content = delta['reasoning_content']
                            # 替换英文标记为中文
                            content = content.replace('Thinking Process:', '思考过程：')
                            # 过滤掉英文内容，只保留中文
                            content = ''.join([c for c in content if ord(c) > 127 or c in '，。！？；：""（）【】'])
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

def main():
    env_vars = load_env()
    if not env_vars:
        print('No .env file found. Please copy env.example to .env and fill in the values.')
        return
    
    history = []
    print('=== LLM Chat Client ===')
    print('Type your message and press Enter to chat.')
    print('Press Ctrl+C to exit.')
    print('======================')
    
    try:
        while True:
            try:
                user_input = input('\nYou: ')
                if not user_input.strip():
                    continue
                
                print('Assistant: ', end='', flush=True)
                response = call_llm_stream(user_input, history, env_vars)
                
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