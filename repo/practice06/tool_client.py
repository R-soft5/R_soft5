import os
import json
import http.client
import re
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


def get_skills_directory():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), '.agents', 'skills')


def parse_yaml_front_matter(content):
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        front_matter_text = match.group(1)
        front_matter = {}
        for line in front_matter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                front_matter[key.strip()] = value.strip().strip('"')
        body = content[match.end():]
        return front_matter, body
    return {}, content


def list_available_skills():
    skills_dir = get_skills_directory()
    if not os.path.exists(skills_dir):
        return "[]"

    skills = []
    for item in os.listdir(skills_dir):
        item_path = os.path.join(skills_dir, item)
        if os.path.isdir(item_path):
            skill_md_path = os.path.join(item_path, 'SKILL.md')
            if os.path.exists(skill_md_path):
                try:
                    with open(skill_md_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    front_matter, _ = parse_yaml_front_matter(content)
                    name = front_matter.get('name', item)
                    description = front_matter.get('description', '')
                    skills.append({"name": name, "description": description})
                except Exception as e:
                    pass
    return json.dumps({"skills": skills}, ensure_ascii=False, indent=2)


def load_skill_content(skill_name):
    skills_dir = get_skills_directory()
    skill_path = os.path.join(skills_dir, skill_name, 'SKILL.md')
    if not os.path.exists(skill_path):
        return f"Error: Skill '{skill_name}' not found"

    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
        _, body = parse_yaml_front_matter(content)
        return body.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def is_notice_request(user_input):
    keywords = ['通知', '写通知', '撰写通知', '起草通知', '润色通知', '修改通知']
    return any(keyword in user_input for keyword in keywords)


def get_system_prompt(skill_content=None):
    skills_json = list_available_skills()
    skills_data = json.loads(skills_json) if skills_json != "[]" else {"skills": []}

    base_prompt = f"""你是一个AI助手，能够使用工具来帮助用户完成任务。

## 可用技能

{json.dumps(skills_data, ensure_ascii=False, indent=2)}

## 工具函数

1. list_available_skills(): 列出所有可用的技能
   - 参数：无
   - 返回：JSON格式的技能列表

2. load_skill_content(skill_name): 加载某个技能的完整内容
   - 参数：skill_name (字符串) - 技能名称
   - 返回：技能的完整说明和使用方法"""

    if skill_content:
        base_prompt += f"""

## 当前激活的技能内容

当用户请求撰写、修改、润色通知时，必须严格遵循以下技能规则：

{skill_content}

"""
    else:
        base_prompt += """

## 工具使用格式

当需要使用工具时，请输出JSON格式的工具调用请求：
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

当用户请求撰写通知时，必须先调用 load_skill_content("notice") 加载技能内容。
"""

    base_prompt += """
## 通知格式要求

当用户请求撰写通知时，你必须：
1. 首先调用 load_skill_content("notice") 获取通知撰写规则
2. 然后根据技能内容生成通知

**关键：通知标题必须以"XX部通知"开头**
- 如果用户指定了部门（如"销售部"），标题应为"销售部通知"
- 如果用户没有指定部门，标题应为"XX部通知"

请使用中文回复。"""

    return base_prompt


tools = {
    'list_available_skills': list_available_skills,
    'load_skill_content': load_skill_content
}


def call_llm(prompt, history, env_vars, skill_content=None):
    base_url = env_vars.get('BASE_URL', 'http://localhost:11434/v1')
    model = env_vars.get('MODEL', 'llama3')
    api_key = env_vars.get('API_KEY', 'your-api-key-here')

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

    messages = [
        {"role": "system", "content": get_system_prompt(skill_content)}
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

    data = {
        'model': model,
        'messages': messages,
        'max_tokens': 1500,
        'temperature': 0.3
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    try:
        request_body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        conn.request('POST', f'{path}/chat/completions', request_body, headers)
        response = conn.getresponse()
        result = response.read().decode('utf-8')
        conn.close()

        response_data = json.loads(result)
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            if 'error' in response_data:
                error_info = response_data['error']
                if isinstance(error_info, dict) and 'message' in error_info:
                    return f'Error: {error_info["message"]}'
                else:
                    return f'Error: {str(error_info)}'
            else:
                return f'Error: Unknown error. Response: {result}'
    except Exception as e:
        return f'Error: {str(e)}'


def process_tool_call(tool_call_json):
    try:
        tool_call = json.loads(tool_call_json)
        if 'tool_call' in tool_call:
            tool_name = tool_call['tool_call']['name']
            parameters = tool_call['tool_call']['parameters']

            if tool_name in tools:
                if tool_name == 'list_available_skills':
                    return tools[tool_name]()
                elif tool_name == 'load_skill_content':
                    return tools[tool_name](parameters['skill_name'])
            else:
                return f'Error: Tool {tool_name} not found'
        else:
            return 'Error: Invalid tool call format'
    except Exception as e:
        return f'Error: {str(e)}'


def process_llm_response(response, history, user_input, env_vars):
    if not response.strip().startswith('{') or 'tool_call' not in response:
        return response

    try:
        tool_call = json.loads(response)
        if 'tool_call' not in tool_call:
            return response

        tool_name = tool_call['tool_call']['name']
        tool_result = process_tool_call(response)
        print(f"\n[工具调用] {tool_name}")
        print(f"[工具返回] {tool_result[:200]}..." if len(str(tool_result)) > 200 else f"[工具返回] {tool_result}")

        history.append({
            "user": user_input,
            "assistant": response,
            "tool_call": tool_call['tool_call'],
            "tool_result": tool_result
        })

        if tool_name == 'load_skill_content':
            prompt = f"技能内容已加载。现在请根据上述技能内容，帮助用户完成以下请求：\n{user_input}"
            next_response = call_llm(prompt, history, env_vars, skill_content=tool_result)
            return process_llm_response(next_response, history, prompt, env_vars)
        elif tool_name == 'list_available_skills':
            prompt = f"技能列表已返回。现在请判断是否需要使用某个技能来帮助用户完成以下请求：\n{user_input}\n\n如果需要使用技能，请调用 load_skill_content 工具。"
            next_response = call_llm(prompt, history, env_vars)
            return process_llm_response(next_response, history, prompt, env_vars)
        else:
            return f"工具调用完成: {tool_name}\n结果: {tool_result}"

    except Exception as e:
        print(f"[错误] 处理工具调用时出错: {str(e)}")
        return response


def generate_notice(department, env_vars):
    if department.strip():
        user_input = f"我是{department}的，请帮我撰写一个关于2026年五一节放假的通知"
    else:
        user_input = "请帮我撰写一个关于2026年五一节放假的通知"

    history = []

    print(f"\n{'='*60}")
    print(f"用户请求: {user_input}")
    print(f"{'='*60}")

    skill_content = None
    if is_notice_request(user_input):
        print("\n[提示] 检测到通知请求，自动加载 notice 技能...")
        skill_content = load_skill_content("notice")
        print(f"[技能内容已加载]")
        response = call_llm(user_input, history, env_vars, skill_content=skill_content)
    else:
        response = call_llm(user_input, history, env_vars)

    final_result = process_llm_response(response, history, user_input, env_vars)

    return final_result


def run_tests(env_vars):
    print("\n" + "=" * 60)
    print("自动测试开始")
    print("=" * 60)

    print("\n【测试1】用户未指定部门，撰写五一节放假通知")
    print("-" * 60)
    result1 = generate_notice("", env_vars)
    print(f"\n生成结果:\n{result1}")
    if "XX部通知" in result1:
        print("✓ 测试1通过：通知以'XX部通知'开头")
    else:
        print("✗ 测试1失败：通知未以'XX部通知'开头")

    print("\n" + "-" * 60)
    print("【测试2】用户指定为销售部，撰写五一节放假通知")
    print("-" * 60)
    result2 = generate_notice("销售部", env_vars)
    print(f"\n生成结果:\n{result2}")
    if "销售部通知" in result2:
        print("✓ 测试2通过：通知以'销售部通知'开头")
    else:
        print("✗ 测试2失败：通知未以'销售部通知'开头")

    print("\n" + "=" * 60)
    print("自动测试完成")
    print("=" * 60)


def main():
    env_vars = load_env()
    if not env_vars:
        print('No .env file found. Please copy env.example to .env and fill in the values.')
        return

    print('=== LLM Skill-Enabled Client (Practice06) ===')
    print('通知撰写工具')
    print('=' * 50)

    print('\n可用技能列表:')
    skills_json = list_available_skills()
    print(skills_json)

    print('\n请选择模式:')
    print('1. 自动测试（测试1和测试2）')
    print('2. 交互模式（输入部门名称生成通知）')
    choice = input('\n请输入选项 (1/2): ').strip()

    if choice == '1':
        run_tests(env_vars)
    else:
        try:
            while True:
                department = input('\n请输入您的部门名称（如：销售部、采购部，直接按回车则使用"XX部"）：').strip()

                print('\n正在生成通知...')
                notice_content = generate_notice(department, env_vars)

                print('\n' + '=' * 60)
                print('生成的通知内容：')
                print('=' * 60)
                print(notice_content)
                print('=' * 60)

                continue_choice = input('\n是否继续生成通知？(y/n): ').strip().lower()
                if continue_choice != 'y':
                    print('感谢使用通知撰写工具！')
                    break

        except KeyboardInterrupt:
            print('\n\n感谢使用通知撰写工具！')


if __name__ == '__main__':
    main()
