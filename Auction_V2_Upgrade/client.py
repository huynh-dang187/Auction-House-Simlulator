import customtkinter as ctk
from tkinter import messagebox
import socket
import threading
import configparser
from PIL import Image
import base64
import io

# --- THEME ---
COLOR_BG = "#000000"
COLOR_CARD = "#121212"
COLOR_TEXT = "#FFFFFF"
COLOR_BTN_BID = "#1a1a1a"

ctk.set_appearance_mode("Dark")

class AuctionClientGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BID WARS: INVENTORY EDITION")
        self.geometry("600x700")
        self.configure(fg_color=COLOR_BG)
        
        self.client_socket = None
        self.is_connected = False
        self.balance = 0 

        # --- LOGIN SCREEN ---
        self.frame_login = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_login.pack(fill="both", expand=True)
        
        box = ctk.CTkFrame(self.frame_login, fg_color=COLOR_CARD, corner_radius=0, border_color="#333", border_width=1)
        box.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85)

        ctk.CTkLabel(box, text="BID WARS", font=("Arial", 30, "bold"), text_color="white").pack(pady=(30, 5))
        
        self.tab_view_login = ctk.CTkTabview(box, width=280, height=300, fg_color="transparent")
        self.tab_view_login.pack(pady=10)
        t_login = self.tab_view_login.add("LOGIN")
        t_reg = self.tab_view_login.add("REGISTER")

        # Inputs Helper
        def create_entry(parent, ph, show=None):
            e = ctk.CTkEntry(parent, placeholder_text=ph, show=show, height=45, fg_color="black", border_color="#444", text_color="white")
            e.pack(pady=8, fill="x")
            return e

        self.u_login = create_entry(t_login, "USERNAME")
        self.p_login = create_entry(t_login, "PASSWORD", "*")
        ctk.CTkButton(t_login, text="ACCESS", fg_color="white", text_color="black", height=45, hover_color="#cccccc", command=self.do_login).pack(pady=15, fill="x")

        self.u_reg = create_entry(t_reg, "USERNAME")
        self.p_reg = create_entry(t_reg, "PASSWORD", "*")
        self.b_reg = create_entry(t_reg, "INITIAL FUNDS ($)")
        ctk.CTkButton(t_reg, text="JOIN", fg_color="white", text_color="black", height=45, hover_color="#cccccc", command=self.do_register).pack(pady=15, fill="x")

        # --- MAIN GAME SCREEN (WITH TABS) ---
        self.frame_main = ctk.CTkFrame(self, fg_color="transparent")
        
        # TABVIEW CHÍNH: MARKET | MY ITEMS
        self.main_tabs = ctk.CTkTabview(self.frame_main, fg_color="transparent")
        self.main_tabs.pack(fill="both", expand=True, padx=10, pady=0)
        
        self.tab_market = self.main_tabs.add("LIVE MARKET")
        self.tab_inventory = self.main_tabs.add("MY ITEMS")

        # === TAB 1: LIVE MARKET (Giao diện cũ) ===
        self.setup_market_tab()

        # === TAB 2: INVENTORY (Giao diện mới) ===
        self.setup_inventory_tab()

    def setup_market_tab(self):
        # Header
        header = ctk.CTkFrame(self.tab_market, height=50, fg_color=COLOR_CARD, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        self.lbl_user = ctk.CTkLabel(header, text="GUEST", font=("Arial", 14, "bold"), text_color="gray")
        self.lbl_user.pack(side="left", padx=20)
        self.lbl_balance = ctk.CTkButton(header, text="$ 0", fg_color="transparent", text_color="#4CAF50", hover=False, font=("Impact", 20), width=100)
        self.lbl_balance.pack(side="right", padx=15, pady=5)

        # Product Area
        product_area = ctk.CTkFrame(self.tab_market, fg_color="transparent")
        product_area.pack(fill="both", expand=True, padx=0, pady=10)
        
        # Left: Image
        self.frame_img = ctk.CTkFrame(product_area, fg_color=COLOR_CARD, corner_radius=0, border_color="#333", border_width=1)
        self.frame_img.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.lbl_image_display = ctk.CTkLabel(self.frame_img, text="[WAITING]", text_color="#444")
        self.lbl_image_display.place(relx=0.5, rely=0.5, anchor="center")

        # Right: Info
        self.frame_info = ctk.CTkFrame(product_area, fg_color=COLOR_CARD, width=220, corner_radius=0, border_color="#333", border_width=1)
        self.frame_info.pack(side="right", fill="y")
        self.frame_info.pack_propagate(False)

        self.lbl_timer = ctk.CTkButton(self.frame_info, text="00s", width=50, height=25, fg_color="black", text_color="white", hover=False, border_width=1, border_color="#333")
        self.lbl_timer.pack(pady=(20, 10))
        self.lbl_item_name = ctk.CTkLabel(self.frame_info, text="...", font=("Arial", 16, "bold"), wraplength=200)
        self.lbl_item_name.pack(pady=5)
        self.lbl_current_price = ctk.CTkLabel(self.frame_info, text="$0", font=("Impact", 40), text_color="white")
        self.lbl_current_price.pack(pady=10)
        self.lbl_winner = ctk.CTkLabel(self.frame_info, text="BIDDER: ---", font=("Arial", 10), text_color="gray")
        self.lbl_winner.pack(pady=(0, 20))

        # Bids
        def create_btn(txt, color):
            ctk.CTkButton(self.frame_info, text=txt, fg_color=color, text_color="white", height=40, font=("Arial", 12, "bold"), 
                          command=lambda: self.bid(int(txt.replace("+$","")))).pack(fill="x", padx=15, pady=5)
        create_btn("+$10", "#2196F3")
        create_btn("+$50", "#FF9800")
        create_btn("+$100", "#F44336")

        # Chat
        self.frame_chat = ctk.CTkFrame(self.tab_market, fg_color=COLOR_CARD, height=150, corner_radius=0, border_width=1, border_color="#333")
        self.frame_chat.pack(fill="x", padx=0, pady=(0, 0))
        self.frame_chat.pack_propagate(False)
        self.txt_chat = ctk.CTkTextbox(self.frame_chat, fg_color="#000000", text_color="#ccc", font=("Arial", 11), corner_radius=0)
        self.txt_chat.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.txt_chat.configure(state="disabled")
        
        chat_in_frame = ctk.CTkFrame(self.frame_chat, fg_color="transparent")
        chat_in_frame.pack(side="right", fill="y", padx=10, pady=10)
        self.entry_chat = ctk.CTkEntry(chat_in_frame, placeholder_text="Type msg...", width=150, height=130, fg_color="#1a1a1a", border_color="#444", text_color="white")
        self.entry_chat.pack(fill="both", expand=True)
        self.entry_chat.bind('<Return>', lambda e: self.send_chat())

    def setup_inventory_tab(self):
        # Refresh Button
        ctk.CTkButton(self.tab_inventory, text="↻ REFRESH INVENTORY", fg_color="#333", hover_color="#444", command=self.req_inventory).pack(fill="x", pady=10)
        
        # Scrollable List
        self.scroll_inv = ctk.CTkScrollableFrame(self.tab_inventory, fg_color="transparent")
        self.scroll_inv.pack(fill="both", expand=True)

    # --- LOGIC ---
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
                self.lbl_user.configure(text=u.upper())
                self.client_socket = s
                self.is_connected = True
                self.frame_login.pack_forget()
                self.frame_main.pack(fill="both", expand=True)
                self.title(f"BID WARS: {u}")
                threading.Thread(target=self.listen, daemon=True).start()
                
                # Tự động load đồ khi vào game
                self.after(1000, self.req_inventory) 

            elif resp.startswith("REG_OK|"):
                messagebox.showinfo("Success", resp.split("|")[1]); s.close()
            else: messagebox.showerror("Error", resp); s.close()
        except Exception as e: messagebox.showerror("Error", str(e))

    def update_balance_ui(self):
        self.lbl_balance.configure(text=f"$ {self.balance}")

    def listen(self):
        buffer = ""
        while self.is_connected:
            try:
                # Tăng buffer lên thật lớn để nhận ảnh
                data = self.client_socket.recv(102400).decode('utf-8') 
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
            self.lbl_current_price.configure(text=f"${parts[2]}")
            self.lbl_winner.configure(text="WAITING FOR BIDS")
            self.lbl_timer.configure(text="30s", fg_color="black")
            
            img_str = parts[3]
            if img_str and img_str != "NO_IMG":
                try:
                    img_bytes = base64.b64decode(img_str)
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    ctk_img = ctk.CTkImage(pil_img, size=(280, 280)) 
                    self.lbl_image_display.configure(image=ctk_img, text="")
                except: self.lbl_image_display.configure(image=None, text="IMG ERR")
            else: self.lbl_image_display.configure(image=None, text="[NO IMAGE]")

        elif msg.startswith("UPDATE|"):
            parts = msg.split("|")
            self.lbl_current_price.configure(text=f"${parts[1]}")
            self.lbl_winner.configure(text=f"TOP: {parts[2]}")
            self.txt_chat.configure(state="normal")
            self.txt_chat.insert("end", f"💰 {parts[2]} bid ${parts[1]}\n")
            self.txt_chat.see("end")
            self.txt_chat.configure(state="disabled")

        elif msg.startswith("TIME|"):
            t = int(msg.split("|")[1])
            self.lbl_timer.configure(text=f"{t}s")
            if t<=5: self.lbl_timer.configure(fg_color="#b71c1c")

        elif msg.startswith("WIN|"):
            self.lbl_timer.configure(text="END", fg_color="#4a148c")
            messagebox.showinfo("Result", f"{msg.split('|')[1]} won!")
            self.txt_chat.configure(state="normal")
            self.txt_chat.insert("end", f"🏆 WINNER: {msg.split('|')[1]}\n")
            self.txt_chat.configure(state="disabled")
            
            # Nếu mình thắng, tự động refresh túi đồ
            if msg.split('|')[1] == self.lbl_user.cget("text").lower(): 
                self.after(2000, self.req_inventory)

        elif msg.startswith("BALANCE|"):
            self.balance = int(msg.split("|")[1])
            self.update_balance_ui()

        elif msg.startswith("CHAT|"):
            self.txt_chat.configure(state="normal")
            self.txt_chat.insert("end", f"[{msg.split('|')[1]}]: {msg.split('|',2)[2]}\n")
            self.txt_chat.see("end")
            self.txt_chat.configure(state="disabled")
        
        # --- [MỚI] XỬ LÝ NHẬN ĐỒ ---
        elif msg.startswith("INV_ITEM|"):
            # Format: INV_ITEM|Name|Price|Date|ImgData
            parts = msg.split("|")
            self.add_inventory_item(parts[1], parts[2], parts[3], parts[4])
        # ---------------------------

        elif msg.startswith("REJECT|"):
            messagebox.showerror("Error", msg.split("|")[1])

    def bid(self, amt):
        if self.client_socket: self.client_socket.send(f"BID|{amt}\n".encode('utf-8'))
    
    def send_chat(self):
        t = self.entry_chat.get()
        if t: 
            self.client_socket.send(f"CHAT|{t}\n".encode('utf-8'))
            self.entry_chat.delete(0, "end")

    # --- INVENTORY LOGIC ---
    def req_inventory(self):
        # Xóa cũ
        for widget in self.scroll_inv.winfo_children(): widget.destroy()
        if self.client_socket: self.client_socket.send("REQ_INVENTORY\n".encode('utf-8'))

    def add_inventory_item(self, name, price, date, img_str):
        # Tạo 1 cái Card cho món đồ
        card = ctk.CTkFrame(self.scroll_inv, fg_color=COLOR_CARD, corner_radius=10)
        card.pack(fill="x", pady=5, padx=5)
        
        # Ảnh nhỏ bên trái
        if img_str and img_str != "NO_IMG":
            try:
                img_bytes = base64.b64decode(img_str)
                pil_img = Image.open(io.BytesIO(img_bytes))
                ctk_img = ctk.CTkImage(pil_img, size=(60, 60))
                ctk.CTkLabel(card, text="", image=ctk_img).pack(side="left", padx=10, pady=5)
            except: pass
        else:
            ctk.CTkLabel(card, text="[NO IMG]", width=60).pack(side="left", padx=10)

        # Thông tin bên phải
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(info, text=name, font=("Arial", 14, "bold"), text_color="white", anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=f"Bought for: ${price}", font=("Arial", 12), text_color="#4CAF50", anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=date, font=("Arial", 10), text_color="gray", anchor="w").pack(fill="x")

if __name__ == "__main__":
    app = AuctionClientGUI()
    app.mainloop()