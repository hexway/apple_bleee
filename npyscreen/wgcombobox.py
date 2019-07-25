#!/usr/bin/env python
import curses

from . import wgtextbox     as textbox
from . import wgmultiline   as multiline
from . import fmForm        as Form
from . import fmPopup       as Popup
from . import wgtitlefield  as titlefield

class ComboBox(textbox.Textfield):
    ENSURE_STRING_VALUE = False
    def __init__(self, screen, value = None, values=None,**keywords):
        self.values = values or []
        self.value = value or None
        if value is 0: 
            self.value = 0
        super(ComboBox, self).__init__(screen, **keywords)
        
    def display_value(self, vl):
        """Overload this function to change how values are displayed.  
Should accept one argument (the object to be represented), and return a string."""
        return str(vl)

    def update(self, **keywords):
        keywords.update({'cursor': False})
        super(ComboBox, self).update(**keywords)
    
    def _print(self):
        if self.value == None or self.value is '':
            printme = '-unset-'
        else:
            try:
                printme = self.display_value(self.values[self.value])
            except IndexError:
                printme = '-error-'
        if self.do_colors():
            self.parent.curses_pad.addnstr(self.rely, self.relx, printme, self.width, self.parent.theme_manager.findPair(self))
        else:
            self.parent.curses_pad.addnstr(self.rely, self.relx, printme, self.width)


    def edit(self):
        #We'll just use the widget one
        super(textbox.Textfield, self).edit()
    
    def set_up_handlers(self):
        super(textbox.Textfield, self).set_up_handlers()

        self.handlers.update({curses.ascii.SP:  self.h_change_value,
                      #curses.ascii.TAB: self.h_change_value,
                      curses.ascii.NL:  self.h_change_value,
                      curses.ascii.CR:  self.h_change_value,
                      ord('x'):         self.h_change_value,
                      ord('k'):         self.h_exit_up,
                      ord('j'):         self.h_exit_down,
                      ord('h'):         self.h_exit_left,
                      ord('l'):         self.h_exit_right,                      
                      })
    
    def h_change_value(self, input):
        "Pop up a window in which to select the values for the field"
        F = Popup.Popup(name = self.name)
        l = F.add(multiline.MultiLine, 
            values = [self.display_value(x) for x in self.values],
            return_exit=True, select_exit=True,
            value=self.value)
        F.display()
        l.edit()
        self.value = l.value


class TitleCombo(titlefield.TitleText):
    _entry_type = ComboBox
    
    def get_values(self):
        try:
            return self.entry_widget.values
        except:
            try:
                return self.__tmp_values
            except:
                return None
    
    def set_values(self, values):
        try:
            self.entry_widget.values = values
        except:
            # probably trying to set the value before the textarea is initialised
            self.__tmp_values = values
            
    def del_values(self):
        del self.entry_widget.values

    values = property(get_values, set_values, del_values)

