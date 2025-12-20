import sqlite3
import hashlib
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="auction_data.db"):
        self.db_name = db_name
        self.create_table()

    def create_table(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Bảng Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                balance INTEGER
            )
        ''')
        # [MỚI] Bảng Inventory (Lưu trữ vật phẩm đã mua)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                item_name TEXT,
                price INTEGER,
                image_data TEXT,
                date_time TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password, initial_balance):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        if cursor.fetchone():
            conn.close()
            return False, "User already exists!"
        hashed_pw = self.hash_password(password)
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (username, hashed_pw, initial_balance))
        conn.commit()
        conn.close()
        return True, f"Account created! Balance: ${initial_balance}"

    def login_user(self, username, password):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        hashed_pw = self.hash_password(password)
        cursor.execute("SELECT balance FROM users WHERE username=? AND password=?", (username, hashed_pw))
        result = cursor.fetchone()
        conn.close()
        if result: return True, result[0]
        else: return False, "Invalid username or password!"

    def get_balance(self, username):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else 0

    def update_balance(self, username, amount):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, username))
        conn.commit()
        conn.close()

    # --- [MỚI] HÀM THÊM VẬT PHẨM VÀO TÚI ---
    def add_item(self, username, item_name, price, image_data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO inventory (username, item_name, price, image_data, date_time) VALUES (?, ?, ?, ?, ?)", 
                       (username, item_name, price, image_data, now))
        conn.commit()
        conn.close()

    # --- [MỚI] HÀM LẤY DANH SÁCH ĐỒ ---
    def get_user_inventory(self, username):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT item_name, price, date_time, image_data FROM inventory WHERE username=?", (username,))
        items = cursor.fetchall()
        conn.close()
        return items