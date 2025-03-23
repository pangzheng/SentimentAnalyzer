# Sentiment Analyzer
Sentiment Analyzer is a tool that uses LLM API (local Ollama or OpenAI) to perform sentiment analysis on multiple columns of content in an Excel file. It can identify "positive," "neutral," and "negative" sentiments, and write the results into a new Excel file. The tool supports dynamic configuration of column names, logging, configuration file validation, and retry mechanisms for API calls.
## Features
- **Sentiment Analysis**: Analyzes the content in specified columns of an Excel sheet based on local Ollama API or OpenAI API, returning "positive," "neutral," or "negative."
- **Dynamic Column Names**: Specifies any number of input columns (such as main post and comments) through a configuration file.
- **JSON Output**: Forces the model to return results in JSON format to reduce hallucinations.
- **Retry Mechanism**: Supports retrying API calls up to 3 times (configurable).
- **Logging**: Generates date-stamped log files (e.g., `analyzer_2025-03-23.log`), with console output support.
- **Configuration Validation**: Automatically checks the integrity of the configuration file, ensuring all necessary parameters are present.
- **Packaging Support**: Can be packaged into a standalone binary using PyInstaller.
## Project Structure
```
sentiment_analyzer/
├── analyzer.py          # Main program
├── config/
│   └── config.toml      # Configuration file
├── logs/                # Log directory (generated at runtime)
│   └── analyzer_YYYY-MM-DD.log
├── README.md            # This document
├── requirements.txt     # Dependency file
```
## Installation
### Prerequisites
- Python 3.8 or higher
- Running Ollama service locally (or OpenAI API Key)
- Ollama service running at `http://localhost:11434/v1` (if using a local model)
### Steps
1. **Clone the Project**
   ```bash
   git clone <repository-url>
   cd sentiment_analyzer
   ```
2. **Create a Virtual Environment (Optional)**
   ```bash
   # Linux/Mac
   python -m venv venv
   source venv/bin/activate  
   # Windows
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   venv\Scripts\activate     
   ```
