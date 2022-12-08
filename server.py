import socket
import threading
import time

class Server(threading.Thread): # Server object is type thread so that it can run simultaniously with the client
    def __init__(self, chatApp): # Initialize with a reference to the Chat App and initial vars
        super(Server, self).__init__()
        self.chatApp = chatApp
        self.port = self.chatApp.port # Get the server port from the Chat App reference
        self.host = "" # Accept all hostnames
        self.hasConnection = False # Connection status
        self.stopSocket = False # Socket interrupt status
        self.file = ""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create new socket
        self.socket.bind((self.host, self.port)) # Bind the socket to host and port stored in the servers vars
        self.socket.listen() # Set socket mode to listen
        self.chatApp.sysMsg("Server is activated on port {0}".format(self.port))

    # Method called by threading on start
    def run(self):
        conn, addr = self.socket.accept()
        if self.stopSocket:
            exit(1)
        init = conn.recv(1024)
        self.hasConnection = True
        
        self.handleInit(init)
        
        while True:
            if len(self.chatApp.ChatForm.chatFeed.values) > self.chatApp.ChatForm.y - 10:
                self.chatApp.clearChat()
            data = conn.recv(1024)
            if not data:
                self.chatApp.sysMsg("This is an empty ")
                self.chatApp.sysMsg("There is something wrong, disconnecting...")
                break
            elif data.decode().startswith('\b/file'):
                self.chatApp.sysMsg("get into run file function")
                self.chatApp.sysMsg(data.decode())
                self.run_file(data.decode().split(" ")[1],conn)
            elif data.decode().startswith('\b/quit'):
                self.chatApp.chatClient.isConnected = False
                self.chatApp.restart()
                break
            else: 
                if data.decode().startswith("peer just changed its name to"):
                    self.chatApp.peer = data.decode().split(' ')[6]
                self.chatApp.ChatForm.chatFeed.values.append("{0} >  {1}".format(self.chatApp.peer, data.decode()))
                self.chatApp.ChatForm.chatFeed.display()

    def handleInit(self, init):
        if not init: # If initial information is empty, set peer vars to unknown
            self.chatApp.peer = "Unknown"
            self.chatApp.peerPort = "unknown"
            self.chatApp.peerIP = 'unknown'
        else: # Decode initial information and set peer vars to values send by peer
            init = init.decode()
            if init.startswith("\b/init"):
                init = init[2:].split(' ')
                self.chatApp.peer = init[1]
                self.chatApp.peerIP = init[2]
                self.chatApp.peerPort = init[3]
            else: # If initial information is not sent correctly 
                self.chatApp.peer = "Unknown"
                self.chatApp.peerPort = "unknown"
                self.chatApp.peerIP = 'unknown'

        if not self.chatApp.chatClient.isConnected: # Send message to inform about connectBack if client socket is not connected
            if self.chatApp.peerIP == "unknown" or self.chatApp.peerPort == "unknown":
                self.chatApp.sysMsg("can not connectback because of missing information of peer")
            else:
                self.chatApp.sysMsg("A peer just connected to you (you can connectback by calling /connectback)")
                self.chatApp.sysMsg("Peer IP: {0}, Peer port: {1}".format(self.chatApp.peerIP, self.chatApp.peerPort))

        self.chatApp.sysMsg("A peer {0} just joined".format(self.chatApp.peer)) # Inform user about peer

    # Method called by Chat App to reset server socket
    def stop(self):
        if self.hasConnection:
            self.socket.close()
        else:
            self.stopSocket = True
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('localhost', self.port))
            time.sleep(0.2)
            self.socket.close()
        self.socket = None
    
    def run_file(self, file_name, conn):
        self.chatApp.sysMsg("Go into this function")
        self.chatApp.sysMsg(file_name)
        self.file = open(file_name, "wb")
        self.chatApp.sysMsg("Start receiving file")
        msg = conn.recv(1024)
        self.file.write(msg)
        while len(msg) == 1024:
            msg = conn.recv(1024)
            self.file.write(msg)
        self.file.close()
        self.chatApp.sysMsg("Finished receiving file")
