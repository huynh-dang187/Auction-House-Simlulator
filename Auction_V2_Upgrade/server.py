import customtkinter as ctk
import socket
import threading
import time
import csv
import configparser
from datetime import datetime
from database import DatabaseManager
import base64
from PIL import Image
import io
import os

# --- THEME SERVER (GIỮ NGUYÊN HOẶC CHỈNH TÙY THÍCH) ---
COLOR_BG = "#1a1b26" # Xám xanh hiện đại
COLOR_SIDEBAR = "#16161e"
COLOR_ACCENT = "#7aa2f7"
COLOR_TEXT_LOG = "#9ece6a" # Xanh lá dịu

ctk.set_appearance_mode("Dark")

class AuctionServerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SERVER COMMAND CENTER (V5 ULTIMATE)")
        self.geometry("950x700")
        self.configure(fg_color=COLOR_BG)
        self.db = DatabaseManager()
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # SIDEBAR
        self.frame_sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.frame_sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.frame_sidebar, text="⚡ AUCTION\nADMIN", font=("Arial", 26, "bold"), text_color=COLOR_ACCENT).pack(pady=(40, 30))

        # INPUTS
        self.create_input("ITEM NAME", "Ex: Dragon Ball Z")
        self.entry_item = self.last_entry
        
        self.create_input("START PRICE ($)", "Ex: 1000")
        self.entry_price = self.last_entry
        
        # IMAGE SELECT
        ctk.CTkLabel(self.frame_sidebar, text="ITEM IMAGE", font=("Arial", 11, "bold"), text_color="#565f89").pack(anchor="w", padx=20)
        self.btn_browse = ctk.CTkButton(self.frame_sidebar, text="📂 Choose Image", fg_color="#24283b", hover_color="#414868", command=self.browse_image)
        self.btn_browse.pack(fill="x", padx=20, pady=(5, 5))
        self.lbl_img_path = ctk.CTkLabel(self.frame_sidebar, text="No file selected", font=("Arial", 10), text_color="gray")
        self.lbl_img_path.pack(pady=(0, 20))
        self.selected_image_path = None

        # ACTIONS
        self.btn_start = ctk.CTkButton(self.frame_sidebar, text="▶ START SESSION", height=45, fg_color=COLOR_ACCENT, hover_color="#5d8eea", font=("Arial", 13, "bold"), text_color="#1a1b26", command=self.start_auction)
        self.btn_start.pack(fill="x", padx=20, pady=10)
        
        # MONITOR
        self.frame_monitor = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_monitor.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(self.frame_monitor, text="SYSTEM LOGS", font=("Arial", 14, "bold"), text_color="#c0caf5").pack(anchor="w", pady=(0,5))
        self.log_area = ctk.CTkTextbox(self.frame_monitor, font=("Consolas", 13), fg_color="#000000", text_color=COLOR_TEXT_LOG, corner_radius=10)
        self.log_area.pack(fill="both", expand=True)
        self.log_area.configure(state="disabled")

        # LOGIC VARS
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

    def create_input(self, label, placeholder):
        ctk.CTkLabel(self.frame_sidebar, text=label, font=("Arial", 11, "bold"), text_color="#565f89").pack(anchor="w", padx=20)
        entry = ctk.CTkEntry(self.frame_sidebar, placeholder_text=placeholder, fg_color="#1a1b26", border_color="#414868", height=35)
        entry.pack(fill="x", padx=20, pady=(0, 15))
        self.last_entry = entry

    def browse_image(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.selected_image_path = file_path
            self.lbl_img_path.configure(text=os.path.basename(file_path))

    def get_encoded_image(self):
        if not self.selected_image_path or not os.path.exists(self.selected_image_path): return "NO_IMG"
        try:
            with Image.open(self.selected_image_path) as img:
                img.thumbnail((350, 350)) # Resize to fit client
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except: return "NO_IMG"

    def start_auction(self):
        item = self.entry_item.get()
        price_str = self.entry_price.get()
        if not item or not price_str: return
        
        self.log("Encoding image...")
        encoded_img = self.get_encoded_image()

        with self.auction_lock:
            self.current_item = item
            self.current_price = int(price_str)
            self.highest_bidder = "Chưa có"
            self.is_auction_active = True
        
        self.log(f"SESSION START: {item} - ${self.current_price}")
        self.broadcast(f"START|{self.current_item}|{self.current_price}|{encoded_img}")
        self.start_timer()

    # --- XỬ LÝ BID & TRỪ TIỀN REAL-TIME ---
    def process_bid(self, client_socket, msg):
        if not self.is_auction_active: return
        try:
            bid_amount = int(msg.split("|")[1])
            player_name = self.client_names[client_socket]
            
            # 1. Lấy tiền hiện tại từ DB
            current_balance = self.db.get_balance(player_name)
            
            # 2. Kiểm tra đủ tiền không (Giá hiện tại + bước giá)
            # Lưu ý: Ở đây ta trừ thẳng tiền Bid vào tài khoản như phí đặt cọc
            # Hoặc bro có thể chỉ check: if current_balance < bid_amount (nếu muốn logic kiểu khác)
            
            if current_balance < bid_amount: # Ví dụ: Phí bid là bid_amount
                 client_socket.send(f"REJECT|Không đủ tiền! Ví còn ${current_balance}\n".encode('utf-8'))
                 return

            with self.auction_lock:
                self.current_price += bid_amount
                self.highest_bidder = player_name
                
                # [QUAN TRỌNG] TRỪ TIỀN NGAY LẬP TỨC
                # (Logic này giả định mỗi lần bid là mất tiền luôn - kiểu đấu giá Pay-to-bid)
                # Nếu bro muốn chỉ trừ người thắng cuối cùng thì bỏ dòng này, 
                # nhưng bro đòi "cập nhật liên tục" thì phải trừ nó mới nhảy số.
                self.db.update_balance(player_name, -bid_amount) 
                
                # [QUAN TRỌNG] GỬI SỐ DƯ MỚI VỀ CHO RIÊNG CLIENT ĐÓ
                new_bal = self.db.get_balance(player_name)
                client_socket.send(f"BALANCE|{new_bal}\n".encode('utf-8'))
                
                self.broadcast(f"UPDATE|{self.current_price}|{player_name}")
                
        except ValueError: pass

    # --- (CÁC HÀM CƠ BẢN KHÁC GIỮ NGUYÊN) ---
    def init_history_file(self):
        try:
            with open("auction_history.csv", mode="x", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Time", "Item", "Winner", "Price"])
        except: pass

    def log(self, message):
        self.log_area.configure(state='normal')
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_area.insert("end", f"{timestamp} {message}\n")
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
            self.log(f"Server initialized on {host}:{port}")
            threading.Thread(target=self.receive_clients, daemon=True).start()
        except Exception as e: self.log(f"ERROR: {e}")

    def receive_clients(self):
        while True:
            try:
                client_socket, _ = self.server_socket.accept()
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
                    success, res = self.db.login_user(user, pwd)
                    if success:
                        if user in self.client_names.values(): client_socket.send("AUTH_FAIL|Already online!".encode('utf-8'))
                        else:
                            client_socket.send(f"AUTH_OK|{res}".encode('utf-8'))
                            username = user
                            break
                    else: client_socket.send(f"AUTH_FAIL|{res}".encode('utf-8'))
                elif cmd == "REGISTER":
                    try: bal = int(parts[3])
                    except: bal = 1000
                    success, msg = self.db.register_user(user, pwd, bal)
                    if success: client_socket.send(f"REG_OK|{msg}".encode('utf-8'))
                    else: client_socket.send(f"REG_FAIL|{msg}".encode('utf-8'))
            
            self.clients.append(client_socket)
            self.client_names[client_socket] = username
            self.log(f"User connected: {username}")
            
            # Gửi trạng thái game hiện tại nếu đang chạy
            if self.is_auction_active:
                client_socket.send(f"START|{self.current_item}|{self.current_price}|NO_IMG\n".encode('utf-8'))
                client_socket.send(f"UPDATE|{self.current_price}|{self.highest_bidder}\n".encode('utf-8'))
                client_socket.send(f"TIME|{self.time_left}\n".encode('utf-8'))

            buffer = ""
            while True:
                try:
                    data = client_socket.recv(40960).decode('utf-8')
                    if not data: break
                    buffer += data
                    while "\n" in buffer:
                        msg, buffer = buffer.split("\n", 1)
                        if msg.startswith("BID|"): self.process_bid(client_socket, msg)
                        elif msg.startswith("CHAT|"):
                            content = msg.split("|", 1)[1]
                            self.broadcast(f"CHAT|{username}|{content}")
                except: break
        except: pass
        finally: self.remove_client(client_socket)

    def remove_client(self, s):
        if s in self.clients:
            self.clients.remove(s)
            if s in self.client_names: del self.client_names[s]
            s.close()

    def broadcast(self, message):
        for client in self.clients:
            try: client.send(f"{message}\n".encode('utf-8'))
            except: pass

    def start_timer(self):
        self.time_left = 30
        threading.Thread(target=self.countdown, daemon=True).start()

    def countdown(self):
        while self.time_left > 0 and self.is_auction_active:
            time.sleep(1)
            self.time_left -= 1
            self.broadcast(f"TIME|{self.time_left}")
        if self.is_auction_active: self.end_auction()

    def end_auction(self):
        with self.auction_lock:
            self.is_auction_active = False
            self.broadcast(f"WIN|{self.highest_bidder}|{self.current_price}")
            # Ở đây không cần trừ tiền nữa vì đã trừ lúc Bid rồi (nếu theo logic ở trên)
            # Hoặc nếu theo logic trừ tiền người thắng thì phải trả lại tiền cho người thua.
            # Để đơn giản cho bài tập: Logic "Pay-to-Bid" (Mất tiền khi đặt giá) là dễ hiện thị số dư giảm nhất.
            self.log(f"Winner: {self.highest_bidder}")
            self.save_history(self.current_item, self.highest_bidder, self.current_price)
    
    def save_history(self, item, winner, price):
        try:
            with open("auction_history.csv", "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item, winner, price])
        except: pass

    def show_history(self):
        top = ctk.CTkToplevel(self)
        top.geometry("600x400")
        top.title("History")
        txt = ctk.CTkTextbox(top)
        txt.pack(fill="both", expand=True)
        try:
            with open("auction_history.csv", "r", encoding="utf-8") as f: txt.insert("0.0", f.read())
        except: txt.insert("0.0", "Empty")

if __name__ == "__main__":
    app = AuctionServerGUI()
    app.mainloop()