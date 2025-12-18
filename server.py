import tkinter as tk
from tkinter import messagebox
import socket
import threading
import time
import csv # [MỚI] Thư viện xử lý file CSV (Excel)
from datetime import datetime # [MỚI] Để lấy thời gian hiện tại

class AuctionServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SÀN ĐẤU GIÁ - ADMIN (SERVER)")
        self.root.geometry("500x650")

        # --- GIAO DIỆN (UI) ---
        self.label_title = tk.Label(root, text="QUẢN LÝ ĐẤU GIÁ", font=("Arial", 16, "bold"), fg="red")
        self.label_title.pack(pady=10)

        # Khu vực nhập liệu
        frame_input = tk.Frame(root)
        frame_input.pack(pady=5)
        
        tk.Label(frame_input, text="Tên vật phẩm:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_item = tk.Entry(frame_input, width=20)
        self.entry_item.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_input, text="Giá khởi điểm ($):").grid(row=1, column=0, padx=5, pady=5)
        self.entry_price = tk.Entry(frame_input, width=20)
        self.entry_price.grid(row=1, column=1, padx=5, pady=5)

        # Frame chứa các nút điều khiển
        frame_btns = tk.Frame(root)
        frame_btns.pack(pady=15)

        self.btn_start = tk.Button(frame_btns, text="MỞ PHIÊN (30s)", bg="green", fg="white", font=("Arial", 11, "bold"), command=self.start_auction)
        self.btn_start.pack(side=tk.LEFT, padx=10)

        # [MỚI] Nút xem lịch sử
        self.btn_history = tk.Button(frame_btns, text="XEM LỊCH SỬ", bg="orange", fg="white", font=("Arial", 11, "bold"), command=self.show_history)
        self.btn_history.pack(side=tk.LEFT, padx=10)

        # Khu vực Log
        tk.Label(root, text="Nhật ký hoạt động:").pack(anchor=tk.W, padx=10)
        self.log_area = tk.Text(root, height=15, width=55, state='disabled', bg="#f0f0f0")
        self.log_area.pack(pady=5)

        # --- LOGIC SERVER ---
        self.clients = []
        self.client_names = {}
        self.current_item = ""
        self.current_price = 0
        self.highest_bidder = "Chưa có"
        self.is_auction_active = False
        self.time_left = 30
        self.auction_lock = threading.Lock()

        # Tạo file history nếu chưa có (Ghi dòng tiêu đề)
        self.init_history_file()

        self.start_server_socket()

    def init_history_file(self):
        """Tạo file CSV nếu chưa tồn tại"""
        try:
            # Mode 'x' là tạo mới, nếu có rồi thì thôi
            with open("auction_history.csv", mode="x", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Thời gian", "Vật phẩm", "Người thắng", "Giá chốt ($)"])
        except FileExistsError:
            pass

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
            self.log(f"--> {name} đã tham gia.")

            if self.is_auction_active:
                client_socket.send(f"START|{self.current_item}|{self.current_price}\n".encode('utf-8'))
                client_socket.send(f"UPDATE|{self.current_price}|{self.highest_bidder}\n".encode('utf-8'))
                client_socket.send(f"TIME|{self.time_left}\n".encode('utf-8'))

            buffer = ""
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data: break
                buffer += data
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    
                    if message.startswith("BID|"):
                        self.process_bid(client_socket, message)
                    elif message.startswith("CHAT|"):
                        content = message.split("|", 1)[1]
                        self.broadcast(f"CHAT|{name}|{content}")
                        print(f"[CHAT] {name}: {content}")
        except:
            pass
        finally:
            self.remove_client(client_socket)

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            self.clients.remove(client_socket)
            name = self.client_names.get(client_socket, "Unknown")
            if client_socket in self.client_names:
                del self.client_names[client_socket]
            self.log(f"<-- {name} đã thoát.")
            client_socket.close()

    def process_bid(self, client_socket, msg):
        if not self.is_auction_active: return
        try:
            bid_amount = int(msg.split("|")[1])
            player_name = self.client_names[client_socket]
            with self.auction_lock:
                self.current_price += bid_amount
                self.highest_bidder = player_name
                print(f"$$ {player_name}: ${self.current_price}") 
                self.broadcast(f"UPDATE|{self.current_price}|{player_name}")
        except ValueError:
            pass

    def broadcast(self, message):
        dead_clients = []
        for client in self.clients:
            try:
                client.send(f"{message}\n".encode('utf-8'))
            except:
                dead_clients.append(client)
        for dead in dead_clients:
            self.remove_client(dead)

    def start_auction(self):
        item = self.entry_item.get()
        price_str = self.entry_price.get()
        if not item or not price_str: return
        with self.auction_lock:
            self.current_item = item
            self.current_price = int(price_str)
            self.highest_bidder = "Chưa có"
            self.is_auction_active = True
        self.log(f"=== BẮT ĐẦU: {item} - ${self.current_price} (30s) ===")
        self.broadcast(f"START|{self.current_item}|{self.current_price}")
        self.start_timer()

    def start_timer(self):
        self.time_left = 30
        threading.Thread(target=self.countdown, daemon=True).start()

    def countdown(self):
        while self.time_left > 0 and self.is_auction_active:
            time.sleep(1)
            self.time_left -= 1
            self.broadcast(f"TIME|{self.time_left}")
        if self.is_auction_active:
            self.end_auction()

    def end_auction(self):
        with self.auction_lock:
            self.is_auction_active = False
            msg = f"WIN|{self.highest_bidder}|{self.current_price}"
            self.broadcast(msg)
            self.log(f"!!! KẾT THÚC: {self.highest_bidder} thắng với ${self.current_price}")
            
            # [MỚI] Lưu vào lịch sử
            self.save_history(self.current_item, self.highest_bidder, self.current_price)

    # --- [MỚI] CÁC HÀM XỬ LÝ FILE ---
    def save_history(self, item, winner, price):
        """Ghi kết quả vào file CSV"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("auction_history.csv", mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                # Ghi dòng: Thời gian, Vật phẩm, Người thắng, Giá
                writer.writerow([timestamp, item, winner, price])
            print("Đã lưu lịch sử đấu giá.")
        except Exception as e:
            print(f"Lỗi lưu file: {e}")

    def show_history(self):
        """Hiện cửa sổ xem lịch sử"""
        # Tạo cửa sổ phụ (Popup)
        history_window = tk.Toplevel(self.root)
        history_window.title("Lịch Sử Đấu Giá")
        history_window.geometry("600x400")

        tk.Label(history_window, text="LỊCH SỬ CÁC PHIÊN ĐẤU GIÁ", font=("Arial", 14, "bold"), fg="blue").pack(pady=10)

        # Khung hiện nội dung (Scrollbar)
        text_area = tk.Text(history_window, height=15, width=70, font=("Consolas", 10))
        text_area.pack(pady=5, padx=10)

        # Đọc file và hiện lên
        try:
            with open("auction_history.csv", mode="r", encoding="utf-8") as file:
                reader = csv.reader(file)
                for row in reader:
                    # Định dạng dòng chữ cho đẹp
                    # row là list: ['2024-12-12 10:00', 'Iphone', 'Teo', '1000']
                    formatted_row = f"{row[0]} | {row[1]:<15} | {row[2]:<10} | ${row[3]}\n"
                    text_area.insert(tk.END, formatted_row)
        except FileNotFoundError:
            text_area.insert(tk.END, "Chưa có dữ liệu lịch sử nào.")
        
        text_area.config(state='disabled') # Không cho sửa
        
        btn_close = tk.Button(history_window, text="Đóng", command=history_window.destroy)
        btn_close.pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = AuctionServerGUI(root)
    root.mainloop()