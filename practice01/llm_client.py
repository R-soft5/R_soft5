import os
import json
import http.client
import time

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        value = value.strip()
                        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        env_vars[key.strip()] = value
    return env_vars

def call_llm(prompt, env_vars):
    base_url = env_vars.get('BASE_URL')
    model = env_vars.get('MODEL')
    api_key = env_vars.get('API_KEY')
    
    if not base_url:
        return 'Error: BASE_URL is not set in .env file', None
    if not model:
        return 'Error: MODEL is not set in .env file', None
    
    try:
        if base_url.startswith('http://'):
            host = base_url[7:].split('/')[0]
            path_parts = base_url[7:].split('/')[1:]
            path = '/' + '/'.join(path_parts) if path_parts else ''
            conn = http.client.HTTPConnection(host)
        elif base_url.startswith('https://'):
            host = base_url[8:].split('/')[0]
            path_parts = base_url[8:].split('/')[1:]
            path = '/' + '/'.join(path_parts) if path_parts else ''
            conn = http.client.HTTPSConnection(host)
        else:
            return f'Error: Invalid BASE_URL format: {base_url}', None
    except Exception as e:
        return f'Error parsing BASE_URL: {str(e)}', None
    
    data = {
        'model': model,
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 500,
        'temperature': 0.7
    }
    
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
    }
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        request_body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        conn.request('POST', f'{path}/chat/completions', request_body, headers)
        response = conn.getresponse()
        result = response.read().decode('utf-8')
        conn.close()
        
        # 记录结束时间
        end_time = time.time()
        
        # 计算响应时间
        response_time = end_time - start_time
        
        if response.status != 200:
            return f'Error: HTTP {response.status} - {result[:200]}', None
        
        response_data = json.loads(result)
        
        # 提取 Token 使用信息
        usage = response_data.get('usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)
        
        # 计算 Token 速度
        tokens_per_second = completion_tokens / response_time if response_time > 0 else 0
        
        # 构建统计信息
        stats = {
            'response_time': round(response_time, 2),
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens,
            'tokens_per_second': round(tokens_per_second, 2)
        }
        
        if 'choices' in response_data and len(response_data['choices']) > 0:
            choice = response_data['choices'][0]
            
            if 'message' in choice:
                if 'content' in choice['message']:
                    content = choice['message']['content']
                    # 如果 content 为空，检查 reasoning_content
                    if not content and 'reasoning_content' in choice['message']:
                        return choice['message']['reasoning_content'], stats
                    return content if content else 'Error: Content is empty', stats
                else:
                    return f'Error: No content in message', stats
            elif 'text' in choice:
                return choice['text'], stats
            else:
                return f'Error: Unexpected response structure', stats
        else:
            if 'error' in response_data:
                error_info = response_data['error']
                if isinstance(error_info, dict) and 'message' in error_info:
                    return f'Error: {error_info["message"]}', None
                else:
                    return f'Error: {str(error_info)}', None
            else:
                return f'Error: Unknown response format', None
    except ConnectionRefusedError:
        return f'Error: Could not connect to {base_url}. Is the LLM service running?', None
    except json.JSONDecodeError as e:
        return f'Error parsing JSON: {str(e)}', None
    except Exception as e:
        return f'Error: {str(e)}', None

if __name__ == '__main__':
    env_vars = load_env()
    if not env_vars:
        print('Error: No .env file found. Please copy env.example to .env and fill in the values.')
    else:
        print('=== LLM Client with Token Statistics ===')
        print(f"Model: {env_vars.get('MODEL', 'Unknown')}")
        print(f"API URL: {env_vars.get('BASE_URL', 'Unknown')}")
        print('=' * 50)
        
        prompt = 'Hello, can you tell me a short joke?'
        print(f'Prompt: {prompt}')
        print()
        
        response, stats = call_llm(prompt, env_vars)
        print(f'Response: {response}')
        print()
        
        # 显示 Token 统计信息
        if stats:
            print('--- Token Statistics ---')
            print(f"响应时间: {stats['response_time']} 秒")
            print(f"提示词 Token: {stats['prompt_tokens']}")
            print(f"回复 Token: {stats['completion_tokens']}")
            print(f"总 Token: {stats['total_tokens']}")
            print(f"生成速度: {stats['tokens_per_second']} tokens/秒")
            print('=' * 50)
