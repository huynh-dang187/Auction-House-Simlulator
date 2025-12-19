import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import socket
import threading
import configparser

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AuctionClientGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SÀN ĐẤU GIÁ V2 - CLIENT (DB INTEGRATED)")
        self.geometry("450x750")
        
        self.client_socket = None
        self.is_connected = False
        self.balance = 0 # Lưu số dư

        # --- MÀN HÌNH LOGIN ---
        self.frame_login = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_login.pack(fill="both", expand=True) 
        
        ctk.CTkLabel(self.frame_login, text="SÀN ĐẤU GIÁ\nCYBERPUNK", font=("Arial", 28, "bold"), text_color="#e74c3c").pack(pady=40)
        
        self.frame_input_login = ctk.CTkFrame(self.frame_login, corner_radius=20)
        self.frame_input_login.pack(pady=10, padx=40, fill="x")
        
        # USERNAME
        ctk.CTkLabel(self.frame_input_login, text="TÀI KHOẢN:", font=("Arial", 12)).pack(pady=(15, 5))
        self.entry_name = ctk.CTkEntry(self.frame_input_login, width=220, placeholder_text="Username")
        self.entry_name.pack(pady=5)

        # [MỚI] PASSWORD
        ctk.CTkLabel(self.frame_input_login, text="MẬT KHẨU:", font=("Arial", 12)).pack(pady=(10, 5))
        self.entry_pass = ctk.CTkEntry(self.frame_input_login, width=220, placeholder_text="Password", show="*")
        self.entry_pass.pack(pady=(5, 20))
        
        # [MỚI] 2 NÚT LOGIN / REGISTER
        self.btn_login = ctk.CTkButton(self.frame_login, text="ĐĂNG NHẬP", fg_color="#3498db", width=220, height=40, command=lambda: self.connect_server("LOGIN"))
        self.btn_login.pack(pady=10)

        self.btn_reg = ctk.CTkButton(self.frame_login, text="ĐĂNG KÝ MỚI", fg_color="#e67e22", width=220, height=40, command=lambda: self.connect_server("REGISTER"))
        self.btn_reg.pack(pady=5)


        # --- MÀN HÌNH CHÍNH (Ẩn) ---
        self.frame_main = ctk.CTkFrame(self, fg_color="transparent")
        
        # Hiển thị số dư
        self.lbl_balance = ctk.CTkLabel(self.frame_main, text="Ví: $0", font=("Arial", 16, "bold"), text_color="#f1c40f")
        self.lbl_balance.pack(pady=(10, 0), padx=20, anchor="e")

        # === PHẦN 1: ĐẤU GIÁ ===
        self.frame_auction = ctk.CTkFrame(self.frame_main, corner_radius=15, border_width=2, border_color="#3498db")
        self.frame_auction.pack(pady=5, padx=10, fill="x")

        self.lbl_timer = ctk.CTkLabel(self.frame_auction, text="WAITING...", font=("Impact", 30), text_color="#95a5a6")
        self.lbl_timer.pack(pady=10)

        self.lbl_item_name = ctk.CTkLabel(self.frame_auction, text="???", font=("Arial", 22, "bold"))
        self.lbl_item_name.pack()
        
        self.lbl_current_price = ctk.CTkLabel(self.frame_auction, text="Giá: $0", font=("Arial", 26, "bold"), text_color="#2ecc71")
        self.lbl_current_price.pack(pady=10)
        
        self.lbl_winner = ctk.CTkLabel(self.frame_auction, text="Người giữ giá: ---", font=("Arial", 14), text_color="#3498db")
        self.lbl_winner.pack(pady=5)

        self.frame_buttons = ctk.CTkFrame(self.frame_auction, fg_color="transparent")
        self.frame_buttons.pack(pady=15)
        
        self.btn_10 = ctk.CTkButton(self.frame_buttons, text="+$10", width=80, fg_color="#3498db", command=lambda: self.bid(10))
        self.btn_10.pack(side="left", padx=5)
        self.btn_50 = ctk.CTkButton(self.frame_buttons, text="+$50", width=80, fg_color="#e67e22", command=lambda: self.bid(50))
        self.btn_50.pack(side="left", padx=5)
        self.btn_100 = ctk.CTkButton(self.frame_buttons, text="+$100", width=80, fg_color="#e74c3c", command=lambda: self.bid(100))
        self.btn_100.pack(side="left", padx=5)

        # === PHẦN 2: CHAT ROOM ===
        self.frame_chat = ctk.CTkFrame(self.frame_main, corner_radius=15)
        self.frame_chat.pack(pady=5, padx=10, fill="both", expand=True)
        ctk.CTkLabel(self.frame_chat, text="KÊNH CHAT", font=("Arial", 12, "bold")).pack(pady=5)
        self.txt_chat_log = ctk.CTkTextbox(self.frame_chat, height=200)
        self.txt_chat_log.pack(pady=5, padx=10, fill="both", expand=True)
        self.txt_chat_log.configure(state="disabled")
        self.frame_chat_input = ctk.CTkFrame(self.frame_chat, fg_color="transparent")
        self.frame_chat_input.pack(side="bottom", fill="x", padx=10, pady=10)
        self.entry_chat = ctk.CTkEntry(self.frame_chat_input, placeholder_text="Nhập tin nhắn...")
        self.entry_chat.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_chat.bind('<Return>', lambda event: self.send_chat())
        self.btn_send = ctk.CTkButton(self.frame_chat_input, text="Gửi", width=60, command=self.send_chat)
        self.btn_send.pack(side="right")

    def connect_server(self, action_type):
        """Hàm xử lý Login/Register"""
        user = self.entry_name.get()
        pwd = self.entry_pass.get()
        
        if not user or not pwd:
            return messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Tài khoản và Mật khẩu!")

        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            host = config.get('NETWORK', 'HOST', fallback='127.0.0.1')
            port = config.getint('NETWORK', 'PORT', fallback=5555)

            # Tạo kết nối mới
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            temp_socket.connect((host, port))
            
            # Gửi lệnh: LOGIN|user|pass hoặc REGISTER|user|pass
            msg = f"{action_type}|{user}|{pwd}"
            temp_socket.send(msg.encode('utf-8'))
            
            # Nhận phản hồi
            response = temp_socket.recv(1024).decode('utf-8')
            
            if response.startswith("AUTH_OK|"):
                # Đăng nhập thành công
                self.balance = int(response.split("|")[1])
                self.lbl_balance.configure(text=f"Ví: ${self.balance}")
                
                self.client_socket = temp_socket
                self.is_connected = True
                
                self.frame_login.pack_forget()
                self.frame_main.pack(fill="both", expand=True)
                self.title(f"Người chơi: {user}")
                
                threading.Thread(target=self.listen_server, daemon=True).start()

            elif response.startswith("AUTH_FAIL|"):
                reason = response.split("|")[1]
                messagebox.showerror("Đăng nhập thất bại", reason)
                temp_socket.close()

            elif response.startswith("REG_OK|"):
                reason = response.split("|")[1]
                messagebox.showinfo("Đăng ký thành công", reason)
                temp_socket.close() # Đăng ký xong bắt đăng nhập lại

            elif response.startswith("REG_FAIL|"):
                reason = response.split("|")[1]
                messagebox.showerror("Đăng ký thất bại", reason)
                temp_socket.close()

        except Exception as e:
            messagebox.showerror("Lỗi kết nối", f"{e}")

    def listen_server(self):
        buffer = ""
        while self.is_connected:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data: break
                buffer += data
                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
                    self.process_message(msg)
            except: break
        
        if self.is_connected:
            messagebox.showerror("Ngắt kết nối", "Server đã đóng!")
            self.destroy()

    def process_message(self, msg):
        if msg.startswith("START|"):
            parts = msg.split("|")
            self.lbl_item_name.configure(text=parts[1])
            self.lbl_current_price.configure(text=f"Giá: ${parts[2]}", text_color="#2ecc71")
            self.lbl_winner.configure(text="Người giữ giá: Chưa có")
            self.lbl_timer.configure(text="30s", text_color="#3498db")
            self.add_chat_log(f"--- BẮT ĐẦU: {parts[1]} ---")

        elif msg.startswith("UPDATE|"):
            parts = msg.split("|")
            self.lbl_current_price.configure(text=f"Giá: ${parts[1]}")
            self.lbl_winner.configure(text=f"Người giữ giá: {parts[2]}")
            self.add_chat_log(f"💰 {parts[2]} lên giá ${parts[1]}")
            
            self.lbl_current_price.configure(text_color="red")
            self.after(500, lambda: self.lbl_current_price.configure(text_color="#2ecc71"))

        elif msg.startswith("TIME|"):
            seconds = int(msg.split("|")[1])
            self.lbl_timer.configure(text=f"{seconds}s")
            if seconds <= 5: self.lbl_timer.configure(text_color="red")

        elif msg.startswith("WIN|"):
            parts = msg.split("|")
            winner = parts[1]
            price = parts[2]
            self.lbl_timer.configure(text="HẾT GIỜ", text_color="#9b59b6")
            messagebox.showinfo("KẾT THÚC", f"{winner} win giá ${price}!")
            self.add_chat_log(f"🏆 {winner} VÔ ĐỊCH (${price})")

        elif msg.startswith("CHAT|"):
            parts = msg.split("|", 2)
            sender = parts[1]
            content = parts[2]
            self.add_chat_log(f"[{sender}]: {content}")
        
        elif msg.startswith("REJECT|"):
            reason = msg.split("|")[1]
            messagebox.showerror("Cảnh báo", reason) 
            # Không thoát app, chỉ báo lỗi
        elif msg.startswith("BALANCE|"):
            new_bal = int(msg.split("|")[1])
            self.balance = new_bal # Cập nhật biến
            self.lbl_balance.configure(text=f"Ví: ${self.balance}") # Cập nhật giao diện
        # ------------------------------------

        elif msg.startswith("REJECT|"):
            reason = msg.split("|")[1]
            messagebox.showerror("Cảnh báo", reason)
            
            
    def bid(self, amount):
        if self.client_socket:
            try:
                self.client_socket.send(f"BID|{amount}\n".encode('utf-8'))
            except: pass

    def send_chat(self):
        msg = self.entry_chat.get()
        if msg and self.client_socket:
            try:
                self.client_socket.send(f"CHAT|{msg}\n".encode('utf-8'))
                self.entry_chat.delete(0, "end")
            except: pass

    def add_chat_log(self, msg):
        self.txt_chat_log.configure(state="normal")
        self.txt_chat_log.insert("end", msg + "\n")
        self.txt_chat_log.see("end")
        self.txt_chat_log.configure(state="disabled")

if __name__ == "__main__":
    app = AuctionClientGUI()
    app.mainloop()