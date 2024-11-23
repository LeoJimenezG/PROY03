from tkinter import Tk, Label, Button, Entry, filedialog
from threading import Thread
from socket import *
import os

buffer: int = 32768

# Cluster Server configurations
serverHost: str = "localhost"
serverPort: int = 5002

# Create a socket for server connections
clientSocket: socket = socket(AF_INET, SOCK_STREAM)


def connect_to_server(server_host: str, server_port: int):
    # Establish the server's address
    serverAddress: tuple = (server_host, server_port)
    try:
        # Connect to the server
        clientSocket.connect(serverAddress)
        print("Successfully connected to the Server \n")
        Thread(target=receive_server_video).start()
    except Exception as e:
        print(f"Error connecting to server: {e} \n")


def send_video():
    try:
        # Open file dialog to select video
        filePath = filedialog.askopenfilename(filetypes=[("Video files", "*.mov")])
        # If file is selected
        if filePath:
            # Get video's information
            with open(file=filePath, mode="rb") as videoFile:
                # Video size
                fileSize = os.path.getsize(filePath)
                # Length of video in 8 bytes
                messageLength = fileSize.to_bytes(8, byteorder="big")
                # Send length of the video to server
                clientSocket.sendall(messageLength)
                # Separate the video into buffer size chunks
                while videoChunk := videoFile.read(buffer):
                    # Send the chunk video to the server
                    clientSocket.sendall(videoChunk)
                print("Video sent successfully \n")
    except Exception as e:
        print(f"Error sending video: {e} \n")


def receive_server_video():
    try:
        # Get the video size from the server
        messageLengthBytes: bytes = clientSocket.recv(8)
        # Convert bytes into integer
        messageLength: int = int.from_bytes(messageLengthBytes, byteorder="big")
        # Open file to write it
        with open(file="processed_video_received.mov", mode="wb") as videoFile:
            totalBytesReceived: int = 0
            # Make sure all information is received
            while totalBytesReceived < messageLength:
                # Receive the video in chunks
                videoChunk: bytes = clientSocket.recv(buffer)
                # If there's no more information
                if not videoChunk:
                    break
                # Write the chunk into the video file
                videoFile.write(videoChunk)
                totalBytesReceived += len(videoChunk)
            # When all information is received
            if totalBytesReceived == messageLength:
                print("Video processed received successfully \n")
            else:
                print("Video transfer incomplete \n")
    except Exception as e:
        print(f"Error receiving video: {e} \n")


def start_connection_server():
    # Get entry's values
    server = hostEntry.get() or serverHost
    port = portEntry.get() or serverPort
    # Connect to server
    connect_to_server(server, int(port))


# Set up GUI
tk = Tk()
tk.title("Cliente")
tk.geometry("300x250")
tk.resizable(width=False, height=False)

# Server details
Label(tk, text="Server Host:").pack(pady=5)
hostEntry = Entry(tk)
hostEntry.insert(0, serverHost)
hostEntry.pack(pady=5)
Label(tk, text="Server Port:").pack(pady=5)
portEntry = Entry(tk)
portEntry.insert(0, str(serverPort))
portEntry.pack(pady=5)

# Connect button
connectButton = Button(tk, text="Connect to Server", command=start_connection_server)
connectButton.pack(pady=10)

# Send video button
sendButton = Button(tk, text="Send Video", command=send_video)
sendButton.pack(pady=10)

tk.mainloop()
