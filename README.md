# Sentiment Analyzer

Sentiment Analyzer 是一个利用 LLM API（本地 Ollama 或 OpenAI ）对 Excel 文件中多列内容进行情感分析的工具。它能够识别"正面"、"中立"和"负面"情感，并将结果写入新的 Excel 文件。工具支持动态配置列名、日志记录、配置文件验证以及 API 调用失败时的重试机制。

## 功能
- **情感分析**：基于本地 Ollama API 或 OpenAI API，分析 Excel 中指定列的内容，返回"正面"、"中立"或"负面"。
- **动态列名**：通过配置文件指定任意数量的输入列（如主贴和评论）。
- **JSON 输出**：强制模型返回 JSON 格式结果，减少幻觉回答。
- **重试机制**：支持 API 调用失败时最多重试 3 次（可配置）。
- **日志记录**：生成带日期的日志文件（如 `analyzer_2025-03-23.log`），支持控制台输出。
- **配置验证**：自动检查配置文件完整性，确保必需参数存在。
- **打包支持**：可使用 PyInstaller 打包为独立二进制文件。

## 项目结构
```
sentiment_analyzer/
├── analyzer.py          # 主程序
├── config/
│   └── config.toml      # 配置文件
├── logs/                # 日志目录（运行时生成）
│   └── analyzer_YYYY-MM-DD.log
├── README.md            # 本文档
├── requirements.txt     # 依赖文件
```

## 安装

### 前提条件
- Python 3.8 或更高版本
- 本地运行的 Ollama 服务（或 OpenAI API Key）
- Ollama 服务运行在 `http://localhost:11434/v1`（如使用本地模型）

