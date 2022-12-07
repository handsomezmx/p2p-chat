import npyscreen
import curses

class ChatForm(npyscreen.FormBaseNew):
    def create(self):
        self.y, self.x  = self.useable_space()
        self.chatFeed = self.add(npyscreen.BoxTitle, name="Feed", editable=False, max_height=self.y-7)
        self.chatInput = self.add(ChatInput, name="Input", footer="Return -> Send", rely=self.y-5)
        self.chatInput.entry_widget.handlers.update({curses.ascii.CR: self.parentApp.sendMessage})
        self.chatInput.entry_widget.handlers.update({curses.ascii.NL: self.parentApp.sendMessage})
        
        
        
        
class ChatInput(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit