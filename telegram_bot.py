import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sys
import os
import yaml
from pathlib import Path
import logging
from datetime import datetime
import requests

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入相关模块
from database import DatabaseManager

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO  # 改回INFO级别以减少无关日志
)
logger = logging.getLogger(__name__)

# 降低第三方库的日志级别
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.INFO) 
logging.getLogger('telegram.ext').setLevel(logging.INFO)
logging.getLogger('asyncio').setLevel(logging.WARNING)

# 加载配置
with open("config.yaml", "r", encoding="utf-8") as f:
    config_data = yaml.safe_load(f)

# 配置类 (简化版)
class Config:
    def __init__(self, data):
        self.config = data

config = Config(config_data)

# 处理函数
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("🤖 消息转发系统已启动")

async def save_file(message, file_type):
    try:
        if file_type == 'photo':
            file = message.photo[-1].get_file()
        else:
            file = message[file_type].get_file()

        file_ext = file.file_path.split('.')[-1]
        save_path = f"files/{int(datetime.now().timestamp())}.{file_ext}"
        file.download(save_path)
        return save_path
    except Exception as e:
        logger.error(f"文件保存失败: {str(e)}")
        return None

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    msg_id = message.message_id
    chat_id = update.effective_chat.id

    try:
        content = ""
        file_type = None
        file_path = None
        
        if message.text:
            content = message.text
            file_type = 'text'
        elif message.photo:
            file_path = await save_file(message, 'photo')
            file_type = 'photo'
            content = "[图片]"
        elif message.document:
            file_path = await save_file(message, 'document')
            file_type = 'document'
            content = f"[文档: {message.document.file_name}]"
        elif message.audio:
            file_path = await save_file(message, 'audio')
            file_type = 'audio'
            content = "[音频]"
        elif message.video:
            file_path = await save_file(message, 'video')
            file_type = 'video'
            content = "[视频]"

        # 初始化数据库
        db_manager = DatabaseManager("message_history.db")
        
        # 存储到数据库
        db_manager.save_message(
            msg_id=msg_id,
            user_id=user.id,
            chat_id=chat_id,
            content=content,
            file_type=file_type,
            file_path=file_path
        )

        # 发送给管理员 - 在消息中包含原始chat_id作为标识
        admin_text = f"📨 新消息来自用户: {user.first_name} (@{user.username}) -- [ID:{chat_id}]\n"
        admin_text += f"💬 消息内容：{content}\n"
        admin_text += f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        await context.bot.send_message(
            chat_id=config.config["telegram"]["admin_chat_id"],
            text=admin_text
        )

        # Bark通知
        if config.config["telegram"].get("bark_api_key"):
            requests.post(
                f"http://yanyuge.cn:8001/{config.config['telegram']['bark_api_key']}/Tg消息/{admin_text}?group=Telegram"
            )
            
        logger.info(f"已转发消息到管理员: {content}")
        print(f"已转发消息到管理员: {content} (来自: {chat_id})")

    except Exception as e:
        logger.error(f"消息处理失败: {str(e)}")
        print(f"消息处理失败: {str(e)}")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理管理员回复"""
    # 调试信息，避免打印整个更新对象
    try:
        print("收到消息更新")
        print(f"更新ID: {update.update_id}")
        print(f"聊天ID: {update.effective_chat.id}")
    except Exception as e:
        print(f"打印更新信息出错: {str(e)}")
    
    # 检查是否是管理员发送的消息
    admin_id = str(config.config["telegram"]["admin_chat_id"])
    print(f"配置中的管理员ID: {admin_id}")
    print(f"当前消息的聊天ID: {update.effective_chat.id}")
    
    if str(update.effective_chat.id) != admin_id:
        print(f"非管理员消息被过滤: {update.effective_chat.id} != {admin_id}")
        return
    else:
        print("确认是管理员发送的消息")

    message = update.effective_message
    
    # 打印调试信息，避免编码问题
    try:
        print(f"收到管理员消息内容: {message.text}")
    except Exception as e:
        print(f"打印消息内容出错: {str(e)}")
    
    # 检查是否是回复消息
    if message.reply_to_message:
        reply_msg = message.reply_to_message
        try:
            print("收到回复消息")
            print(f"回复消息ID: {reply_msg.message_id}")
        except Exception as e:
            print(f"打印回复信息出错: {str(e)}")
        
        # 尝试从回复的消息中提取用户ID
        try:
            # 从文本中提取用户ID，格式为"新消息来自用户 xxx (@xxx) [ID:xxxx]"
            text = reply_msg.text
            
            # 方法1: 提取[ID:xxxx]部分
            if "[ID:" in text and "]" in text:
                print("找到[ID:xxx]标记")
                id_start = text.find("[ID:") + 4
                id_end = text.find("]", id_start)
                id_part = text[id_start:id_end]
                print(f"提取的ID部分: '{id_part}'")
                
                if id_part.isdigit():
                    user_id = id_part
                    print(f"从标识中提取到用户ID: {user_id}")
                    
                    # 发送回复消息
                    try:
                        # 构建带有管理员信息和时间的回复消息
                        admin_name = update.effective_user.username or update.effective_user.first_name
                        reply_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        formatted_message = f"📩 来自管理员 @{admin_name} 的回复\n⏰ {reply_time}\n\n{message.text}"
                        
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=formatted_message
                        )
                        print(f"成功发送消息到用户 {user_id}")
                        logger.info(f"成功回复用户 {user_id}: {message.text}")
                        return
                    except Exception as e:
                        print(f"发送消息失败: {str(e)}")
                        logger.error(f"发送消息失败: {str(e)}")
            else:
                print("未找到[ID:xxx]标记")
            
            # 方法2: 使用数据库
            print("尝试从数据库获取用户ID")
            db_manager = DatabaseManager("message_history.db")
            recent_messages = db_manager.get_recent_messages(10)
            
            print(f"从数据库获取到 {len(recent_messages)} 条消息")
            
            if recent_messages and len(recent_messages) > 0:
                print("获取到最近消息记录")
                
                # 获取最近的非管理员用户ID
                user_id = None
                for m in recent_messages:
                    if str(m["chat_id"]) != admin_id:
                        user_id = m["chat_id"]  # 使用chat_id而不是user_id
                        print(f"从数据库中找到非管理员聊天ID: {user_id}")
                        break
                
                if user_id:
                    print(f"将使用用户ID: {user_id}")
                    
                    # 发送回复消息
                    try:
                        # 构建带有管理员信息和时间的回复消息
                        admin_name = update.effective_user.username or update.effective_user.first_name
                        reply_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        formatted_message = f"📩 来自管理员 @{admin_name} 的回复\n⏰ {reply_time}\n\n{message.text}"
                        
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=formatted_message
                        )
                        print(f"成功发送消息到用户 {user_id}")
                        logger.info(f"成功回复用户 {user_id}: {message.text}")
                        return
                    except Exception as e:
                        print(f"发送消息失败: {str(e)}")
                        logger.error(f"发送消息失败: {str(e)}")
            
            # 都失败了
            print("无法找到目标用户ID，所有方法都失败了")
            logger.error("无法找到目标用户ID")
        except Exception as e:
            logger.error(f"回复转发失败: {str(e)}")
            print(f"回复转发错误: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("这不是一个回复消息，将被忽略")

async def main():
    # 调试信息：输出当前配置
    print("=========== 当前配置信息 ===========")
    print(f"Telegram Bot Token: {config.config['telegram']['bot_token']}")
    print(f"管理员 Chat ID: {config.config['telegram']['admin_chat_id']}")
    print(f"Web 服务器端口: {config.config['web_server']['port']}")
    print("===================================")
    
    # 初始化并运行应用
    app = Application.builder().token(config.config["telegram"]["bot_token"]).build()
    
    print("=========== 注册处理器 ===========")
    # 添加处理器
    app.add_handler(CommandHandler("start", start))
    print("已注册 start 命令处理器")
    
    # 处理来自用户的消息
    user_filter = ~filters.Chat(chat_id=config.config["telegram"]["admin_chat_id"])
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & user_filter,
        forward_to_admin
    ))
    print("已注册 用户文本消息 处理器")
    
    app.add_handler(MessageHandler(
        filters.ATTACHMENT & user_filter,
        forward_to_admin
    ))
    print("已注册 用户附件消息 处理器")
    
    # 处理来自管理员的回复
    admin_filter = filters.Chat(chat_id=config.config["telegram"]["admin_chat_id"])
    app.add_handler(MessageHandler(
        filters.TEXT & admin_filter,
        handle_admin_reply
    ))
    print("已注册 管理员回复消息 处理器")
    print("==================================")
    
    # 运行机器人
    print("开始初始化 Telegram 机器人...")
    await app.initialize()
    print("开始启动 Telegram 机器人...")
    await app.start()
    print("开始轮询 Telegram 消息...")
    await app.updater.start_polling()
    
    logger.info("Telegram机器人已启动")
    print("Telegram机器人已启动并正在接收消息...")
    
    # 保持运行
    print("进入等待状态，机器人将持续运行")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
    