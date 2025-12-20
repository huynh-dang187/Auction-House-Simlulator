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

# --- THEME BLACK ---
COLOR_BG = "#000000"
COLOR_PANEL = "#121212"
COLOR_TEXT_LOG = "#00ff00"

ctk.set_appearance_mode("Dark")

class AuctionServerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ADMIN COMMAND - PURE BLACK")
        self.geometry("1000x650")
        self.configure(fg_color=COLOR_BG)
        self.db = DatabaseManager()
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=COLOR_PANEL)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="AUCTION\nCONTROL", font=("Arial", 24, "bold"), text_color="white").pack(pady=(40, 40))

        self.entry_item = self.create_input("ITEM NAME", "Ex: iPhone 16")
        self.entry_price = self.create_input("START PRICE", "Ex: 1000")
        
        ctk.CTkLabel(self.sidebar, text="IMAGE ASSET", font=("Arial", 10, "bold"), text_color="#777", anchor="w").pack(fill="x", padx=20, pady=(10, 2))
        self.btn_browse = ctk.CTkButton(self.sidebar, text="📂 BROWSE FILE", fg_color="#000000", border_color="white", border_width=1, hover_color="#333333", command=self.browse_image)
        self.btn_browse.pack(fill="x", padx=20, pady=(5, 5))
        self.lbl_img_status = ctk.CTkLabel(self.sidebar, text="No file", font=("Arial", 10), text_color="gray")
        self.lbl_img_status.pack(pady=(0, 20))
        self.selected_image_path = None

        self.btn_start = ctk.CTkButton(self.sidebar, text="START SESSION", height=50, fg_color="white", text_color="black", hover_color="#cccccc", font=("Arial", 14, "bold"), command=self.start_auction)
        self.btn_start.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(self.sidebar, text="VIEW HISTORY", fg_color="transparent", border_width=1, border_color="#555", text_color="gray", command=self.show_history).pack(side="bottom", pady=20, fill="x", padx=20)

        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.log_area = ctk.CTkTextbox(self.main_area, font=("Consolas", 12), fg_color="#0a0a0a", text_color=COLOR_TEXT_LOG, border_color="#333", border_width=1)
        self.log_area.pack(fill="both", expand=True)
        self.log_area.configure(state="disabled")

        self.clients = []
        self.client_names = {}
        self.current_item = ""
        self.current_price = 0
        self.highest_bidder = "None"
        self.current_image_data = "NO_IMG"
        self.is_auction_active = False
        self.time_left = 30
        self.auction_lock = threading.Lock()
        
        self.init_history_file()
        self.start_server_socket()

    def create_input(self, label, ph):
        ctk.CTkLabel(self.sidebar, text=label, font=("Arial", 10, "bold"), text_color="#777", anchor="w").pack(fill="x", padx=20, pady=(10, 2))
        e = ctk.CTkEntry(self.sidebar, placeholder_text=ph, fg_color="#000000", border_color="#444", height=40)
        e.pack(fill="x", padx=20, pady=(0, 5))
        return e

    def browse_image(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("Image", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.selected_image_path = file_path
            self.lbl_img_status.configure(text=os.path.basename(file_path), text_color="white")

    def get_encoded_image(self):
        if not self.selected_image_path or not os.path.exists(self.selected_image_path): return "NO_IMG"
        try:
            with Image.open(self.selected_image_path) as img:
                img.thumbnail((300, 300))
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except: return "NO_IMG"

    def start_auction(self):
        item = self.entry_item.get()
        price_str = self.entry_price.get()
        if not item or not price_str: return
        self.log(f"Encoding image...")
        self.current_image_data = self.get_encoded_image()
        with self.auction_lock:
            self.current_item = item
            self.current_price = int(price_str)
            self.highest_bidder = "None"
            self.is_auction_active = True
        self.log(f"SESSION START: {item}")
        self.broadcast(f"START|{self.current_item}|{self.current_price}|{self.current_image_data}")
        self.start_timer()

    def handle_client(self, client_socket):
        username = ""
        try:
            while True:
                auth_data = client_socket.recv(1024).decode('utf-8')
                if not auth_data: return
                parts = auth_data.split("|")
                cmd = parts[0]
                if cmd == "LOGIN":
                    success, res = self.db.login_user(parts[1], parts[2])
                    if success:
                        if parts[1] in self.client_names.values(): client_socket.send("AUTH_FAIL|Online!".encode('utf-8'))
                        else:
                            client_socket.send(f"AUTH_OK|{res}".encode('utf-8'))
                            username = parts[1]
                            break
                    else: client_socket.send(f"AUTH_FAIL|{res}".encode('utf-8'))
                elif cmd == "REGISTER":
                    try: bal = int(parts[3])
                    except: bal = 1000
                    success, msg = self.db.register_user(parts[1], parts[2], bal)
                    if success: client_socket.send(f"REG_OK|{msg}".encode('utf-8'))
                    else: client_socket.send(f"REG_FAIL|{msg}".encode('utf-8'))
            self.clients.append(client_socket)
            self.client_names[client_socket] = username
            self.log(f"Connected: {username}")
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
                        elif msg.startswith("CHAT|"): self.broadcast(f"CHAT|{username}|{msg.split('|', 1)[1]}")
                        elif msg.startswith("REQ_INVENTORY"):
                            items = self.db.get_user_inventory(username)
                            for item in items:
                                send_msg = f"INV_ITEM|{item[0]}|{item[1]}|{item[2]}|{item[3]}\n"
                                client_socket.send(send_msg.encode('utf-8'))
                                time.sleep(0.05)
                except: break
        except: pass
        finally: self.remove_client(client_socket)

    def process_bid(self, client_socket, msg):
        if not self.is_auction_active: return
        try:
            bid_amount = int(msg.split("|")[1])
            player_name = self.client_names[client_socket]
            current_balance = self.db.get_balance(player_name)
            if current_balance < bid_amount:
                 client_socket.send(f"REJECT|Not enough funds! Balance: ${current_balance}\n".encode('utf-8'))
                 return
            with self.auction_lock:
                
                # --- [MỚI] LUẬT CHỐNG SNIPING (BÙ GIỜ) ---
                if self.time_left <= 5:
                    self.time_left += 10
                    self.broadcast(f"CHAT|SYSTEM|⏳ SNIPE DETECTED! TIME EXTENDED +10s!")
                    self.broadcast(f"TIME|{self.time_left}")
                # ----------------------------------------

                self.current_price += bid_amount
                self.highest_bidder = player_name
                self.db.update_balance(player_name, -bid_amount)
                new_bal = self.db.get_balance(player_name)
                client_socket.send(f"BALANCE|{new_bal}\n".encode('utf-8'))
                self.broadcast(f"UPDATE|{self.current_price}|{player_name}")
        except ValueError: pass

    def broadcast(self, message):
        for c in self.clients:
            try: c.send(f"{message}\n".encode('utf-8'))
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
            self.log(f"Winner: {self.highest_bidder}")
            if self.highest_bidder != "None":
                self.db.add_item(self.highest_bidder, self.current_item, self.current_price, self.current_image_data)
            self.save_history(self.current_item, self.highest_bidder, self.current_price)
    
    def init_history_file(self):
        try:
            with open("auction_history.csv", "x", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["Time", "Item", "Winner", "Price"])
        except: pass
    def log(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert("end", f"> {message}\n")
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
            self.log(f"System ready on {host}:{port}")
            threading.Thread(target=self.receive_clients, daemon=True).start()
        except Exception as e: self.log(f"Error: {e}")
    def receive_clients(self):
        while True:
            try:
                c, _ = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(c,), daemon=True).start()
            except: break
    def remove_client(self, s):
        if s in self.clients:
            self.clients.remove(s)
            if s in self.client_names: del self.client_names[s]
            s.close()
    def save_history(self, item, winner, price):
        try:
            with open("auction_history.csv", "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item, winner, price])
        except: pass
    def show_history(self):
        top = ctk.CTkToplevel(self)
        top.geometry("600x400")
        txt = ctk.CTkTextbox(top)
        txt.pack(fill="both", expand=True)
        try:
            with open("auction_history.csv", "r", encoding="utf-8") as f: txt.insert("0.0", f.read())
        except: txt.insert("0.0", "Empty")

if __name__ == "__main__":
    app = AuctionServerGUI()
    app.mainloop()