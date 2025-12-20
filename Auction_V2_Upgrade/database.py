import sqlite3
import hashlib

class DatabaseManager:
    def __init__(self, db_name="auction_data.db"):
        self.db_name = db_name
        self.create_table()

    def create_table(self):
        """Tạo bảng User nếu chưa có"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                balance INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    def hash_password(self, password):
        """Mã hóa mật khẩu bằng SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()

    # Sửa dòng này: thêm tham số initial_balance
    def register_user(self, username, password, initial_balance):
        """Đăng ký user mới với số dư tùy chọn"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        if cursor.fetchone():
            conn.close()
            return False, "Tên này đã tồn tại!"
        
        hashed_pw = self.hash_password(password)
        
        # Sửa dòng này: thay số 1000 cứng bằng biến initial_balance
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (username, hashed_pw, initial_balance))
        
        conn.commit()
        conn.close()
        return True, f"Đăng ký thành công! Ví: ${initial_balance}"

    def login_user(self, username, password):
        """Kiểm tra đăng nhập"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        hashed_pw = self.hash_password(password)
        cursor.execute("SELECT balance FROM users WHERE username=? AND password=?", (username, hashed_pw))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return True, result[0] # Trả về số dư
        else:
            return False, "Sai tài khoản hoặc mật khẩu!"

    def get_balance(self, username):
        """Lấy số dư hiện tại"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else 0

    def update_balance(self, username, amount):
        """Cập nhật tiền (amount âm là trừ, dương là cộng)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, username))
        conn.commit()
        conn.close()