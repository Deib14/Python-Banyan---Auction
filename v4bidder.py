import socket
import threading
import json
from tkinter import *

PORT = 5000


class BidderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bidder")

        self.socket = None
        self.name = ""

        self.build_connection_ui()

    def build_connection_ui(self):
        Label(self.root, text="Server IP:").pack()
        self.ip_entry = Entry(self.root)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack()

        Label(self.root, text="Your Name:").pack()
        self.name_entry = Entry(self.root)
        self.name_entry.pack()

        Button(self.root, text="Connect",
               command=self.connect_to_server).pack(pady=5)

    def connect_to_server(self):
        server_ip = self.ip_entry.get()
        self.name = self.name_entry.get()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server_ip, PORT))

        for widget in self.root.winfo_children():
            widget.destroy()

        self.build_main_ui()
        threading.Thread(target=self.receive_messages,
                         daemon=True).start()

    def build_main_ui(self):
        Label(self.root, text="Current Item:").pack()
        self.item_label = Label(self.root, text="Waiting...")
        self.item_label.pack()

        Label(self.root, text="Time Remaining:").pack()
        self.time_label = Label(self.root, text="0")
        self.time_label.pack()

        Label(self.root, text="Highest Bid:").pack()
        self.highest_bid_label = Label(self.root, text="$0")
        self.highest_bid_label.pack()

        Label(self.root, text="Enter Bid:").pack()
        self.bid_entry = Entry(self.root)
        self.bid_entry.pack()

        self.bid_button = Button(self.root,
                                 text="Place Bid",
                                 command=self.place_bid)
        self.bid_button.pack(pady=5)

        self.status_label = Label(self.root, text="")
        self.status_label.pack()

    def place_bid(self):
        try:
            message = {
                "name": self.name,
                "bid": int(self.bid_entry.get())
            }
            self.socket.send(json.dumps(message).encode())
        except:
            self.status_label.config(text="Invalid Bid")

    def receive_messages(self):
        while True:
            try:
                data = self.socket.recv(1024).decode()
                message = json.loads(data)

                if message["type"] == "update":
                    self.root.after(0, lambda m=message:
                        self.highest_bid_label.config(
                            text=f"${m['highest_bid']} ({m['bidder']})"
                        ))

                elif message["type"] == "timer":
                    self.root.after(0, lambda m=message:
                        self.time_label.config(text=m["time"]))

                elif message["type"] == "item":
                    self.root.after(0, lambda m=message:
                        self.item_label.config(text=m["item"]))

                elif message["type"] == "end":
                    self.root.after(0, lambda m=message:
                        self.status_label.config(
                            text=f"Auction Ended! Winner: {m['winner']}"))
                    self.root.after(0,
                        lambda: self.bid_button.config(state=DISABLED))

            except:
                break


if __name__ == "__main__":
    root = Tk()
    BidderGUI(root)
    root.mainloop()