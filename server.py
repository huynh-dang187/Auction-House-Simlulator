# FILE: server.py
import tkinter as tk
from tkinter import messagebox
import socket
import threading

class AuctionServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SÀN ĐẤU GIÁ - ADMIN (SERVER)")
        self.root.geometry("400x400")

        # --- UI COMPONENTS (Giữ nguyên như cũ) ---
        self.label_title = tk.Label(root, text="QUẢN LÝ ĐẤU GIÁ", font=("Arial", 16, "bold"), fg="red")
        self.label_title.pack(pady=10)

        frame_item = tk.Frame(root)
        frame_item.pack(pady=5)
        tk.Label(frame_item, text="Tên vật phẩm:").pack(side=tk.LEFT)
        self.entry_item = tk.Entry(frame_item, width=25)
        self.entry_item.pack(side=tk.LEFT, padx=5)

        frame_price = tk.Frame(root)
        frame_price.pack(pady=5)
        tk.Label(frame_price, text="Giá khởi điểm ($):").pack(side=tk.LEFT)
        self.entry_price = tk.Entry(frame_price, width=25)
        self.entry_price.pack(side=tk.LEFT, padx=5)

        self.btn_start = tk.Button(root, text="MỞ PHIÊN ĐẤU GIÁ", bg="green", fg="white", font=("Arial", 11, "bold"), command=self.start_auction)
        self.btn_start.pack(pady=15)

        tk.Label(root, text="Nhật ký hoạt động:").pack(anchor=tk.W, padx=10)
        self.log_area = tk.Text(root, height=10, width=45, state='disabled', bg="#f0f0f0")
        self.log_area.pack(pady=5)

        # --- PHẦN MẠNG (NEW) ---
        self.clients = [] # Danh sách lưu các client kết nối
        self.start_server_socket()

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def start_server_socket(self):
        """Khởi tạo Socket server chạy ngầm"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(("0.0.0.0", 5555)) # Mở cổng 5555
            self.server_socket.listen(5) # Cho phép tối đa 5 người đợi
            self.log("Server đang lắng nghe tại port 5555...")
            
            # QUAN TRỌNG: Chạy vòng lặp chờ kết nối ở một LUỒNG KHÁC (Thread)
            # Nếu không dùng Thread, giao diện sẽ bị treo cứng tại dòng accept()
            receive_thread = threading.Thread(target=self.receive_clients)
            receive_thread.daemon = True # Tắt thread khi tắt app chính
            receive_thread.start()
            
        except Exception as e:
            self.log(f"Lỗi khởi tạo Server: {e}")

    def receive_clients(self):
        """Hàm chạy ngầm để đón khách"""
        while True:
            try:
                # Chờ client kết nối (Blocking)
                client_socket, client_addr = self.server_socket.accept()
                
                # Khi có người vào:
                self.clients.append(client_socket)
                self.log(f"--> Có kết nối mới từ: {client_addr}")
                
                # (Ngày mai sẽ thêm phần lắng nghe tin nhắn của Client này ở đây)
                
            except Exception as e:
                print("Lỗi nhận client:", e)
                break

    def start_auction(self):
        item = self.entry_item.get()
        price = self.entry_price.get()
        if not item or not price: return
        self.log(f"--> [BẮT ĐẦU] {item} - ${price}")
        # (Ngày mai sẽ code gửi tin nhắn cho Client ở đây)

if __name__ == "__main__":
    root = tk.Tk()
    app = AuctionServerGUI(root)
    root.mainloop()