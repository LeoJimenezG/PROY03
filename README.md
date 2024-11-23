# PROY03
Client-Cluster Server project school to process video in different nodes and send it back to client.

-- How does it work --
- The whole project consists on three main different codes: Client, ClusterServer and ClusterNode.
  - Client: this code is used to connect to the ClusterServer, send a video (preferably less than 20 seconds) and receive it back processed.
  - ClusterServer: its the brain of the project, it will listen for the client connection and the nodes connections. It will receive the video from the Client and once an specific number of nodes are connected, it will separate the video into equal segments and send them to each of the connected nodes for them to process them. Finally, it will receive the processed video, verify it and send it back to the Client.
  - ClusterNode: this code connects to the ClusterServer. When more nodes connect, it will receive a segment of the whole video and will process it applying a gray scale. When the segment is received, first, will send a message to the server to let it know its ready, then the processed segment will be sent back.
- Some of the main characteristics needed to work can be changed according to the different needs. However, it is not exactly proggramed to be a very robust project.

     
