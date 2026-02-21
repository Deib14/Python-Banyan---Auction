import socket
import threading
import json
import time
from tkinter import *

HOST = '0.0.0.0'
PORT = 5000

class AuctionServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Auction Server")

        self.item_name = "Gaming Laptop"
        self.current_highest_bid = 100
        self.highest_bidder = "None"
        self.duration = 30
        self.auction_active = True

        self.clients = []
        self.lock = threading.Lock()

        self.build_ui()
        threading.Thread(target=self.start_server, daemon=True).start()
        threading.Thread(target=self.auction_timer, daemon=True).start()

    def build_ui(self):
        Label(self.root, text=f"Item: {self.item_name}", font=("Arial", 16)).pack(pady=5)

        self.bid_label = Label(self.root, text=f"Highest Bid: ${self.current_highest_bid}", font=("Arial", 14))
        self.bid_label.pack()

        self.bidder_label = Label(self.root, text="Highest Bidder: None", font=("Arial", 12))
        self.bidder_label.pack()

        self.timer_label = Label(self.root, text=f"Time Remaining: {self.duration}s", font=("Arial", 12))
        self.timer_label.pack(pady=5)

        self.status_label = Label(self.root, text="Auction Running", fg="green")
        self.status_label.pack()

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORT))
        server.listen()
        print("Server listening...")

        while self.auction_active:
            client, addr = server.accept()
            print(f"Connected: {addr}")
            self.clients.append(client)
            threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()

    def handle_client(self, client):
        while self.auction_active:
            try:
                data = client.recv(1024).decode()
                if not data:
                    break

                bid_data = json.loads(data)
                self.process_bid(bid_data)

            except:
                break
        client.close()

    def process_bid(self, bid_data):
        with self.lock:
            name = bid_data["name"]
            amount = bid_data["bid"]

            if amount > self.current_highest_bid and self.auction_active:
                self.current_highest_bid = amount
                self.highest_bidder = name

                self.root.after(0, self.update_ui)

                self.broadcast({
                    "type": "update",
                    "highest_bid": amount,
                    "bidder": name
                })

    def update_ui(self):
        self.bid_label.config(text=f"Highest Bid: ${self.current_highest_bid}")
        self.bidder_label.config(text=f"Highest Bidder: {self.highest_bidder}")

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(json.dumps(message).encode())
            except:
                pass

    def auction_timer(self):
        for remaining in range(self.duration, 0, -1):
            time.sleep(1)
            self.root.after(0, lambda r=remaining: self.timer_label.config(text=f"Time Remaining: {r}s"))

        self.auction_active = False
        self.root.after(0, self.end_auction)

    def end_auction(self):
        self.status_label.config(text="Auction Ended", fg="red")

        self.broadcast({
            "type": "end",
            "winner": self.highest_bidder,
            "amount": self.current_highest_bid
        })

if __name__ == "__main__":
    root = Tk()
    AuctionServerGUI(root)
    root.mainloop()