### 步骤
1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd sentiment_analyzer
   ```

2. **创建虚拟环境（可选）**
   ```bash
   # Linux/Mac
   python -m venv venv
   source venv/bin/activate  

   # Windows
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   venv\Scripts\activate     
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **安装并运行 Ollama（本地模型）- 可选**
   - 下载并安装 Ollama（参考 [Ollama 官网](https://ollama.ai/)）。
   - 拉取模型（例如 `qwen2.5:7b-instruct-q4_K_M`）：
     ```bash
     ollama pull qwen2.5:7b-instruct-q4_K_M
     ```
   - 启动 Ollama 服务：
     ```bash
     ollama serve
     ```

## 配置

编辑 `config/config.toml` 文件，配置 Ollama API 或 OpenAI API 参数、Excel 列名和提示词：

   ```toml
   [openai]
   base_url = "http://localhost:11434/v1"  # Ollama API 的基础 URL（或 OpenAI 的 "https://api.openai.com/v1"）
   api_key = "ollama"                     # 对于 Ollama，通常为 "ollama"；对于 OpenAI，填写您的 API Key
   model = "qwen2.5:7b-instruct-q4_K_M"   # 使用的模型名称
   max_tokens = 2048                      # 模型生成响应的最大 token 数
   temperature = 0                        # 控制生成文本的随机性，0 到 1 之间
   timeout = 60                           # API 请求超时时间（秒）
   max_retries = 3                        # API 调用失败时的最大重试次数
   retry_interval = 1                     # 重试间隔（秒）

   [logging]
   level = "INFO"                         # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
   path = "../logs/analyzer.log"          # 日志基础路径，实际文件会追加日期
   console_output = "True"                # 是否在控制台输出日志，"True" 或 "False"

   [excel]
   content_columns = ["标题/微博内容", "评论内容"]  # 待分析的列名列表，可自定义

   [prompt]
   system_prompt = "你是一个情感分析助手，仅返回 JSON 格式：{\"sentiment\": \"正面|中立|负面\"}"  # 系统提示词
   static_prompt = """
   你是一个情感分析专家，请分析以下内容的情感倾向，并以 JSON 格式返回结果，格式如下：
   
   json

   {"sentiment": "正面"}
   
   其中 "sentiment" 的值只能是"正面"、"中立"或"负面"之一，不允许其他值或额外字段。

   **分析规则**：
   1. 主贴明确讨论时，允许识别评论隐含关联（如主贴关于"A"，评论说"B"则视为负面）
   2. 主贴无关"A"时，仅分析评论中明确提到的内容
   3. 负面评价必须明确指向"A"产品/服务且含负面词
   4. 提及竞品但未比较"A"时标中立

   **内容**：
   """  # 静态提示词，后接动态内容
   ```

**注意**：
- `[openai]`：必填 `api_key`、`model`、`max_tokens` 和 `temperature`，其他参数可选。
- `[excel]`：`content_columns` 为列表，可指定任意数量的列名。
- `[prompt]`：`system_prompt` 和 `static_prompt` 必填，用于控制模型行为。

## 使用方法

### 运行 Python 脚本
```bash
python analyzer.py input.xlsx output.xlsx
```
- `input.xlsx`：输入 Excel 文件，需包含 `[excel].content_columns` 中指定的列。
- `output.xlsx`：输出 Excel 文件，新增"情感倾向"列。

### 可选参数
- `--config`：指定配置文件路径，默认 `config/config.toml`

  ```bash
  python analyzer.py input.xlsx output.xlsx --config custom_config.toml
  ```

### 运行例子
```bash
cd sentiment_analyzer
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
venv\Scripts\activate  
py.exe .\analyzer.py .\example_data\test.xlsx .\example_data\test1.xlsx
```

### 日志
- 日志文件生成在 `logs/` 目录下，例如 `logs/analyzer_2025-03-23.log`。
- 如果 `console_output = "True"`，日志同时输出到控制台。

## 打包为二进制文件

使用 PyInstaller 将脚本打包为独立的可执行文件：

1. **安装 PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **打包命令**
   - 配置文件打到 exe 文件中
      ```bash
      pyinstaller -F --add-data "config/config.toml;config" analyzer.py
      ```
     - `-F`：生成单一可执行文件。
     - `--add-data`：包含配置文件（Windows 用 `;` 分隔，Linux/Mac 用 `:`）。
   - 配置文件不到 exe 文件中

      ```bash
      pyinstaller -F analyzer.py
      ```   
   

3. **运行二进制文件**
   - 输出文件位于 `dist/analyzer`（或 `dist/analyzer.exe`）
   
   - 打配置文件运行
   
      ```bash
      ./dist/analyzer input.xlsx output.xlsx
      ```
   - 没打配置文件运行
   
      ```bash
      ./dist/analyzer input.xlsx output.xlsx --config `$config.toml绝对路径`/config.toml
      ``` 

**注意**：打包后的二进制文件仍需本地 Ollama 服务运行，除非使用 OpenAI API 或其他公有云 LLM 。

## 情感分析规则
- **正面**：积极评价。
- **负面**：明确指向"A"的负面评价。
- **中立**：无明确情感，或提及竞品但未比较。
- **LLM处理错误**：API 调用失败或返回无效结果时的默认值。

## 依赖
列于 `requirements.txt`：
```
pandas>=1.5.0
openpyxl>=3.0.0
openai>=1.0.0
toml>=0.10.2
pyinstaller
```

## 注意事项
- **Ollama 配置**：确保 Ollama 服务在 `http://localhost:11434/v1` 运行，并已加载指定模型。
- **模型支持**：Ollama 模型需支持 JSON 输出（`response_format={"type": "json_object"}`），否则可能返回非 JSON 格式，导致默认值为"LLM处理错误"。
- **Excel 列名**：输入文件列名必须与 `config.toml` 中的 `[excel].content_columns` 一致。
- **配置完整性**：运行前确保配置文件包含所有必需项，否则会抛出错误。
- **权限**：确保运行目录有写入权限以生成日志和输出文件。

## 示例日志
```
2025-03-23 10:00:00,130 - INFO - 日志系统初始化完成，日志文件：logs/analyzer_2025-03-23.log
2025-03-23 10:00:00,131 - DEBUG - API 原始输出（尝试 1/3）：{"sentiment": "正面"}
2025-03-23 10:00:00,132 - DEBUG - 情感分析结果：正面
```

## 贡献
欢迎提交 Issue 或 Pull Request！

## 许可证
MIT License