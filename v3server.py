import socket
import threading
import json
import time
from tkinter import *

HOST = "0.0.0.0"
PORT = 5000

AUTO_EXTEND_THRESHOLD = 5
AUTO_EXTEND_TIME = 10


class AuctionServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Auctioneer")

        self.server_socket = None
        self.clients = []

        self.auction_active = False
        self.paused = False
        self.lock = threading.Lock()

        self.current_highest_bid = 0
        self.highest_bidder = "None"
        self.time_remaining = 0

        self.build_ui()
        threading.Thread(target=self.start_server, daemon=True).start()

    def build_ui(self):

        Label(self.root, text="Item Name:").pack()
        self.item_entry = Entry(self.root)
        self.item_entry.pack()

        Label(self.root, text="Starting Price:").pack()
        self.price_entry = Entry(self.root)
        self.price_entry.pack()

        Label(self.root, text="Duration (seconds):").pack()
        self.duration_entry = Entry(self.root)
        self.duration_entry.pack()

        self.start_button = Button(self.root, text="Start Auction",
                                   command=self.start_auction)
        self.start_button.pack(pady=5)

        self.pause_button = Button(self.root, text="Pause",
                                   command=self.toggle_pause)
        self.pause_button.pack(pady=5)

        self.status_label = Label(self.root, text="Waiting...")
        self.status_label.pack(pady=5)

        self.bid_label = Label(self.root, text="Highest Bid: $0")
        self.bid_label.pack()

        self.timer_label = Label(self.root, text="Time Remaining: 0")
        self.timer_label.pack()

        Label(self.root, text="Bid History").pack()
        self.history_list = Listbox(self.root, width=40, height=8)
        self.history_list.pack(pady=5)

    # ---------------- SERVER ---------------- #

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()

        while True:
            client, addr = self.server_socket.accept()
            self.clients.append(client)
            threading.Thread(target=self.handle_client,
                             args=(client,), daemon=True).start()

    def handle_client(self, client):
        while True:
            try:
                data = client.recv(1024).decode()
                if not data:
                    break
                bid_data = json.loads(data)
                self.process_bid(bid_data)
            except:
                break

    # ---------------- AUCTION LOGIC ---------------- #

    def start_auction(self):
        try:
            self.item = self.item_entry.get()
            self.current_highest_bid = int(self.price_entry.get())
            self.time_remaining = int(self.duration_entry.get())
        except:
            self.status_label.config(text="Invalid input")
            return

        self.highest_bidder = "None"
        self.auction_active = True
        self.paused = False

        self.history_list.delete(0, END)
        self.status_label.config(text="Auction Running")

        self.update_ui()
        threading.Thread(target=self.timer_thread, daemon=True).start()

    def toggle_pause(self):
        if not self.auction_active:
            return

        self.paused = not self.paused

        if self.paused:
            self.status_label.config(text="Paused")
        else:
            self.status_label.config(text="Auction Running")

    def process_bid(self, bid_data):
        with self.lock:
            if not self.auction_active or self.paused:
                return

            name = bid_data["name"]
            amount = bid_data["bid"]

            if amount > self.current_highest_bid:
                self.current_highest_bid = amount
                self.highest_bidder = name

                # AUTO EXTEND
                if self.time_remaining <= AUTO_EXTEND_THRESHOLD:
                    self.time_remaining += AUTO_EXTEND_TIME

                self.root.after(0, self.update_ui)
                self.root.after(0, lambda:
                    self.history_list.insert(END, f"{name} bid ${amount}")
                )

                self.broadcast({
                    "type": "update",
                    "bidder": name,
                    "highest_bid": amount
                })

    def timer_thread(self):
        while self.time_remaining > 0 and self.auction_active:
            if not self.paused:
                time.sleep(1)
                self.time_remaining -= 1
                self.root.after(0, self.update_timer)
            else:
                time.sleep(0.2)

        if self.auction_active:
            self.end_auction()

    def end_auction(self):
        self.auction_active = False
        self.status_label.config(
            text=f"Auction Ended! Winner: {self.highest_bidder}"
        )

        self.broadcast({
            "type": "end",
            "winner": self.highest_bidder,
            "amount": self.current_highest_bid
        })

    # ---------------- UI HELPERS ---------------- #

    def update_ui(self):
        self.bid_label.config(
            text=f"Highest Bid: ${self.current_highest_bid} ({self.highest_bidder})"
        )

    def update_timer(self):
        self.timer_label.config(
            text=f"Time Remaining: {self.time_remaining}"
        )

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(json.dumps(message).encode())
            except:
                pass


if __name__ == "__main__":
    root = Tk()
    AuctionServerGUI(root)
    root.mainloop()