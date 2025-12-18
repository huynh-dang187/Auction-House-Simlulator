import tkinter as tk
from tkinter import messagebox
import socket
import threading

class AuctionClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sàn Đấu Giá Online - Client")
        self.root.geometry("400x650") # Kéo dài ra để chứa khung chat
        
        self.client_socket = None
        self.is_connected = False

        # --- MÀN HÌNH LOGIN ---
        self.frame_login = tk.Frame(root)
        tk.Label(self.frame_login, text="THAM GIA ĐẤU GIÁ", font=("Arial", 14, "bold")).pack(pady=30)
        tk.Label(self.frame_login, text="Nhập tên của bạn:").pack()
        self.entry_name = tk.Entry(self.frame_login, width=30)
        self.entry_name.pack(pady=10)
        self.entry_name.bind('<Return>', lambda event: self.connect_to_server())
        tk.Button(self.frame_login, text="VÀO PHÒNG", bg="blue", fg="white", command=self.connect_to_server).pack(pady=10)
        self.frame_login.pack()

        # --- MÀN HÌNH CHÍNH (Ẩn) ---
        self.frame_main = tk.Frame(root)
        
        # === PHẦN 1: ĐẤU GIÁ (GAME) ===
        self.frame_auction = tk.LabelFrame(self.frame_main, text="Sàn Đấu Giá", font=("Arial", 10, "bold"), fg="red")
        self.frame_auction.pack(pady=5, padx=10, fill="x")

        self.lbl_timer = tk.Label(self.frame_auction, text="WAITING...", font=("Arial", 20, "bold"), fg="gray")
        self.lbl_timer.pack(pady=5)

        self.lbl_item_name = tk.Label(self.frame_auction, text="???", font=("Arial", 18, "bold"), fg="black")
        self.lbl_item_name.pack()
        
        self.lbl_current_price = tk.Label(self.frame_auction, text="Giá: $0", font=("Arial", 16, "bold"), fg="green")
        self.lbl_current_price.pack(pady=5)
        
        self.lbl_winner = tk.Label(self.frame_auction, text="Người giữ giá: ---", font=("Arial", 12), fg="blue")
        self.lbl_winner.pack(pady=5)

        frame_buttons = tk.Frame(self.frame_auction)
        frame_buttons.pack(pady=10)
        self.btn_10 = tk.Button(frame_buttons, text="+$10", bg="lightblue", width=8, command=lambda: self.bid(10))
        self.btn_10.pack(side=tk.LEFT, padx=5)
        self.btn_50 = tk.Button(frame_buttons, text="+$50", bg="orange", width=8, command=lambda: self.bid(50))
        self.btn_50.pack(side=tk.LEFT, padx=5)
        self.btn_100 = tk.Button(frame_buttons, text="+$100", bg="red", fg="white", width=8, command=lambda: self.bid(100))
        self.btn_100.pack(side=tk.LEFT, padx=5)

        # === PHẦN 2: CHAT ROOM (MỚI) ===
        self.frame_chat = tk.LabelFrame(self.frame_main, text="Phòng Chat", font=("Arial", 10, "bold"), fg="blue")
        self.frame_chat.pack(pady=5, padx=10, fill="both", expand=True)

        # Khung hiện tin nhắn
        self.listbox_chat = tk.Listbox(self.frame_chat, height=10)
        self.listbox_chat.pack(side=tk.TOP, fill="both", expand=True, padx=5, pady=5)
        
        # Thanh cuộn cho chat
        scrollbar = tk.Scrollbar(self.listbox_chat)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.listbox_chat.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox_chat.yview)

        # Khung nhập tin nhắn
        frame_chat_input = tk.Frame(self.frame_chat)
        frame_chat_input.pack(side=tk.BOTTOM, fill="x", padx=5, pady=5)
        
        self.entry_chat = tk.Entry(frame_chat_input)
        self.entry_chat.pack(side=tk.LEFT, fill="x", expand=True)
        self.entry_chat.bind('<Return>', lambda event: self.send_chat()) # Enter là gửi
        
        tk.Button(frame_chat_input, text="Gửi", command=self.send_chat).pack(side=tk.RIGHT, padx=5)

    def connect_to_server(self):
        name = self.entry_name.get()
        if not name: return messagebox.showwarning("Lỗi", "Nhập tên đi bro!")
        
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(("127.0.0.1", 5555))
            self.client_socket.send(name.encode('utf-8'))
            
            self.is_connected = True
            self.frame_login.pack_forget()
            self.frame_main.pack(fill="both", expand=True)
            self.root.title(f"Người chơi: {name}")
            
            threading.Thread(target=self.listen_server, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Server chưa mở!\n{e}")

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
            self.root.quit()

    def process_message(self, msg):
        if msg.startswith("START|"):
            parts = msg.split("|")
            self.lbl_item_name.config(text=parts[1])
            self.lbl_current_price.config(text=f"Giá: ${parts[2]}")
            self.lbl_winner.config(text="Người giữ giá: Chưa có")
            self.lbl_timer.config(text="30s", fg="blue")
            self.add_chat_log(f"--- BẮT ĐẦU: {parts[1]} ---")

        elif msg.startswith("UPDATE|"):
            parts = msg.split("|")
            self.lbl_current_price.config(text=f"Giá: ${parts[1]}")
            self.lbl_winner.config(text=f"Người giữ giá: {parts[2]}")
            self.add_chat_log(f"💰 {parts[2]} lên giá ${parts[1]}")

        elif msg.startswith("TIME|"):
            seconds = int(msg.split("|")[1])
            self.lbl_timer.config(text=f"{seconds}s")
            if seconds <= 5: self.lbl_timer.config(fg="red")

        elif msg.startswith("WIN|"):
            parts = msg.split("|")
            winner = parts[1]
            price = parts[2]
            self.lbl_timer.config(text="HẾT GIỜ", fg="purple")
            messagebox.showinfo("KẾT THÚC", f"{winner} win giá ${price}!")
            self.add_chat_log(f"🏆 {winner} VÔ ĐỊCH (${price})")

        # --- [MỚI] XỬ LÝ TIN NHẮN CHAT ---
        elif msg.startswith("CHAT|"):
            # CHAT|Tên|Nội dung
            parts = msg.split("|", 2) # Cắt tối đa 2 lần để tránh lỗi nếu nội dung có dấu |
            sender = parts[1]
            content = parts[2]
            self.add_chat_log(f"[{sender}]: {content}")

    def bid(self, amount):
        if self.client_socket:
            try:
                self.client_socket.send(f"BID|{amount}\n".encode('utf-8'))
            except: pass

    def send_chat(self):
        """Gửi tin nhắn chat"""
        msg = self.entry_chat.get()
        if msg and self.client_socket:
            try:
                # Gửi lệnh CHAT
                self.client_socket.send(f"CHAT|{msg}\n".encode('utf-8'))
                self.entry_chat.delete(0, tk.END) # Xóa ô nhập sau khi gửi
            except: pass

    def add_chat_log(self, msg):
        """Thêm dòng mới vào khung chat"""
        self.listbox_chat.insert(tk.END, msg)
        self.listbox_chat.yview(tk.END) # Tự cuộn xuống cuối

if __name__ == "__main__":
    root = tk.Tk()
    app = AuctionClientGUI(root)
    root.mainloop()