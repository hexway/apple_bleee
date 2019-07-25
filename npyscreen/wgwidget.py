#!/usr/bin/python
import codecs
import copy
import sys
import curses
import curses.ascii
#import curses.wrapper
import weakref
from . import npysGlobalOptions as GlobalOptions
from . import wgwidget_proto
import locale
import warnings

from .globals import DEBUG

# experimental
from .eveventhandler import EventHandler



EXITED_DOWN  =  1
EXITED_UP    = -1
EXITED_LEFT  = -2
EXITED_RIGHT =  2
EXITED_ESCAPE= 127
EXITED_MOUSE = 130

SETMAX       = 'SETMAX'
RAISEERROR   = 'RAISEERROR'

ALLOW_NEW_INPUT = True

TEST_SETTINGS = {
    'TEST_INPUT': None,
    'TEST_INPUT_LOG': [],
    'CONTINUE_AFTER_TEST_INPUT': False,
    'INPUT_GENERATOR': None,
    }


def add_test_input_from_iterable(test_input):
    global TEST_SETTINGS
    if not TEST_SETTINGS['TEST_INPUT']:
        TEST_SETTINGS['TEST_INPUT'] = []
    TEST_SETTINGS['TEST_INPUT'].extend([ch for ch in test_input])
    
def add_test_input_ch(test_input):
    global TEST_SETTINGS
    if not TEST_SETTINGS['TEST_INPUT']:
        TEST_SETTINGS['TEST_INPUT'] = []
    TEST_SETTINGS['TEST_INPUT'].append(test_input)
    

class ExhaustedTestInput(Exception):
    pass

class NotEnoughSpaceForWidget(Exception):
    pass

class InputHandler(object):
    "An object that can handle user input"

    def handle_input(self, _input):
        """Returns True if input has been dealt with, and no further action needs taking.
        First attempts to look up a method in self.input_handers (which is a dictionary), then
        runs the methods in self.complex_handlers (if any), which is an array of form (test_func, dispatch_func).
        If test_func(input) returns true, then dispatch_func(input) is called. Check to see if parent can handle.
        No further action taken after that point."""
        
        if _input in self.handlers:
            self.handlers[_input](_input)
            return True
        
        try:
            _unctrl_input = curses.ascii.unctrl(_input)
        except TypeError:
            _unctrl_input = None
        
        if _unctrl_input and (_unctrl_input in self.handlers):
            self.handlers[_unctrl_input](_input)
            return True


        if not hasattr(self, 'complex_handlers'): 
            return False
        else:
            for test, handler in self.complex_handlers:
                if test(_input) is not False: 
                    handler(_input)
                    return True
        if hasattr(self, 'parent_widget') and hasattr(self.parent_widget, 'handle_input'):
            if self.parent_widget.handle_input(_input):
                return True
        elif hasattr(self, 'parent') and hasattr(self.parent, 'handle_input'):
            if self.parent.handle_input(_input):
                return True

        else:
            pass
    # If we've got here, all else has failed, so:
        return False

    def set_up_handlers(self):
        """This function should be called somewhere during object initialisation (which all library-defined widgets do). You might like to override this in your own definition,
but in most cases the add_handers or add_complex_handlers methods are what you want."""
        #called in __init__
        self.handlers = {
                   curses.ascii.NL:     self.h_exit_down,
                   curses.ascii.CR:     self.h_exit_down,
                   curses.ascii.TAB:    self.h_exit_down,
                   curses.KEY_BTAB:     self.h_exit_up,
                   curses.KEY_DOWN:     self.h_exit_down,
                   curses.KEY_UP:       self.h_exit_up,
                   curses.KEY_LEFT:     self.h_exit_left,
                   curses.KEY_RIGHT:    self.h_exit_right,
                   # "^P":                self.h_exit_up,
                   # "^N":                self.h_exit_down,
                   curses.ascii.ESC:    self.h_exit_escape,
                   curses.KEY_MOUSE:    self.h_exit_mouse,
                   }

        self.complex_handlers = []

    def add_handlers(self, handler_dictionary):
        """Update the dictionary of simple handlers.  Pass in a dictionary with keyname (eg "^P" or curses.KEY_DOWN) as the key, and the function that key should call as the values """
        self.handlers.update(handler_dictionary)
    
    def add_complex_handlers(self, handlers_list):
        """add complex handlers: format of the list is pairs of
        (test_function, callback) sets"""

        for pair in handlers_list:
            assert len(pair) == 2
        self.complex_handlers.extend(handlers_list)
        
    def remove_complex_handler(self, test_function):
        _new_list = []
        for pair in self.complex_handlers:
            if not pair[0] == test_function:
                _new_list.append(pair)
        self.complex_handlers = _new_list

