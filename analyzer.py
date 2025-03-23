import pandas as pd
import argparse
import sys
import os
import toml
import logging
import json
import time
from openai import OpenAI
from datetime import datetime
from typing import Dict, Any, List
import openai


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    设置日志记录，日志文件名包含日期
    Args:
        config (dict): 配置对象，包含日志路径等相关信息
    Returns:
        logger: 日志实例
    """
    # 检测是否为打包环境
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)
    
    # 获取基础日志路径并追加日期
    base_log_path = os.path.join(base_path, config['logging']['path'])
    log_dir = os.path.dirname(base_log_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 动态生成带日期的日志文件名
    date_str = datetime.now().strftime('%Y-%m-%d')
    log_filename = f"analyzer_{date_str}.log"
    log_path = os.path.join(log_dir, log_filename)
    
    handlers = [logging.FileHandler(log_path)]
    if config['logging'].get('console_output', True): # 默认输出到控制台
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=getattr(logging, config['logging']['level']),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成，日志文件：{log_path}")
    return logger

def validate_config(config: Dict[str, Any], logger: logging.Logger):
    """
    验证配置文件的完整性，检查所有必需的配置项是否存在。
    Args:
        config (dict): 配置对象
        logger: 日志实例
    """
    required_sections = ['openai', 'logging', 'excel', 'prompt']
    required_openai_keys = ['api_key', 'model', 'max_tokens', 'temperature']
    required_logging_keys = ['level', 'path']
    required_excel_keys = ['content_columns']
    required_prompt_keys = ['system_prompt', 'static_prompt']

    for section in required_sections:
        if section not in config:
            error_message = f"配置文件缺少必需的 section: {section}"
            logger.error(error_message)
            raise ValueError(error_message)

    for key in required_openai_keys:
        if key not in config['openai']:
            error_message = f"配置文件缺少必需的 openai key: {key}"
            logger.error(error_message)
            raise ValueError(error_message)

    for key in required_logging_keys:
        if key not in config['logging']:
            error_message = f"配置文件缺少必需的 logging key: {key}"
            logger.error(error_message)
            raise ValueError(error_message)

    for key in required_excel_keys:
        if key not in config['excel']:
            error_message = f"配置文件缺少必需的 excel key: {key}"
            logger.error(error_message)
            raise ValueError(error_message)

    for key in required_prompt_keys:
        if key not in config['prompt']:
            error_message = f"配置文件缺少必需的 prompt key: {key}"
            logger.error(error_message)
            raise ValueError(error_message)
        
def load_config(config_file: str, logger: logging.Logger) -> Dict[str, Any]:
    """
    加载 TOML 配置文件，记录日志
    Args:
        config_file: 配置文件相对路径
        logger: 日志实例
    Returns:
        config (dict): 解析后的配置对象
    """
    # 检测是否为打包环境
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)

    config_path = os.path.join(base_path, config_file) 
    try:
        logger.debug(f"尝试加载配置文件：{config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        logger.info(f"配置文件加载成功：{config_path}")

        # 验证配置文件的完整性
        validate_config(config, logger)

        return config
    except FileNotFoundError:
        error_message = f"配置文件 {config_path} 不存在"
        logger.error(error_message)
        raise ValueError(error_message)
    except Exception as e:
        error_message = f"加载配置文件 {config_path} 失败: {str(e)}"
        logger.error(error_message)
        raise ValueError(error_message)

def setup_openai_client(config: Dict[str, Any], logger: logging.Logger) -> openai.OpenAI:
    """
    设置 OpenAI 客户端，支持更多服务器参数
    Args:
        config: 配置对象（字典类型），包含 API Key、基础 URL 等信息
        logger: 日志实例
    Returns:
        client: OpenAI 客户端实例
    """
    api_key = config['openai'].get('api_key')
    if not api_key:
        logger.error("配置文件中缺少 OpenAI API Key")
        raise ValueError("请在 config/config.toml 中设置 openai.api_key")
    
    # 获取可选的服务器参数
    base_url = config['openai'].get('base_url', 'https://api.openai.com/v1')
    timeout = config['openai'].get('timeout', 30)  # 默认超时 30 秒

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )
   
        logger.info(f"OpenAI 客户端初始化完成，base_url={base_url}, timeout={timeout}s")
        return client
    except Exception as e:
        logger.error(f"OpenAI 客户端初始化失败：{str(e)}")
        raise


def generate_prompt(contents: List[str], config: Dict[str, Any]) -> str:
    """生成提示词"""
    static_prompt = config['prompt']['static_prompt']
    dynamic_prompt = "".join([f"内容 {i + 1}：{content}\n" for i, content in enumerate(contents)])
    return static_prompt + dynamic_prompt

def analyze_sentiment(
    contents: List[str],
    client: openai.OpenAI,
    config: Dict[str, Any],
    logger: logging.Logger
) -> str:
    """
    使用 OpenAI API 分析情感倾向
    Args:
        contents: 待分析的内容列表
        client: OpenAI 客户端实例
        config: 配置对象，包含模型、最大 tokens 等信息
        logger: 日志实例
    Returns:
        sentiment (str): 情感倾向，如 "正面"、"中立" 或 "负面"
    """
   
    prompt = generate_prompt(contents, config)
    system_prompt = config['prompt']['system_prompt']

    max_retries = config['openai'].get('max_retries', 3)  # 默认重试 3 次
    retry_interval = config['openai'].get('retry_interval', 1)  # 默认间隔 1 秒

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=config['openai']['model'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config['openai']['max_tokens'],
                temperature=config['openai']['temperature'],
                response_format={"type": "json_object"}  # 强制 JSON 输出
            )
            
            raw_output = response.choices[0].message.content.strip()
            logger.debug(f"API 原始输出（尝试 {attempt + 1}/{max_retries}）：{raw_output}")

            try:
                result = json.loads(raw_output)
                sentiment = result.get('sentiment')
                valid_sentiments = ['正面', '中立', '负面']

                if sentiment in valid_sentiments:
                    logger.debug(f"情感分析结果：{sentiment}")
                    return sentiment
                else:
                    error_message = f"JSON 中 sentiment 值为无效情感：{sentiment},(尝试 {attempt + 1}/{max_retries})"
                    logger.warning(error_message)
                    if attempt < max_retries - 1:  # 如果不是最后一次尝试
                        logger.info(f"等待 {retry_interval} 秒后重试...")
                        time.sleep(retry_interval)
                    else:
                        logger.error(f"JSON 中参数无效以达到最大重试次数 {max_retries}")
                        return 'LLM处理错误'
            except json.JSONDecodeError:
                error_message = f"API 返回非 JSON 格式：{raw_output},(尝试 {attempt + 1}/{max_retries})"
                logger.warning(error_message)
                if attempt < max_retries - 1:  # 如果不是最后一次尝试
                    logger.info(f"等待 {retry_interval} 秒后重试...")
                    time.sleep(retry_interval)
                else:
                    logger.error(f"API 返回非 JSON 格式以达到最大重试次数 {max_retries}")
                    return 'LLM处理错误'
      
        except Exception as e:
            error_message = f"大模型 API 调用错误（尝试 {attempt + 1}/{max_retries}）：{str(e)}"
            logger.error(error_message)

            if attempt < max_retries - 1:  # 如果不是最后一次尝试
                logger.info(f"等待 {retry_interval} 秒后重试...")
                time.sleep(retry_interval)
            else:
                logger.error(f"大模型 API 调用错误达到最大重试次数 {max_retries}")
                return 'LLM处理错误'

def process_excel(
    input_file: str,
    output_file: str,
    config: dict,
    client: OpenAI,
    logger: logging.Logger
):
    """
    处理 Excel 文件并添加情感标签
    Args:
        input_file (str): 输入的 Excel 文件路径
        output_file (str): 输出的 Excel 文件路径
        config: 配置对象，包含日志、OpenAI 等信息
        client: OpenAI 客户端实例
        logger: 日志实例
    Returns:
        None
    """
    try:
        logger.info(f"开始处理文件：{input_file}")

        # 文件类型验证
        if not input_file.lower().endswith(('.xls', '.xlsx')):
            logger.error("输入文件不是 Excel 文件")
            raise ValueError("输入文件不是 Excel 文件")
        
        df = pd.read_excel(input_file)
        
        # 从配置文件获取列名列表
        content_columns = config['excel']['content_columns']

        if not all(col in df.columns for col in content_columns):
            logger.error("Excel 文件缺少必要的列")
            raise ValueError("Excel 文件缺少必要的列：{content_columns}")
        
        def apply_analyze_sentiment(row: pd.Series, columns: List[str]) -> str:
            """
            根据列名列表动态构建参数并调用 analyze_sentiment
            Args:
                row (pd.Series): Excel 文件中的一行数据
                columns (List[str]): 列名列表，用于从行数据中提取内容
            Returns:
                str: 情感分析结果，如 "正面"、"中立" 或 "负面"
            """
            contents = [str(row[col]) if pd.notna(row[col]) else '' for col in columns]
            return analyze_sentiment(contents, client, config, logger)
        
        df['情感倾向'] = df.apply(lambda row: apply_analyze_sentiment(row, content_columns), axis=1)
        
        df.to_excel(output_file, index=False)
        logger.info(f"处理完成，结果已保存到 {output_file}")
        
    except Exception as e:
        logger.error(f"处理文件时出错：{str(e)}")
        raise  # 抛出异常

def main():
    parser = argparse.ArgumentParser(description='Excel 数据情感分析工具（使用 LLM）')
    parser.add_argument('input', help='输入 Excel 文件路径')
    parser.add_argument('output', help='输出 Excel 文件路径')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='日志级别')
    parser.add_argument('--config', default='config/config.toml', help='配置文件路径')
    args = parser.parse_args()
    
    # 初始化临时日志器
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    temp_logger = logging.getLogger(__name__)

    # 加载配置
    config = load_config(args.config, temp_logger)
    
    # 设置日志
    config['logging']['level'] = args.log_level # 使用命令行参数设置日志级别
    logger = setup_logging(config)
    
    # 设置 OpenAI 客户端
    client = setup_openai_client(config, logger)
    try: 
        # 处理 Excel 文件
        process_excel(args.input, args.output, config, client, logger)
    except Exception as e:
        logger.critical("程序异常退出")
        sys.exit(1)
if __name__ == "__main__":
    main()