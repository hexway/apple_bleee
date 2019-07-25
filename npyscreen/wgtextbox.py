#!/usr/bin/python
import curses
import curses.ascii
import sys
import locale
#import curses.wrapper
from . import wgwidget as widget
from . import npysGlobalOptions as GlobalOptions

class TextfieldBase(widget.Widget):
    ENSURE_STRING_VALUE = True
    def __init__(self, screen, value='', highlight_color='CURSOR', highlight_whole_widget=False,
        invert_highlight_color=True,
        **keywords):
        try:
            self.value = value or ""
        except:
            self.value = ""
        
        
        super(TextfieldBase, self).__init__(screen, **keywords)

        if GlobalOptions.ASCII_ONLY or locale.getpreferredencoding() == 'US-ASCII':
            self._force_ascii = True
        else:
            self._force_ascii = False
        
        self.cursor_position = False
        
        self.highlight_color = highlight_color
        self.highlight_whole_widget = highlight_whole_widget
        self.invert_highlight_color = invert_highlight_color
        self.show_bold = False
        self.highlight = False
        self.important = False
        
        self.syntax_highlighting = False
        self._highlightingdata   = None
        self.left_margin = 0
        
        self.begin_at = 0   # Where does the display string begin?
    
        self.set_text_widths()
        self.update()
        
    def set_text_widths(self):
        if self.on_last_line:
            self.maximum_string_length = self.width - 2  # Leave room for the cursor
        else:   
            self.maximum_string_length = self.width - 1  # Leave room for the cursor at the end of the string.

    def resize(self):
        self.set_text_widths()

    
    def calculate_area_needed(self):
        "Need one line of screen, and any width going"
        return 1,0

    def update(self, clear=True, cursor=True):
        """Update the contents of the textbox, without calling the final refresh to the screen"""
        # cursor not working. See later for a fake cursor
        #if self.editing: pmfuncs.show_cursor()
        #else: pmfuncs.hide_cursor()

        # Not needed here -- gets called too much!
        #pmfuncs.hide_cursor()
        
        if clear: self.clear()
        
        if self.hidden:
            return True
        
        value_to_use_for_calculations = self.value        
        
        if self.ENSURE_STRING_VALUE:
            if value_to_use_for_calculations in (None, False, True):
                value_to_use_for_calculations = ''
                self.value = ''

        if self.begin_at < 0: self.begin_at = 0
        
        if self.left_margin >= self.maximum_string_length:
            raise ValueError
        
        if self.editing:
            if isinstance(self.value, bytes):
                # use a unicode version of self.value to work out where the cursor is.
                # not always accurate, but better than the bytes
                value_to_use_for_calculations = self.display_value(self.value).decode(self.encoding, 'replace')
            if cursor:
                if self.cursor_position is False:
                    self.cursor_position = len(value_to_use_for_calculations)

                elif self.cursor_position > len(value_to_use_for_calculations):
                    self.cursor_position = len(value_to_use_for_calculations)

                elif self.cursor_position < 0:
                    self.cursor_position = 0

                if self.cursor_position < self.begin_at:
                    self.begin_at = self.cursor_position

                while self.cursor_position > self.begin_at + self.maximum_string_length - self.left_margin: # -1:
                    self.begin_at += 1
            else:
                if self.do_colors():
                    self.parent.curses_pad.bkgdset(' ', self.parent.theme_manager.findPair(self, self.highlight_color) | curses.A_STANDOUT)
                else:
                    self.parent.curses_pad.bkgdset(' ',curses.A_STANDOUT)



        # Do this twice so that the _print method can ignore it if needed.
        if self.highlight:
            if self.do_colors():
                if self.invert_highlight_color:
                    attributes=self.parent.theme_manager.findPair(self, self.highlight_color) | curses.A_STANDOUT
                else:
                    attributes=self.parent.theme_manager.findPair(self, self.highlight_color)
                self.parent.curses_pad.bkgdset(' ', attributes)
            else:
                self.parent.curses_pad.bkgdset(' ',curses.A_STANDOUT)
            

        if self.show_bold:
            self.parent.curses_pad.attron(curses.A_BOLD)
        if self.important and not self.do_colors():
            self.parent.curses_pad.attron(curses.A_UNDERLINE)


        self._print()
        
        
        

        # reset everything to normal
        self.parent.curses_pad.attroff(curses.A_BOLD)
        self.parent.curses_pad.attroff(curses.A_UNDERLINE)
        self.parent.curses_pad.bkgdset(' ',curses.A_NORMAL)
        self.parent.curses_pad.attrset(0)
        if self.editing and cursor:
            self.print_cursor()
    
    def print_cursor(self):
        # This needs fixing for Unicode multi-width chars.

        # Cursors do not seem to work on pads.
        #self.parent.curses_pad.move(self.rely, self.cursor_position - self.begin_at)
        # let's have a fake cursor
        _cur_loc_x = self.cursor_position - self.begin_at + self.relx + self.left_margin
        # The following two lines work fine for ascii, but not for unicode
        #char_under_cur = self.parent.curses_pad.inch(self.rely, _cur_loc_x)
        #self.parent.curses_pad.addch(self.rely, self.cursor_position - self.begin_at + self.relx, char_under_cur, curses.A_STANDOUT)
        #The following appears to work for unicode as well.
        try:
            #char_under_cur = self.value[self.cursor_position] #use the real value
            char_under_cur = self._get_string_to_print()[self.cursor_position]
            char_under_cur = self.safe_string(char_under_cur)
        except IndexError:
            char_under_cur = ' '
        except TypeError:
            char_under_cur = ' '
        if self.do_colors():
            self.parent.curses_pad.addstr(self.rely, self.cursor_position - self.begin_at + self.relx + self.left_margin, char_under_cur, self.parent.theme_manager.findPair(self, 'CURSOR_INVERSE'))
        else:
            self.parent.curses_pad.addstr(self.rely, self.cursor_position - self.begin_at + self.relx + self.left_margin, char_under_cur, curses.A_STANDOUT)
            

    def print_cursor_pre_unicode(self):
        # Cursors do not seem to work on pads.
        #self.parent.curses_pad.move(self.rely, self.cursor_position - self.begin_at)
        # let's have a fake cursor
        _cur_loc_x = self.cursor_position - self.begin_at + self.relx + self.left_margin
        # The following two lines work fine for ascii, but not for unicode
        #char_under_cur = self.parent.curses_pad.inch(self.rely, _cur_loc_x)
        #self.parent.curses_pad.addch(self.rely, self.cursor_position - self.begin_at + self.relx, char_under_cur, curses.A_STANDOUT)
        #The following appears to work for unicode as well.
        try:
            char_under_cur = self.display_value(self.value)[self.cursor_position]
        except:
            char_under_cur = ' '

        self.parent.curses_pad.addstr(self.rely, self.cursor_position - self.begin_at + self.relx + self.left_margin, char_under_cur, curses.A_STANDOUT)
        

    def display_value(self, value):
        if value == None:
            return ''
        else:
            try:
                str_value = str(value)
            except UnicodeEncodeError:
                str_value = self.safe_string(value)
                return str_value
            except ReferenceError:                
                return ">*ERROR*ERROR*ERROR*<"
            return self.safe_string(str_value)

    
    def find_width_of_char(self, ch):
        return 1
    
    def _print_unicode_char(self, ch):
        # return the ch to print.  For python 3 this is just ch
        if self._force_ascii:
            return ch.encode('ascii', 'replace')
        elif sys.version_info[0] >= 3:
            return ch
        else:
            return ch.encode('utf-8', 'strict')
    
    def _get_string_to_print(self):
        string_to_print = self.display_value(self.value)
        if not string_to_print:
            return None
        string_to_print = string_to_print[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin]
        
        if sys.version_info[0] >= 3:
            string_to_print = self.display_value(self.value)[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin]
        else:
            # ensure unicode only here encoding here.
            dv = self.display_value(self.value)
            if isinstance(dv, bytes):
                dv = dv.decode(self.encoding, 'replace')
            string_to_print = dv[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin]
        return string_to_print
    
    
    def _print(self):
        string_to_print = self._get_string_to_print()
        if not string_to_print:
            return None
        string_to_print = string_to_print[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin]
        
        if sys.version_info[0] >= 3:
            string_to_print = self.display_value(self.value)[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin]
        else:
            # ensure unicode only here encoding here.
            dv = self.display_value(self.value)
            if isinstance(dv, bytes):
                dv = dv.decode(self.encoding, 'replace')
            string_to_print = dv[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin]
        
        column = 0
        place_in_string = 0
        if self.syntax_highlighting:
            self.update_highlighting(start=self.begin_at, end=self.maximum_string_length+self.begin_at-self.left_margin)
            while column <= (self.maximum_string_length - self.left_margin):
                if not string_to_print or place_in_string > len(string_to_print)-1:
                    break
                width_of_char_to_print = self.find_width_of_char(string_to_print[place_in_string])
                if column - 1 + width_of_char_to_print > self.maximum_string_length:
                    break 
                try:
                    highlight = self._highlightingdata[self.begin_at+place_in_string]
                except:
                    highlight = curses.A_NORMAL                
                self.parent.curses_pad.addstr(self.rely,self.relx+column+self.left_margin, 
                    self._print_unicode_char(string_to_print[place_in_string]), 
                    highlight
                    )
                column += self.find_width_of_char(string_to_print[place_in_string])
                place_in_string += 1
        else:
            if self.do_colors():
                if self.show_bold and self.color == 'DEFAULT':
                    color = self.parent.theme_manager.findPair(self, 'BOLD') | curses.A_BOLD
                elif self.show_bold:
                    color = self.parent.theme_manager.findPair(self, self.color) | curses.A_BOLD
                elif self.important:
                    color = self.parent.theme_manager.findPair(self, 'IMPORTANT') | curses.A_BOLD
                else:
                    color = self.parent.theme_manager.findPair(self)
            else:
                if self.important or self.show_bold:
                    color = curses.A_BOLD
                else:
                    color = curses.A_NORMAL

            while column <= (self.maximum_string_length - self.left_margin):
                if not string_to_print or place_in_string > len(string_to_print)-1:
                    if self.highlight_whole_widget:
                        self.parent.curses_pad.addstr(self.rely,self.relx+column+self.left_margin, 
                            ' ', 
                            color
                            )
                        column += width_of_char_to_print
                        place_in_string += 1
                        continue
                    else:
                        break
                        
                width_of_char_to_print = self.find_width_of_char(string_to_print[place_in_string])
                if column - 1 + width_of_char_to_print > self.maximum_string_length:
                    break 
                self.parent.curses_pad.addstr(self.rely,self.relx+column+self.left_margin, 
                    self._print_unicode_char(string_to_print[place_in_string]), 
                    color
                    )
                column += width_of_char_to_print
                place_in_string += 1
    
    
    
    
    
    def _print_pre_unicode(self):
        # This method was used to print the string before we became interested in unicode.
        
        string_to_print = self.display_value(self.value)
        if string_to_print == None: return
        
        if self.syntax_highlighting:
            self.update_highlighting(start=self.begin_at, end=self.maximum_string_length+self.begin_at-self.left_margin)
            for i in range(len(string_to_print[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin])):
                try:
                    highlight = self._highlightingdata[self.begin_at+i]
                except:
                    highlight = curses.A_NORMAL
                self.parent.curses_pad.addstr(self.rely,self.relx+i+self.left_margin, 
                    string_to_print[self.begin_at+i], 
                    highlight 
                    )
        
        elif self.do_colors():
            coltofind = 'DEFAULT'
            if self.show_bold and self.color == 'DEFAULT':
                coltofind = 'BOLD'
            if self.show_bold:
                self.parent.curses_pad.addstr(self.rely,self.relx+self.left_margin, string_to_print[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin], 
                                                    self.parent.theme_manager.findPair(self, coltofind) | curses.A_BOLD)
            elif self.important:
                coltofind = 'IMPORTANT'
                self.parent.curses_pad.addstr(self.rely,self.relx+self.left_margin, string_to_print[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin], 
                                                    self.parent.theme_manager.findPair(self, coltofind) | curses.A_BOLD)
            else:
                self.parent.curses_pad.addstr(self.rely,self.relx+self.left_margin, string_to_print[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin], 
                                                self.parent.theme_manager.findPair(self))
        else:
            if self.important:
                self.parent.curses_pad.addstr(self.rely,self.relx+self.left_margin, 
                        string_to_print[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin], curses.A_BOLD)
            elif self.show_bold:
                self.parent.curses_pad.addstr(self.rely,self.relx+self.left_margin, 
                        string_to_print[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin], curses.A_BOLD)

            else:
                self.parent.curses_pad.addstr(self.rely,self.relx+self.left_margin, 
                    string_to_print[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin])
    
    def update_highlighting(self, start=None, end=None, clear=False):
        if clear or (self._highlightingdata == None):
            self._highlightingdata = []
        
        string_to_print = self.display_value(self.value)


