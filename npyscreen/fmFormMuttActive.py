import weakref
import re
import curses
import collections
from . import fmFormMutt
from . import fmFormWithMenus
from . import npysNPSFilteredData
from . import wgtextbox

# This file defines Action Controllers
# and Widgets
# and Forms


##########################################################################################
# Action Controllers
##########################################################################################

class ActionControllerSimple(object):
    def __init__(self, parent=None):
        try:
            self.parent = weakref.proxy(parent)
        except:
            self.parent = parent
        self._action_list = []
        self.create()
    
    def create(self):
        pass
    
    def add_action(self, ident, function, live):
        ident = re.compile(ident)
        self._action_list.append({'identifier': ident, 
                                  'function': function, 
                                  'live': live 
                                  })
    
    def process_command_live(self, command_line, control_widget_proxy):
        for a in self._action_list:
            if a['identifier'].match(command_line) and a['live']==True:
                a['function'](command_line, control_widget_proxy, live=True)
                
    def process_command_complete(self, command_line, control_widget_proxy):
        for a in self._action_list:
            if a['identifier'].match(command_line):
                a['function'](command_line, control_widget_proxy, live=False)


##########################################################################################
# Widgets
##########################################################################################

class TextCommandBox(wgtextbox.Textfield):
    def __init__(self, screen, 
                    history=False, 
                    history_max=100, 
                    set_up_history_keys=False,
                    *args, **keywords):
        super(TextCommandBox, self).__init__(screen, *args, **keywords)
        self.history = history
        self._history_store = collections.deque(maxlen=history_max)        
        self._current_history_index = False
        self._current_command = None
        if set_up_history_keys:
            self.set_up_history_keys()
        
        # History functions currently not complete.
        
    def set_up_handlers(self):
        super(TextCommandBox, self).set_up_handlers()
        self.handlers.update({
                   curses.ascii.NL:     self.h_execute_command,
                   curses.ascii.CR:     self.h_execute_command,
        })
    
    def set_up_history_keys(self):
        self.handlers.update({
            "^P":   self.h_get_previous_history,
            "^N":   self.h_get_next_history,
            curses.KEY_UP: self.h_get_previous_history,
            curses.KEY_DOWN: self.h_get_next_history,
        })
    
    def h_get_previous_history(self, ch):
        if self._current_history_index is False:
            self._current_command = self.value
            _current_history_index = -1
        else:
            _current_history_index = self._current_history_index - 1
        try:
            self.value = self._history_store[_current_history_index]
        except IndexError:
            return True
        self.cursor_position = len(self.value)
        self._current_history_index = _current_history_index
        self.display()
    
    def h_get_next_history(self, ch):
        if self._current_history_index is False:
            return True
        elif self._current_history_index == -1:
            self.value = self._current_command
            self._current_history_index = False
            self.cursor_position = len(self.value)
            self.display()
            return True
        else:
            _current_history_index = self._current_history_index + 1
        try:
            self.value = self._history_store[_current_history_index]
        except IndexError:
            return True
        self.cursor_position = len(self.value)
        self._current_history_index = _current_history_index
        self.display()

    def h_execute_command(self, *args, **keywords):
        if self.history:
            self._history_store.append(self.value)
            self._current_history_index = False
        self.parent.action_controller.process_command_complete(self.value, weakref.proxy(self))
        self.value = ''
        
    def when_value_edited(self):
        super(TextCommandBox, self).when_value_edited()
        if self.editing:
            self.parent.action_controller.process_command_live(self.value, weakref.proxy(self))
        else:
            self.parent.action_controller.process_command_complete(self.value, weakref.proxy(self))

