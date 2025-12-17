# FILE: client.py
import tkinter as tk
from tkinter import messagebox
import socket
import threading

class AuctionClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sàn Đấu Giá Online - Client")
        self.root.geometry("400x450")
        
        self.client_socket = None # Biến để lưu kết nối mạng

        # --- UI LOGIN (Giữ nguyên) ---
        self.frame_login = tk.Frame(root)
        tk.Label(self.frame_login, text="THAM GIA ĐẤU GIÁ", font=("Arial", 14, "bold")).pack(pady=30)
        tk.Label(self.frame_login, text="Nhập tên của bạn:").pack()
        self.entry_name = tk.Entry(self.frame_login, width=30)
        self.entry_name.pack(pady=10)
        self.entry_name.bind('<Return>', lambda event: self.connect_to_server())
        tk.Button(self.frame_login, text="VÀO PHÒNG", bg="blue", fg="white", command=self.connect_to_server).pack(pady=10)
        self.frame_login.pack()

        # --- UI ĐẤU GIÁ (Giữ nguyên) ---
        self.frame_auction = tk.Frame(root)
        self.lbl_status = tk.Label(self.frame_auction, text="Đang chờ Admin mở phiên...", font=("Arial", 12), fg="gray")
        self.lbl_status.pack(pady=10)
        self.lbl_item_name = tk.Label(self.frame_auction, text="???", font=("Arial", 20, "bold"), fg="red")
        self.lbl_item_name.pack(pady=5)
        self.lbl_current_price = tk.Label(self.frame_auction, text="Giá hiện tại: $0", font=("Arial", 16, "bold"), fg="green")
        self.lbl_current_price.pack(pady=10)

        frame_buttons = tk.Frame(self.frame_auction)
        frame_buttons.pack(pady=15)
        self.btn_10 = tk.Button(frame_buttons, text="+$10", bg="lightblue", width=8, command=lambda: self.bid(10))
        self.btn_10.pack(side=tk.LEFT, padx=5)
        self.btn_50 = tk.Button(frame_buttons, text="+$50", bg="orange", width=8, command=lambda: self.bid(50))
        self.btn_50.pack(side=tk.LEFT, padx=5)
        self.btn_100 = tk.Button(frame_buttons, text="+$100", bg="red", fg="white", width=8, command=lambda: self.bid(100))
        self.btn_100.pack(side=tk.LEFT, padx=5)

        tk.Label(self.frame_auction, text="Diễn biến cuộc đua:").pack(anchor=tk.W, padx=10)
        self.listbox_log = tk.Listbox(self.frame_auction, height=8, width=50)
        self.listbox_log.pack(pady=5)

    def connect_to_server(self):
        name = self.entry_name.get()
        if not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên!")
            return
        
        # --- KẾT NỐI SOCKET (NEW) ---
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(("127.0.0.1", 5555)) # Kết nối tới Server Localhost
            
            # Gửi tên cho Server (Login Protocol đơn giản)
            # Encode sang bytes để gửi qua mạng
            self.client_socket.send(name.encode('utf-8')) 

            # Nếu kết nối OK thì chuyển cảnh
            self.frame_login.pack_forget()
            self.frame_auction.pack()
            self.root.title(f"Người chơi: {name}")
            self.log_message(f"--> Đã kết nối tới Server thành công!")

        except Exception as e:
            messagebox.showerror("Lỗi kết nối", f"Không tìm thấy Server!\n{e}")

    def bid(self, amount):
        # Ngày mai sẽ code gửi tiền
        self.log_message(f"Bạn chọn giá: +${amount} (Chưa gửi mạng)")

    def log_message(self, msg):
        self.listbox_log.insert(tk.END, msg)
        self.listbox_log.yview(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = AuctionClientGUI(root)
    root.mainloop()