###########################################################################################
# Handler Methods here - npc convention - prefix with h_

    def h_exit_down(self, _input):
        """Called when user leaves the widget to the next widget"""
        if not self._test_safe_to_exit():
            return False
        self.editing = False
        self.how_exited = EXITED_DOWN
        
    def h_exit_right(self, _input):
        if not self._test_safe_to_exit():
            return False
        self.editing = False
        self.how_exited = EXITED_RIGHT

    def h_exit_up(self, _input):
        if not self._test_safe_to_exit():
            return False
        """Called when the user leaves the widget to the previous widget"""
        self.editing = False
        self.how_exited = EXITED_UP
        
    def h_exit_left(self, _input):
        if not self._test_safe_to_exit():
            return False
        self.editing = False
        self.how_exited = EXITED_LEFT
        
    def h_exit_escape(self, _input):
        if not self._test_safe_to_exit():
            return False
        self.editing = False
        self.how_exited = EXITED_ESCAPE

    def h_exit_mouse(self, _input):
        mouse_event = self.parent.safe_get_mouse_event()
        if mouse_event and self.intersted_in_mouse_event(mouse_event):
            self.handle_mouse_event(mouse_event)
        else:
            if mouse_event and self._test_safe_to_exit():
                curses.ungetmouse(*mouse_event)
                ch = self.parent.curses_pad.getch()
                assert ch == curses.KEY_MOUSE
            self.editing = False
            self.how_exited = EXITED_MOUSE
    
    



