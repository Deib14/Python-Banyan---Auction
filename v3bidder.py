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
        self.build_connection_ui()

    # REMOVE THIS FUNCTION FOR FINAL VERSION IF NEEDED
    def build_connection_ui(self):
        Label(self.root, text="Server IP:").pack()
        self.ip_entry = Entry(self.root)
        self.ip_entry.pack()

        Button(self.root, text="Connect",
               command=self.connect_to_server).pack(pady=5)

    def connect_to_server(self):
        server_ip = self.ip_entry.get()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server_ip, PORT))

        self.ip_entry.destroy()
        self.build_main_ui()

        threading.Thread(target=self.receive_messages,
                         daemon=True).start()

    def build_main_ui(self):
        Label(self.root, text="Your Name:").pack()
        self.name_entry = Entry(self.root)
        self.name_entry.pack()

        Label(self.root, text="Bid Amount:").pack()
        self.bid_entry = Entry(self.root)
        self.bid_entry.pack()

        self.bid_button = Button(self.root,
                                 text="Place Bid",
                                 command=self.place_bid)
        self.bid_button.pack(pady=5)

        self.message_label = Label(self.root, text="")
        self.message_label.pack(pady=5)

    def place_bid(self):
        try:
            message = {
                "name": self.name_entry.get(),
                "bid": int(self.bid_entry.get())
            }
            self.socket.send(json.dumps(message).encode())
        except:
            self.message_label.config(text="Invalid Bid")

    def receive_messages(self):
        while True:
            try:
                data = self.socket.recv(1024).decode()
                message = json.loads(data)

                if message["type"] == "update":
                    self.root.after(0, lambda:
                        self.message_label.config(
                            text=f"{message['bidder']} bid ${message['highest_bid']}"
                        )
                    )

                elif message["type"] == "end":
                    self.root.after(0, lambda:
                        self.message_label.config(
                            text=f"Auction Ended! Winner: {message['winner']}"
                        )
                    )
                    self.root.after(0,
                        lambda: self.bid_button.config(state=DISABLED))

            except:
                break


if __name__ == "__main__":
    root = Tk()
    BidderGUI(root)
    root.mainloop()