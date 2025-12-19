import customtkinter as ctk
import tkinter as tk # Vẫn cần cho messagebox
from tkinter import messagebox
import socket
import threading
import time
import csv
import configparser
from datetime import datetime
from database import DatabaseManager # [MỚI] Import Database

# --- CẤU HÌNH UI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AuctionServerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SERVER ADMIN - SÀN ĐẤU GIÁ V2 (DB INTEGRATED)")
        self.geometry("650x750")
        
        self.db = DatabaseManager() # [MỚI] Khởi tạo DB

        # --- UI SETUP ---
        self.label_title = ctk.CTkLabel(self, text="HỆ THỐNG QUẢN TRỊ ĐẤU GIÁ", font=("Roboto", 24, "bold"), text_color="#3498db")
        self.label_title.pack(pady=20)

        self.frame_input = ctk.CTkFrame(self)
        self.frame_input.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(self.frame_input, text="Tên vật phẩm:").grid(row=0, column=0, padx=15, pady=10)
        self.entry_item = ctk.CTkEntry(self.frame_input, width=300, placeholder_text="Ví dụ: iPhone 15 Pro Max")
        self.entry_item.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(self.frame_input, text="Giá khởi điểm ($):").grid(row=1, column=0, padx=15, pady=10)
        self.entry_price = ctk.CTkEntry(self.frame_input, width=300, placeholder_text="Ví dụ: 1000")
        self.entry_price.grid(row=1, column=1, padx=10, pady=10)

        self.frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_btns.pack(pady=15)

        self.btn_start = ctk.CTkButton(self.frame_btns, text="MỞ PHIÊN (30s)", fg_color="green", hover_color="darkgreen", font=("Arial", 14, "bold"), command=self.start_auction)
        self.btn_start.pack(side="left", padx=10)

        self.btn_history = ctk.CTkButton(self.frame_btns, text="XEM LỊCH SỬ", fg_color="#e67e22", hover_color="#d35400", font=("Arial", 14, "bold"), command=self.show_history)
        self.btn_history.pack(side="left", padx=10)

        ctk.CTkLabel(self, text="Nhật ký hoạt động (System Logs):", anchor="w").pack(fill="x", padx=25)
        self.log_area = ctk.CTkTextbox(self, height=300)
        self.log_area.pack(pady=5, padx=20, fill="both", expand=True)
        self.log_area.configure(state="disabled")

        # --- LOGIC ---
        self.clients = []
        self.client_names = {} # socket -> username
        self.current_item = ""
        self.current_price = 0
        self.highest_bidder = "Chưa có"
        self.is_auction_active = False
        self.time_left = 30
        self.auction_lock = threading.Lock()

        self.init_history_file()
        self.start_server_socket()

    def init_history_file(self):
        try:
            with open("auction_history.csv", mode="x", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Thời gian", "Vật phẩm", "Người thắng", "Giá chốt ($)"])
        except FileExistsError: pass

    def log(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert("end", message + "\n")
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
            self.log(f"Server DB đang chạy tại {host}:{port}...")
            threading.Thread(target=self.receive_clients, daemon=True).start()
        except Exception as e:
            self.log(f"Lỗi Server: {e}")

    def receive_clients(self):
        while True:
            try:
                client_socket, client_addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except: break

    def handle_client(self, client_socket):
        username = ""
        try:
            # --- [BƯỚC 1: XÁC THỰC (LOGIN/REGISTER)] ---
            while True:
                auth_data = client_socket.recv(1024).decode('utf-8')
                if not auth_data: return
                
                # Cấu trúc: CMD|user|pass
                parts = auth_data.split("|")
                cmd = parts[0]
                user = parts[1]
                pwd = parts[2]

                if cmd == "LOGIN":
                    success, result = self.db.login_user(user, pwd)
                    if success:
                        if user in self.client_names.values(): # Check đang online
                            client_socket.send("AUTH_FAIL|Tài khoản này đang online!".encode('utf-8'))
                        else:
                            balance = result
                            client_socket.send(f"AUTH_OK|{balance}".encode('utf-8'))
                            username = user
                            break # Thoát vòng lặp auth để vào game
                    else:
                        client_socket.send(f"AUTH_FAIL|{result}".encode('utf-8'))
                
                elif cmd == "REGISTER":
                    success, msg = self.db.register_user(user, pwd)
                    if success:
                        client_socket.send(f"REG_OK|{msg}".encode('utf-8'))
                    else:
                        client_socket.send(f"REG_FAIL|{msg}".encode('utf-8'))
            
            # --- [BƯỚC 2: VÀO GAME] ---
            self.clients.append(client_socket)
            self.client_names[client_socket] = username
            self.log(f"--> {username} đã đăng nhập.")

            # Gửi trạng thái game hiện tại
            if self.is_auction_active:
                client_socket.send(f"START|{self.current_item}|{self.current_price}\n".encode('utf-8'))
                client_socket.send(f"UPDATE|{self.current_price}|{self.highest_bidder}\n".encode('utf-8'))
                client_socket.send(f"TIME|{self.time_left}\n".encode('utf-8'))

            # Vòng lặp nhận lệnh game
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
        except:
            pass
        finally:
            self.remove_client(client_socket)

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            self.clients.remove(client_socket)
            name = self.client_names.get(client_socket, "Unknown")
            if client_socket in self.client_names:
                del self.client_names[client_socket]
            self.log(f"<-- {name} đã thoát.")
            client_socket.close()

    def process_bid(self, client_socket, msg):
        if not self.is_auction_active: return
        try:
            bid_amount = int(msg.split("|")[1])
            player_name = self.client_names[client_socket]
            
            # --- [MỚI] CHECK TIỀN TRONG DB ---
            current_balance = self.db.get_balance(player_name)
            
            # Nếu tiền trong ví < Giá hiện tại + Bước giá
            if current_balance < (self.current_price + bid_amount):
                # Gửi thông báo riêng cho người đó
                client_socket.send(f"REJECT|Không đủ tiền! Ví còn ${current_balance}\n".encode('utf-8'))
                return
            # ---------------------------------

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
        self.log(f"=== BẮT ĐẦU: {item} - ${self.current_price} (30s) ===")
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
            
            # --- [FIX UPDATE] TRỪ TIỀN & BÁO CHO CLIENT ---
            if self.highest_bidder != "Chưa có":
                # 1. Trừ tiền trong DB
                self.db.update_balance(self.highest_bidder, -self.current_price)
                
                # 2. Lấy số dư mới nhất
                new_balance = self.db.get_balance(self.highest_bidder)
                
                # 3. Tìm socket của người thắng để gửi tin báo số dư mới
                for client_sock, name in self.client_names.items():
                    if name == self.highest_bidder:
                        try:
                            # Gửi lệnh cập nhật ví: BALANCE|Tiền_mới
                            client_sock.send(f"BALANCE|{new_balance}\n".encode('utf-8'))
                        except: pass
                        break
                
                self.log(f"!!! KẾT THÚC: {self.highest_bidder} thắng với ${self.current_price} (Ví còn ${new_balance})")
            else:
                self.log("!!! KẾT THÚC: Không ai mua.")
            # ----------------------------------------------

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
        history_window.title("Lịch Sử Đấu Giá")
        history_window.geometry("700x500")
        history_window.attributes("-topmost", True)

        ctk.CTkLabel(history_window, text="LỊCH SỬ CÁC PHIÊN ĐẤU GIÁ", font=("Arial", 18, "bold"), text_color="#e67e22").pack(pady=15)
        text_area = ctk.CTkTextbox(history_window, height=350)
        text_area.pack(pady=5, padx=20, fill="both", expand=True)

        try:
            with open("auction_history.csv", mode="r", encoding="utf-8") as file:
                reader = csv.reader(file)
                for row in reader:
                    formatted_row = f"{row[0]} | {row[1]:<15} | {row[2]:<10} | ${row[3]}\n"
                    text_area.insert("end", formatted_row)
        except FileNotFoundError:
            text_area.insert("end", "Chưa có dữ liệu lịch sử nào.")
        text_area.configure(state='disabled')

if __name__ == "__main__":
    app = AuctionServerGUI()
    app.mainloop()