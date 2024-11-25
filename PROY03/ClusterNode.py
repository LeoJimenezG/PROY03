from threading import Thread
from socket import *
import os
import cv2

buffer: int = 32768

# Cluster server configurations
serverHost: str = "localhost"
serverPort: int = 5005

# Create a socket for server connections
nodeSocket: socket = socket(AF_INET, SOCK_STREAM)
nodeId = 2


def connect_to_server(server_host: str, server_port: int):
    # Server address
    serverAddress: tuple = (server_host, server_port)
    try:
        # Connect to server
        nodeSocket.connect(serverAddress)
        print("Connection to server successful \n")
        Thread(target=receive_video_segment).start()
    except Exception as e:
        print(f"Error connecting to server: {e} \n")


def receive_video_segment():
    try:
        # Receive the video segment size
        segmentSizeBytes: bytes = nodeSocket.recv(8)
        # Convert bytes to integer
        segmentSize: int = int.from_bytes(segmentSizeBytes, byteorder="big")
        # If there's data
        if segmentSize > 0:
            segment: bytes = b""
            totalBytesReceived: int = 0
            # While there's data
            while totalBytesReceived < segmentSize:
                # Receive data in buffer size chunks
                chunk: bytes = nodeSocket.recv(buffer)
                # If there's no more data
                if not chunk:
                    break
                # Add chunk to the whole video segment
                segment += chunk
                totalBytesReceived += len(chunk)
            # If all information is received
            if totalBytesReceived == segmentSize:
                print(f"Video segment received successfully \n")
                # Process the video segment
                process_video_segment(segment)
            else:
                print("Segment transfer failed \n")
    except Exception as e:
        print(f"Error receiving video: {e} \n")


def send_processed_video(video: bytes):
    try:
        # Indicate server processed segment is been sent back
        message: bytes = "BACK".encode()
        nodeSocket.sendall(message)
        # Get segment size
        videoSize: int = len(video)
        # Convert integer into bytes
        videoSizeBytes: bytes = videoSize.to_bytes(8, byteorder="big")
        # Send size to server
        nodeSocket.sendall(videoSizeBytes)
        # Send processed video to server
        nodeSocket.sendall(video)
        print(f"Processed video sent successfully \n")
    except Exception as e:
        print(f"Error sending processed video: {e} \n")


def process_video_segment(videoSegment: bytes):
    try:
        # Create a temporal file with the segment
        tempFile = f"temp_segment_{nodeId}.mov"
        with open(tempFile, "wb") as temp:
            temp.write(videoSegment)

        # Process the video
        cap = cv2.VideoCapture(tempFile)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        processedFile = f"processed_segment_{nodeId}.mov"
        out = cv2.VideoWriter(
            processedFile,
            fourcc,
            cap.get(cv2.CAP_PROP_FPS),
            (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))),
            isColor=False)
        # Apply a gray filter
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            out.write(grayFrame)
        cap.release()
        out.release()
        # Rewrite video segment
        with open(processedFile, "rb") as processed:
            processedVideoSegment = processed.read()
        # Send the processed segment
        send_processed_video(video=processedVideoSegment)
    except Exception as e:
        print(f"Error processing video: {e} \n")
    finally:
        # Delete temporal files
        if os.path.exists(tempFile):
            os.remove(tempFile)
        if os.path.exists(processedFile):
            os.remove(processedFile)


connect_to_server(server_host=serverHost, server_port=serverPort)
