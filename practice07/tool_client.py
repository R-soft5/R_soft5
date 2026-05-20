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


def search_files(directory, keyword):
    if not os.path.exists(directory):
        return f"Error: Directory '{directory}' not found"

    if not os.path.isdir(directory):
        return f"Error: '{directory}' is not a directory"

    results = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if keyword in content:
                        results.append(filepath)
                except Exception as e:
                    pass
    return json.dumps({"files": results, "count": len(results)}, ensure_ascii=False)


def read_file(filepath):
    if not os.path.exists(filepath):
        return f"Error: File '{filepath}' not found"

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def write_file(filepath, content):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: Content written to {filepath}"
    except Exception as e:
        return f"Error: {str(e)}"


def fetch_webpage(url):
    try:
        if url.startswith('http://'):
            host = url[7:].split('/')[0]
            path = '/' + '/'.join(url[7:].split('/')[1:]) if len(url[7:].split('/')) > 1 else '/'
            conn = http.client.HTTPConnection(host)
        elif url.startswith('https://'):
            host = url[8:].split('/')[0]
            path = '/' + '/'.join(url[8:].split('/')[1:]) if len(url[8:].split('/')) > 1 else '/'
            conn = http.client.HTTPSConnection(host)
        else:
            return f"Error: Invalid URL format"

        headers = {'User-Agent': 'Mozilla/5.0'}
        conn.request('GET', path, headers=headers)
        response = conn.getresponse()
        result = response.read().decode('utf-8', errors='ignore')
        conn.close()
        return result
    except Exception as e:
        return f"Error: {str(e)}"


tools = {
    'list_available_skills': list_available_skills,
    'load_skill_content': load_skill_content,
    'search_files': search_files,
    'read_file': read_file,
    'write_file': write_file,
    'fetch_webpage': fetch_webpage
}


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
   - 返回：技能的完整说明和使用方法

3. search_files(directory, keyword): 在指定目录下搜索包含关键词的文件
   - 参数：directory (字符串) - 要搜索的目录路径
   - 参数：keyword (字符串) - 要搜索的关键词
   - 返回：JSON格式，包含文件路径列表

4. read_file(filepath): 读取文件内容
   - 参数：filepath (字符串) - 文件路径
   - 返回：文件内容

5. write_file(filepath, content): 写入内容到文件
   - 参数：filepath (字符串) - 文件路径
   - 参数：content (字符串) - 要写入的内容
   - 返回：成功或错误信息

6. fetch_webpage(url): 获取网页内容
   - 参数：url (字符串) - 网页URL
   - 返回：网页HTML内容"""

    if skill_content:
        base_prompt += f"""

## 当前激活的技能内容

当用户请求撰写、修改、润色通知时，必须严格遵循以下技能规则：

{skill_content}

"""

    base_prompt += """

## 链式工具调用规则

当你需要完成复杂任务时，可以使用链式工具调用。链式调用允许你：
1. 执行一个工具并获取结果
2. 根据结果决定下一步操作
3. 将中间结果作为后续工具的输入

### 决策格式

完成时要返回：
```json
{"done": true, "answer": "最终回答内容"}
```

继续调用工具时要返回：
```json
{"done": false, "tool_call": {"name": "工具名称", "arguments": {"参数名": "参数值"}}}
```

### 链式调用示例

用户请求："查找 practice06 目录下所有包含 'def' 关键词的文件"

正确流程：
1. 先调用 search_files 搜索文件
2. 根据返回的文件列表，决定是否需要读取文件内容
3. 根据中间结果生成最终回答

### 上下文变量

在链式调用过程中，中间结果会存储在上下文中供后续步骤使用。
你可以在 arguments 中引用之前的变量名来使用这些结果。

