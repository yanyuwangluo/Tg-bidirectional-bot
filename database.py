import sqlite3
from pathlib import Path
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self._create_tables()

    def _create_tables(self):
        """创建必要的数据库表"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      msg_id INTEGER,
                      user_id INTEGER,
                      chat_id INTEGER,
                      content TEXT,
                      file_type TEXT,
                      file_path TEXT,
                      timestamp DATETIME)''')
        conn.commit()
        conn.close()

    def save_message(self, msg_id, user_id, chat_id, content, file_type=None, file_path=None):
        """保存消息到数据库"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO messages 
                     (msg_id, user_id, chat_id, content, file_type, file_path, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (msg_id, user_id, chat_id, content, file_type, file_path, datetime.now()))
        conn.commit()
        conn.close()

    def get_recent_messages(self, limit=50):
        """获取最近的消息记录"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT ?", (limit,))
        messages = []
        for row in c.fetchall():
            messages.append({
                "id": row[0],
                "msg_id": row[1],
                "user_id": row[2],
                "chat_id": row[3],
                "content": row[4],
                "file_type": row[5],
                "file_path": row[6],
                "timestamp": row[7]
            })
        conn.close()
        return messages