3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Install and Run Ollama (Local Model) - Optional**
   - Download and install Ollama (refer to [Ollama website](https://ollama.ai/)).
   - Pull the model (e.g., `qwen2.5:7b-instruct-q4_K_M`):
     ```bash
     ollama pull qwen2.5:7b-instruct-q4_K_M
     ```
   - Start the Ollama service:
     ```bash
     ollama serve
     ```
## Configuration
Edit `config/config.toml` to configure Ollama API or OpenAI API parameters, Excel column names, and prompts:
   ```toml
   [openai]
   base_url = "http://localhost:11434/v1"  # Base URL of the Ollama API (or "https://api.openai.com/v1" for OpenAI)
   api_key = "ollama"                     # For Ollama, usually "ollama"; for OpenAI, provide your API Key
   model = "qwen2.5:7b-instruct-q4_K_M"   # Model name to use
   max_tokens = 2048                      # Maximum number of tokens the model can generate in a response
   temperature = 0                        # Controls the randomness of generated text, between 0 and 1
   timeout = 60                           # Timeout for API requests (seconds)
   max_retries = 3                        # Maximum number of retries on failed API calls
   retry_interval = 1                     # Retry interval in seconds
   [logging]
   level = "INFO"                         # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
   path = "../logs/analyzer.log"          # Base path for log files, with date appended
   console_output = "True"                # Whether to output logs to the console, "True" or "False"
   [excel]
   content_columns = ["标题/微博内容", "评论内容"]  # Column names to be analyzed, can be customized
   [prompt]
   system_prompt = "你是一个情感分析助手，仅返回 JSON 格式：{\"sentiment\": \"正面|中立|负面\"}"  # System prompt
   static_prompt = """
   你是一个情感分析专家，请分析以下内容的情感倾向，并以 JSON 格式返回结果，格式如下：
   
   json
   {"sentiment": "正面"}
   
   其中 "sentiment" 的值只能是"正面"、"中立"或"负面"之一，不允许其他值或额外字段。
   **分析规则**：
   1. 当主贴明确讨论时，允许识别评论隐含关联（如主贴关于"A"，评论说"B"则视为负面）
   2. 主贴无关"A"时，仅分析评论中明确提到的内容
   3. 负面评价必须明确指向"A"产品/服务且含负面词
   4. 提及竞品但未比较"A"时标中立
   **内容**：
   """  # Static prompt, followed by dynamic content
   ```
**Note**:
- `[openai]`: Required fields are `api_key`, `model`, `max_tokens`, and `temperature`. Other parameters are optional.
- `[excel]`: `content_columns` is a list, can specify any number of column names.
- `[prompt]`: Both `system_prompt` and `static_prompt` are required to control model behavior.
## Usage
### Run Python Script
```bash
python analyzer.py input.xlsx output.xlsx
```
- `input.xlsx`: Input Excel file, must contain columns specified in `[excel].content_columns`.
- `output.xlsx`: Output Excel file with an additional "情感倾向" column.
### Optional Parameters
- `--config`: Specify a custom configuration file path (default is `config/config.toml`)
  ```bash
  python analyzer.py input.xlsx output.xlsx --config custom_config.toml
  ```
### Example Run Command
```bash
cd sentiment_analyzer
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
venv\Scripts\activate  
py.exe .\analyzer.py .\example_data\test.xlsx .\example_data\test1.xlsx
```
### Logging
- Log files are generated in the `logs/` directory, e.g., `logs/analyzer_2025-03-23.log`.
- If `console_output = "True"`, logs are also output to the console.
## Packaging as a Binary File
Use PyInstaller to package the script into an independent executable file:
1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```
2. **Packaging Command**
   - Include configuration files in the exe file:
      ```bash
      pyinstaller -F --add-data "config/config.toml;config" analyzer.py
      ```
     - `-F`: Generate a single executable file.
     - `--add-data`: Includes configuration files (Windows uses `;`, Linux/Mac use `:`).
   - Do not include configuration files in the exe:
      ```bash
      pyinstaller -F analyzer.py
      ```

3. **Run the Binary File**
   - Output file is located at `dist/analyzer` or `dist/analyzer.exe`
   
   - Run with config included
   
      ```bash
      ./dist/analyzer input.xlsx output.xlsx
      ```
   - Run without config included

      ```bash
      ./dist/analyzer input.xlsx output.xlsx --config `$config.toml绝对路径`/config.toml
      ```

**Note**: The packaged binary file still requires a running local Ollama service, unless using the OpenAI API or another public cloud LLM.
## Sentiment Analysis Rules
- **Positive**: Positive evaluations.
- **Negative**: Clear negative evaluation of "A".
- **Neutral**: No clear sentiment, or mentions competitors without comparison.
- **LLM Processing Error**: Default value when API call fails or returns invalid results.
## Dependencies
Listed in `requirements.txt`:
```
pandas>=1.5.0
openpyxl>=3.0.0
openai>=1.0.0
toml>=0.10.2
pyinstaller
```
## Notes
- **Ollama Configuration**: Ensure the Ollama service is running at `http://localhost:11434/v1` and the specified model has been loaded.
- **Model Support**: The Ollama models must support JSON output (`response_format={"type": "json_object"}`); otherwise, they might return non-JSON formats leading to default values of "LLM Processing Error."
- **Excel Column Names**: Input file column names must match those specified in `[excel].content_columns` in the `config.toml`.
- **Configuration Integrity**: Ensure all necessary items are present in the configuration file before running; otherwise, errors will be thrown.
- **Permissions**: Ensure write permissions in the working directory to generate logs and output files.
## Example Log
```
2025-03-23 10:00:00,130 - INFO - Logging system initialized successfully, log file: logs/analyzer_2025-03-23.log
2025-03-23 10:00:00,131 - DEBUG - Raw API output (attempt 1/3): {"sentiment": "正面"}
2025-03-23 10:00:00,132 - DEBUG - Sentiment analysis result: 正面
```
## Contributing
Contributions are welcome! Feel free to submit issues or pull requests.
## License
MIT License
