from socket import *
from threading import Thread
import cv2
import os

buffer: int = 32768

# Server configurations
host: str = "0.0.0.0"
serverPort: int = 5002
serverAddress: tuple = (host, serverPort)

# Cluster configurations
clusterPort: int = 5005
clusterAddress: tuple = (host, clusterPort)

# Create a socket for client connections
serverSocket: socket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)
serverSocket.listen(1)

# Create a socket for cluster connections
clusterSocket: socket = socket(AF_INET, SOCK_STREAM)
clusterSocket.bind(clusterAddress)
clusterSocket.listen(3)

# Connections
clientConnection: socket
clusterNodeConnections: {} = {}
receivedSegments: {} = {}


def listen_client_connection():
    global clientConnection
    # Keep listening for client connections
    while True:
        # Get the information from the connected client
        clientConnection, clientAddress = serverSocket.accept()
        print(f"Client connected from {clientAddress} \n")
        try:
            # Get the size of the video
            messageLengthBytes: bytes = clientConnection.recv(8)
            # Convert bytes to integer
            messageLength: int = int.from_bytes(messageLengthBytes, byteorder="big")
            # Write the information into a file
            with open(file="video_received.mov", mode="wb") as videoFile:
                totalBytesReceived: int = 0
                # While there's information
                while totalBytesReceived < messageLength:
                    # Receive data in buffer size chunks
                    videoChunk: bytes = clientConnection.recv(buffer)
                    # If there's no more information
                    if not videoChunk:
                        break
                    # Write the chunk into the file
                    videoFile.write(videoChunk)
                    totalBytesReceived += len(videoChunk)
                # If all information is received
                if totalBytesReceived == messageLength:
                    print("Video received successfully \n")
                else:
                    print("Video receiving incomplete \n")
        except Exception as e:
            print(f"Error receiving video: {e} \n")
        finally:
            break


def listen_node_connection():
    global clusterNodeConnections
    numNodes: int = 0
    # Until 3 nodes are available
    while numNodes < 2:
        try:
            # Get the information from the connected node
            nodeConnection, nodeAddress = clusterSocket.accept()
            print(f"Cluster Node connected from {nodeAddress} \n")
            # Save the node connection information using its numNode as a key
            clusterNodeConnections[numNodes] = [nodeConnection, nodeAddress]
            # Increase the number of connected nodes
            numNodes += 1
            # Set the connection on a thread
            Thread(target=handle_node_messages, args=(nodeConnection, nodeAddress)).start()
        except Exception as e:
            print(f"Error accepting connection: {e} \n")
    # Once there are enough nodes, send each one a segment
    divide_video_segment(numberParts=numNodes)


def handle_node_messages(nodeConnection, nodeAddress):
    global receivedSegments
    # Keep listening for node responses
    while True:
        # Get the first message from the node
        firstMessage: str = nodeConnection.recv(8).decode()
        # If the node responded
        if firstMessage.startswith("BACK"):
            try:
                # Get the size of the video segment
                segmentSizeBytes: bytes = nodeConnection.recv(8)
                # Convert bytes to integer
                segmentSize: int = int.from_bytes(segmentSizeBytes, byteorder="big")
                videoSegment: bytes = b""
                totalBytesReceived: int = 0
                # While data is received
                while totalBytesReceived < segmentSize:
                    # Receive data in buffer size chunks
                    chunk: bytes = nodeConnection.recv(buffer)
                    # If there's no more data
                    if not chunk:
                        break
                    # Add the chunk to segment
                    videoSegment += chunk
                    totalBytesReceived += len(chunk)
                nodeKey = None
                # Check the node's number using the ip address
                for key, value in clusterNodeConnections.items():
                    if value[1] == nodeAddress:
                        nodeKey = key
                        break
                # Save the segment for later use
                if totalBytesReceived == segmentSize and nodeKey is not None:
                    # Assign the received segment to the responding node
                    receivedSegments[nodeKey] = videoSegment
                    print(f"Segment received correctly from node {clusterNodeConnections[nodeKey][1]} \n")
            except Exception as e:
                print(f"Error receiving video: {e} \n")
        # If all nodes responded back with their corresponding segment
        if len(receivedSegments) == len(clusterNodeConnections):
            # Combine back the video
            combine_video_segments()
            break


def divide_video_segment(numberParts: int):
    global clusterNodeConnections
    print("Sending segments to each node \n")
    # Get the name of video received from client
    videoPath: str = "video_received.mov"
    try:
        # If the video has been received
        if os.path.exists(videoPath):
            # Create directory if necessary
            os.makedirs("segments", exist_ok=True)
            # Clean previous segments
            for file in os.listdir("segments"):
                os.remove(os.path.join("segments", file))
            # Open video and get its details
            cap = cv2.VideoCapture(videoPath)
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            totalFrames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            # Calculate frames per segment
            framesPerSegment = totalFrames // numberParts
            # Divide video into segments
            for i in range(numberParts):
                outputSegment = os.path.join("segments", f"segment_{i}.mov")
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                out = cv2.VideoWriter(outputSegment, fourcc, fps, (width, height))
                # Calculate frames per segment
                framesToWrite = framesPerSegment if i < numberParts - 1 else totalFrames - (
                            framesPerSegment * (numberParts - 1))
                for _ in range(framesToWrite):
                    ret, frame = cap.read()
                    if not ret:
                        break
                    out.write(frame)
                out.release()
            cap.release()
            print("Video division successful \n")
            send_video_nodes()
    except Exception as e:
        print(f"Error dividing video into segments : {e} \n")


def send_video_nodes():
    global clusterNodeConnections
    print("Sending segments to each node \n")
    try:
        # Send segments
        for i, filename in enumerate(sorted(os.listdir("segments"))):
            filePath = os.path.join("segments", filename)
            with open(filePath, "rb") as f:
                # Get segment data
                data = f.read()
                # Set the segment size into 8 bytes
                segmentSizeBytes: bytes = len(data).to_bytes(8, byteorder="big")
                # Send the segment size to the node
                clusterNodeConnections[i][0].sendall(segmentSizeBytes)
                # Send segment data
                clusterNodeConnections[i][0].sendall(data)
                print(f"Segment: {filename} sent to node {i} \n")
    except Exception as e:
        print(f"Error sending segments to nodes: {e} \n")


def combine_video_segments():
    print("All segments received, combining video \n")
    # Open a file
    with open(file="processed_video.mov", mode="wb") as outVideo:
        # Get the segments according to its number
        for key in sorted(receivedSegments.keys()):
            # Write the segments into the file
            outVideo.write(receivedSegments[key])
    print("All segments combined successfully \n")
    # Send the video back to client
    send_video_client()


def send_video_client():
    global clientConnection
    print("Sending video back to client \n")
    # Get the name of the processed video
    videoProcessed = "processed_video.mov"
    try:
        # If the video has been completed
        if os.path.exists(videoProcessed):
            # Read the video's data
            with open(file=videoProcessed, mode="rb") as video:
                videoData: bytes = video.read()
            # Get the video size
            videoSize: int = len(videoData)
            # Convert integer to bytes in 8 bytes
            videoSizeBytes: bytes = videoSize.to_bytes(8, byteorder="big")
            # Send the segment size to client
            clientConnection.sendall(videoSizeBytes)
            # Send the processed video
            clientConnection.sendall(videoData)
            print("Processed video sent successfully \n")
    except Exception as e:
        print(f"Error sending video back to client: {e} \n")


def start_server():
    # Create thread for handling the client connection
    Thread(target=listen_client_connection).start()
    # Create thread for handling cluster connections
    Thread(target=listen_node_connection).start()


start_server()
