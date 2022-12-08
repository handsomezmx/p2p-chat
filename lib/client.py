import socket
import threading
from pathlib import PurePath
import sys
import time
import os

class Client(threading.Thread): # Client object is type thread so that it can run simultaniously with the server
    def __init__(self, chatApp): # Initialize with a reference to the Chat App
        super(Client, self).__init__()
        self.chatApp = chatApp
        self.isConnected = False # Connection status

    # Start method called by threading module
    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create new socket
        self.socket.settimeout(5)

    def conn(self, args):
        if self.chatApp.nickname == "": # Check if a nickname is set and return False if not
            self.chatApp.sysMsg(self.chatApp.lang['nickNotSet'])
            return False
        host = args[0] # IP of peer
        port = int(args[1]) # Port of peer
        self.chatApp.sysMsg(self.chatApp.lang['connectingToPeer'].format(host, port))
        try: # Try to connect and catch error on fail
            self.socket.connect((host, port))
        except socket.error:
            self.chatApp.sysMsg(self.chatApp.lang['failedConnectingTimeout'])
            return False
        self.socket.send("\b/init {0} {1} {2}".format(self.chatApp.nickname, self.chatApp.hostname, self.chatApp.port).encode()) # Exchange initial information (nickname, ip, port)
        self.chatApp.sysMsg(self.chatApp.lang['connected'])
        self.isConnected = True # Set connection status to true
    
    # Method called by Chat App to reset client socket
    def stop(self):
        self.socket.close()
        self.socket = None

    # Method to send data to a peer
    def send(self, msg):
        if msg != '':
            try:
                self.socket.send(msg.encode())
                return True
            except socket.error as error:
                self.chatApp.sysMsg(self.chatApp.lang['failedSentData'])
                self.chatApp.sysMsg(error)
                self.isConnected = False
                return False

    def send_file (self, file_name):
        try:
            self.send("\b/file {0}".format(file_name))
            file_name = file_name[0]
            file = open(file_name, "rb")
            file_name=PurePath(file_name).name
            # self.socket.send(file_name.encode())
            # self.chatApp.sysMsg("file name: " + file_name)
            # ack = self.socket.recv(1024)
            # if ack.decode == file_name:
            msg = file.read(1024)
            while msg:
                self.socket.send(msg)
                msg = file.read(1024)
            self.chatApp.sysMsg("Sent file {} successfully".format(file_name))
            file.close()
            return True
        
        except FileNotFoundError as error:
            self.chatApp.sysMsg("File not found")
            self.chatApp.sysMsg(error)
            self.isConnected = False
            return False

        except socket.error as error:
            self.chatApp.sysMsg(self.chatApp.lang['failedSentData'])
            self.chatApp.sysMsg(error)
            self.isConnected = False
            return False





    


