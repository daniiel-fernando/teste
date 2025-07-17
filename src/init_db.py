import sqlite3
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config

# Caminho absoluto para o banco de dados
db_path = Config.get_db_path()
print("USANDO BANCO DE DADOS EM:", db_path)

# Conectar e criar tabelas
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        name TEXT,
        email TEXT,
        department TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
"""
)

# Tabela de computadores
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS computers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        computer_name TEXT UNIQUE NOT NULL,
        ip_address TEXT,
        mac_address TEXT,
        department TEXT NOT NULL,
        user_name TEXT,
        status TEXT DEFAULT 'offline',
        client_version TEXT,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
)
# Tabela de mensagens
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT NOT NULL,
        image_path TEXT,
        sender_id INTEGER,
        recipients TEXT, -- JSON array
        urgent BOOLEAN DEFAULT 0,
        confirmation_required BOOLEAN DEFAULT 0,
        sound_enabled BOOLEAN DEFAULT 1,
        status TEXT DEFAULT 'sent',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users (id)
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS message_read_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id INTEGER NOT NULL,
        computer_id INTEGER NOT NULL,
        computer_name TEXT NOT NULL,
        status TEXT DEFAULT 'unread', -- 'unread', 'delivered', 'read'
        delivered_at TIMESTAMP,
        read_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (message_id) REFERENCES messages (id),
        FOREIGN KEY (computer_id) REFERENCES computers (id),
        UNIQUE(message_id, computer_id)
    )
"""
)
# Tabela de agendamentos
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS scheduled_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT NOT NULL,
        image_path TEXT,
        recipients TEXT, -- JSON array
        schedule_time TEXT NOT NULL,
        frequency TEXT, -- 'once', 'daily', 'weekdays', 'weekends'
        is_active BOOLEAN DEFAULT 1,
        sender_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_executed TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users (id)
    )
"""
)
conn.close()

print("✅ Banco de dados inicializado com sucesso em:", db_path)
print("✅ Banco de dados inicializado com sucesso em:", db_path)
print("USANDO BANCO DE DADOS EM:", db_path)
