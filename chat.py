import npyscreen
import sys
import lib.server as server
import lib.client as client
from lib.form import ChatForm
from lib.form import ChatInput
import time
import curses
import socket
import datetime
import pyperclip
import os
import json
from io import StringIO

class ChatApp(npyscreen.NPSAppManaged):
    # Method called at start by npyscreen
    def onStart(self):
        jsonFile = open('lang/en.json')
        self.lang = json.loads(jsonFile.read())
        jsonFile.close()

        self.ChatForm = self.addForm('MAIN', ChatForm, name='Advanced p2p secure free chat app') # Add ChatForm as the main form of npyscreen

        #Get this PCs public IP and catch errors
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            self.hostname = s.getsockname()[0]
            s.close()
        except socket.error as error:
            self.sysMsg(self.lang['noInternetAccess'])
            self.sysMsg(self.lang['failedFetchPublicIP'])
            self.hostname = "0.0.0.0"

        #Define initial variables
        self.port = 8080 # Port the server runs on
        self.nickname = "" # Empty variable to be filled with users nickname
        self.peer = "" # Peer nickname
        self.peerIP = "0" # IP of peer
        self.peerPort = "0" # Port of peer
        self.historyLog = [] # Array for message log
        self.messageLog = [] # Array for chat log
        self.historyPos = 0 # Int for current position in message history

        

        # Start Server and Client threads
        self.chatServer = server.Server(self)
        self.chatServer.daemon = True
        self.chatServer.start()
        self.chatClient = client.Client(self)
        self.chatClient.start()

        # Dictionary for commands. Includes funtion to call and number of needed arguments
        self.commandDict = {
            "connect": [self.chatClient.conn, 2],
            "disconnect": [self.restart, 0],
            "nickname": [self.setNickname, 1],
            "quit": [self.exitApp, 0],
            "port": [self.restart, 1],
            "connectback": [self.connectBack, 0],
            "clear": [self.clearChat, 0],
            "help": [self.commandHelp, 0],
            # "file": [self.]
        }


    # Method to reset server and client sockets
    def restart(self, args=None):
        self.sysMsg(self.lang['restarting'])
        if not args == None and args[0] != self.port:
            self.port = int(args[0])
        if self.chatClient.isConnected:
            self.chatClient.send("\b/quit")
            time.sleep(0.2)
        self.chatClient.stop()
        self.chatServer.stop()
        self.chatClient = client.Client(self)
        self.chatClient.start()
        self.chatServer = server.Server(self)
        self.chatServer.daemon = True
        self.chatServer.start()

    # Method to set nickname of client | Nickname will be sent to peer for identification
    def setNickname(self, args):
        self.nickname = args[0]
        self.sysMsg("{0}".format(self.lang['setNickname'].format(args[0])))
        if self.chatClient.isConnected:
            self.chatClient.send("\b/nick {0}".format(args[0]))

    # Method to render system info on chat feed
    def sysMsg(self, msg):
        self.messageLog.append("[SYSTEM] "+str(msg))
        if len(self.ChatForm.chatFeed.values) > self.ChatForm.y - 10:
            self.clearChat()
        if len(str(msg)) > self.ChatForm.x - 20:
            self.ChatForm.chatFeed.values.append('[SYSTEM] '+str(msg[:self.ChatForm.x-20]))
            self.ChatForm.chatFeed.values.append(str(msg[self.ChatForm.x-20:]))
        else:
            self.ChatForm.chatFeed.values.append('[SYSTEM] '+str(msg))
        self.ChatForm.chatFeed.display()

    # Method to send a message to a connected peer
    def sendMessage(self, _input):
        msg = self.ChatForm.chatInput.value
        if msg == "":
            return False
        if len(self.ChatForm.chatFeed.values) > self.ChatForm.y - 11:
                self.clearChat()
        self.messageLog.append(self.lang['you']+" > "+msg)
        self.historyLog.append(msg)
        self.historyPos = len(self.historyLog)
        self.ChatForm.chatInput.value = ""
        self.ChatForm.chatInput.display()
        if msg.startswith('/'):
            self.commandHandler(msg)
        else:
            if self.chatClient.isConnected:
                if self.chatClient.send(msg):
                    self.ChatForm.chatFeed.values.append(self.lang['you']+" > "+msg)
                    self.ChatForm.chatFeed.display()
            else:
                self.sysMsg(self.lang['notConnected'])

    # Method to connect to a peer that connected to the server
    def connectBack(self):
        if self.chatServer.hasConnection and not self.chatClient.isConnected:
            if self.peerIP == "unknown" or self.peerPort == "unknown":
                self.sysMsg(self.lang['failedConnectPeerUnkown'])
                return False
            self.chatClient.conn([self.peerIP, int(self.peerPort)])
        else:
            self.sysMsg(self.lang['alreadyConnected'])

   
    #Method to clear the chat feed
    def clearChat(self):
        self.ChatForm.chatFeed.values = []
        self.ChatForm.chatFeed.display()

    # Method to exit the app | Exit command will be sent to a connected peer so that they can disconnect their sockets
    def exitApp(self):
        self.sysMsg(self.lang['exitApp'])
        if self.chatClient.isConnected:
            self.chatClient.send("\b/quit")
        self.chatClient.stop()
        self.chatServer.stop()
        exit(1)

    # Method to handle commands
    def commandHandler(self, msg):
        msg = msg.split(' ')
        command = msg[0][1:]
        args = msg[1:]
        if command in self.commandDict:
            if self.commandDict[command][1] == 0:
                self.commandDict[command][0]()
            elif len(args) == self.commandDict[command][1]:
                self.commandDict[command][0](args)
            else:
                self.sysMsg(self.lang['commandWrongSyntax'].format(command, self.commandDict[command][1], len(args)))
        else:
            self.sysMsg(self.lang['commandNotFound'])
        

    # Method to print a list of all commands
    def commandHelp(self):
        if len(self.ChatForm.chatFeed.values) + len(self.commandDict) + 1 > self.ChatForm.y - 10:
            self.clearChat()
        self.sysMsg(self.lang['commandList'])
        for command in self.commandDict:
            if not self.lang['commands'][command] == "":
                self.sysMsg(self.lang['commands'][command])

if __name__ == '__main__':
    chatApp = ChatApp().run() # Start the app if chat.py is executed
    