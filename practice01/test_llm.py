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
    
    if not base_url:
        return 'Error: BASE_URL not found'
    if not model:
        return 'Error: MODEL not found'
    
    if base_url.startswith('http://'):
        host = base_url[7:].split('/')[0]
        path = '/' + '/'.join(base_url[7:].split('/')[1:]) if len(base_url[7:].split('/')) > 1 else ''
        conn = http.client.HTTPConnection(host)
    elif base_url.startswith('https://'):
        host = base_url[8:].split('/')[0]
        path = '/' + '/'.join(base_url[8:].split('/')[1:]) if len(base_url[8:].split('/')) > 1 else ''
        conn = http.client.HTTPSConnection(host)
    else:
        return 'Error: Invalid BASE_URL'
    
    data = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 150,
        'temperature': 0.7
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + api_key if api_key else ''
    }
    
    try:
        request_body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        print('[DEBUG] Request URL:', host + path + '/chat/completions')
        print('[DEBUG] Request body:', request_body.decode('utf-8'))
        
        conn.request('POST', path + '/chat/completions', request_body, headers)
        response = conn.getresponse()
        result = response.read().decode('utf-8')
        conn.close()
        
        print('[DEBUG] Status:', response.status, response.reason)
        print('[DEBUG] Response:', result[:500])
        
        if not result:
            return 'Error: Empty response'
        
        response_data = json.loads(result)
        
        if 'choices' in response_data and len(response_data['choices']) > 0:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']
            elif 'text' in choice:
                return choice['text']
            else:
                return 'Error: Unexpected structure'
        else:
            if 'error' in response_data:
                return 'Error: ' + str(response_data['error'])
            else:
                return 'Error: Unknown format'
    except Exception as e:
        return 'Error: ' + str(e)

if __name__ == '__main__':
    env_vars = load_env()
    if not env_vars:
        print('No .env file found')
    else:
        print('Loaded env:', env_vars)
        prompt = 'Hello, can you tell me a short joke?'
        response = call_llm(prompt, env_vars)
        print('Prompt:', prompt)
        print('Response:', response)
