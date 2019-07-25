#!/usr/bin/python

from .wgtextbox   import Textfield
from .wgwidget    import Widget
#from .wgmultiline import MultiLine
from . import wgwidget as widget
import curses

class _ToggleControl(Widget):
    def set_up_handlers(self):
        super(_ToggleControl, self).set_up_handlers()
        
        self.handlers.update({
                curses.ascii.SP: self.h_toggle,
                ord('x'):        self.h_toggle,
                curses.ascii.NL: self.h_select_exit,
                curses.ascii.CR: self.h_select_exit,
                ord('j'):        self.h_exit_down,
                ord('k'):        self.h_exit_up,
                ord('h'):        self.h_exit_left,
                ord('l'):        self.h_exit_right,                      
            })
    
    def h_toggle(self, ch):
        if self.value is False or self.value is None or self.value == 0: 
            self.value = True
        else: 
            self.value = False
        self.whenToggled()
    
    def whenToggled(self):
        pass
    
    def h_select_exit(self, ch):
        if not self.value:
            self.h_toggle(ch)
        self.editing = False
        self.how_exited = widget.EXITED_DOWN


class CheckboxBare(_ToggleControl):
    False_box = '[ ]'
    True_box  = '[X]'
    
    def __init__(self, screen, value = False, **keywords):
        super(CheckboxBare, self).__init__(screen, **keywords)
        self.value = value
        self.hide  = False
    
    def calculate_area_needed(self):
        return 1, 4
    
    def update(self, clear=True):
        if clear: self.clear()
        if self.hidden:
            self.clear()
            return False
        if self.hide: return True

        if self.value:
            cb_display = self.__class__.True_box
        else:
            cb_display = self.__class__.False_box
        
        if self.do_colors():    
            self.parent.curses_pad.addstr(self.rely, self.relx, cb_display, self.parent.theme_manager.findPair(self, 'CONTROL'))
        else:
            self.parent.curses_pad.addstr(self.rely, self.relx, cb_display)
        
        if self.editing:
            if self.value:
                char_under_cur = 'X'
            else:
                char_under_cur = ' '
            if self.do_colors():
                self.parent.curses_pad.addstr(self.rely, self.relx + 1, char_under_cur, self.parent.theme_manager.findPair(self) | curses.A_STANDOUT)
            else:
                self.parent.curses_pad.addstr(self.rely,  self.relx + 1, curses.A_STANDOUT)
            
            
    
    


class Checkbox(_ToggleControl):
    False_box = '[ ]'
    True_box  = '[X]'
    
    def __init__(self, screen, value = False, **keywords):
        self.value = value
        super(Checkbox, self).__init__(screen, **keywords)
        
        self._create_label_area(screen)
        
        
        self.show_bold = False
        self.highlight = False
        self.important = False
        self.hide      = False
        
    def _create_label_area(self, screen):
        l_a_width = self.width - 5
        
        if l_a_width < 1:
             raise ValueError("Width of checkbox + label must be at least 6")
           
        self.label_area = Textfield(screen, rely=self.rely, relx=self.relx+5, 
                      width=self.width-5, value=self.name)
        

    def update(self, clear=True):
        if clear: self.clear()
        if self.hidden:
            self.clear()
            return False
        if self.hide: return True

        if self.value:
            cb_display = self.__class__.True_box
        else:
            cb_display = self.__class__.False_box
        
        if self.do_colors():    
            self.parent.curses_pad.addstr(self.rely, self.relx, cb_display, self.parent.theme_manager.findPair(self, 'CONTROL'))
        else:
            self.parent.curses_pad.addstr(self.rely, self.relx, cb_display)

        self._update_label_area()

    def _update_label_area(self, clear=True):
        self.label_area.value = self.name
        self._update_label_row_attributes(self.label_area, clear=clear)
    
    def _update_label_row_attributes(self, row, clear=True):
        if self.editing:
            row.highlight = True
        else:
            row.highlight = False
        
        if self.show_bold: 
            row.show_bold = True
        else: 
            row.show_bold = False
            
        if self.important:
            row.important = True
        else:
            row.important = False

        if self.highlight: 
            row.highlight = True
        else: 
            row.highlight = False

        row.update(clear=clear)
        
    def calculate_area_needed(self):
        return 1,0

class CheckBox(Checkbox):
    pass

   
class RoundCheckBox(Checkbox):
    False_box = '( )'
    True_box  = '(X)'
    
class CheckBoxMultiline(Checkbox):
    def _create_label_area(self, screen):    
        self.label_area = []
        for y in range(self.height):
            self.label_area.append(
               Textfield(screen, rely=self.rely+y, 
                           relx=self.relx+5, 
                           width=self.width-5, 
                           value=None) 
            )
    
    def _update_label_area(self, clear=True):
        for x in range(len(self.label_area)):
            if x >= len(self.name):
                self.label_area[x].value = ''
                self.label_area[x].hidden = True
            else:
                self.label_area[x].value = self.name[x]
                self.label_area[x].hidden = False
                self._update_label_row_attributes(self.label_area[x], clear=clear)
                
    def calculate_area_needed(self):
        return 0,0
        
class RoundCheckBoxMultiline(CheckBoxMultiline):
    False_box = '( )'
    True_box  = '(X)'
    

