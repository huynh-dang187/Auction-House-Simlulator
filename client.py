# FILE: client.py
import tkinter as tk
from tkinter import messagebox

class AuctionClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sàn Đấu Giá Online - Client")
        self.root.geometry("400x450")

        # --- MÀN HÌNH 1: ĐĂNG NHẬP ---
        self.frame_login = tk.Frame(root)
        tk.Label(self.frame_login, text="THAM GIA ĐẤU GIÁ", font=("Arial", 14, "bold")).pack(pady=30)
        tk.Label(self.frame_login, text="Nhập tên của bạn:").pack()
        
        self.entry_name = tk.Entry(self.frame_login, width=30)
        self.entry_name.pack(pady=10)
        self.entry_name.bind('<Return>', lambda event: self.connect_to_server()) # Bấm Enter là login luôn
        
        tk.Button(self.frame_login, text="VÀO PHÒNG", bg="blue", fg="white", font=("Arial", 10, "bold"), command=self.connect_to_server).pack(pady=10)
        self.frame_login.pack()

        # --- MÀN HÌNH 2: ĐẤU GIÁ (Mặc định ẩn) ---
        self.frame_auction = tk.Frame(root)
        
        # Thông tin món đồ
        self.lbl_status = tk.Label(self.frame_auction, text="Đang chờ Admin mở phiên...", font=("Arial", 12), fg="gray")
        self.lbl_status.pack(pady=10)
        
        self.lbl_item_name = tk.Label(self.frame_auction, text="???", font=("Arial", 20, "bold"), fg="red")
        self.lbl_item_name.pack(pady=5)
        
        self.lbl_current_price = tk.Label(self.frame_auction, text="Giá hiện tại: $0", font=("Arial", 16, "bold"), fg="green")
        self.lbl_current_price.pack(pady=10)

        # 3 Nút bấm đấu giá
        frame_buttons = tk.Frame(self.frame_auction)
        frame_buttons.pack(pady=15)
        
        self.btn_10 = tk.Button(frame_buttons, text="+$10", font=("Arial", 12), bg="lightblue", width=8, command=lambda: self.bid(10))
        self.btn_10.pack(side=tk.LEFT, padx=5)
        
        self.btn_50 = tk.Button(frame_buttons, text="+$50", font=("Arial", 12), bg="orange", width=8, command=lambda: self.bid(50))
        self.btn_50.pack(side=tk.LEFT, padx=5)
        
        self.btn_100 = tk.Button(frame_buttons, text="+$100", font=("Arial", 12), bg="red", fg="white", width=8, command=lambda: self.bid(100))
        self.btn_100.pack(side=tk.LEFT, padx=5)

        # Log đấu giá
        tk.Label(self.frame_auction, text="Diễn biến cuộc đua:").pack(anchor=tk.W, padx=10)
        self.listbox_log = tk.Listbox(self.frame_auction, height=8, width=50)
        self.listbox_log.pack(pady=5)

    def connect_to_server(self):
        """Xử lý khi bấm nút Vào Phòng"""
        name = self.entry_name.get()
        if not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên để vào phòng!")
            return
        
        # Chuyển cảnh
        self.frame_login.pack_forget()
        self.frame_auction.pack()
        self.root.title(f"Người chơi: {name}")
        self.log_message(f"--> Bạn ({name}) đã vào phòng chờ.")

    def bid(self, amount):
        """Xử lý khi bấm nút ra giá"""
        # TODO: Sau này sẽ gửi Socket ở đây
        self.log_message(f"Bạn vừa ra giá: +${amount}")

    def log_message(self, msg):
        self.listbox_log.insert(tk.END, msg)
        self.listbox_log.yview(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = AuctionClientGUI(root)
    root.mainloop()