请使用中文回复。"""

    return base_prompt


def call_llm(prompt, history=None, env_vars=None, system_prompt=None):
    if env_vars is None:
        env_vars = load_env()

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

    if system_prompt is None:
        system_prompt = get_system_prompt()

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        for msg in history:
            messages.append(msg)

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


class ChainedCallContext:
    def __init__(self, max_iterations=10):
        self.max_iterations = max_iterations
        self.steps = []
        self.variables = {}
        self.current_iteration = 0

    def add_step(self, tool_name, arguments, result):
        self.steps.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "iteration": self.current_iteration
        })
        var_key = f"step_{len(self.steps)}_result"
        self.variables[var_key] = result
        if tool_name == "search_files":
            try:
                result_data = json.loads(result)
                self.variables["last_search_files"] = result_data.get("files", [])
            except:
                pass
        elif tool_name == "read_file":
            self.variables["last_file_content"] = result
        elif tool_name == "fetch_webpage":
            self.variables["last_webpage"] = result

    def get_history_text(self):
        if not self.steps:
            return "（暂无已执行的工具调用）"

        history = []
        for i, step in enumerate(self.steps, 1):
            history.append(f"步骤 {i}:")
            history.append(f"  工具: {step['tool_name']}")
            history.append(f"  参数: {json.dumps(step['arguments'], ensure_ascii=False)}")
            result_preview = str(step['result'])[:200]
            if len(str(step['result'])) > 200:
                result_preview += "..."
            history.append(f"  结果: {result_preview}")
            history.append("")

        return "\n".join(history)

    def get_variables_text(self):
        if not self.variables:
            return "（暂无上下文变量）"

        vars_text = []
        for key, value in self.variables.items():
            if key == "last_webpage":
                preview = str(value)[:300]
                if len(str(value)) > 300:
                    preview += "..."
                vars_text.append(f"  {key}: {preview}")
            else:
                vars_text.append(f"  {key}: {str(value)[:200]}")
        return "\n".join(vars_text)

    def increment_iteration(self):
        self.current_iteration += 1
        return self.current_iteration

    def is_max_iterations_reached(self):
        return self.current_iteration >= self.max_iterations

    def is_complete(self):
        if not self.steps:
            return False
        return self.steps[-1].get("result", "").startswith("Error:") is False


def build_analysis_prompt(user_request, context):
    prompt = f"""## 用户请求
{user_request}

## 已执行的工具调用历史
{context.get_history_text()}

## 当前上下文变量
{context.get_variables_text()}

## 决策规则

请根据上述信息，决定下一步操作：

1. **如果任务已完成**，返回：
```json
{{"done": true, "answer": "最终回答内容"}}
```

2. **如果需要继续调用工具**，返回：
```json
{{"done": false, "tool_call": {{"name": "工具名称", "arguments": {{"参数名": "参数值"}}}}}}
```

### 决策指南

- 如果用户请求涉及多个步骤，先执行前置步骤（如搜索文件）
- 如果前置步骤返回了结果，检查结果是否满足用户需求
- 如果结果不完整或需要更多信息，继续调用下一个工具
- 可以在 arguments 中使用上下文变量名来引用之前的值
- 如果所有步骤都成功执行，生成最终回答并设置 done: true

## 输出格式要求

