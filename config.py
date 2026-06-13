import sqlite3
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8336283371:AAFBn6_zGinLTfkr194RNaHCyEKUhifozWw"
OWNER_ID = 7806950316
DB_PATH = "database.db"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 100000,
            bank INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def load_user(user_id: int, username: str = "Игрок") -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, balance, bank, banned, is_admin FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return {"id": row[0], "username": row[1], "balance": row[2], "bank": row[3], "banned": bool(row[4]), "is_admin": bool(row[5])}
    
    cursor.execute("INSERT INTO users (id, username, balance, bank, banned, is_admin) VALUES (?, ?, ?, ?, ?, ?)", (user_id, username, 100000, 0, 0, 0))
    conn.commit()
    conn.close()
    return {"id": user_id, "username": username, "balance": 100000, "bank": 0, "banned": False, "is_admin": False}

def update_funds(user_id: int, balance: int, bank: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ?, bank = ? WHERE id = ?", (balance, bank, user_id))
    conn.commit()
    conn.close()

MINES_GAMES = {}
  
