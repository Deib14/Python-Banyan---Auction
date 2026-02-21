import socket
import threading
import json
import time
from tkinter import *
from tkinter import ttk

HOST = "0.0.0.0"
PORT = 5000

AUTO_EXTEND_THRESHOLD = 5
AUTO_EXTEND_TIME = 10


class AuctionServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Auction Server")
        self.root.geometry("500x600")
        self.root.configure(bg="#1e1e1e")

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

    # ---------------- UI ---------------- #

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        Label(self.root, text="Auction Server", font=("Arial", 20, "bold"),
              fg="white", bg="#1e1e1e").pack(pady=10)

        # Item Input
        self.item_entry = self.create_entry("Item Name")
        self.price_entry = self.create_entry("Starting Price")
        self.duration_entry = self.create_entry("Duration (seconds)")

        self.start_btn = self.create_button("Start Auction", self.start_auction)
        self.pause_btn = self.create_button("Pause", self.toggle_pause)

        self.status_label = Label(self.root, text="Waiting...",
                                  fg="yellow", bg="#1e1e1e", font=("Arial", 12))
        self.status_label.pack(pady=5)

        self.bid_label = Label(self.root, text="Highest Bid: $0",
                               fg="cyan", bg="#1e1e1e", font=("Arial", 14))
        self.bid_label.pack()

        self.timer_label = Label(self.root, text="Time: 0",
                                 fg="white", bg="#1e1e1e", font=("Arial", 12))
        self.timer_label.pack(pady=5)

        Label(self.root, text="Bid History",
              fg="white", bg="#1e1e1e").pack(pady=5)

        self.history = Listbox(self.root, width=50, height=10,
                               bg="#2e2e2e", fg="white")
        self.history.pack(pady=5)

    def create_entry(self, placeholder):
        entry = Entry(self.root, width=30)
        entry.insert(0, placeholder)
        entry.pack(pady=5)
        return entry

    def create_button(self, text, command):
        btn = Button(self.root, text=text, width=20,
                     bg="#3a3a3a", fg="white",
                     activebackground="#555555",
                     command=command)
        btn.pack(pady=5)
        return btn

    # ---------------- Server ---------------- #

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

    # ---------------- Auction Logic ---------------- #

    def start_auction(self):
        try:
            self.item = self.item_entry.get()
            self.current_highest_bid = int(self.price_entry.get())
            self.time_remaining = int(self.duration_entry.get())
        except:
            self.status_label.config(text="Invalid Input", fg="red")
            return

        self.highest_bidder = "None"
        self.auction_active = True
        self.paused = False

        self.history.delete(0, END)
        self.status_label.config(text=f"Auction Running: {self.item}",
                                 fg="green")

        self.update_ui()

        threading.Thread(target=self.timer_thread, daemon=True).start()

    def toggle_pause(self):
        if not self.auction_active:
            return

        self.paused = not self.paused
        if self.paused:
            self.status_label.config(text="Paused", fg="orange")
        else:
            self.status_label.config(text="Auction Running", fg="green")

    def process_bid(self, bid_data):
        with self.lock:
            if not self.auction_active or self.paused:
                return

            name = bid_data["name"]
            amount = bid_data["bid"]

            if amount > self.current_highest_bid:
                self.current_highest_bid = amount
                self.highest_bidder = name

                # Auto Extend
                if self.time_remaining <= AUTO_EXTEND_THRESHOLD:
                    self.time_remaining += AUTO_EXTEND_TIME

                self.root.after(0, self.update_ui)
                self.root.after(0, lambda:
                    self.history.insert(END, f"{name} bid ${amount}"))

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
            text=f"Winner: {self.highest_bidder} (${self.current_highest_bid})",
            fg="red"
        )

        self.broadcast({
            "type": "end",
            "winner": self.highest_bidder,
            "amount": self.current_highest_bid
        })

    # ---------------- Helpers ---------------- #

    def update_ui(self):
        self.bid_label.config(
            text=f"Highest Bid: ${self.current_highest_bid} ({self.highest_bidder})"
        )

    def update_timer(self):
        self.timer_label.config(text=f"Time: {self.time_remaining}")

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