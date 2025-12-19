import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import socket
import threading
import configparser

# Setup Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AuctionClientGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SÀN ĐẤU GIÁ V2 - CLIENT")
        self.geometry("450x750")
        
        self.client_socket = None
        self.is_connected = False

        # --- MÀN HÌNH LOGIN ---
        self.frame_login = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_login.pack(fill="both", expand=True) 
        
        ctk.CTkLabel(self.frame_login, text="SÀN ĐẤU GIÁ\nCYBERPUNK", font=("Arial", 28, "bold"), text_color="#e74c3c").pack(pady=60)
        
        self.frame_input_login = ctk.CTkFrame(self.frame_login, corner_radius=20)
        self.frame_input_login.pack(pady=20, padx=40, fill="x")
        
        ctk.CTkLabel(self.frame_input_login, text="MẬT DANH:", font=("Arial", 14)).pack(pady=(20, 5))
        self.entry_name = ctk.CTkEntry(self.frame_input_login, width=200, placeholder_text="Nhập tên...", height=40, font=("Arial", 14))
        self.entry_name.pack(pady=10)
        
        self.entry_name.bind('<Return>', lambda event: self.connect_to_server())
        
        self.btn_join = ctk.CTkButton(self.frame_login, text="THAM CHIẾN 🚀", fg_color="#e74c3c", hover_color="#c0392b", height=50, width=200, font=("Arial", 16, "bold"), command=self.connect_to_server)
        self.btn_join.pack(pady=30)

        # --- MÀN HÌNH CHÍNH (Ẩn) ---
        self.frame_main = ctk.CTkFrame(self, fg_color="transparent")
        
        # === PHẦN 1: ĐẤU GIÁ (GAME) ===
        self.frame_auction = ctk.CTkFrame(self.frame_main, corner_radius=15, border_width=2, border_color="#3498db")
        self.frame_auction.pack(pady=10, padx=10, fill="x")

        self.lbl_timer = ctk.CTkLabel(self.frame_auction, text="WAITING...", font=("Impact", 30), text_color="#95a5a6")
        self.lbl_timer.pack(pady=10)

        self.lbl_item_name = ctk.CTkLabel(self.frame_auction, text="???", font=("Arial", 22, "bold"))
        self.lbl_item_name.pack()
        
        self.lbl_current_price = ctk.CTkLabel(self.frame_auction, text="Giá: $0", font=("Arial", 26, "bold"), text_color="#2ecc71")
        self.lbl_current_price.pack(pady=10)
        
        self.lbl_winner = ctk.CTkLabel(self.frame_auction, text="Người giữ giá: ---", font=("Arial", 14), text_color="#3498db")
        self.lbl_winner.pack(pady=5)

        # Các nút bấm
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

    def connect_to_server(self):
        if self.is_connected: return 

        name = self.entry_name.get()
        if not name: return messagebox.showwarning("Lỗi", "Nhập tên đi bro!")
        
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            host = config.get('NETWORK', 'HOST', fallback='127.0.0.1')
            port = config.getint('NETWORK', 'PORT', fallback=5555)

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port)) 
            self.client_socket.send(name.encode('utf-8'))
            
            self.is_connected = True
            self.frame_login.pack_forget()
            self.frame_main.pack(fill="both", expand=True)
            self.title(f"Người chơi: {name}")
            
            threading.Thread(target=self.listen_server, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Server chưa mở hoặc sai IP!\n{e}")
            self.is_connected = False

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
            except:
                break
        
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
            
            # Hiệu ứng nhấp nháy (Đổi màu chữ sang Đỏ rồi về Xanh)
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
            messagebox.showerror("Không vào được", f"Lỗi: {reason}")
            self.destroy()

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