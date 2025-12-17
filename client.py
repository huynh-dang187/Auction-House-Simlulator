# FILE: client.py
import tkinter as tk
from tkinter import messagebox
import socket
import threading

class AuctionClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sàn Đấu Giá Online - Client")
        self.root.geometry("400x500")
        
        self.client_socket = None
        self.is_connected = False

        # --- UI LOGIN ---
        self.frame_login = tk.Frame(root)
        tk.Label(self.frame_login, text="THAM GIA ĐẤU GIÁ", font=("Arial", 14, "bold")).pack(pady=30)
        tk.Label(self.frame_login, text="Nhập tên của bạn:").pack()
        self.entry_name = tk.Entry(self.frame_login, width=30)
        self.entry_name.pack(pady=10)
        self.entry_name.bind('<Return>', lambda event: self.connect_to_server())
        tk.Button(self.frame_login, text="VÀO PHÒNG", bg="blue", fg="white", command=self.connect_to_server).pack(pady=10)
        self.frame_login.pack()

        # --- UI ĐẤU GIÁ ---
        self.frame_auction = tk.Frame(root)
        self.lbl_status = tk.Label(self.frame_auction, text="Đang chờ Admin mở phiên...", font=("Arial", 12), fg="gray")
        self.lbl_status.pack(pady=10)
        
        self.lbl_item_name = tk.Label(self.frame_auction, text="???", font=("Arial", 20, "bold"), fg="red")
        self.lbl_item_name.pack(pady=5)
        
        self.lbl_current_price = tk.Label(self.frame_auction, text="Giá hiện tại: $0", font=("Arial", 18, "bold"), fg="green")
        self.lbl_current_price.pack(pady=10)
        
        self.lbl_winner = tk.Label(self.frame_auction, text="Người giữ giá: ---", font=("Arial", 12), fg="blue")
        self.lbl_winner.pack(pady=5)

        frame_buttons = tk.Frame(self.frame_auction)
        frame_buttons.pack(pady=15)
        self.btn_10 = tk.Button(frame_buttons, text="+$10", bg="lightblue", width=8, command=lambda: self.bid(10))
        self.btn_10.pack(side=tk.LEFT, padx=5)
        self.btn_50 = tk.Button(frame_buttons, text="+$50", bg="orange", width=8, command=lambda: self.bid(50))
        self.btn_50.pack(side=tk.LEFT, padx=5)
        self.btn_100 = tk.Button(frame_buttons, text="+$100", bg="red", fg="white", width=8, command=lambda: self.bid(100))
        self.btn_100.pack(side=tk.LEFT, padx=5)

        tk.Label(self.frame_auction, text="Diễn biến:").pack(anchor=tk.W, padx=10)
        self.listbox_log = tk.Listbox(self.frame_auction, height=8, width=50)
        self.listbox_log.pack(pady=5)

    def connect_to_server(self):
        name = self.entry_name.get()
        if not name: return messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên!")
        
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(("127.0.0.1", 5555))
            self.client_socket.send(name.encode('utf-8')) # Gửi tên đăng nhập
            
            self.is_connected = True
            
            # Chuyển màn hình
            self.frame_login.pack_forget()
            self.frame_auction.pack()
            self.root.title(f"Người chơi: {name}")
            
            # Bắt đầu luồng lắng nghe tin nhắn từ Server
            threading.Thread(target=self.listen_server, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không kết nối được Server!\n{e}")

    def listen_server(self):
        """Hàm chạy ngầm để nhận lệnh từ Server"""
        while self.is_connected:
            try:
                msg = self.client_socket.recv(1024).decode('utf-8')
                if not msg: break
                
                # Xử lý các lệnh nhận được
                if msg.startswith("START|"):
                    # START|Iphone|1000
                    parts = msg.split("|")
                    self.update_auction_ui(parts[1], parts[2], "Chưa có")
                    self.log_message(f"Admin bắt đầu đấu giá: {parts[1]}")
                    
                elif msg.startswith("UPDATE|"):
                    # UPDATE|1010|Tèo
                    parts = msg.split("|")
                    price = parts[1]
                    winner = parts[2]
                    self.lbl_current_price.config(text=f"Giá hiện tại: ${price}")
                    self.lbl_winner.config(text=f"Người giữ giá: {winner}")
                    self.log_message(f"{winner} vừa ra giá ${price}")
                    
            except:
                break

    def update_auction_ui(self, item, price, winner):
        self.lbl_item_name.config(text=item)
        self.lbl_current_price.config(text=f"Giá hiện tại: ${price}")
        self.lbl_winner.config(text=f"Người giữ giá: {winner}")
        self.lbl_status.config(text="ĐANG ĐẤU GIÁ...", fg="green")

    def bid(self, amount):
        """Gửi lệnh BID lên server"""
        if self.client_socket:
            try:
                # Protocol: BID|10
                self.client_socket.send(f"BID|{amount}\n".encode('utf-8'))
            except:
                self.log_message("Mất kết nối Server!")

    def log_message(self, msg):
        self.listbox_log.insert(tk.END, msg)
        self.listbox_log.yview(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = AuctionClientGUI(root)
    root.mainloop()