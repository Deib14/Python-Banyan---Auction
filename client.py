import socket
import threading
import json
from tkinter import *

SERVER_IP = "192.168.1.5"   # CHANGE THIS
PORT = 5000

class BidderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Auction Bidder")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((SERVER_IP, PORT))

        self.build_ui()
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def build_ui(self):
        Label(self.root, text="Enter Your Name").pack()
        self.name_entry = Entry(self.root)
        self.name_entry.pack()

        Label(self.root, text="Enter Bid Amount").pack()
        self.bid_entry = Entry(self.root)
        self.bid_entry.pack()

        self.bid_button = Button(self.root, text="Place Bid", command=self.place_bid)
        self.bid_button.pack(pady=5)

        self.message_label = Label(self.root, text="")
        self.message_label.pack()

    def place_bid(self):
        try:
            bid = int(self.bid_entry.get())
            name = self.name_entry.get()

            message = {
                "name": name,
                "bid": bid
            }

            self.socket.send(json.dumps(message).encode())
        except:
            self.message_label.config(text="Invalid bid amount")

    def receive_messages(self):
        while True:
            try:
                data = self.socket.recv(1024).decode()
                message = json.loads(data)

                if message["type"] == "update":
                    self.root.after(0, lambda:
                        self.message_label.config(
                            text=f"Highest Bid: ${message['highest_bid']} by {message['bidder']}"
                        )
                    )

                elif message["type"] == "end":
                    self.root.after(0, lambda:
                        self.message_label.config(
                            text=f"Auction Ended! Winner: {message['winner']} (${message['amount']})"
                        )
                    )
                    self.root.after(0, lambda: self.bid_button.config(state=DISABLED))

            except:
                break

if __name__ == "__main__":
    root = Tk()
    BidderGUI(root)
    root.mainloop()