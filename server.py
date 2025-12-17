# FILE: server.py
import tkinter as tk
from tkinter import messagebox
import socket
import threading

class AuctionServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SÀN ĐẤU GIÁ - ADMIN (SERVER)")
        self.root.geometry("450x500") # Cao hơn chút để hiện log

        # --- UI (Giữ nguyên) ---
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
        self.log_area = tk.Text(root, height=15, width=50, state='disabled', bg="#f0f0f0")
        self.log_area.pack(pady=5)

        # --- LOGIC MẠNG & GAME ---
        self.clients = []
        self.client_names = {}
        
        self.current_item = ""
        self.current_price = 0
        self.highest_bidder = "Chưa có"
        self.is_auction_active = False
        
        # --- [NEW] KHÓA AN TOÀN ---
        self.auction_lock = threading.Lock() # Tạo cái khóa

        self.start_server_socket()

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def start_server_socket(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(("0.0.0.0", 5555))
            self.server_socket.listen(5)
            self.log("Server đang lắng nghe tại port 5555...")
            threading.Thread(target=self.receive_clients, daemon=True).start()
        except Exception as e:
            self.log(f"Lỗi Server: {e}")

    def receive_clients(self):
        while True:
            try:
                client_socket, client_addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except:
                break

    def handle_client(self, client_socket):
        try:
            name = client_socket.recv(1024).decode('utf-8')
            self.clients.append(client_socket)
            self.client_names[client_socket] = name
            
            self.log(f"--> {name} đã tham gia phòng.")
            
            if self.is_auction_active:
                client_socket.send(f"START|{self.current_item}|{self.current_price}".encode('utf-8'))

            # --- [LOGIC MỚI] XỬ LÝ DÍNH GÓI TIN ---
            buffer = ""
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data: break
                
                buffer += data # Cộng dồn dữ liệu mới vào bộ đệm
                
                # Cứ hễ thấy dấu xuống dòng là cắt ra xử lý
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1) # Cắt 1 phát
                    
                    if message and message.startswith("BID|"):
                        self.process_bid(client_socket, message)
            # --------------------------------------

        except:
            pass
        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
                name = self.client_names.get(client_socket, "Unknown")
                del self.client_names[client_socket]
                self.log(f"<-- {name} đã thoát.")
                client_socket.close()

    def process_bid(self, client_socket, msg):
        if not self.is_auction_active: return

        try:
            bid_amount = int(msg.split("|")[1])
            player_name = self.client_names[client_socket]

            # --- [NEW] ĐOẠN NÀY QUAN TRỌNG NHẤT ---
            # Bắt đầu khóa biến current_price lại
            with self.auction_lock: 
                self.current_price += bid_amount
                self.highest_bidder = player_name
                
                self.log(f"$$ {player_name} trả thêm ${bid_amount}. Giá mới: ${self.current_price}")

                # Broadcast luôn trong lúc khóa để đảm bảo đồng bộ
                update_msg = f"UPDATE|{self.current_price}|{player_name}"
                self.broadcast(update_msg)
            # Ra khỏi with -> Tự động mở khóa cho người khác vào
            # --------------------------------------

        except ValueError:
            pass

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(message.encode('utf-8'))
            except:
                pass

    def start_auction(self):
        item = self.entry_item.get()
        price_str = self.entry_price.get()
        
        if not item or not price_str: return
        
        # Cũng nên khóa lúc reset game cho chắc
        with self.auction_lock:
            self.current_item = item
            self.current_price = int(price_str)
            self.highest_bidder = "Chưa có"
            self.is_auction_active = True
        
        self.log(f"=== BẮT ĐẦU: {item} - ${self.current_price} ===")
        msg = f"START|{self.current_item}|{self.current_price}"
        self.broadcast(msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = AuctionServerGUI(root)
    root.mainloop()