class Widget(InputHandler, wgwidget_proto._LinePrinter, EventHandler):
    "A base class for widgets. Do not use directly"
    
    _SAFE_STRING_STRIPS_NL = True
    
    def destroy(self):
        """Destroy the widget: methods should provide a mechanism to destroy any references that might
        case a memory leak.  See select. module for an example"""
        pass
        
    def __init__(self, screen, 
            relx=0, rely=0, name=None, value=None, 
            width = False, height = False,
            max_height = False, max_width=False,
            editable=True,
            hidden=False,
            color='DEFAULT',
            use_max_space=False,
            check_value_change=True,
            check_cursor_move=True,
            value_changed_callback=None,
            **keywords):
        """The following named arguments may be supplied:
        name= set the name of the widget.
        width= set the width of the widget.
        height= set the height.
        max_height= let the widget choose a height up to this maximum.
        max_width=  let the widget choose a width up to this maximum.
        editable=True/False the user may change the value of the widget.
        hidden=True/False The widget is hidden.
        check_value_change=True - perform a check on every keypress and run when_value_edit if the value is different.
        check_cursor_move=True - perform a check every keypress and run when_cursor_moved if the cursor has moved.
        value_changed_callback - should be None or a Function.  If it is a function, it will have be called when the value changes
                               and passed the keyword argument widget=self.
        """
        self.check_value_change=check_value_change
        self.check_cursor_move =check_cursor_move
        self.hidden = hidden
        self.interested_in_mouse_even_when_not_editable = False# used only for rare widgets to allow user to click
                                                        # even if can't actually select the widget.  See mutt-style forms
                                                        
        try:
            self.parent = weakref.proxy(screen)
        except TypeError:
            self.parent = screen
        self.use_max_space = use_max_space    
        self.set_relyx(rely, relx)
        #self.relx = relx
        #self.rely = rely
        self.color = color
        self.encoding = 'utf-8'#locale.getpreferredencoding()
        if GlobalOptions.ASCII_ONLY or locale.getpreferredencoding() == 'US-ASCII':
            self._force_ascii = True
        else:
            self._force_ascii = False
        
        
        self.set_up_handlers()
        
        # To allow derived classes to set this and then call this method safely...
        try:
            self.value
        except AttributeError:
            self.value = value

        # same again
        try:
            self.name
        except:
            self.name=name
            
        self.request_width =  width     # widgets should honour if possible
        self.request_height = height    # widgets should honour if possible

        self.max_height = max_height
        self.max_width = max_width

        self.set_size()

        self.editing = False        # Change to true during an edit
        
        self.editable = editable
        if self.parent.curses_pad.getmaxyx()[0]-1 == self.rely: self.on_last_line = True
        else: self.on_last_line = False
        
        if value_changed_callback:
            self.value_changed_callback = value_changed_callback
        else:
            self.value_changed_callback = None
        
        self.initialize_event_handling()
    
    def set_relyx(self, y, x):
        """
        Set the position of the widget on the Form.  If y or x is a negative value,
        npyscreen will try to position it relative to the bottom or right edge of the 
        Form.  Note that this ignores any margins that the Form may have defined.
        This is currently an experimental feature.  A future version of the API may 
        take account of the margins set by the parent Form.
        """
        self._requested_rely = y
        self._requested_relx = x
        if y >= 0:
            self.rely = y
        else:
            self._requested_rely = y
            self.rely = self.parent.curses_pad.getmaxyx()[0] + y
            # I don't think there is any real value in using these margins
            #if self.parent.BLANK_LINES_BASE and not self.use_max_space:
            #    self.rely -= self.parent.BLANK_LINES_BASE
            if self.rely < 0:
                self.rely = 0
        if x >= 0:
            self.relx = x            
        else:
            self.relx = self.parent.curses_pad.getmaxyx()[1] + x
            # I don't think there is any real value in using these margins
            #if self.parent.BLANK_COLUMNS_RIGHT and not self.use_max_space:
            #    self.relx -= self.parent.BLANK_COLUMNS_RIGHT
            if self.relx < 0:
                self.relx = 0
    
    def _move_widget_on_terminal_resize(self):
        if self._requested_rely < 0 or self._requested_relx < 0:
            self.set_relyx(self._requested_rely, self._requested_relx)
    
    def _resize(self):
        "Internal Method. This will be the method called when the terminal resizes."
        self._move_widget_on_terminal_resize()
        self._recalculate_size()
        if self.parent.curses_pad.getmaxyx()[0]-1 == self.rely: self.on_last_line = True
        else: self.on_last_line = False
        self.resize()
        self.when_resized()
    
    def resize(self):
        "Widgets should override this to control what should happen when they are resized."
        pass
        
    def _recalculate_size(self):
        return self.set_size()
    
    def when_resized(self):
        # this method is called when the widget has been resized.
        pass
    
        
    def do_colors(self):
        "Returns True if the widget should try to paint in coloour."
        if curses.has_colors() and not GlobalOptions.DISABLE_ALL_COLORS:
            return True
        else:
            return False
        
    def space_available(self):
        """The space available left on the screen, returned as rows, columns"""
        if self.use_max_space:
            y, x = self.parent.useable_space(self.rely, self.relx)
        else:
            y, x = self.parent.widget_useable_space(self.rely, self.relx)
        return y,x

    def calculate_area_needed(self): 
        """Classes should provide a function to
calculate the screen area they need, returning either y,x, or 0,0 if
they want all the screen they can.  However, do not use this to say how
big a given widget is ... use .height and .width instead"""
        return 0,0

    def set_size(self):
        """Set the size of the object, reconciling the user's request with the space available"""
        my, mx = self.space_available()
        #my = my+1 # Probably want to remove this.
        ny, nx = self.calculate_area_needed()
        
        max_height = self.max_height
        max_width  = self.max_width
        # What to do if max_height or max_width is negative
        if max_height not in (None, False) and max_height < 0:
            max_height = my + max_height
        if max_width not in (None, False) and max_width < 0:
            max_width = mx + max_width
            
        if max_height not in (None, False) and max_height <= 0:
            raise NotEnoughSpaceForWidget("Not enough space for requested size")  
        if max_width not in (None, False) and max_width <= 0:
            raise NotEnoughSpaceForWidget("Not enough space for requested size")
        
        if ny > 0:
            if my >= ny: 
                self.height = ny
            else: 
                self.height = RAISEERROR
        elif max_height:
            if max_height <= my: 
                self.height = max_height
            else: 
                self.height = self.request_height
        else: 
            self.height = (self.request_height or my)
        
        #if mx <= 0 or my <= 0:
        #    raise Exception("Not enough space for widget")


        if nx > 0:                 # if a minimum space is specified....
            if mx >= nx:           # if max width is greater than needed space 
                self.width = nx    # width is needed space
            else: 
                self.width = RAISEERROR    # else raise an error
        elif self.max_width:       # otherwise if a max width is speciied
            if max_width <= mx: 
                self.width = max_width
            else: 
                self.width = RAISEERROR
        else: 
            self.width = self.request_width or mx

        if self.height == RAISEERROR or self.width == RAISEERROR:
            # Not enough space for widget
            raise NotEnoughSpaceForWidget("Not enough space: max y and x = %s , %s. Height and Width = %s , %s " % (my, mx, self.height, self.width) ) # unsafe. Need to add error here.
    
    def update(self, clear=True):
        """How should object display itself on the screen. Define here, but do not actually refresh the curses
        display, since this should be done as little as possible.  This base widget puts nothing on screen."""
        if self.hidden:
            self.clear()
            return True

    def display(self):
        """Do an update of the object AND refresh the screen"""
        if self.hidden:
            self.clear()
            self.parent.refresh()
        else:
            self.update()
            self.parent.refresh()

    def set_editable(self, value):
        if value: self._is_editable = True
        else: self._is_editable = False

    def get_editable(self):
        return(self._is_editable)

    def clear(self, usechar=' '):
        """Blank the screen area used by this widget, ready for redrawing"""
        for y in range(self.height):
