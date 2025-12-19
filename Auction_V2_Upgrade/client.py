import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import socket
import threading
import configparser

# --- THEME CONFIG ---
COLOR_BG = "#121212"
COLOR_CARD = "#1e1e1e"
COLOR_PRIMARY = "#3D5AFE" # Xanh đậm hiện đại
COLOR_SUCCESS = "#00E676" # Xanh lá Neon
COLOR_WARNING = "#FFC107" # Vàng
COLOR_ERROR = "#FF1744"   # Đỏ
COLOR_TEXT = "#ECEFF1"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class AuctionClientGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BID WARS: ONLINE")
        self.geometry("450x800")
        self.configure(fg_color=COLOR_BG)
        
        self.client_socket = None
        self.is_connected = False
        self.balance = 0 

        # --- LOGIN SCREEN (CENTERED CARD) ---
        self.frame_login = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_login.pack(fill="both", expand=True)
        
        # Center Container
        self.center_box = ctk.CTkFrame(self.frame_login, fg_color=COLOR_CARD, corner_radius=20, border_width=1, border_color="#333")
        self.center_box.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.7)

        ctk.CTkLabel(self.center_box, text="BID WARS", font=("Impact", 40), text_color=COLOR_PRIMARY).pack(pady=(40, 5))
        ctk.CTkLabel(self.center_box, text="Marketplace Access", font=("Arial", 12), text_color="gray").pack(pady=(0, 20))

        # TABS
        self.tab_view = ctk.CTkTabview(self.center_box, width=300, height=300, corner_radius=15, fg_color="transparent")
        self.tab_view.pack(pady=10, fill="both", expand=True)
        
        self.tab_login = self.tab_view.add("LOGIN")
        self.tab_reg = self.tab_view.add("REGISTER")

        # --> Tab Login
        self.entry_login_user = ctk.CTkEntry(self.tab_login, placeholder_text="Username", height=45, fg_color="#111", border_color="#444")
        self.entry_login_user.pack(pady=(20, 15), padx=20, fill="x")
        self.entry_login_pass = ctk.CTkEntry(self.tab_login, placeholder_text="Password", height=45, fg_color="#111", border_color="#444", show="•")
        self.entry_login_pass.pack(pady=(0, 20), padx=20, fill="x")
        ctk.CTkButton(self.tab_login, text="ENTER MARKET", height=50, fg_color=COLOR_PRIMARY, font=("Arial", 14, "bold"), command=self.do_login).pack(pady=10, padx=20, fill="x")

        # --> Tab Register
        self.entry_reg_user = ctk.CTkEntry(self.tab_reg, placeholder_text="New Username", height=45, fg_color="#111", border_color="#444")
        self.entry_reg_user.pack(pady=(10, 10), padx=20, fill="x")
        self.entry_reg_pass = ctk.CTkEntry(self.tab_reg, placeholder_text="Password", height=45, fg_color="#111", border_color="#444", show="•")
        self.entry_reg_pass.pack(pady=(0, 10), padx=20, fill="x")
        self.entry_reg_confirm = ctk.CTkEntry(self.tab_reg, placeholder_text="Confirm Password", height=45, fg_color="#111", border_color="#444", show="•")
        self.entry_reg_confirm.pack(pady=(0, 20), padx=20, fill="x")
        ctk.CTkButton(self.tab_reg, text="CREATE ACCOUNT", height=50, fg_color=COLOR_SUCCESS, font=("Arial", 14, "bold"), text_color="black", command=self.do_register).pack(pady=10, padx=20, fill="x")

        # --- MAIN GAME SCREEN ---
        self.frame_main = ctk.CTkFrame(self, fg_color="transparent")
        
        # 1. Header (Balance)
        self.header_frame = ctk.CTkFrame(self.frame_main, height=60, fg_color=COLOR_CARD, corner_radius=0)
        self.header_frame.pack(fill="x", pady=(0, 10))
        
        self.lbl_title = ctk.CTkLabel(self.header_frame, text="LIVE AUCTION", font=("Arial", 14, "bold"), text_color="gray")
        self.lbl_title.pack(side="left", padx=20)
        
        self.lbl_balance = ctk.CTkButton(self.header_frame, text="$ 0", font=("Consolas", 16, "bold"), fg_color="#111", border_color="#ffd700", border_width=1, text_color="#ffd700", hover=False, width=100)
        self.lbl_balance.pack(side="right", padx=15, pady=10)

        # 2. The Arena (Item Card)
        self.frame_arena = ctk.CTkFrame(self.frame_main, fg_color=COLOR_CARD, corner_radius=20, border_color="#333", border_width=1)
        self.frame_arena.pack(pady=10, padx=15, fill="x")

        # Timer Badge
        self.lbl_timer = ctk.CTkButton(self.frame_arena, text="00s", width=60, height=30, fg_color="#333", hover=False, font=("Arial", 12, "bold"))
        self.lbl_timer.pack(pady=(15, 5))

        self.lbl_item_name = ctk.CTkLabel(self.frame_arena, text="WAITING FOR ITEM...", font=("Arial", 20, "bold"), text_color="white")
        self.lbl_item_name.pack(pady=5)
        
        # Price Display (Big)
        self.lbl_current_price = ctk.CTkLabel(self.frame_arena, text="$ 0", font=("Impact", 48), text_color=COLOR_SUCCESS)
        self.lbl_current_price.pack(pady=10)
        
        self.lbl_winner = ctk.CTkLabel(self.frame_arena, text="Current Highest: ---", font=("Arial", 12), text_color=COLOR_PRIMARY)
        self.lbl_winner.pack(pady=(0, 20))

        # 3. Control Pad (Buttons)
        self.frame_controls = ctk.CTkFrame(self.frame_main, fg_color="transparent")
        self.frame_controls.pack(pady=5, padx=15, fill="x")
        
        self.btn_10 = ctk.CTkButton(self.frame_controls, text="+$10", height=50, fg_color="#333", font=("Arial", 14, "bold"), command=lambda: self.bid(10))
        self.btn_10.pack(side="left", fill="x", expand=True, padx=5)
        
        self.btn_50 = ctk.CTkButton(self.frame_controls, text="+$50", height=50, fg_color="#444", font=("Arial", 14, "bold"), command=lambda: self.bid(50))
        self.btn_50.pack(side="left", fill="x", expand=True, padx=5)
        
        self.btn_100 = ctk.CTkButton(self.frame_controls, text="+$100", height=50, fg_color="#555", font=("Arial", 14, "bold"), command=lambda: self.bid(100))
        self.btn_100.pack(side="left", fill="x", expand=True, padx=5)

        # 4. Chat Room
        self.frame_chat = ctk.CTkFrame(self.frame_main, fg_color=COLOR_CARD, corner_radius=15)
        self.frame_chat.pack(pady=15, padx=15, fill="both", expand=True)
        
        ctk.CTkLabel(self.frame_chat, text="LIVE CHAT", font=("Arial", 10, "bold"), text_color="gray").pack(pady=5, anchor="w", padx=15)
        
        self.txt_chat_log = ctk.CTkTextbox(self.frame_chat, fg_color="#111", text_color="#ccc", font=("Arial", 12))
        self.txt_chat_log.pack(pady=5, padx=10, fill="both", expand=True)
        self.txt_chat_log.configure(state="disabled")
        
        self.chat_input_frame = ctk.CTkFrame(self.frame_chat, fg_color="transparent")
        self.chat_input_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        self.entry_chat = ctk.CTkEntry(self.chat_input_frame, placeholder_text="Say something...", height=40, fg_color="#222", border_color="#444")
        self.entry_chat.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_chat.bind('<Return>', lambda event: self.send_chat())
        
        self.btn_send = ctk.CTkButton(self.chat_input_frame, text="➤", width=50, height=40, fg_color=COLOR_PRIMARY, command=self.send_chat)
        self.btn_send.pack(side="right")

    # --- LOGIC FUNCTIONS (GIỮ NGUYÊN) ---
    def do_login(self):
        user = self.entry_login_user.get()
        pwd = self.entry_login_pass.get()
        self.connect_server("LOGIN", user, pwd)

    def do_register(self):
        user = self.entry_reg_user.get()
        pwd = self.entry_reg_pass.get()
        confirm_pwd = self.entry_reg_confirm.get()
        if pwd != confirm_pwd:
            return messagebox.showerror("Error", "Passwords do not match!")
        self.connect_server("REGISTER", user, pwd)

    def connect_server(self, action_type, user, pwd):
        if not user or not pwd:
            return messagebox.showwarning("Warning", "Please fill all fields!")
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            host = config.get('NETWORK', 'HOST', fallback='127.0.0.1')
            port = config.getint('NETWORK', 'PORT', fallback=5555)

            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            temp_socket.connect((host, port))
            msg = f"{action_type}|{user}|{pwd}"
            temp_socket.send(msg.encode('utf-8'))
            response = temp_socket.recv(1024).decode('utf-8')
            
            if response.startswith("AUTH_OK|"):
                self.balance = int(response.split("|")[1])
                self.lbl_balance.configure(text=f"$ {self.balance}")
                self.client_socket = temp_socket
                self.is_connected = True
                self.frame_login.pack_forget()
                self.frame_main.pack(fill="both", expand=True)
                self.title(f"PLAYER: {user}")
                threading.Thread(target=self.listen_server, daemon=True).start()

            elif response.startswith("AUTH_FAIL|"):
                messagebox.showerror("Failed", response.split("|")[1])
                temp_socket.close()

            elif response.startswith("REG_OK|"):
                messagebox.showinfo("Success", response.split("|")[1])
                self.tab_view.set("LOGIN") 
                self.entry_login_user.insert(0, user)
                temp_socket.close()

            elif response.startswith("REG_FAIL|"):
                messagebox.showerror("Failed", response.split("|")[1])
                temp_socket.close()
        except Exception as e:
            messagebox.showerror("Connection Error", f"{e}")

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
            messagebox.showerror("Disconnected", "Server closed connection.")
            self.destroy()

    def process_message(self, msg):
        if msg.startswith("START|"):
            parts = msg.split("|")
            self.lbl_item_name.configure(text=parts[1])
            self.lbl_current_price.configure(text=f"$ {parts[2]}", text_color=COLOR_SUCCESS)
            self.lbl_winner.configure(text="Highest Bidder: ---")
            self.lbl_timer.configure(text="30s", fg_color=COLOR_PRIMARY)
            self.add_chat_log(f"--- SYSTEM: Auction Started for {parts[1]} ---")

        elif msg.startswith("UPDATE|"):
            parts = msg.split("|")
            self.lbl_current_price.configure(text=f"$ {parts[1]}")
            self.lbl_winner.configure(text=f"Highest Bidder: {parts[2]}")
            self.add_chat_log(f"💰 {parts[2]} bid ${parts[1]}")
            self.lbl_current_price.configure(text_color=COLOR_WARNING)
            self.after(300, lambda: self.lbl_current_price.configure(text_color=COLOR_SUCCESS))

        elif msg.startswith("BALANCE|"):
            new_bal = int(msg.split("|")[1])
            self.balance = new_bal
            self.lbl_balance.configure(text=f"$ {self.balance}")

        elif msg.startswith("TIME|"):
            seconds = int(msg.split("|")[1])
            self.lbl_timer.configure(text=f"{seconds}s")
            if seconds <= 5: self.lbl_timer.configure(fg_color=COLOR_ERROR)

        elif msg.startswith("WIN|"):
            parts = msg.split("|")
            winner = parts[1]
            price = parts[2]
            self.lbl_timer.configure(text="END", fg_color="#9b59b6")
            messagebox.showinfo("AUCTION ENDED", f"{winner} won for ${price}!")
            self.add_chat_log(f"🏆 {winner} WON THE ITEM (${price})")

        elif msg.startswith("CHAT|"):
            parts = msg.split("|", 2)
            self.add_chat_log(f"[{parts[1]}]: {parts[2]}")
        
        elif msg.startswith("REJECT|"):
            messagebox.showerror("Alert", msg.split("|")[1])

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