import logging
import os
import yaml
import requests
import threading
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database import DatabaseManager
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 初始化配置
class ConfigManager:
    def __init__(self):
        self.config_path = Path("config.yaml")
        self.config = self._load_config()
        self._validate_config()
        self._setup_paths()

    def _load_config(self):
        """加载并解析YAML配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError("配置文件 config.yaml 不存在")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _validate_config(self):
        """验证必要配置项是否存在"""
        required_keys = [
            ("telegram", "bot_token"),
            ("telegram", "admin_chat_id"),
            ("web_server", "secret_key")
        ]
        
        for section, key in required_keys:
            if section not in self.config or key not in self.config[section]:
                raise ValueError(f"缺少必要配置项 [{section}][{key}]")

    def _setup_paths(self):
        """创建必要的目录结构"""
        Path(self.config["file_storage"]["path"]).mkdir(exist_ok=True)
        Path("templates").mkdir(exist_ok=True)

config = ConfigManager()

# 初始化数据库
db_manager = DatabaseManager(str(config.config["database"]["path"]))

# 初始化Flask应用
web_app = Flask(__name__)
web_app.secret_key = config.config["web_server"]["secret_key"]
web_app.config['MAX_CONTENT_LENGTH'] = config.config["file_storage"]["max_size"]

# Web前端路由
@web_app.route('/')
def index():
    return render_template('index.html')

@web_app.route('/api/messages')
def api_messages():
    auth = request.headers.get('Authorization')
    if auth != f'Basic {config.config["web_server"]["secret_key"]}':
        return jsonify({"error": "Unauthorized"}), 401
    
    messages = db_manager.get_recent_messages()
    return jsonify([{
        "id": m["id"],
        "user": f"@{m['user_id']}" if m["user_id"] else "未知用户",
        "content": m["content"],
        "type": m["file_type"],
        "time": m["timestamp"]
    } for m in messages])

@web_app.route('/files/<path:filepath>')
def serve_file(filepath):
    return send_from_directory(Path("files"), filepath)

# 主程序入口
def main():
    # 启动Telegram机器人（在单独进程中运行）
    bot_process = subprocess.Popen([sys.executable, "telegram_bot.py"], 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1)
    
    # 创建线程来读取和打印子进程输出
    def read_output(stream, prefix):
        for line in stream:
            # 只打印非调试信息和重要信息
            if "DEBUG" not in line and "- httpx -" not in line and "- httpcore -" not in line:
                print(f"{prefix}: {line.strip()}")
    
    import threading
    stdout_thread = threading.Thread(target=read_output, args=(bot_process.stdout, "机器人"))
    stderr_thread = threading.Thread(target=read_output, args=(bot_process.stderr, "机器人错误"))
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    stdout_thread.start()
    stderr_thread.start()
    
    logger.info("Telegram机器人已在单独进程中启动")
    
    # 在主线程中运行Flask
    web_app.run(
        host='0.0.0.0',
        port=config.config["web_server"]["port"]
    )

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("程序正在关闭...")