class TextCommandBoxTraditional(TextCommandBox):
    # EXPERIMENTAL
    # WILL PASS INPUT TO A LINKED WIDGET - THE LINKED WIDGET
    # UNLESS PUT IN TO COMMAND LINE MODE BY THE ENTRY OF BEGINNING_OF_COMMAND_LINE_CHARS
    # WILL NEED TO BE ALTERED TO LOOK AS IF IT IS BEING EDITED TOO.
    BEGINNING_OF_COMMAND_LINE_CHARS = (":", "/")
    def __init__(self, screen,
                    history=True, 
                    history_max=100, 
                    set_up_history_keys=True,
                    *args, **keywords):
        super(TextCommandBoxTraditional, self).__init__(screen,
         history=history,
         history_max=history_max, 
         set_up_history_keys=set_up_history_keys,
         *args, **keywords
        )
        self.linked_widget = None
        self.always_pass_to_linked_widget = []
    
    def handle_input(self, inputch):
        try:
            inputchstr = chr(inputch)
        except:
            inputchstr = False
        
        try:
            input_unctrl = curses.ascii.unctrl(inputch)
        except TypeError:
            input_unctrl = False
            
        if not self.linked_widget:
            return super(TextCommandBoxTraditional, self).handle_input(inputch)
        
        if (inputch in self.always_pass_to_linked_widget) or \
            (inputchstr in self.always_pass_to_linked_widget) or \
            (input_unctrl in self.always_pass_to_linked_widget):
            rtn = self.linked_widget.handle_input(inputch)
            self.linked_widget.update()
            return rtn

        if inputchstr and (self.value == '' or self.value == None):
            if inputchstr in self.BEGINNING_OF_COMMAND_LINE_CHARS or \
                inputch in self.BEGINNING_OF_COMMAND_LINE_CHARS:
                return super(TextCommandBoxTraditional, self).handle_input(inputch)
            
        if self.value:
            return super(TextCommandBoxTraditional, self).handle_input(inputch)
        
        rtn = self.linked_widget.handle_input(inputch)
        self.linked_widget.update()
        return rtn


##########################################################################################
# Form Classes
##########################################################################################

class FormMuttActive(fmFormMutt.FormMutt):
    DATA_CONTROLER    = npysNPSFilteredData.NPSFilteredDataList
    ACTION_CONTROLLER  = ActionControllerSimple
    COMMAND_WIDGET_CLASS = TextCommandBox
    def __init__(self, *args, **keywords):
        # first create action_controller, so that the create methods
        # of forms can use it.
        self.action_controller = self.ACTION_CONTROLLER(parent=self)
        # then call the superclass init method.
        super(FormMuttActive, self).__init__(*args, **keywords)
        self.set_value(self.DATA_CONTROLER())
        

class FormMuttActiveWithMenus(FormMuttActive, fmFormWithMenus.FormBaseNewWithMenus):
    def __init__(self, *args, **keywords):
        super(FormMuttActiveWithMenus, self).__init__(*args, **keywords)
        self.initialize_menus()
        
class FormMuttActiveTraditional(fmFormMutt.FormMutt):
    DATA_CONTROLER    = npysNPSFilteredData.NPSFilteredDataList
    ACTION_CONTROLLER  = ActionControllerSimple
    COMMAND_WIDGET_CLASS = TextCommandBoxTraditional
    def __init__(self, *args, **keywords):
        # First create action_controller so that create methods of forms 
        # can use it.
        self.action_controller        = self.ACTION_CONTROLLER(parent=self)
        super(FormMuttActiveTraditional, self).__init__(*args, **keywords)
        self.set_value(self.DATA_CONTROLER())
        self.wCommand.linked_widget   = self.wMain
        self.wMain.editable           = False
        self.wMain.always_show_cursor = True
        
        # special mouse handling
        self.wMain.interested_in_mouse_even_when_not_editable = True

class FormMuttActiveTraditionalWithMenus(FormMuttActiveTraditional, 
 fmFormWithMenus.FormBaseNewWithMenus):
    def __init__(self, *args, **keywords):
        super(FormMuttActiveTraditionalWithMenus, self).__init__(*args, **keywords)
        self.initialize_menus()