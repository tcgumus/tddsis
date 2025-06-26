import os
import sqlite3
from datetime import datetime

class ChatDatabase:
    def __init__(self):
        db_dir = os.path.join(os.path.expanduser("~"), "EddieApp", "database")
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, "chat_history.db")
        
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS conversations(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """
        )
        
        cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender TEXT NOT NULL, 
                message TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            )
        """
        )
        
        conn.commit()
        conn.close()
    
    def create_conversation(self, title = "Yeni Konuşma"):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
        """
            INSERT INTO conversations (title, created_at, updated_at)
            VALUES (?, ?, ?)
        """, (title, current_time, current_time)
        )
        
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return conversation_id

    def update_conversation_title(self, conversation_id, new_title):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
        """
            UPDATE conversations
            SET title = ?, updated_at = ?
            WHERE id = ?
        """, (new_title, current_time, conversation_id)
        )
        
        conn.commit()
        conn.close()
    
    def add_message(self, conversation_id, sender, message):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
        """
            INSERT INTO messages (conversation_id, sender, message, timestamp)
            VALUES (?, ?, ?, ?)
        """, (conversation_id, sender, message, current_time)
        )
        
        cursor.execute(
        """
            UPDATE conversations 
            SET updated_at = ?
            WHERE id = ?
        """, (current_time, conversation_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_all_conversations(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
        """
            SELECT id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC 
        """
        )
        
        conversations = cursor.fetchall()
        conn.close()
        
        return conversations

    def get_conversation_messages(self, conversation_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
        """
            SELECT id, sender, message, timestamp
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
        """, (conversation_id,)  
        )
        
        messages = cursor.fetchall()
        conn.close()
        
        return messages

    def delete_conversation(self, conversation_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
        """
            DELETE FROM conversations
            WHERE id = ?
        """, (conversation_id,)  
        )
        
        conn.commit()
        conn.close()