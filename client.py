import socket
import threading
from pathlib import PurePath

# Client thread class which can run synchronization with the server thread
class Client(threading.Thread):
    def __init__(self, p2p):
        super(Client, self).__init__()
        self.p2p = p2p
        self.has_connected = False 

    # Function to start the client thread
    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)

    # Function to connect the host and peer
    def conn(self, args):
        # Check if the user name is entered or not
        if self.p2p.user_name == "":
            self.p2p.system_message("You should set your user_name first")
            return False
        # Receive the host_name and port number from the parameter
        host = args[0]
        port = int(args[1])
        self.p2p.system_message("Connecting to {0} on port {1}".format(host, port))
        try:
            self.socket.connect((host, port))
        except socket.error:
            self.p2p.system_message("Connection failed timed out")
            return False
        # Send initial message including username, IP address, and port number of the host to the peer
        self.socket.send("\b/init {0} {1} {2}".format(self.p2p.user_name, self.p2p.hostname, self.p2p.port).encode()) # Exchange initial information (user_name, ip, port)
        self.p2p.system_message("successfully connected")
        self.has_connected = True
    
    # Function to close the thread in order for quit or restart
    def stop(self):
        self.socket.close()
        self.socket = None

    # Function to send message to the peer
    def send(self, message):
        if message != '':
            try:
                self.socket.send(message.encode())
                return True
            except socket.error as error:
                self.p2p.system_message("Sending failed")
                self.p2p.system_message(error)
                self.has_connected = False
                return False

    # Function to send file to the peer
    def send_file (self, file_name):
        try:           
            self.send("\b/file {0}".format(file_name[0]))
            file_name = file_name[0]
            file  = open(file_name, "rb")            
            file_name=PurePath(file_name).name
            message = file.read(1024)
            while message:
                self.socket.send(message)
                message = file.read(1024)
            self.p2p.system_message(message.decode())
            self.socket.send(message)

            self.p2p.system_message("Sent file {} successfully".format(file_name))
            file.close()
            return True
       
            
        except FileNotFoundError as error:
            self.p2p.system_message("File not found")
            self.p2p.system_message(error)
            self.has_connected = False
            return False

        except socket.error as error:
            self.p2p.system_message("Sending failed")
            self.p2p.system_message(error)
            self.has_connected = False
            return False





    


