import socket
import threading
import tkinter as tk
from tkinter import ttk

PORT = 5000

class AuctionClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Auction Client")
        self.root.geometry("900x600")
        self.root.configure(bg="#1e1e1e")

        self.current_bid = 0
        self.build_connect_ui()

    # -------- CONNECT UI --------
    def build_connect_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        ttk.Label(self.root, text="Connect to Auction",
                  font=("Segoe UI", 18)).pack(pady=20)

        self.name_entry = ttk.Entry(self.root)
        self.name_entry.pack(pady=5)
        self.name_entry.insert(0, "Your Name")

        self.ip_entry = ttk.Entry(self.root)
        self.ip_entry.pack(pady=5)
        self.ip_entry.insert(0, "127.0.0.1")

        ttk.Button(self.root, text="Connect",
                   command=self.connect).pack(pady=10)

    # -------- MAIN UI --------
    def build_main_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        ttk.Label(self.root, text="LIVE AUCTION",
                  font=("Segoe UI", 18)).pack(pady=10)

        self.item_label = ttk.Label(self.root, text="Current Item: None")
        self.item_label.pack()

        self.timer_label = ttk.Label(self.root, text="Time Remaining: 0")
        self.timer_label.pack()

        self.bid_label = ttk.Label(self.root, text="Highest Bid: 0")
        self.bid_label.pack(pady=10)

        self.history = tk.Text(self.root, height=15,
                               width=80, bg="#ffffff",
                               fg="black")
        self.history.pack(pady=10)

        self.bid_entry = ttk.Entry(self.root)
        self.bid_entry.pack(pady=5)

        ttk.Button(self.root, text="Place Bid",
                   command=self.place_bid).pack(pady=5)

    # -------- NETWORK --------
    def connect(self):
        self.name = self.name_entry.get()
        ip = self.ip_entry.get()

        self.client = socket.socket(socket.AF_INET,
                                    socket.SOCK_STREAM)
        self.client.connect((ip, PORT))

        threading.Thread(target=self.receive,
                         daemon=True).start()

        self.build_main_ui()

    def receive(self):
        while True:
            try:
                msg = self.client.recv(1024).decode()

                if msg.startswith("ITEM"):
                    _, item = msg.split("|")
                    self.item_label.config(
                        text=f"Current Item: {item}")
                    self.history.insert(tk.END,
                                        f"\nNew Item: {item}\n")

                elif msg.startswith("TIME"):
                    _, time_left = msg.split("|")
                    self.timer_label.config(
                        text=f"Time Remaining: {time_left}")

                elif msg.startswith("BIDUPDATE"):
                    _, name, amount = msg.split("|")
                    self.current_bid = int(amount)
                    self.bid_label.config(
                        text=f"Highest Bid: {amount} ({name})")
                    self.history.insert(tk.END,
                                        f"{name} bid {amount}\n")

                elif msg.startswith("END"):
                    self.history.insert(tk.END,
                                        "\nAuction Ended\n")

            except:
                break

    def place_bid(self):
        try:
            amount = int(self.bid_entry.get())
            if amount >= self.current_bid + 100:
                self.client.send(
                    f"BID|{self.name}|{amount}".encode())
            else:
                self.history.insert(tk.END,
                                    "Bid must be +100 higher\n")
        except:
            pass


root = tk.Tk()
app = AuctionClient(root)
root.mainloop()