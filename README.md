# Python AI智能体开发教学项目

## 项目结构

```
├── .gitignore          # Git忽略文件配置
├── env.example         # 环境变量配置模板
├── venv/               # 虚拟环境目录
├── .agents/
│   └── skills/         # 技能目录
│       └── notice/    # 通知撰写技能
│           └── SKILL.md
├── practice01/         # 第一个练习目录
│   ├── llm_client.py   # 基础LLM客户端实现
│   └── chat_client.py  # 交互式聊天客户端实现
├── practice02/         # 第二个练习目录
│   └── tool_client.py  # 工具调用客户端实现
├── practice03/         # 第三个练习目录
│   └── tool_client.py  # 工具调用客户端实现（含网络访问功能）
├── practice04/         # 第四个练习目录
│   └── tool_client.py  # 工具调用客户端实现（含聊天历史管理功能）
├── practice05/         # 第五个练习目录
│   ├── tool_client.py  # 工具调用客户端实现（含AnythingLLM集成）
│   └── chat_client.py  # 交互式聊天客户端实现
└── practice06/         # 第六个练习目录
    └── tool_client.py  # 技能系统客户端实现
```

## 代码功能说明

### env.example
- **功能**：提供OpenAI兼容协议LLM的配置模板
- **内容**：包含BASE_URL、MODEL、API_KEY等必要配置参数
- **使用方法**：复制为.env文件并填写正确的参数值

### practice01/llm_client.py
- **功能**：
  1. 读取项目根目录的.env文件内容
  2. 使用Python标准http库访问用户定义的LLM
  3. 支持HTTP和HTTPS协议
  4. 实现完整的错误处理和响应解析
- **技术点**：
  - 环境变量读取与解析
  - HTTP/HTTPS请求构建
  - JSON数据处理
  - 异常处理
  - 命令行交互

### practice01/chat_client.py
- **功能**：
  1. 支持终端界面输入聊天内容
  2. 支持LLM流式输出（逐字显示）
  3. 支持历史聊天记录自动添加到上下文
  4. 直到用户按Ctrl+C退出终端，否则一直循环
  5. 自动限制历史记录长度，避免上下文过长
- **技术点**：
  - 流式API调用
  - 终端实时输出
  - 聊天历史管理
  - 异常处理（Ctrl+C退出）
  - 上下文窗口管理

### practice02/tool_client.py
- **功能**：
  1. 实现5个文件操作工具：列出文件、重命名文件、删除文件、创建文件、读取文件
  2. 将工具调用能力作为系统提示词发送给LLM
  3. 支持LLM生成工具调用请求并执行
  4. 支持终端界面交互，直到用户按Ctrl+C退出
- **技术点**：
  - 工具函数设计与实现
  - 系统提示词设计
  - LLM工具调用模式
  - JSON数据处理与解析
  - 终端交互与异常处理

### practice03/tool_client.py
- **功能**：
  1. 继承practice02的所有文件操作工具
  2. 新增网络访问功能：访问网页并返回网页内容
  3. 将网络访问能力作为工具添加到系统提示词
  4. 支持LLM生成网络访问工具调用请求并执行
  5. 支持终端界面交互，直到用户按Ctrl+C退出
- **技术点**：
  - 网络请求实现
  - 网页内容获取与处理
  - 工具扩展与集成
  - 系统提示词更新
  - 内容长度限制处理

### practice06/tool_client.py
- **功能**：
  1. 实现技能系统，支持动态加载和执行技能
  2. `list_available_skills()` 函数：读取 `.agents/skills` 目录下所有技能的 SKILL.md 文件，解析 YAML front matter 中的 name 和 description 字段
  3. `load_skill_content(skill_name)` 函数：加载指定技能的完整内容（YAML front matter 之后的部分）
  4. `is_notice_request(user_input)` 函数：智能检测用户是否请求撰写通知
  5. 将技能列表以 JSON 格式通过 system prompt 发送给 LLM
  6. 当检测到通知请求时，自动加载 notice 技能内容并发送给 LLM
  7. 支持两种运行模式：自动测试模式和交互模式
- **技术点**：
  - YAML front matter 解析（使用正则表达式）
  - 动态目录扫描和技能发现
  - 技能系统与 LLM 的集成
  - System prompt 动态构建
  - 智能技能检测与自动加载
  - 多模式运行（自动测试/交互）