请严格按照上述 JSON 格式返回决策结果，不要包含其他内容。
"""
    return prompt


def parse_llm_decision(response):
    if response is None:
        return {"done": True, "answer": "Error: LLM returned None"}

    response = response.strip()

    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            if '"done": true' in response.lower() or '"done":true' in response.lower():
                answer_match = re.search(r'"answer"\s*:\s*"([^"]*)"', response)
                if answer_match:
                    return {"done": True, "answer": answer_match.group(1)}
                return {"done": True, "answer": response}
            return {"done": True, "answer": f"无法解析LLM响应: {response[:200]}"}

    try:
        decision = json.loads(json_str)
        if 'done' not in decision:
            return {"done": True, "answer": f"JSON格式错误，缺少done字段: {json_str}"}
        if decision['done'] and 'answer' not in decision:
            return {"done": True, "answer": "任务完成但未提供answer"}
        if not decision['done'] and 'tool_call' not in decision:
            return {"done": True, "answer": f"JSON格式错误，缺少tool_call字段: {json_str}"}
        return decision
    except json.JSONDecodeError as e:
        return {"done": True, "answer": f"JSON解析失败: {str(e)}, 原始响应: {response[:200]}"}


def execute_chained_tool_call(user_request, env_vars=None, max_iterations=10):
    if env_vars is None:
        env_vars = load_env()

    context = ChainedCallContext(max_iterations=max_iterations)
    system_prompt = get_system_prompt()

    messages = []
    messages.append({"role": "system", "content": system_prompt})

    user_message = {"role": "user", "content": user_request}
    messages.append(user_message)

    print(f"\n{'='*60}")
    print(f"链式工具调用开始")
    print(f"用户请求: {user_request}")
    print(f"最大迭代次数: {max_iterations}")
    print(f"{'='*60}\n")

    while not context.is_max_iterations_reached():
        context.increment_iteration()
        iteration = context.current_iteration

        print(f"[迭代 {iteration}] 构建分析提示词...")

        analysis_prompt = build_analysis_prompt(user_request, context)
        messages.append({"role": "user", "content": analysis_prompt})

        print(f"[迭代 {iteration}] 调用LLM进行决策...")

        response = call_llm(analysis_prompt, env_vars=env_vars)
        print(f"[迭代 {iteration}] LLM响应: {response[:300]}..." if len(response) > 300 else f"[迭代 {iteration}] LLM响应: {response}")

        if response.startswith("Error:"):
            return f"LLM调用失败: {response}"

        messages.append({"role": "assistant", "content": response})

        decision = parse_llm_decision(response)

        if decision.get("done"):
            print(f"\n[迭代 {iteration}] 任务完成")
            return decision.get("answer", "任务完成但无返回内容")

        tool_call = decision.get("tool_call", {})
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})

        if tool_name not in tools:
            print(f"[迭代 {iteration}] 错误: 工具 {tool_name} 不存在")
            return f"错误: 工具 {tool_name} 不存在"

        print(f"[迭代 {iteration}] 执行工具: {tool_name}")
        print(f"[迭代 {iteration}] 参数: {json.dumps(arguments, ensure_ascii=False)}")

        try:
            if tool_name == 'list_available_skills':
                result = tools[tool_name]()
            elif tool_name == 'load_skill_content':
                result = tools[tool_name](arguments['skill_name'])
            elif tool_name == 'search_files':
                result = tools[tool_name](arguments['directory'], arguments['keyword'])
            elif tool_name == 'read_file':
                result = tools[tool_name](arguments['filepath'])
            elif tool_name == 'write_file':
                result = tools[tool_name](arguments['filepath'], arguments['content'])
            elif tool_name == 'fetch_webpage':
                result = tools[tool_name](arguments['url'])
            else:
                result = f"Error: Tool {tool_name} not implemented"
        except Exception as e:
            result = f"Error: Tool execution failed: {str(e)}"

        print(f"[迭代 {iteration}] 工具返回: {str(result)[:200]}..." if len(str(result)) > 200 else f"[迭代 {iteration}] 工具返回: {result}")

        context.add_step(tool_name, arguments, result)

        messages.append({
            "role": "tool",
            "content": str(result)
        })

    print(f"\n达到最大迭代次数 {max_iterations}，停止执行")
    return f"达到最大迭代次数限制。当前上下文:\n{context.get_history_text()}"


def run_tests():
    env_vars = load_env()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    practice06_dir = os.path.join(os.path.dirname(base_dir), 'practice06')

    print("\n" + "="*60)
    print("测试1: 文件搜索链式调用")
    print("="*60)
    test1_request = f"请查找 {practice06_dir} 目录下所有包含'def'关键词的文件，并总结这些文件的主要内容"
    result1 = execute_chained_tool_call(test1_request, env_vars, max_iterations=10)
    print(f"\n测试1结果:\n{result1}")

    print("\n" + "="*60)
    print("测试2: 多文件操作")
    print("="*60)

    test_dir = os.path.join(base_dir, 'test_data')
    os.makedirs(test_dir, exist_ok=True)

    file1_path = os.path.join(test_dir, '1.txt')
    file2_path = os.path.join(test_dir, '2.txt')
    result_path = os.path.join(test_dir, 'result.txt')

    with open(file1_path, 'w', encoding='utf-8') as f:
        f.write("25")
    with open(file2_path, 'w', encoding='utf-8') as f:
        f.write("17")

    print(f"已创建测试文件: {file1_path} = 25, {file2_path} = 17")

    test2_request = f"读取 {file1_path} 和 {file2_path} 两个文件，文件内容的都是正整数，把两个数相加的和写入 {result_path} 文件。"
    result2 = execute_chained_tool_call(test2_request, env_vars, max_iterations=10)
    print(f"\n测试2结果:\n{result2}")

    if os.path.exists(result_path):
        with open(result_path, 'r', encoding='utf-8') as f:
            sum_result = f.read()
        print(f"result.txt 内容: {sum_result}")

    print("\n" + "="*60)
    print("测试3: 网页处理链式调用")
    print("="*60)
    summary_path = os.path.join(base_dir, 'summary.txt')
    test3_request = f"访问 https://www.nsu.edu.cn/HTML/news/2024/06/article_3974.html 并总结页面内容，保存到 {summary_path}"
    result3 = execute_chained_tool_call(test3_request, env_vars, max_iterations=10)
    print(f"\n测试3结果:\n{result3}")

    if os.path.exists(summary_path):
        print(f"摘要已保存到: {summary_path}")


if __name__ == "__main__":
    run_tests()