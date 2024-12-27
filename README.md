# PROY03 🎥

A Client-Cluster Server project designed to process videos across multiple nodes and send the processed result back to the client.

---

## 📘 How Does It Work?

The project is divided into three main components: **Client**, **ClusterServer**, and **ClusterNode**.

### 🖥️ Client Code
- The client connects to the ClusterServer to upload a video file.
- Once the processing is complete, the client receives the processed video back.

### 🧠 ClusterServer Code
- Acts as the central coordinator for the system.
- Handles connections from both the Client and multiple ClusterNodes.
- Once the client uploads a video:
  1. The server waits until a specific number of nodes are connected.
  2. Splits the video into equal segments.
  3. Distributes these segments to the connected nodes for processing.
- After receiving the processed segments from the nodes:
  1. Verifies the integrity of the processed video.
  2. Reassembles the video and sends it back to the client.

### ⚙️ ClusterNode Code
- Each node connects to the ClusterServer and awaits instructions.
- Once connected:
  1. Receives a segment of the video from the server.
  2. Processes the segment by applying a grayscale filter.
  3. Notifies the server when the processing is complete.
  4. Sends the processed segment back to the server.

---

## 💡 Notes
- The largest video tested was approximately 60 seconds long. Videos longer than this may require adjustments or optimizations.
- The system is designed for educational purposes and may not handle robust or large-scale production scenarios without further enhancements.
- Currently, only the video stream (frames) is processed, and the audio is removed. Future updates may address this limitation.