## 教学目标

1. **环境配置**：
   - 学习如何设置Python虚拟环境
   - 理解环境变量配置的重要性
   - 掌握Git版本控制的基础配置

2. **网络编程**：
   - 学习使用Python标准库进行HTTP请求
   - 理解REST API的基本调用方式
   - 掌握JSON数据的序列化和反序列化
   - 学习流式API的使用方法

3. **LLM集成**：
   - 了解OpenAI兼容协议的基本结构
   - 学习如何与不同的LLM服务进行交互
   - 掌握API密钥管理的最佳实践
   - 理解对话上下文的管理方法

4. **项目结构**：
   - 学习如何组织Python项目目录
   - 理解模块化编程的基本概念
   - 掌握配置文件的管理方法

5. **用户交互**：
   - 学习如何构建交互式命令行应用
   - 掌握流式输出的实现方法
   - 理解用户输入的处理和异常捕获

6. **工具调用**：
   - 学习如何设计和实现工具函数
   - 理解LLM工具调用的工作原理
   - 掌握系统提示词的设计方法
   - 学习如何处理工具调用请求和响应

7. **网络访问**：
   - 学习使用Python标准库进行网络请求
   - 理解HTTP/HTTPS协议的基本原理
   - 掌握网页内容获取与处理方法
   - 学习如何将网络访问能力集成到工具调用系统中

8. **技能系统**：
   - 学习如何设计和实现技能（Skill）结构
   - 理解 YAML front matter 的解析方法
   - 掌握技能列表的动态发现机制
   - 学习如何通过 system prompt 向 LLM 传递技能信息
   - 理解技能调用流程和上下文管理

## 运行方法

1. 复制环境变量模板并填写配置：
   ```bash
   copy env.example .env
   # 编辑.env文件，填写正确的LLM配置
   ```

2. 激活虚拟环境：
   ```bash
   venv\Scripts\activate  # Windows
   # 或
   source venv/bin/activate  # Linux/Mac
   ```

3. 运行基础LLM客户端（practice01）：
   ```bash
   python practice01/llm_client.py
   ```

4. 运行交互式聊天客户端（practice01）：
   ```bash
   python practice01/chat_client.py
   ```
   - 在终端中输入消息并按Enter发送
   - 观察LLM的流式输出
   - 按Ctrl+C退出客户端

5. 运行工具调用客户端（practice02）：
   ```bash
   python practice02/tool_client.py
   ```
   - 在终端中输入文件操作请求，例如："List files in the practice01 directory"
   - 观察LLM生成工具调用请求并执行
   - 按Ctrl+C退出客户端

6. 运行带网络访问功能的工具调用客户端（practice03）：
   ```bash
   python practice03/tool_client.py
   ```
   - 在终端中输入文件操作或网络访问请求，例如："Fetch content from https://example.com"
   - 观察LLM生成工具调用请求并执行
   - 按Ctrl+C退出客户端

7. 运行技能系统客户端（practice06）：
   ```bash
   python practice06/tool_client.py
   ```
   - 程序提供两种运行模式：
     - 选项1（自动测试）：自动测试两个场景
       - 测试1：撰写五一节放假通知（未指定部门）→ 应输出"XX部通知"
       - 测试2：撰写五一节放假通知（销售部）→ 应输出"销售部通知"
     - 选项2（交互模式）：用户输入部门名称生成通知
   - 观察 LLM 如何自动调用 notice 技能并生成正确格式的通知

## 扩展建议

- 尝试集成不同的LLM服务（如OpenAI、Anthropic、本地部署的模型等）
- 实现更复杂的对话管理功能
- 添加错误重试机制和超时处理
- 构建简单的命令行界面或Web界面
- 添加更多技能（如代码审查、数据分析等）
- 实现技能的参数化调用

## 注意事项

- 请不要将包含真实API密钥的.env文件提交到版本控制系统
- 确保LLM服务已正确配置并运行
- 根据不同LLM服务的要求调整API参数
- 技能目录结构：`.agents/skills/<skill-name>/SKILL.md`
- SKILL.md 文件必须包含有效的 YAML front matter
