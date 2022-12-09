import socket
import threading
import time

# Server thread class which can run synchronization with client thread
class Server(threading.Thread):
    def __init__(self, p2p):
        super(Server, self).__init__()
        self.p2p = p2p
        self.port = self.p2p.port
        self.host = ""
        self.hasConnection = False 
        self.stopSocket = False # Socket interrupt status
        self.file = ""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create new socket
        self.socket.bind((self.host, self.port)) # Bind the socket to host and port stored in the servers vars
        self.socket.listen() # Set socket mode to listen
        self.p2p.system_message("Server is activated on port {0}".format(self.port))

    # Method called by threading on start
    def run(self):
        conn, addr = self.socket.accept()
        if self.stopSocket:
            exit(1)
        init = conn.recv(1024)
        self.hasConnection = True
        
        self.handleInit(init)
        
        while True:
            if len(self.p2p.P2P_display.p2pTalks.values) > self.p2p.P2P_display.y - 10:
                self.p2p.clear_all()
            data = conn.recv(1024)
            if not data:
                self.p2p.system_message("This is an empty ")
                self.p2p.system_message("There is something wrong, disconnecting...")
                break
            elif data.decode().startswith('\b/file'):
                self.p2p.system_message("get into run file function")
                self.p2p.system_message(data.decode())
                self.run_file(data.decode().split(" ")[1],conn)
            elif data.decode().startswith('\b/quit'):
                self.p2p.client_thread.has_connected = False
                self.p2p.restart()
                break
            else: 
                if data.decode().startswith("peer just changed its name to"):
                    self.p2p.peerName = data.decode().split(' ')[6]
                self.p2p.P2P_display.p2pTalks.values.append("{0} >  {1}".format(self.p2p.peerName, data.decode()))
                self.p2p.P2P_display.p2pTalks.display()

    # Function to receive the initial message about the peer user_name, ip address, and port number
    def handleInit(self, init):
        # Check if there is empty initialization
        # If empty, set all three parameter as unknown
        if not init:
            self.p2p.peerName = "Unknown"
            self.p2p.peerPort = "unknown"
            self.p2p.peerIP = 'unknown'
        else: # Decode initial information and set peer vars to values send by peer
            init = init.decode()
            if init.startswith("\b/init"):
                init = init[2:].split(' ')
                self.p2p.peerName = init[1]
                self.p2p.peerIP = init[2]
                self.p2p.peerPort = init[3]
            else: # If initial information is not sent correctly 
                self.p2p.peerName = "Unknown"
                self.p2p.peerPort = "unknown"
                self.p2p.peerIP = 'unknown'

        if not self.p2p.client_thread.has_connected: # Send message to inform about connectBack if client socket is not connected
            if self.p2p.peerIP == "unknown" or self.p2p.peerPort == "unknown":
                self.p2p.system_message("can not connectback because of missing information of peer")
            else:
                self.p2p.system_message("A peer just connected to you (you can connectback by calling /connectback)")
                self.p2p.system_message("Peer IP: {0}, Peer port: {1}".format(self.p2p.peerIP, self.p2p.peerPort))

        self.p2p.system_message("A peer {0} just joined".format(self.p2p.peerName)) # Inform user about peer

    # Function to restart or exit the server socket
    def stop(self):
        if self.hasConnection:
            self.socket.close()
        else:
            self.stopSocket = True
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('localhost', self.port))
            time.sleep(0.2)
            self.socket.close()
        self.socket = None
    
    # Function to receive file from the client
    def run_file(self, file_name, conn):
        self.p2p.system_message("Go into this function")
        self.p2p.system_message(file_name)
        self.file = open(file_name, "wb")
        self.p2p.system_message("Start receiving file")
        message = conn.recv(1024)
        self.file.write(message)
        while len(message) == 1024:
            message = conn.recv(1024)
            self.file.write(message)
        self.file.close()
        self.p2p.system_message("Finished receiving file")
