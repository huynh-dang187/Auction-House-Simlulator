import customtkinter as ctk
from tkinter import messagebox
import socket
import threading
import configparser
from PIL import Image
import base64
import io

# --- THEME ---
COLOR_BG = "#1a1b26"       
COLOR_CARD = "#24283b"     
COLOR_PRIMARY = "#7aa2f7"  
COLOR_SUCCESS = "#9ece6a"  
COLOR_WARNING = "#e0af68"  
COLOR_ERROR = "#f7768e"    
COLOR_TEXT = "#c0caf5"     

ctk.set_appearance_mode("Dark")

class AuctionClientGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BID WARS: V5.1 COMPACT")
        self.geometry("480x700") # [FIX] Giảm chiều cao xuống 700 cho vừa màn hình laptop
        self.configure(fg_color=COLOR_BG)
        
        self.client_socket = None
        self.is_connected = False
        self.balance = 0 

        # --- LOGIN SCREEN ---
        self.frame_login = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_login.pack(fill="both", expand=True)
        
        box = ctk.CTkFrame(self.frame_login, fg_color=COLOR_CARD, corner_radius=20, border_color="#414868", border_width=1)
        box.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85)

        ctk.CTkLabel(box, text="BID WARS", font=("Arial", 32, "bold"), text_color=COLOR_PRIMARY).pack(pady=(30, 5))
        ctk.CTkLabel(box, text="Virtual Marketplace", font=("Arial", 12), text_color="#565f89").pack(pady=(0, 20))
        
        self.tab_view = ctk.CTkTabview(box, width=280, height=320, fg_color="transparent")
        self.tab_view.pack(pady=10)
        t_login = self.tab_view.add("LOGIN")
        t_reg = self.tab_view.add("REGISTER")

        # Inputs
        def create_entry(parent, ph, show=None):
            e = ctk.CTkEntry(parent, placeholder_text=ph, show=show, height=40, fg_color="#1a1b26", border_color="#414868")
            e.pack(pady=8, fill="x")
            return e

        self.u_login = create_entry(t_login, "Username")
        self.p_login = create_entry(t_login, "Password", "*")
        ctk.CTkButton(t_login, text="LOG IN", height=40, fg_color=COLOR_PRIMARY, font=("Arial", 12, "bold"), command=self.do_login).pack(pady=15, fill="x")

        self.u_reg = create_entry(t_reg, "New Username")
        self.p_reg = create_entry(t_reg, "Password", "*")
        self.b_reg = create_entry(t_reg, "Initial Balance ($)")
        ctk.CTkButton(t_reg, text="REGISTER", height=40, fg_color=COLOR_SUCCESS, font=("Arial", 12, "bold"), text_color="#1a1b26", command=self.do_register).pack(pady=15, fill="x")

        # --- MAIN GAME SCREEN ---
        self.frame_main = ctk.CTkFrame(self, fg_color="transparent")
        
        # 1. HEADER
        head = ctk.CTkFrame(self.frame_main, height=60, fg_color=COLOR_CARD, corner_radius=15, border_color="#414868", border_width=1)
        head.pack(fill="x", pady=(10, 5), padx=10)
        
        ctk.CTkLabel(head, text="👤", font=("Arial", 24)).pack(side="left", padx=(15, 5))
        self.lbl_user = ctk.CTkLabel(head, text="Player", font=("Arial", 14, "bold"), text_color=COLOR_TEXT)
        self.lbl_user.pack(side="left")
        
        bal_frame = ctk.CTkFrame(head, fg_color="#1a1b26", corner_radius=10)
        bal_frame.pack(side="right", padx=15, pady=8)
        self.lbl_balance = ctk.CTkLabel(bal_frame, text="$ 0", font=("Impact", 18), text_color=COLOR_WARNING)
        self.lbl_balance.pack(padx=15, pady=2)

        # 2. ARENA (LAYOUT NGANG - FIX TRÀN MÀN HÌNH)
        self.frame_arena = ctk.CTkFrame(self.frame_main, fg_color=COLOR_CARD, corner_radius=20)
        self.frame_arena.pack(fill="x", padx=10, pady=5)
        
        # Chia cột: Cột 0 (Ảnh) - Cột 1 (Thông tin)
        self.frame_arena.grid_columnconfigure(0, weight=0)
        self.frame_arena.grid_columnconfigure(1, weight=1)

        # [Cột 0] Ảnh (Nhỏ hơn xíu: 140x140)
        self.lbl_image_display = ctk.CTkLabel(self.frame_arena, text="", width=140, height=140, fg_color="#15161e", corner_radius=15)
        self.lbl_image_display.grid(row=0, column=0, rowspan=4, padx=15, pady=15)

        # [Cột 1] Thông tin (Nằm bên phải ảnh)
        self.lbl_timer = ctk.CTkButton(self.frame_arena, text="00s", width=60, height=25, fg_color="#1a1b26", hover=False, font=("Arial", 12, "bold"), text_color=COLOR_ERROR)
        self.lbl_timer.grid(row=0, column=1, sticky="e", padx=15, pady=(15, 0))

        self.lbl_item_name = ctk.CTkLabel(self.frame_arena, text="WAITING...", font=("Arial", 18, "bold"), text_color="white", anchor="w")
        self.lbl_item_name.grid(row=1, column=1, sticky="w", padx=5)
        
        self.lbl_current_price = ctk.CTkLabel(self.frame_arena, text="$ 0", font=("Impact", 36), text_color=COLOR_SUCCESS, anchor="w")
        self.lbl_current_price.grid(row=2, column=1, sticky="w", padx=5)
        
        self.lbl_winner = ctk.CTkLabel(self.frame_arena, text="---", font=("Arial", 11), text_color=COLOR_PRIMARY, anchor="w")
        self.lbl_winner.grid(row=3, column=1, sticky="w", padx=5, pady=(0, 15))

        # 3. CONTROL PAD
        ctrl = ctk.CTkFrame(self.frame_main, fg_color="transparent")
        ctrl.pack(fill="x", padx=10, pady=5)
        
        def create_bid_btn(amt, color):
            return ctk.CTkButton(ctrl, text=f"+${amt}", height=45, fg_color=color, font=("Arial", 15, "bold"), 
                                 text_color="#1a1b26", command=lambda: self.bid(amt))

        create_bid_btn(10, "#7dcfff").pack(side="left", fill="x", expand=True, padx=3)
        create_bid_btn(50, "#7aa2f7").pack(side="left", fill="x", expand=True, padx=3)
        create_bid_btn(100, "#bb9af7").pack(side="left", fill="x", expand=True, padx=3)

        # 4. CHAT (Bây giờ sẽ có đủ chỗ để hiển thị)
        self.txt_chat = ctk.CTkTextbox(self.frame_main, fg_color=COLOR_CARD, font=("Arial", 12), text_color="#a9b1d6", corner_radius=10)
        self.txt_chat.pack(fill="both", padx=10, pady=(5, 5), expand=True) # expand=True để nó chiếm hết phần còn lại
        self.txt_chat.configure(state="disabled")
        
        chat_in = ctk.CTkFrame(self.frame_main, fg_color="transparent")
        chat_in.pack(fill="x", padx=10, pady=(0, 10))
        self.entry_chat = ctk.CTkEntry(chat_in, placeholder_text="Type a message...", height=35, fg_color=COLOR_CARD, border_color="#414868")
        self.entry_chat.pack(side="left", fill="x", expand=True)
        self.entry_chat.bind('<Return>', lambda e: self.send_chat())
        ctk.CTkButton(chat_in, text="➤", width=40, height=35, fg_color=COLOR_PRIMARY, command=self.send_chat).pack(side="right", padx=(5,0))

    # --- LOGIC (GIỮ NGUYÊN) ---
    def do_login(self): self.connect_server("LOGIN", self.u_login.get(), self.p_login.get())
    def do_register(self):
        bal = self.b_reg.get()
        if not bal.isdigit(): return messagebox.showerror("Error", "Balance must be number")
        self.connect_server("REGISTER", self.u_reg.get(), self.p_reg.get(), bal)

    def connect_server(self, type, u, p, bal=None):
        if not u or not p: return
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            host = config.get('NETWORK', 'HOST', fallback='127.0.0.1')
            port = config.getint('NETWORK', 'PORT', fallback=5555)
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            msg = f"{type}|{u}|{p}" + (f"|{bal}" if bal else "")
            s.send(msg.encode('utf-8'))
            resp = s.recv(1024).decode('utf-8')
            
            if resp.startswith("AUTH_OK|"):
                self.balance = int(resp.split("|")[1])
                self.update_balance_ui()
                self.lbl_user.configure(text=u)
                self.client_socket = s
                self.is_connected = True
                self.frame_login.pack_forget()
                self.frame_main.pack(fill="both", expand=True)
                self.title(f"BID WARS: {u}")
                threading.Thread(target=self.listen, daemon=True).start()
            elif resp.startswith("REG_OK|"):
                messagebox.showinfo("Success", resp.split("|")[1])
                s.close()
            else:
                messagebox.showerror("Error", resp)
                s.close()
        except Exception as e: messagebox.showerror("Error", str(e))

    def update_balance_ui(self):
        self.lbl_balance.configure(text=f"$ {self.balance}")

    def listen(self):
        buffer = ""
        while self.is_connected:
            try:
                data = self.client_socket.recv(40960).decode('utf-8') 
                if not data: break
                buffer += data
                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
                    self.process(msg)
            except: break
        if self.is_connected: self.destroy()

    def process(self, msg):
        if msg.startswith("START|"):
            parts = msg.split("|")
            self.lbl_item_name.configure(text=parts[1])
            self.lbl_current_price.configure(text=f"$ {parts[2]}")
            self.lbl_winner.configure(text="Waiting for bids...")
            self.lbl_timer.configure(text="30s", fg_color="#1a1b26", text_color="white")
            
            img_str = parts[3]
            if img_str and img_str != "NO_IMG":
                try:
                    img_bytes = base64.b64decode(img_str)
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    ctk_img = ctk.CTkImage(pil_img, size=(140, 140)) # [FIX] Resize nhỏ lại cho layout ngang
                    self.lbl_image_display.configure(image=ctk_img, text="")
                except: self.lbl_image_display.configure(image=None, text="IMG ERR")
            else: self.lbl_image_display.configure(image=None, text="[NO IMG]")
            self.add_log(f"🔔 NEW ROUND: {parts[1]}")

        elif msg.startswith("UPDATE|"):
            parts = msg.split("|")
            self.lbl_current_price.configure(text=f"$ {parts[1]}", text_color=COLOR_WARNING)
            self.lbl_winner.configure(text=f"Last Bid: {parts[2]}")
            self.add_log(f"💰 {parts[2]} bid ${parts[1]}")
            self.after(300, lambda: self.lbl_current_price.configure(text_color=COLOR_SUCCESS))

        elif msg.startswith("TIME|"):
            t = int(msg.split("|")[1])
            self.lbl_timer.configure(text=f"{t}s")
            if t<=5: self.lbl_timer.configure(fg_color=COLOR_ERROR, text_color="#1a1b26")

        elif msg.startswith("WIN|"):
            self.lbl_timer.configure(text="END", fg_color="#bb9af7")
            messagebox.showinfo("Result", f"{msg.split('|')[1]} won!")
            self.add_log(f"🏆 WINNER: {msg.split('|')[1]}")

        # [TÍNH NĂNG CẬP NHẬT TIỀN]
        elif msg.startswith("BALANCE|"):
            self.balance = int(msg.split("|")[1]) # Lấy số tiền mới từ Server
            self.update_balance_ui()               # Cập nhật giao diện

        elif msg.startswith("CHAT|"):
            self.add_log(f"[{msg.split('|')[1]}]: {msg.split('|',2)[2]}")

        elif msg.startswith("REJECT|"):
            messagebox.showerror("Error", msg.split("|")[1])

    def bid(self, amt):
        if self.client_socket: self.client_socket.send(f"BID|{amt}\n".encode('utf-8'))
    
    def send_chat(self):
        t = self.entry_chat.get()
        if t: 
            self.client_socket.send(f"CHAT|{t}\n".encode('utf-8'))
            self.entry_chat.delete(0, "end")

    def add_log(self, t):
        self.txt_chat.configure(state="normal")
        self.txt_chat.insert("end", t+"\n")
        self.txt_chat.see("end")
        self.txt_chat.configure(state="disabled")

if __name__ == "__main__":
    app = AuctionClientGUI()
    app.mainloop()