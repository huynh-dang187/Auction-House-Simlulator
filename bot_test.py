# FILE: bot_test.py
import socket
import threading
import time

def run_bot(bot_name, times):
    try:
        # 1. Kết nối
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 5555))
        
        # 2. Đăng nhập
        s.send(bot_name.encode('utf-8'))
        
        # Chờ xíu cho server xử lý login
        time.sleep(0.5) 
        
        print(f"🤖 {bot_name} bắt đầu spam {times} lần...")
        
        # 3. SPAM LIÊN TỤC
        for i in range(times):
            s.send(b"BID|10 \n")
            # Nghỉ cực ngắn để tránh dính gói tin (TCP Stream) 
            # nhưng vẫn đủ nhanh để gây áp lực cho Server
            time.sleep(0.01) 
            
        print(f"✅ {bot_name} đã spam xong!")
        s.close()
        
    except Exception as e:
        print(f"Bot lỗi: {e}")

if __name__ == "__main__":
    # Chạy 3 con Bot cùng lúc, mỗi con spam 100 phát
    # Tổng cộng Server phải xử lý 300 lệnh cộng tiền gần như cùng lúc
    t1 = threading.Thread(target=run_bot, args=("Bot_A", 100))
    t2 = threading.Thread(target=run_bot, args=("Bot_B", 100))
    t3 = threading.Thread(target=run_bot, args=("Bot_C", 100))

    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()
    print("=== TẤT CẢ BOT ĐÃ HOÀN THÀNH ===")