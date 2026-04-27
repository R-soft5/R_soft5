import os
import json
import http.client

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

def call_llm(prompt, env_vars):
    base_url = env_vars.get('BASE_URL')
    model = env_vars.get('MODEL')
    api_key = env_vars.get('API_KEY')
    
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
    
    # 构建请求数据
    data = {
        'model': model,
        'prompt': prompt,
        'max_tokens': 150,
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

if __name__ == '__main__':
    env_vars = load_env()
    if not env_vars:
        print('No .env file found. Please copy env.example to .env and fill in the values.')
    else:
        prompt = 'Hello, can you tell me a short joke?'
        response = call_llm(prompt, env_vars)
        print('Prompt:', prompt)
        print('Response:', response)