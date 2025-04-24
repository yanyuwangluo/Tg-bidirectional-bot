# Telegram消息转发系统

一个基于Python的Telegram消息转发系统，支持接收用户消息并转发给管理员，管理员回复后自动转发给原用户。系统提供美观的Web界面查看所有消息历史。

## 功能特点

- 🔄 **双向消息转发**：用户发送给机器人的消息转发给管理员，管理员回复后自动转发给用户
- 📷 **多媒体支持**：支持文本、图片、视频、音频、文档等多种类型消息
- 🌐 **Web管理界面**：美观的响应式Web界面，可查看所有历史消息
- 🔐 **密钥验证**：Web界面需输入正确密钥才能访问，保障安全性
- 📱 **响应式设计**：适配各种设备屏幕，手机、平板、电脑均可使用
- 🔔 **即时通知**：支持Bark推送通知，确保及时接收消息

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/yanyuwangluo/Tg-bidirectional-bot.git
cd Tg-bidirectional-bot
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置系统

编辑`config.yaml`文件：

```yaml
telegram:
  bot_token: "YOUR_BOT_TOKEN"    # 从BotFather获取的机器人Token
  admin_chat_id: YOUR_CHAT_ID    # 管理员的Telegram Chat ID
  bark_api_key: "YOUR_BARK_KEY"  # 可选，Bark推送通知的API Key

web_server:
  port: 5000                     # Web服务器端口
  secret_key: "YOUR_SECRET_KEY"  # Web界面访问密钥和API认证密钥

file_storage:
  path: "files"                  # 文件存储路径
  max_size: 10485760             # 最大文件大小 (10MB)

database:
  path: "message_history.db"     # 数据库文件路径
```

### 4. 创建目录结构

```bash
mkdir -p files templates
```

## 启动系统

```bash
python app.py
```

启动后，系统会自动运行Telegram机器人和Web服务器。

## 使用方法

### Telegram机器人设置

1. 在Telegram中找到 [@BotFather](https://t.me/BotFather)
2. 使用 `/newbot` 命令创建新机器人
3. 按照提示输入机器人名称和用户名
4. 获取Bot Token并填入`config.yaml`
5. 启动系统后，用户可以向你的机器人发送消息

### 获取管理员Chat ID

1. 在Telegram中向 [@userinfobot](https://t.me/userinfobot) 发送消息
2. 机器人会回复你的个人信息，包含你的Chat ID
3. 将此ID填入`config.yaml`的`admin_chat_id`字段

### 使用Web界面

1. 访问 `http://your-server-ip:5000`
2. 输入在`config.yaml`中设置的`secret_key`作为访问密钥
3. 登录后可查看所有消息历史

### 回复用户消息

1. 当用户向机器人发送消息时，你作为管理员会收到转发消息
2. 直接在Telegram中回复该消息
3. 系统会自动将你的回复转发给原用户

## 项目结构

```
telegram-message-forwarder/
├── app.py                # 主应用程序
├── config.yaml           # 配置文件
├── database.py           # 数据库管理模块
├── telegram_bot.py       # Telegram机器人模块
├── files/                # 媒体文件存储目录
├── templates/            # Web模板目录
│   └── index.html        # Web界面
├── message_history.db    # SQLite数据库文件
└── requirements.txt      # 依赖项列表
```

## 常见问题

### 1. 回复消息没有发送给用户

确保你是直接回复机器人转发的消息，而不是发送新消息。系统通过回复关系识别目标用户。

### 2. 无法接收图片或文件

检查`files`目录是否存在且有写入权限。系统需要将接收到的文件保存到此目录。

### 3. Web界面无法访问

- 确认服务器防火墙已开放对应端口（默认5000）
- 验证密钥是否与`config.yaml`中的`secret_key`一致

### 4. 如何修改访问密钥

编辑`config.yaml`文件中的`web_server.secret_key`字段，同时需要更新`templates/index.html`中的`API_KEY`常量（约在第169行）。

## 技术栈

- **后端**：Python, Flask, SQLite
- **Telegram API**：python-telegram-bot
- **前端**：HTML, CSS, JavaScript, Bootstrap 5
- **通知**：Bark API (可选)

## 许可证

[LICENSE NAME] - 查看 [LICENSE](LICENSE) 文件了解更多信息。 
