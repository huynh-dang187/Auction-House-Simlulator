# FILE: server.py
import tkinter as tk
from tkinter import messagebox

class AuctionServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SÀN ĐẤU GIÁ - ADMIN (SERVER)")
        self.root.geometry("400x350")

        # --- UI COMPONENTS ---
        # 1. Tiêu đề
        self.label_title = tk.Label(root, text="QUẢN LÝ ĐẤU GIÁ", font=("Arial", 16, "bold"), fg="red")
        self.label_title.pack(pady=10)

        # 2. Nhập tên vật phẩm
        frame_item = tk.Frame(root)
        frame_item.pack(pady=5)
        tk.Label(frame_item, text="Tên vật phẩm:").pack(side=tk.LEFT)
        self.entry_item = tk.Entry(frame_item, width=25)
        self.entry_item.pack(side=tk.LEFT, padx=5)

        # 3. Nhập giá khởi điểm
        frame_price = tk.Frame(root)
        frame_price.pack(pady=5)
        tk.Label(frame_price, text="Giá khởi điểm ($):").pack(side=tk.LEFT)
        self.entry_price = tk.Entry(frame_price, width=25)
        self.entry_price.pack(side=tk.LEFT, padx=5)

        # 4. Nút Start
        self.btn_start = tk.Button(root, text="MỞ PHIÊN ĐẤU GIÁ", bg="green", fg="white", font=("Arial", 11, "bold"), command=self.start_auction)
        self.btn_start.pack(pady=15)

        # 5. Log hiển thị trạng thái
        tk.Label(root, text="Nhật ký hoạt động:").pack(anchor=tk.W, padx=10)
        self.log_area = tk.Text(root, height=8, width=45, state='disabled', bg="#f0f0f0")
        self.log_area.pack(pady=5)
        
        self.log("Server đã khởi tạo giao diện admin.")

    def log(self, message):
        """Hàm ghi log vào khung text"""
        self.log_area.config(state='normal') # Mở khóa để ghi
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END) # Tự cuộn xuống dưới cùng
        self.log_area.config(state='disabled') # Khóa lại không cho xóa

    def start_auction(self):
        """Xử lý nút Bắt đầu"""
        item = self.entry_item.get()
        price = self.entry_price.get()
        
        if not item or not price:
            messagebox.showerror("Thiếu thông tin", "Vui lòng nhập tên món đồ và giá!")
            return
            
        if not price.isdigit():
            messagebox.showerror("Lỗi giá", "Giá tiền phải là số nguyên!")
            return

        self.log(f"--> [BẮT ĐẦU] Vật phẩm: {item} | Giá: ${price}")
        # TODO: Sau này sẽ thêm code Socket gửi cho Client ở đây

if __name__ == "__main__":
    root = tk.Tk()
    app = AuctionServerGUI(root)
    root.mainloop()