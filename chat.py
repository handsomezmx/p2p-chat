import npyscreen
import sys
import server as server
import client as client
from form import ChatForm
from form import ChatInput
import time
import socket
import pyperclip
import json
from io import StringIO


commands = {
    "connect": "/connect [host] [port] | Connect to a peer",
    "disconnect": "/disconnect | Disconnect from the current chat",
    "nickname": "/nickname [nickname] | Set your nickname",
    "quit": "/quit | Quit the app",
    "port": "/port [port] | Restart server on specified port",
    "connectback": "/connectback | Connect to the client that is connected to your server",
    "clear": "/clear | Clear the chat. Logs will not be deleted",
    "log": "/log | Logs all messages of the current session to a file",
    "help": "/help | Shows this help"
}

class ChatApp(npyscreen.NPSAppManaged):
    def onStart(self):

        self.ChatForm = self.addForm('MAIN', ChatForm, name='Advanced p2p secure free chat app') # Add ChatForm as the main form of npyscreen
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            self.hostname = s.getsockname()[0]
            s.close()
        except socket.error as error:
            self.sysMsg("Can not connect to Internet")
            self.sysMsg("Can not get Public IP")
            self.hostname = "0.0.0.0"

        self.port = 6667
        self.nickname = ""
        self.peer = "" 
        self.peerIP = "0" 
        self.peerPort = "0" 

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
            "file": [self.chatClient.send_file, 1]
        }


    # Method to reset server and client sockets
    def restart(self, args=None):
        self.sysMsg("Restarting")
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
        self.sysMsg("Set name to {0}".format(args[0]))
        if self.chatClient.isConnected:
            self.chatClient.send("peer just changed its name to {0}".format(args[0]))

    # Method to render system info on chat feed
    def sysMsg(self, msg):
        if len(self.ChatForm.chatFeed.values) > self.ChatForm.y - 10:
            self.clearChat()
        if len(str(msg)) > self.ChatForm.x - 20:
            self.ChatForm.chatFeed.values.append('[SYSTEM] '+ str(msg[:self.ChatForm.x-20]))
            self.ChatForm.chatFeed.values.append(str(msg[self.ChatForm.x-20:]))
        else:
            self.ChatForm.chatFeed.values.append('[SYSTEM] '+ str(msg))
        self.ChatForm.chatFeed.display()

    # Method to send a message to a connected peer
    def sendMessage(self, _input):
        msg = self.ChatForm.chatInput.value
        if msg == "":
            return False
        if len(self.ChatForm.chatFeed.values) > self.ChatForm.y - 11:
                self.clearChat()
        self.ChatForm.chatInput.value = ""
        self.ChatForm.chatInput.display()
        if msg.startswith('/'):
            self.commandHandler(msg)
        else:
            if self.chatClient.isConnected:
                if self.chatClient.send(msg):
                    self.ChatForm.chatFeed.values.append("You"+" > "+msg)
                    self.ChatForm.chatFeed.display()
            else:
                self.sysMsg("You are not connected to a peer")

    # Method to connect to a peer that connected to the server
    def connectBack(self):
        if self.chatServer.hasConnection and not self.chatClient.isConnected:
            if self.peerIP == "unknown" or self.peerPort == "unknown":
                self.sysMsg("can not connectback because of missing information of peer")
                return False
            self.chatClient.conn([self.peerIP, int(self.peerPort)])
        else:
            self.sysMsg("Already connected to a peer")

   
    #Method to clear the chat feed
    def clearChat(self):
        self.ChatForm.chatFeed.values = []
        self.ChatForm.chatFeed.display()

    # Method to exit the app | Exit command will be sent to a connected peer so that they can disconnect their sockets
    def exitApp(self):
        self.sysMsg("Exiting...")
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
                self.sysMsg("/{0} takes {1} argument(s) but {2} was/were given.".format(command, self.commandDict[command][1], len(args)))
        else:
            self.sysMsg("Command not found. Try /help for a list of commands!")

    # Method to print a list of all commands
    def commandHelp(self):
        if len(self.ChatForm.chatFeed.values) + len(self.commandDict) + 1 > self.ChatForm.y - 10:
            self.clearChat()
        self.sysMsg("Here's a list of available commands:")
        for command in commands:
            if not commands[command] == "":
                self.sysMsg(commands[command])

if __name__ == '__main__':
    chatApp = ChatApp().run() # Start the app if chat.py is executed
    