#This method is too slow
#           for x in range(self.width+1):
#               try:
#                   # We are in a try loop in case the cursor is moved off the bottom right corner of the screen
#                   self.parent.curses_pad.addch(self.rely+y, self.relx + x, usechar)
#               except: pass
#Use this instead
            if self.do_colors():
                self.parent.curses_pad.addstr(self.rely+y, self.relx, usechar * (self.width), self.parent.theme_manager.findPair(self, self.parent.color))  # used to be width + 1
            else:
                self.parent.curses_pad.addstr(self.rely+y, self.relx, usechar * (self.width))  # used to be width + 1

    def edit(self):
        """Allow the user to edit the widget: ie. start handling keypresses."""
        self.editing = 1
        self._pre_edit()
        self._edit_loop()
        return self._post_edit()

    def _pre_edit(self):
        self.highlight = 1
        old_value = self.value
        self.how_exited = False

    def _edit_loop(self):
        if not self.parent.editing:
            _i_set_parent_editing = True
            self.parent.editing   = True
        else:
            _i_set_parent_editing = False
        while self.editing and self.parent.editing:
            self.display()
            self.get_and_use_key_press()
        if _i_set_parent_editing:
            self.parent.editing = False
        
        if self.editing:
            self.editing    = False
            self.how_exited = True

    def _post_edit(self):
        self.highlight = 0
        self.update()
        
    def _get_ch(self):
        #try:
        #    # Python3.3 and above - returns unicode
        #    ch = self.parent.curses_pad.get_wch()
        #    self._last_get_ch_was_unicode = True
        #except AttributeError:
            
        # For now, disable all attempt to use get_wch()
        # but everything that follows could be in the except clause above.
        
            # Try to read utf-8 if possible.
        _stored_bytes =[]
        self._last_get_ch_was_unicode = True
        global ALLOW_NEW_INPUT
        if ALLOW_NEW_INPUT == True and locale.getpreferredencoding() == 'UTF-8':
            ch = self.parent.curses_pad.getch()
            if ch <= 127:
                rtn_ch = ch
                self._last_get_ch_was_unicode = False
                return rtn_ch
            elif ch <= 193:
                rtn_ch = ch
                self._last_get_ch_was_unicode = False
                return rtn_ch
            # if we are here, we need to read 1, 2 or 3 more bytes.
            # all of the subsequent bytes should be in the range 128 - 191, 
            # but we'll risk not checking...
            elif 194 <= ch <= 223: 
                    # 2 bytes
                    _stored_bytes.append(ch)
                    _stored_bytes.append(self.parent.curses_pad.getch())
            elif 224 <= ch <= 239: 
                    # 3 bytes 
                    _stored_bytes.append(ch)
                    _stored_bytes.append(self.parent.curses_pad.getch()) 
                    _stored_bytes.append(self.parent.curses_pad.getch()) 
            elif 240 <= ch <= 244: 
                    # 4 bytes 
                    _stored_bytes.append(ch) 
                    _stored_bytes.append(self.parent.curses_pad.getch()) 
                    _stored_bytes.append(self.parent.curses_pad.getch()) 
                    _stored_bytes.append(self.parent.curses_pad.getch())
            elif ch >= 245:
                # probably a control character
                self._last_get_ch_was_unicode = False
                return ch
            
            if sys.version_info[0] >= 3:
                ch = bytes(_stored_bytes).decode('utf-8', errors='strict')
            else:
                ch = ''.join([chr(b) for b in _stored_bytes])
                ch = ch.decode('utf-8')
        else:
            ch = self.parent.curses_pad.getch()
            self._last_get_ch_was_unicode = False
        
        # This line should not be in the except clause.
        return ch

    def try_adjust_widgets(self):
        if hasattr(self.parent, "adjust_widgets"):
            self.parent.adjust_widgets()
        if hasattr(self.parent, "parentApp"):
            if hasattr(self.parent.parentApp, "_internal_adjust_widgets"):
                self.parent.parentApp._internal_adjust_widgets()
            if hasattr(self.parent.parentApp, "adjust_widgets"):
                self.parent.parentApp.adjust_widgets()
            
    
    def try_while_waiting(self):
        if hasattr(self.parent, "while_waiting"):
            self.parent.while_waiting()
        if hasattr(self.parent, "parentApp"):
            if hasattr(self.parent.parentApp, "_internal_while_waiting"):
                self.parent.parentApp._internal_while_waiting()
            if hasattr(self.parent.parentApp, "while_waiting"):
                self.parent.parentApp.while_waiting()

    def get_and_use_key_press(self):
        global TEST_SETTINGS
        if (TEST_SETTINGS['TEST_INPUT'] is None) and (TEST_SETTINGS['INPUT_GENERATOR'] is None):
            curses.raw()
            curses.cbreak()
            curses.meta(1)
            self.parent.curses_pad.keypad(1)
            if self.parent.keypress_timeout:
                curses.halfdelay(self.parent.keypress_timeout)
                ch = self._get_ch()
                if ch == -1:
                    return self.try_while_waiting()
            else:
                self.parent.curses_pad.timeout(-1)
                ch = self._get_ch()
            # handle escape-prefixed rubbish.
            if ch == curses.ascii.ESC:
                #self.parent.curses_pad.timeout(1)
                self.parent.curses_pad.nodelay(1)
                ch2 = self.parent.curses_pad.getch()
                if ch2 != -1: 
                    ch = curses.ascii.alt(ch2)
                self.parent.curses_pad.timeout(-1) # back to blocking mode
                #curses.flushinp()
        elif (TEST_SETTINGS['INPUT_GENERATOR']):
            self._last_get_ch_was_unicode = True
            try:
                ch = next(TEST_SETTINGS['INPUT_GENERATOR'])
            except StopIteration:
                if TEST_SETTINGS['CONTINUE_AFTER_TEST_INPUT']:
                    TEST_SETTINGS['INPUT_GENERATOR'] = None
                    return
                else:
                    raise ExhaustedTestInput
        else:
            self._last_get_ch_was_unicode = True
            try:
                ch = TEST_SETTINGS['TEST_INPUT'].pop(0)
                TEST_SETTINGS['TEST_INPUT_LOG'].append(ch)
            except IndexError:
                if TEST_SETTINGS['CONTINUE_AFTER_TEST_INPUT']:
                    TEST_SETTINGS['TEST_INPUT'] = None
                    return
                else:
                    raise ExhaustedTestInput
        
        self.handle_input(ch)
        if self.check_value_change:
            self.when_check_value_changed()
        if self.check_cursor_move:
            self.when_check_cursor_moved()
        
        
        self.try_adjust_widgets()
            
    def intersted_in_mouse_event(self, mouse_event):
        if not self.editable and not self.interested_in_mouse_even_when_not_editable:
            return False
        mouse_id, x, y, z, bstate = mouse_event
        x += self.parent.show_from_x
        y += self.parent.show_from_y
        if self.relx <= x <= self.relx + self.width-1 + self.parent.show_atx:
            if self.rely  <= y <= self.rely + self.height-1 + self.parent.show_aty:
                return True
        return False
    
    def handle_mouse_event(self, mouse_event):
        # mouse_id, x, y, z, bstate = mouse_event
        pass
    
    def interpret_mouse_event(self, mouse_event):
        mouse_id, x, y, z, bstate = mouse_event
        x += self.parent.show_from_x
        y += self.parent.show_from_y
        rel_y       = y - self.rely - self.parent.show_aty
        rel_x = x - self.relx - self.parent.show_atx
        return (mouse_id, rel_x, rel_y, z, bstate)
        
    #def when_parent_changes_value(self):
        # Can be called by forms when they chage their value.
        #pass

    def _safe_to_exit(self):
        return True
        
    def safe_to_exit(self):
        return True
    
    def _test_safe_to_exit(self):
        if self._safe_to_exit() and self.safe_to_exit():
            return True
        else:
            return False
    

    def when_check_value_changed(self):
        "Check whether the widget's value has changed and call when_valued_edited if so."
        try:
            if self.value == self._old_value:
                return False
        except AttributeError:
            self._old_value = copy.deepcopy(self.value)
            self.when_value_edited()
        # Value must have changed:
        self._old_value = copy.deepcopy(self.value)
        self._internal_when_value_edited()
        self.when_value_edited()
        if hasattr(self, 'parent_widget'):
            self.parent_widget.when_value_edited()
            self.parent_widget._internal_when_value_edited()
        return True
    
    def _internal_when_value_edited(self):
        if self.value_changed_callback:
            return self.value_changed_callback(widget=self)
    
    def when_value_edited(self):
        """Called when the user edits the value of the widget.  Will usually also be called the first time
        that the user edits the widget."""
        pass
    
    def when_check_cursor_moved(self):
        if hasattr(self, 'cursor_line'):
            cursor = self.cursor_line
        elif hasattr(self, 'cursor_position'):
            cursor = self.cursor_position
        elif hasattr(self, 'edit_cell'):
            cursor = copy.copy(self.edit_cell)
        else:
            return None
        try:
            if self._old_cursor == cursor:
                return False
        except AttributeError:
            pass
        # Value must have changed:
        self._old_cursor = cursor
        self.when_cursor_moved()
        if hasattr(self, 'parent_widget'):
            self.parent_widget.when_cursor_moved()
        
    def when_cursor_moved(self):
        "Called when the cursor moves"
        pass

    def safe_string(self, this_string):
        """Check that what you are trying to display contains only
        printable chars.  (Try to catch dodgy input).  Give it a string,
        and it will return a string safe to print - without touching
        the original.  In Python 3 this function is not needed
        
        N.B. This will return a unicode string on python 3 and a utf-8 string
        on python2
        """
        try:
            if not this_string: 
                return ""
            #this_string = str(this_string)
            # In python 3
            #if sys.version_info[0] >= 3:
            #    return this_string.replace('\n', ' ')
            if self.__class__._SAFE_STRING_STRIPS_NL == True:
                rtn_value = this_string.replace('\n', ' ')
            else:
                rtn_value = this_string
        
            # Does the terminal want ascii?
            if self._force_ascii:
                if isinstance(rtn_value, bytes):
                    # no it isn't.
                    try:
                        rtn_value = rtn_value.decode(self.encoding, 'replace')
                    except TypeError:
                        # Python2.6
                        rtn_value = rtn_value.decode(self.encoding, 'replace')
                else:
                    if sys.version_info[0] >= 3:
                        # even on python3, in this case, we want a string that
                        # contains only ascii chars - but in unicode, so:
                        rtn_value = rtn_value.encode('ascii', 'replace').decode()
                        return rtn_value     
                    else:
                        return rtn_value.encode('ascii', 'replace')
                return rtn_value
            # If not....
            if not GlobalOptions.ASCII_ONLY:
                # is the string already unicode?
                if isinstance(rtn_value, bytes):
                    # no it isn't.
                    try:
                        rtn_value = rtn_value.decode(self.encoding, 'replace')
                    except:
                        # Python2.6
                        rtn_value = rtn_value.decode(self.encoding, 'replace')
                if sys.version_info[0] >= 3:
                    return rtn_value     
                else:
                    return rtn_value.encode('utf-8', 'replace')
            else:
                rtn = self.safe_filter(this_string)
                return rtn
        except:
            if DEBUG:
                raise
            else:
                return "*ERROR DISPLAYING STRING*"
    
    def safe_filter(self, this_string):
        try:
            this_string = this_string.decode(self.encoding, 'replace')
            return this_string.encode('ascii', 'replace').decode()
        except:
            # Things have gone badly wrong if we get here, but let's try to salvage it.
            try:
                if self._safe_filter_value_cache[0] == this_string:
                    return self._safe_filter_value_cache[1]
            except AttributeError:
                pass
            s = []
            for cha in this_string.replace('\n', ' '):
                #if curses.ascii.isprint(cha):
                #    s.append(cha)
                #else:
                #    s.append('?')
                try:
                    s.append(str(cha))
                except:
                    s.append('?')
            s = ''.join(s)
        
            self._safe_filter_value_cache = (this_string, s)
        
            return s
        
        #s = ''
        #for cha in this_string.replace('\n', ''):
        #    try:
        #        s += cha.encode('ascii')
        #    except:
        #        s += '?'
        #return s
        
class DummyWidget(Widget):
    "This widget is invisible and does nothing.  Which is sometimes important."
    def __init__(self, screen, *args, **keywords):
        super(DummyWidget, self).__init__(screen, *args, **keywords)
        self.height = 0
        self.widget = 0
        self.parent = screen
    def display(self):
        pass
    def update(self, clear=False):
        pass
    def set_editable(self, value):
        if value: self._is_editable = True
        else: self._is_editable = False
    def get_editable(self):
        return(self._is_editable)
    def clear(self, usechar=' '):
        pass
    def calculate_area_needed(self):
        return 0,0