class Textfield(TextfieldBase):
    def show_brief_message(self, message):
        curses.beep()
        keep_for_a_moment = self.value
        self.value = message
        self.editing=False
        self.display()
        curses.napms(1200)
        self.editing=True
        self.value = keep_for_a_moment
        

    def edit(self):
        self.editing = 1
        if self.cursor_position is False:
            self.cursor_position = len(self.value or '')
        self.parent.curses_pad.keypad(1)
        
        self.old_value = self.value
        
        self.how_exited = False

        while self.editing:
            self.display()
            self.get_and_use_key_press()

        self.begin_at = 0
        self.display()
        self.cursor_position = False
        return self.how_exited, self.value

    ###########################################################################################
    # Handlers and methods

    def set_up_handlers(self):
        super(Textfield, self).set_up_handlers()    
    
        # For OS X
        del_key = curses.ascii.alt('~')
        
        self.handlers.update({curses.KEY_LEFT:    self.h_cursor_left,
                           curses.KEY_RIGHT:   self.h_cursor_right,
                   curses.KEY_DC:      self.h_delete_right,
                   curses.ascii.DEL:   self.h_delete_left,
                   curses.ascii.BS:    self.h_delete_left,
                   curses.KEY_BACKSPACE: self.h_delete_left,
                   # mac os x curses reports DEL as escape oddly
                   # no solution yet                   
                   "^K":           self.h_erase_right,
                   "^U":           self.h_erase_left,
            })

        self.complex_handlers.extend((
                        (self.t_input_isprint, self.h_addch),
                        # (self.t_is_ck, self.h_erase_right),
                        # (self.t_is_cu, self.h_erase_left),
                        ))

    def t_input_isprint(self, inp):
        if self._last_get_ch_was_unicode and inp not in '\n\t\r':
            return True
        if curses.ascii.isprint(inp) and \
        (chr(inp) not in '\n\t\r'): 
            return True
        else: 
            return False
        
        
    def h_addch(self, inp):
        if self.editable:
            #self.value = self.value[:self.cursor_position] + curses.keyname(input) \
            #   + self.value[self.cursor_position:]
            #self.cursor_position += len(curses.keyname(input))
            
            # workaround for the metamode bug:
            if self._last_get_ch_was_unicode == True and isinstance(self.value, bytes):
                # probably dealing with python2.
                ch_adding = inp
                self.value = self.value.decode()
            elif self._last_get_ch_was_unicode == True:
                ch_adding = inp
            else:
                try:
                    ch_adding = chr(inp)
                except TypeError:
                    ch_adding = input
            self.value = self.value[:self.cursor_position] + ch_adding \
                + self.value[self.cursor_position:]
            self.cursor_position += len(ch_adding)

            # or avoid it entirely:
            #self.value = self.value[:self.cursor_position] + curses.ascii.unctrl(input) \
            #   + self.value[self.cursor_position:]
            #self.cursor_position += len(curses.ascii.unctrl(input))

    def h_cursor_left(self, input):
        self.cursor_position -= 1

    def h_cursor_right(self, input):
        self.cursor_position += 1

    def h_delete_left(self, input):
        if self.editable and self.cursor_position > 0:
            self.value = self.value[:self.cursor_position-1] + self.value[self.cursor_position:]
        
        self.cursor_position -= 1
        self.begin_at -= 1

    
    def h_delete_right(self, input):
        if self.editable:
            self.value = self.value[:self.cursor_position] + self.value[self.cursor_position+1:]

    def h_erase_left(self, input):
        if self.editable:
            self.value = self.value[self.cursor_position:]
            self.cursor_position=0
    
    def h_erase_right(self, input):
        if self.editable:
            self.value = self.value[:self.cursor_position]
            self.cursor_position = len(self.value)
            self.begin_at = 0
    
    def handle_mouse_event(self, mouse_event):
        #mouse_id, x, y, z, bstate = mouse_event
        #rel_mouse_x = x - self.relx - self.parent.show_atx
        mouse_id, rel_x, rel_y, z, bstate = self.interpret_mouse_event(mouse_event)
        self.cursor_position = rel_x + self.begin_at
        self.display()

    
class FixedText(TextfieldBase):
    def set_up_handlers(self):
        super(FixedText, self).set_up_handlers()
        self.handlers.update({curses.KEY_LEFT:    self.h_cursor_left,
                           curses.KEY_RIGHT:   self.h_cursor_right,
                           ord('k'):    self.h_exit_up,
                           ord('j'):    self.h_exit_down,
                           })
    
    
    def h_cursor_left(self, input):
        if self.begin_at > 0:
            self.begin_at -= 1

    def h_cursor_right(self, input):
        if len(self.value) - self.begin_at > self.maximum_string_length:
            self.begin_at += 1

    def update(self, clear=True,):
        super(FixedText, self).update(clear=clear, cursor=False)
    
    def edit(self):
        self.editing = 1
        self.highlight = False
        self.cursor_position = 0
        self.parent.curses_pad.keypad(1)
        
        self.old_value = self.value
        
        self.how_exited = False

        while self.editing:
            self.display()
            self.get_and_use_key_press()

        self.begin_at = 0
        self.highlight = False
        self.display()

        return self.how_exited, self.value

