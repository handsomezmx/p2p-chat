import npyscreen
import server as server
import client as client
import time
import socket
import curses
from io import StringIO

# Required package to pip install: 'socket', 'threading', 'curses', 'npyscreen', 'time'

class P2P_display(npyscreen.FormBaseNew):
    def create(self):
        self.y, self.x  = self.useable_space()
        self.p2pTalks = self.add(npyscreen.BoxTitle, name="Feed", editable=False, max_height=self.y-7)
        self.chatInput = self.add(ChatInput, name="Input", footer="Return -> Send", rely=self.y-5)
        self.chatInput.entry_widget.handlers.update({curses.ascii.CR: self.parentApp.sendMessage})
        self.chatInput.entry_widget.handlers.update({curses.ascii.NL: self.parentApp.sendMessage})
              
class ChatInput(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit

# helper function
all_commands_hints = {
    "connect": "/connect [host] [port] --- Connect to a peer",
    "disconnect": "/disconnect --- Disconnect from the current peer",
    "user_name": "/user_name [user_name] --- Set your user_name",
    "quit": "/quit --- Quit the p2p app",
    "port": "/port [port] --- Restart server on provided port",
    "connectback": "/connectback --- Connect back to the client that is connected to your server",
    "file": "/file [filename] --- Send a file to the client",
    "clear": "/clear --- Clear all displayed chat",
    "all": "/all --- Display all commands"
}

# Display command helper function
def all_command_hints_display():
    result = ""
    for item in all_commands_hints:
        result += all_commands_hints[item]
    return result

# Receive the hostname by self connecting to "8.8.8.8"
def recv_hostname(conn):
    conn.connect(("8.8.8.8", 80))
    host_name = conn.getsockname()[0]
    conn.close()
    return host_name


class P2P(npyscreen.NPSAppManaged):
    def onStart(self):
        self.P2P_display = self.addForm('MAIN', P2P_display, name='Advanced p2p secure free chat app')
        # Host information initialization
        self_conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
           self.hostname = recv_hostname(self_conn)
        except socket.error as error:
            self.system_message("Doesn't find host name and please connect to the Internet!")
            self.hostname = "0.0.0.0"
        self.port = 6667
        self.user_name = ""

        # Peer information initialization
        self.peerName = "" 
        self.peerIP = "0" 
        self.peerPort = "0"

        # Server and client thread initialization
        self.server_thread = server.Server(self)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.client_thread = client.Client(self)
        self.client_thread.start()

        # Initialize command sets and ensure the argument is right
        self.command_set = {
            "connect": [self.client_thread.conn, 2],
            "disconnect": [self.restart, 0],
            "user_name": [self.setuser_name, 1],
            "quit": [self.exitApp, 0],
            "port": [self.restart, 1],
            "connectback": [self.connectBack, 0],
            "clear": [self.clear_all, 0],
            "all": [self.command_display, 0],
            "file": [self.client_thread.send_file, 1]
        }

    # Method to print a list of all commands
    def command_display(self):
        if len(self.P2P_display.p2pTalks.values) + len(self.command_set) + 1 > self.P2P_display.y - 10:
            self.clear_all()
        self.system_message("All available commands:")
        for item in all_commands_hints:            
            self.system_message(all_commands_hints[item])

    # Method to reset server and client sockets
    def restart(self, args=None):
        self.system_message("Restarting")
        if not args == None and args[0] != self.port:
            self.port = int(args[0])
        if self.client_thread.has_connected:
            self.client_thread.send("\b/quit")
            time.sleep(0.2)
        self.client_thread.stop()
        self.server_thread.stop()
        self.client_thread = client.Client(self)
        self.client_thread.start()
        self.server_thread = server.Server(self)
        self.server_thread.daemon = True
        self.server_thread.start()

    # Method to set user_name of client | user_name will be sent to peer for identification
    def setuser_name(self, args):
        self.user_name = args[0]
        self.system_message("Set name to {0}".format(args[0]))
        if self.client_thread.has_connected:
            self.client_thread.send("peer just changed its name to {0}".format(args[0]))

    # Method to render system info on chat feed
    def system_message(self, message):
        if len(self.P2P_display.p2pTalks.values) > self.P2P_display.y - 10:
            self.clear_all()
        if len(str(message)) > self.P2P_display.x - 20:
            self.P2P_display.p2pTalks.values.append('[SYSTEM] '+ str(message[:self.P2P_display.x-20]))
            self.P2P_display.p2pTalks.values.append(str(message[self.P2P_display.x-20:]))
        else:
            self.P2P_display.p2pTalks.values.append('[SYSTEM] '+ str(message))
        self.P2P_display.p2pTalks.display()

    # Method to send a message to a connected peer
    def sendMessage(self, _input):
        message = self.P2P_display.chatInput.value
        if message == "":
            return False
        if len(self.P2P_display.p2pTalks.values) > self.P2P_display.y - 11:
                self.clear_all()
        self.P2P_display.chatInput.value = ""
        self.P2P_display.chatInput.display()
        if message.startswith('/'):
            self.commandHandler(message)
        else:
            if self.client_thread.has_connected:
                if self.client_thread.send(message):
                    self.P2P_display.p2pTalks.values.append("You"+" > "+ message)
                    self.P2P_display.p2pTalks.display()
            else:
                self.system_message("You are not connected to a peer")

    # Method to connect to a peer that connected to the server
    def connectBack(self):
        if self.server_thread.hasConnection and not self.client_thread.has_connected:
            if self.peerIP == "unknown" or self.peerPort == "unknown":
                self.system_message("can not connectback because of missing information of peer")
                return False
            self.client_thread.conn([self.peerIP, int(self.peerPort)])
        else:
            self.system_message("Already connected to a peer")

   
    #Method to clear the chat feed
    def clear_all(self):
        self.P2P_display.p2pTalks.values = []
        self.P2P_display.p2pTalks.display()

    # Method to exit the app | Exit command will be sent to a connected peer so that they can disconnect their sockets
    def exitApp(self):
        self.system_message("Exiting...")
        if self.client_thread.has_connected:
            self.client_thread.send("\b/quit")
        self.client_thread.stop()
        self.server_thread.stop()
        exit(1)

    # Method to handle commands
    def commandHandler(self, message):
        message = message.split(' ')
        command = message[0][1:]
        args = message[1:]
        if command in self.command_set:
            if self.command_set[command][1] == 0:
                self.command_set[command][0]()
            elif len(args) == self.command_set[command][1]:
                self.command_set[command][0](args)
            else:
                self.system_message("/{0} takes {1} argument(s) but {2} was/were given.".format(command, self.command_set[command][1], len(args)))
        else:
            self.system_message("Command not found. Try /all for a list of commands!")



if __name__ == '__main__':
    p2p = P2P().run() # Start the app if chat.py is executed
    