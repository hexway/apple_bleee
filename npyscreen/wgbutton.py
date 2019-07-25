#!/usr/bin/python
import curses
import locale
import weakref
from . import npysGlobalOptions as GlobalOptions
from . import wgwidget    as widget
from . import wgcheckbox  as checkbox

class MiniButton(checkbox._ToggleControl):
    DEFAULT_CURSOR_COLOR = None
    def __init__(self, screen, name='Button', cursor_color=None, *args, **keywords):
        self.encoding = 'utf-8'
        self.cursor_color = cursor_color or self.__class__.DEFAULT_CURSOR_COLOR
        if GlobalOptions.ASCII_ONLY or locale.getpreferredencoding() == 'US-ASCII':
            self._force_ascii = True
        else:
            self._force_ascii = False
        self.name = self.safe_string(name)
        self.label_width = len(name) + 2
        super(MiniButton, self).__init__(screen, *args, **keywords)
        if 'color' in keywords:
            self.color = keywords['color']
        else:
            self.color = 'CONTROL'
        
    def calculate_area_needed(self):
        return 1, self.label_width+2

    def update(self, clear=True):
        if clear: self.clear()
        if self.hidden:
            self.clear()
            return False
        
        
        if self.value and self.do_colors():
            self.parent.curses_pad.addstr(self.rely, self.relx, '>', self.parent.theme_manager.findPair(self))
            self.parent.curses_pad.addstr(self.rely, self.relx+self.width-1, '<', self.parent.theme_manager.findPair(self))
        elif self.value:
            self.parent.curses_pad.addstr(self.rely, self.relx, '>')
            self.parent.curses_pad.addstr(self.rely, self.relx+self.width-1, '<')
            
        
        if self.editing:
            button_state = curses.A_STANDOUT
        else:
            button_state = curses.A_NORMAL
        
        button_name = self.name
        if isinstance(button_name, bytes):
            button_name = button_name.decode(self.encoding, 'replace')
        button_name = button_name.center(self.label_width)
        
        if self.do_colors():
            if self.cursor_color:
                if self.editing:
                    button_attributes = self.parent.theme_manager.findPair(self, self.cursor_color)
                else:
                    button_attributes  = self.parent.theme_manager.findPair(self, self.color)
            else:    
                button_attributes = self.parent.theme_manager.findPair(self, self.color) | button_state
        else:
            button_attributes = button_state
        
        self.add_line(self.rely, self.relx+1,
            button_name,
            self.make_attributes_list(button_name, button_attributes),
            self.label_width
            )


class MiniButtonPress(MiniButton):
    # NB.  The when_pressed_function functionality is potentially dangerous. It can set up
    # a circular reference that the garbage collector will never free. 
    # If this is a risk for your program, it is best to subclass this object and
    # override when_pressed_function instead.  Otherwise your program will leak memory.
    def __init__(self, screen, when_pressed_function=None, *args, **keywords):
        super(MiniButtonPress, self).__init__(screen, *args, **keywords)
        self.when_pressed_function = when_pressed_function
    
    def set_up_handlers(self):
        super(MiniButtonPress, self).set_up_handlers()
        
        self.handlers.update({
                curses.ascii.NL: self.h_toggle,
                curses.ascii.CR: self.h_toggle,
            })
        
    def destroy(self):
        self.when_pressed_function = None
        del self.when_pressed_function
    
    def h_toggle(self, ch):
        self.value = True
        self.display()
        if self.when_pressed_function:
            self.when_pressed_function()
        else:
            self.whenPressed()
        self.value = False
        self.display()
    
    def whenPressed(self):
        pass
