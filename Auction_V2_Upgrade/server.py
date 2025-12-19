import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import socket
import threading
import csv
import time
import configparser
from datetime import datetime
from database import DatabaseManager

# --- COLOR PALETTE (CYBERPUNK THEME) ---
COLOR_BG = "#0f0f0f"           # Đen sâu
COLOR_SIDEBAR = "#1a1a1a"      # Xám đen
COLOR_ACCENT = "#00e5ff"       # Xanh Neon (Cyan)
COLOR_TEXT_MAIN = "#ffffff"    # Trắng
COLOR_TEXT_LOG = "#00ff00"     # Xanh lá Hacker
COLOR_DANGER = "#ff004d"       # Đỏ Neon

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class AuctionServerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SERVER COMMAND CENTER")
        self.geometry("900x600")
        self.configure(fg_color=COLOR_BG)

        self.db = DatabaseManager()

        # --- LAYOUT CHÍNH: 2 CỘT ---
        self.grid_columnconfigure(1, weight=1) # Cột nội dung giãn ra
        self.grid_rowconfigure(0, weight=1)

        # === 1. SIDEBAR (THANH BÊN TRÁI) ===
        self.frame_sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.frame_sidebar.grid(row=0, column=0, sticky="nsew")
        self.frame_sidebar.grid_rowconfigure(4, weight=1) # Đẩy log xuống dưới

        # Logo / Title
        ctk.CTkLabel(self.frame_sidebar, text="⚡ AUCTION\nMASTER", font=("Impact", 28), text_color=COLOR_ACCENT).pack(pady=(40, 20))

        # Input Fields
        ctk.CTkLabel(self.frame_sidebar, text="ITEM NAME", font=("Arial", 10, "bold"), text_color="gray").pack(anchor="w", padx=20)
        self.entry_item = ctk.CTkEntry(self.frame_sidebar, placeholder_text="Ex: Dragon Sword", fg_color="#333", border_color="#555")
        self.entry_item.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(self.frame_sidebar, text="START PRICE ($)", font=("Arial", 10, "bold"), text_color="gray").pack(anchor="w", padx=20)
        self.entry_price = ctk.CTkEntry(self.frame_sidebar, placeholder_text="Ex: 5000", fg_color="#333", border_color="#555")
        self.entry_price.pack(fill="x", padx=20, pady=(0, 20))

        # Buttons (Big & Bold)
        self.btn_start = ctk.CTkButton(self.frame_sidebar, text="▶ START SESSION", fg_color=COLOR_ACCENT, text_color="black", font=("Arial", 12, "bold"), hover_color="#00b8cc", height=40, command=self.start_auction)
        self.btn_start.pack(fill="x", padx=20, pady=10)

        self.btn_history = ctk.CTkButton(self.frame_sidebar, text="📂 VIEW LOGS", fg_color="transparent", border_width=2, border_color="gray", text_color="white", hover_color="#333", height=40, command=self.show_history)
        self.btn_history.pack(fill="x", padx=20, pady=10)

        # Footer info
        ctk.CTkLabel(self.frame_sidebar, text="v2.0.0 Stable", font=("Arial", 10), text_color="#555").pack(side="bottom", pady=20)

        # === 2. MAIN MONITOR (BÊN PHẢI) ===
        self.frame_monitor = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_monitor.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Status Bar
        self.frame_status = ctk.CTkFrame(self.frame_monitor, height=50, fg_color="#222")
        self.frame_status.pack(fill="x", pady=(0, 15))
        
        self.lbl_status = ctk.CTkLabel(self.frame_status, text="● SERVER ONLINE", font=("Consolas", 12, "bold"), text_color=COLOR_TEXT_LOG)
        self.lbl_status.pack(side="left", padx=15)
        
        ctk.CTkLabel(self.frame_status, text="PORT: 5555", font=("Consolas", 12, "bold"), text_color="gray").pack(side="right", padx=15)

        # Terminal Log
        ctk.CTkLabel(self.frame_monitor, text="SYSTEM TERMINAL >_", font=("Consolas", 14, "bold"), text_color="gray", anchor="w").pack(fill="x")
        
        self.log_area = ctk.CTkTextbox(self.frame_monitor, font=("Consolas", 12), fg_color="black", text_color=COLOR_TEXT_LOG, corner_radius=5)
        self.log_area.pack(fill="both", expand=True, pady=5)
        self.log_area.configure(state="disabled")

        # --- LOGIC INITIALIZATION ---
        self.clients = []
        self.client_names = {}
        self.current_item = ""
        self.current_price = 0
        self.highest_bidder = "Chưa có"
        self.is_auction_active = False
        self.time_left = 30
        self.auction_lock = threading.Lock()

        self.init_history_file()
        self.start_server_socket()

    # --- (GIỮ NGUYÊN TOÀN BỘ LOGIC CŨ TỪ ĐÂY TRỞ XUỐNG) ---
    def init_history_file(self):
        try:
            with open("auction_history.csv", mode="x", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Thời gian", "Vật phẩm", "Người thắng", "Giá chốt ($)"])
        except FileExistsError: pass

    def log(self, message):
        self.log_area.configure(state='normal')
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_area.insert("end", f"{timestamp} {message}\n") # Thêm timestamp cho chuyên nghiệp
        self.log_area.see("end")
        self.log_area.configure(state='disabled')

    def start_server_socket(self):
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            host = config.get('NETWORK', 'HOST', fallback='0.0.0.0') 
            port = config.getint('NETWORK', 'PORT', fallback=5555)

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((host, port))
            self.server_socket.listen(5)
            self.log(f"System initialized on {host}:{port}")
            threading.Thread(target=self.receive_clients, daemon=True).start()
        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")

    def receive_clients(self):
        while True:
            try:
                client_socket, client_addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except: break

    def handle_client(self, client_socket):
        username = ""
        try:
            while True:
                auth_data = client_socket.recv(1024).decode('utf-8')
                if not auth_data: return
                parts = auth_data.split("|")
                cmd = parts[0]
                user = parts[1]
                pwd = parts[2]

                if cmd == "LOGIN":
                    success, result = self.db.login_user(user, pwd)
                    if success:
                        if user in self.client_names.values():
                            client_socket.send("AUTH_FAIL|Tài khoản này đang online!".encode('utf-8'))
                        else:
                            balance = result
                            client_socket.send(f"AUTH_OK|{balance}".encode('utf-8'))
                            username = user
                            break
                    else:
                        client_socket.send(f"AUTH_FAIL|{result}".encode('utf-8'))
                
                elif cmd == "REGISTER":
                    success, msg = self.db.register_user(user, pwd)
                    if success:
                        client_socket.send(f"REG_OK|{msg}".encode('utf-8'))
                    else:
                        client_socket.send(f"REG_FAIL|{msg}".encode('utf-8'))
            
            self.clients.append(client_socket)
            self.client_names[client_socket] = username
            self.log(f"User connected: {username} (IP: {client_socket.getpeername()[0]})")

            if self.is_auction_active:
                client_socket.send(f"START|{self.current_item}|{self.current_price}\n".encode('utf-8'))
                client_socket.send(f"UPDATE|{self.current_price}|{self.highest_bidder}\n".encode('utf-8'))
                client_socket.send(f"TIME|{self.time_left}\n".encode('utf-8'))

            buffer = ""
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data: break
                buffer += data
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    if message.startswith("BID|"):
                        self.process_bid(client_socket, message)
                    elif message.startswith("CHAT|"):
                        content = message.split("|", 1)[1]
                        self.broadcast(f"CHAT|{username}|{content}")
                        print(f"[CHAT] {username}: {content}")
        except: pass
        finally:
            self.remove_client(client_socket)

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            self.clients.remove(client_socket)
            name = self.client_names.get(client_socket, "Unknown")
            if client_socket in self.client_names:
                del self.client_names[client_socket]
            self.log(f"User disconnected: {name}")
            client_socket.close()

    def process_bid(self, client_socket, msg):
        if not self.is_auction_active: return
        try:
            bid_amount = int(msg.split("|")[1])
            player_name = self.client_names[client_socket]
            current_balance = self.db.get_balance(player_name)
            
            if current_balance < (self.current_price + bid_amount):
                client_socket.send(f"REJECT|Không đủ tiền! Ví còn ${current_balance}\n".encode('utf-8'))
                return

            with self.auction_lock:
                self.current_price += bid_amount
                self.highest_bidder = player_name
                print(f"$$ {player_name}: ${self.current_price}") 
                self.broadcast(f"UPDATE|{self.current_price}|{player_name}")
        except ValueError: pass

    def broadcast(self, message):
        dead_clients = []
        for client in self.clients:
            try:
                client.send(f"{message}\n".encode('utf-8'))
            except:
                dead_clients.append(client)
        for dead in dead_clients:
            self.remove_client(dead)

    def start_auction(self):
        item = self.entry_item.get()
        price_str = self.entry_price.get()
        if not item or not price_str: return
        with self.auction_lock:
            self.current_item = item
            self.current_price = int(price_str)
            self.highest_bidder = "Chưa có"
            self.is_auction_active = True
        self.log(f"SESSION START: {item} - ${self.current_price}")
        self.broadcast(f"START|{self.current_item}|{self.current_price}")
        self.start_timer()

    def start_timer(self):
        self.time_left = 30
        threading.Thread(target=self.countdown, daemon=True).start()

    def countdown(self):
        while self.time_left > 0 and self.is_auction_active:
            time.sleep(1)
            self.time_left -= 1
            self.broadcast(f"TIME|{self.time_left}")
        if self.is_auction_active:
            self.end_auction()

    def end_auction(self):
        with self.auction_lock:
            self.is_auction_active = False
            msg = f"WIN|{self.highest_bidder}|{self.current_price}"
            self.broadcast(msg)
            
            if self.highest_bidder != "Chưa có":
                self.db.update_balance(self.highest_bidder, -self.current_price)
                new_balance = self.db.get_balance(self.highest_bidder)
                for client_sock, name in self.client_names.items():
                    if name == self.highest_bidder:
                        try:
                            client_sock.send(f"BALANCE|{new_balance}\n".encode('utf-8'))
                        except: pass
                        break
                self.log(f"SESSION END: Winner {self.highest_bidder} (${self.current_price})")
            else:
                self.log("SESSION END: No Bids.")
            self.save_history(self.current_item, self.highest_bidder, self.current_price)

    def save_history(self, item, winner, price):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("auction_history.csv", mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, item, winner, price])
        except: pass

    def show_history(self):
        history_window = ctk.CTkToplevel(self)
        history_window.title("History Logs")
        history_window.geometry("700x500")
        history_window.configure(fg_color=COLOR_BG)
        history_window.attributes("-topmost", True)

        ctk.CTkLabel(history_window, text="TRANSACTION HISTORY", font=("Impact", 20), text_color=COLOR_ACCENT).pack(pady=15)
        text_area = ctk.CTkTextbox(history_window, height=350, fg_color="#111", text_color="white", font=("Consolas", 11))
        text_area.pack(pady=5, padx=20, fill="both", expand=True)

        try:
            with open("auction_history.csv", mode="r", encoding="utf-8") as file:
                reader = csv.reader(file)
                for row in reader:
                    formatted_row = f"{row[0]} | {row[1]:<15} | {row[2]:<10} | ${row[3]}\n"
                    text_area.insert("end", formatted_row)
        except FileNotFoundError:
            text_area.insert("end", "No records found.")
        text_area.configure(state='disabled')

if __name__ == "__main__":
    app = AuctionServerGUI()
    app.mainloop()