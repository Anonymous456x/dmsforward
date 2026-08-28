import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'shared.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined_date TEXT,
        is_premium INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        refer_count INTEGER DEFAULT 0
    )''')
    
    # Accounts table (user added accounts)
    c.execute('''CREATE TABLE IF NOT EXISTS user_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        phone TEXT,
        session_string TEXT,
        added_date TEXT,
        status TEXT DEFAULT 'active'
    )''')
    
    # DM History
    c.execute('''CREATE TABLE IF NOT EXISTS dm_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        target TEXT,
        message TEXT,
        count INTEGER,
        sent INTEGER,
        date TEXT
    )''')
    
    # Payments for cloning
    c.execute('''CREATE TABLE IF NOT EXISTS clone_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        utr TEXT,
        date TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    
    # Bot clones
    c.execute('''CREATE TABLE IF NOT EXISTS bot_clones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bot_token TEXT,
        bot_username TEXT,
        created_date TEXT,
        status TEXT DEFAULT 'stopped',
        env_data TEXT
    )''')
    
    # Available bots for cloning
    c.execute('''CREATE TABLE IF NOT EXISTS available_bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bot_token TEXT,
        bot_username TEXT,
        status TEXT DEFAULT 'available'
    )''')
    
    # Ads
    c.execute('''CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad_text TEXT,
        media_type TEXT,
        media_id TEXT,
        created_date TEXT,
        status TEXT DEFAULT 'active'
    )''')
    
    # Auto Reply
    c.execute('''CREATE TABLE IF NOT EXISTS auto_reply (
        user_id INTEGER PRIMARY KEY,
        reply_text TEXT,
        is_active INTEGER DEFAULT 0
    )''')
    
    # Pending Requests
    c.execute('''CREATE TABLE IF NOT EXISTS pending_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        target_user_id INTEGER,
        request_date TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    
    # Redeem Codes
    c.execute('''CREATE TABLE IF NOT EXISTS redeem_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        reward_type TEXT,
        reward_value INTEGER,
        created_date TEXT,
        used_by INTEGER DEFAULT NULL,
        is_used INTEGER DEFAULT 0
    )''')
    
    conn.commit()
    conn.close()

# ========== USERS ==========
def db_add_user(user_id, username, first_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name, joined_date) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def db_get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def db_get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, username, is_premium FROM users")
    users = c.fetchall()
    conn.close()
    return users

def db_update_premium(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ========== ACCOUNTS ==========
def db_add_account(user_id, phone, session):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO user_accounts (user_id, phone, session_string, added_date) VALUES (?, ?, ?, ?)",
        (user_id, phone, session, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def db_get_accounts(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM user_accounts WHERE user_id = ? AND status = 'active'", (user_id,))
    accounts = c.fetchall()
    conn.close()
    return accounts

def db_remove_account(user_id, account_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE user_accounts SET status = 'removed' WHERE id = ? AND user_id = ?", (account_id, user_id))
    conn.commit()
    conn.close()

# ========== DM HISTORY ==========
def db_add_dm_history(user_id, target, message, count, sent):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO dm_history (user_id, target, message, count, sent, date) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, target, message, count, sent, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

# ========== PAYMENTS ==========
def db_add_clone_payment(user_id, amount, utr):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO clone_payments (user_id, amount, utr, date, status) VALUES (?, ?, ?, ?, 'pending')",
        (user_id, amount, utr, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def db_get_pending_payments():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM clone_payments WHERE status = 'pending' ORDER BY id DESC")
    payments = c.fetchall()
    conn.close()
    return payments

def db_approve_payment(payment_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE clone_payments SET status = 'approved' WHERE id = ?", (payment_id,))
    c.execute("SELECT user_id FROM clone_payments WHERE id = ?", (payment_id,))
    user_id = c.fetchone()[0]
    c.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return user_id

# ========== CLONE BOTS ==========
def db_add_clone(user_id, bot_token, bot_username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO bot_clones (user_id, bot_token, bot_username, created_date, status) VALUES (?, ?, ?, ?, 'stopped')",
        (user_id, bot_token, bot_username, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def db_get_available_bots():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM available_bots WHERE status = 'available' LIMIT 1")
    bot = c.fetchone()
    conn.close()
    return bot

def db_add_available_bot(bot_token, bot_username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO available_bots (bot_token, bot_username, status) VALUES (?, ?, 'available')",
        (bot_token, bot_username)
    )
    conn.commit()
    conn.close()

def db_mark_bot_used(bot_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE available_bots SET status = 'used' WHERE id = ?", (bot_id,))
    conn.commit()
    conn.close()

def db_get_user_clones(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT bot_token, bot_username, created_date, status FROM bot_clones WHERE user_id = ? ORDER BY id DESC", (user_id,))
    clones = c.fetchall()
    conn.close()
    return clones

def db_get_clone_by_token(user_id, bot_token):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT * FROM bot_clones WHERE user_id = ? AND bot_token = ?",
        (user_id, bot_token)
    )
    clone = c.fetchone()
    conn.close()
    return clone

def db_update_clone_status(user_id, bot_token, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE bot_clones SET status = ? WHERE user_id = ? AND bot_token = ?",
        (status, user_id, bot_token)
    )
    conn.commit()
    conn.close()

def db_update_clone_env(user_id, bot_token, env_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    env_json = json.dumps(env_data)
    c.execute(
        "UPDATE bot_clones SET env_data = ? WHERE user_id = ? AND bot_token = ?",
        (env_json, user_id, bot_token)
    )
    conn.commit()
    conn.close()

def db_get_clone_env(user_id, bot_token):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT env_data FROM bot_clones WHERE user_id = ? AND bot_token = ?",
        (user_id, bot_token)
    )
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        return json.loads(result[0])
    return None

# ========== PENDING REQUESTS ==========
def db_add_pending_request(user_id, target_user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO pending_requests (user_id, target_user_id, request_date) VALUES (?, ?, ?)",
        (user_id, target_user_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def db_get_pending_requests(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM pending_requests WHERE target_user_id = ? AND status = 'pending'", (user_id,))
    requests = c.fetchall()
    conn.close()
    return requests

def db_accept_request(request_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE pending_requests SET status = 'accepted' WHERE id = ?", (request_id,))
    conn.commit()
    conn.close()

# ========== REDEEM CODES ==========
def db_add_redeem_code(code, reward_type, reward_value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO redeem_codes (code, reward_type, reward_value, created_date) VALUES (?, ?, ?, ?)",
        (code, reward_type, reward_value, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def db_use_redeem_code(code, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM redeem_codes WHERE code = ? AND is_used = 0", (code,))
    code_data = c.fetchone()
    if code_data:
        c.execute("UPDATE redeem_codes SET is_used = 1, used_by = ? WHERE code = ?", (user_id, code))
        conn.commit()
        conn.close()
        return code_data
    conn.close()
    return None

init_db()
print("✅ Database initialized!")
