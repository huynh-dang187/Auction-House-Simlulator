import tkinter as tk
from tkinter import messagebox
import socket
import threading

class AuctionClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sàn Đấu Giá Online - Client")
        self.root.geometry("400x550")
        
        self.client_socket = None
        self.is_connected = False

        # --- MÀN HÌNH 1: LOGIN ---
        self.frame_login = tk.Frame(root)
        tk.Label(self.frame_login, text="THAM GIA ĐẤU GIÁ", font=("Arial", 14, "bold")).pack(pady=30)
        tk.Label(self.frame_login, text="Nhập tên của bạn:").pack()
        self.entry_name = tk.Entry(self.frame_login, width=30)
        self.entry_name.pack(pady=10)
        self.entry_name.bind('<Return>', lambda event: self.connect_to_server())
        tk.Button(self.frame_login, text="VÀO PHÒNG", bg="blue", fg="white", command=self.connect_to_server).pack(pady=10)
        self.frame_login.pack()

        # --- MÀN HÌNH 2: ĐẤU GIÁ (Mặc định ẩn) ---
        self.frame_auction = tk.Frame(root)
        
        # 1. Đồng hồ đếm ngược (MỚI)
        self.lbl_timer = tk.Label(self.frame_auction, text="WAITING...", font=("Arial", 20, "bold"), fg="gray")
        self.lbl_timer.pack(pady=5)

        # 2. Thông tin món đồ
        self.lbl_item_name = tk.Label(self.frame_auction, text="???", font=("Arial", 18, "bold"), fg="red")
        self.lbl_item_name.pack(pady=5)
        
        self.lbl_current_price = tk.Label(self.frame_auction, text="Giá: $0", font=("Arial", 16, "bold"), fg="green")
        self.lbl_current_price.pack(pady=5)
        
        self.lbl_winner = tk.Label(self.frame_auction, text="Người giữ giá: ---", font=("Arial", 12), fg="blue")
        self.lbl_winner.pack(pady=5)

        # 3. Nút bấm
        frame_buttons = tk.Frame(self.frame_auction)
        frame_buttons.pack(pady=15)
        
        self.btn_10 = tk.Button(frame_buttons, text="+$10", bg="lightblue", width=8, command=lambda: self.bid(10))
        self.btn_10.pack(side=tk.LEFT, padx=5)
        self.btn_50 = tk.Button(frame_buttons, text="+$50", bg="orange", width=8, command=lambda: self.bid(50))
        self.btn_50.pack(side=tk.LEFT, padx=5)
        self.btn_100 = tk.Button(frame_buttons, text="+$100", bg="red", fg="white", width=8, command=lambda: self.bid(100))
        self.btn_100.pack(side=tk.LEFT, padx=5)

        # 4. Log
        tk.Label(self.frame_auction, text="Diễn biến:").pack(anchor=tk.W, padx=10)
        self.listbox_log = tk.Listbox(self.frame_auction, height=10, width=50)
        self.listbox_log.pack(pady=5)

    def connect_to_server(self):
        name = self.entry_name.get()
        if not name: return messagebox.showwarning("Lỗi", "Vui lòng nhập tên!")
        
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(("127.0.0.1", 5555))
            self.client_socket.send(name.encode('utf-8')) # Gửi tên
            
            self.is_connected = True
            
            # Chuyển màn hình
            self.frame_login.pack_forget()
            self.frame_auction.pack()
            self.root.title(f"Người chơi: {name}")
            
            threading.Thread(target=self.listen_server, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tìm thấy Server!\n{e}")

    def listen_server(self):
        """Lắng nghe dữ liệu từ Server (Có xử lý buffer)"""
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
        
        # Nếu thoát vòng lặp -> Mất kết nối
        if self.is_connected: # Chỉ báo lỗi nếu chưa chủ động tắt
            messagebox.showerror("Ngắt kết nối", "Server đã đóng!")
            self.root.quit()

    def process_message(self, msg):
        """Xử lý từng lệnh đơn lẻ"""
        if msg.startswith("START|"):
            # START|Tên|Giá
            parts = msg.split("|")
            self.lbl_item_name.config(text=parts[1])
            self.lbl_current_price.config(text=f"Giá: ${parts[2]}")
            self.lbl_winner.config(text="Người giữ giá: Chưa có")
            self.lbl_timer.config(text="30s", fg="blue")
            self.log_message(f"--> BẮT ĐẦU: {parts[1]}")

        elif msg.startswith("UPDATE|"):
            # UPDATE|Giá|Tên
            parts = msg.split("|")
            self.lbl_current_price.config(text=f"Giá: ${parts[1]}")
            self.lbl_winner.config(text=f"Người giữ giá: {parts[2]}")
            self.log_message(f"{parts[2]} trả ${parts[1]}")

        elif msg.startswith("TIME|"):
            # TIME|29
            seconds = int(msg.split("|")[1])
            self.lbl_timer.config(text=f"{seconds}s")
            if seconds <= 5:
                self.lbl_timer.config(fg="red")

        elif msg.startswith("WIN|"):
            # WIN|Tên|Giá
            parts = msg.split("|")
            winner = parts[1]
            price = parts[2]
            self.lbl_timer.config(text="HẾT GIỜ", fg="purple")
            messagebox.showinfo("KẾT THÚC", f"Chúc mừng {winner} thắng với giá ${price}!")
            self.log_message(f"=== {winner} THẮNG CUỘC ===")

    def bid(self, amount):
        if self.client_socket:
            try:
                # Gửi lệnh có \n
                self.client_socket.send(f"BID|{amount}\n".encode('utf-8'))
            except:
                self.log_message("Lỗi gửi tin!")

    def log_message(self, msg):
        self.listbox_log.insert(tk.END, msg)
        self.listbox_log.yview(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = AuctionClientGUI(root)
    root.mainloop()