#  BID WARS - REAL-TIME AUCTION SYSTEM

**Team:** Group 13
**Course:** Network Programming

---

##  KEY FEATURES
1.  **Real-time Bidding:** Instant updates on price, winner, and wallet balance (Real-time Economy).
2.  **Anti-Sniping Mechanism:** Automatically extends time by 10s if a bid is placed in the last 5s.
3.  **Live Image Streaming:** Server streams product images directly to Clients via Socket (Base64).
4.  **Inventory System:** Winners receive items in their personal inventory (saved in SQLite DB).
5.  **Immersive Experience:** Dark Mode UI with interactive Sound Effects (Bid, Win, Tick-tock).

---

##  INSTALLATION & USAGE

### Option 1: Run Executable (Recommended)
*No Python installation required.*

1.  Go to the **`Application`** folder.
2.  Run **`Auction_Server.exe`** to start the host.
3.  Run **`Auction_Client.exe`** (Open multiple instances to simulate players).

**⚠️ Important:** Do not move the `.exe` files out of the folder containing `assets`, `sounds`, and `config.ini`.

### Option 2: Run from Source
*Requires Python installed.*

1.  Install dependencies: `pip install customtkinter pillow`
2.  Start Server: `python server.py`
3.  Start Client: `python client.py`

---

## 📂 PROJECT STRUCTURE
Nhom13_Auction_System/             
│
├── README.md                       <-- Project documentation and setup guide
│
├── Application/                    <-- Ready-to-run version (No Python required)
│   │
│   ├── Auction_Server.exe          <-- Server executable (Run this FIRST)
│   ├── Auction_Client.exe          <-- Client executable (Run this SECOND)
│   │
│   ├── config.ini                  <-- Network configuration file (Critical for connection)
│   │
│   ├── assets/                     <-- Contains product images (Required for display)
│   │   ├── iphone.png
│   │   └── ...
│   │
│   └── sounds/                     <-- Contains sound effects (Required for audio)
│       ├── bid.wav
│       ├── tick.wav
│       └── win.wav
│
└── Source_Code/                    <-- Original Python scripts (For teacher/dev review)
    │
    ├── server.py                   <-- Server logic and socket handling
    ├── client.py                   <-- Client GUI and interaction logic
    ├── database.py                 <-- SQLite database manager
    ├── config.ini                  <-- Configuration file for source code
    ├── assets/                     <-- Source copy of images
    └── sounds/                     <-- Source copy of audio files
