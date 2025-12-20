# BID WARS - HỆ THỐNG ĐẤU GIÁ REAL-TIME

**Nhóm thực hiện:** Nhóm 13(1 thành viên)-Huỳnh Nguyễn Đăng 
**Môn học:** Lập trình mạng

---

## TÍNH NĂNG NỔI BẬT
1.  **Đấu giá thời gian thực:** Cập nhật giá, người thắng và trừ tiền ngay lập tức (Real-time Economy).
2.  **Anti-Sniping (Chống cướp giờ):** Tự động cộng thêm 10s nếu có người Bid vào 5s cuối.
3.  **Truyền tải hình ảnh:** Server gửi ảnh sản phẩm trực tiếp xuống Client qua Socket.
4.  **Túi đồ (Inventory):** Lưu vật phẩm đã thắng vào Database để xem lại.
5.  **Trải nghiệm:** Giao diện Dark Mode, có âm thanh tương tác (Bid, Win, Tick-tock).

---

## HƯỚNG DẪN CÀI ĐẶT & CHẠY

### Cách 1: Chạy ngay (Khuyên dùng)
*Không cần cài Python, chỉ cần chạy file .exe*

1.  Vào thư mục **`Application`**.
2.  Chạy file **`Auction_Server.exe`** (Để khởi động máy chủ).
3.  Chạy file **`Auction_Client.exe`** (Chạy nhiều lần để mở nhiều người chơi).

**⚠️ Lưu ý quan trọng:** Tuyệt đối không di chuyển file `.exe` ra khỏi thư mục chứa `assets`, `sounds` và `config.ini`.

### Cách 2: Chạy bằng Source Code
*Yêu cầu đã cài Python*

1.  Cài thư viện: `pip install customtkinter pillow`
2.  Chạy Server: `python server.py`
3.  Chạy Client: `python client.py`