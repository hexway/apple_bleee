#!/usr/bin/python
from . import wgwidget    as widget
from . import npysGlobalOptions as GlobalOptions
import locale
import sys
import curses
import textwrap
import re
from functools import reduce

class MultiLineEdit(widget.Widget):
    _SAFE_STRING_STRIPS_NL = False
    def __init__(self, screen, autowrap=True, slow_scroll=True, scroll_exit=True, value=None, **keywords):
        self.value = value or ''
        super(MultiLineEdit, self).__init__(screen, **keywords)
        self.cursor_position = 0
        self.start_display_at = 0 #Line number

        self.maximum_display_width  = self.width - 1 # Leave room for cursor
        self.maximum_display_height = self.height
        self.slow_scroll = slow_scroll
        self.scroll_exit = scroll_exit
        self.encoding = locale.getpreferredencoding()
        self.autowrap = autowrap
        self.wrapon = re.compile("\s+|-+")
        
        if GlobalOptions.ASCII_ONLY or locale.getpreferredencoding() == 'US-ASCII':
            self._force_ascii = True
        else:
            self._force_ascii = False


    def safe_filter(self, this_string):
        s = []
        for cha in this_string:   #.replace('\n', ''): Not of this widget
            if cha == "\n":
                s.append(cha)
            else:
                try:
                    s.append(str(cha))
                except:
                    s.append('?')
        s = ''.join(s)
        return s
        


    def get_value_as_list(self, upto=None, keepends=False, useEncoding=True):
        if useEncoding:
            text_to_print = self.safe_string(self.value)
        else:
            text_to_print = self.value
        if upto:
            text = text_to_print[:upto]
        else:
            text = text_to_print
        if upto:
            lines = text.splitlines(keepends)
        else:
            lines = text.splitlines()
        return lines

    def translate_cursor(self, y):
        """Translate cursor position from point in a str to y,x on in widget (you'll need to add in rely, relx yourself)"""
        if self.value == "": return 0,0
        position = y
        if position == 0: 
            return 0,0
        text_to_cursor = self.get_value_as_list(upto=position, keepends=True, useEncoding=False)
        y = (len(text_to_cursor))-1
        x = len(text_to_cursor[-1])
        if text_to_cursor[-1][-1] == '\n': 
            y += 1
            x = 0
        return y, x
            
    def calculate_area_needed(self):
        return 0,0

    def update(self, clear=True):
        if clear: self.clear()
        display_length = self.maximum_display_height
        display_width = self.maximum_display_width
        xdisplay_offset = 0
        text_to_display = self.get_value_as_list()
        if self.cursor_position < 0: self.cursor_position = 0
        if self.cursor_position > len(self.value): self.cursor_position = len(self.value)

        self.cursory, self.cursorx = self.translate_cursor(self.cursor_position)
    
        if self.editing:
            if self.slow_scroll:
                if self.cursory > self.start_display_at+display_length-1:
                    self.start_display_at = self.cursory - (display_length-1) 

                if self.cursory < self.start_display_at:
                    self.start_display_at = self.cursory
            
            else:
                if self.cursory > self.start_display_at+(display_length-1):
                    self.start_display_at = self.cursory

                if self.cursory < self.start_display_at:
                    self.start_display_at = self.cursory - (display_length-1)
            
            if self.start_display_at < 0:
                self.start_display_at=0

            if self.cursorx > display_width:
                xdisplay_offset = self.cursorx - display_width
        
        max_display = len(text_to_display[self.start_display_at:])

        for line_counter in range(self.height):
            if line_counter >= len(text_to_display)-self.start_display_at: 
                break
            
            line_to_display = text_to_display[self.start_display_at+line_counter][xdisplay_offset:]
            line_to_display = self.safe_string(line_to_display)
            if isinstance(line_to_display, bytes):
                line_to_display = line_to_display.decode(self.encoding, 'replace')
            column = 0
            place_in_string = 0
            while column <= (display_width):
                if not line_to_display:
                    break
                if place_in_string >= len(line_to_display):
                    break
                width_of_char_to_print = 1 # self.find_width_of_char(string_to_print[place_in_string])
                                           # change this when actually have a function to do this
                if column - 1 + width_of_char_to_print > display_width:
                    break
                
                if self.do_colors():
                    color = self.parent.theme_manager.findPair(self)
                else:
                    color = curses.A_NORMAL
                
                self.parent.curses_pad.addstr(self.rely+line_counter,self.relx+column, 
                    self._print_unicode_char(line_to_display[place_in_string]), 
                    color
                    )
                column += width_of_char_to_print
                place_in_string += 1
                
            # This needs altering using the methods from the textbox class
            # to properly deal with unicode.
            
            #if self.do_colors():
            #    self.parent.curses_pad.addnstr(self.rely+line_counter, self.relx, 
            #        text_to_display[self.start_display_at+line_counter][xdisplay_offset:], display_width,
            #        self.parent.theme_manager.findPair(self))
            #else:
            #    self.parent.curses_pad.addnstr(self.rely+line_counter, self.relx, 
            #        text_to_display[self.start_display_at+line_counter][xdisplay_offset:], display_width)
            #

        if self.editing:
            # Cursors do not seem to work on pads.
            #self.parent_screen.move(self.rely, self.cursor_position - self.begin_at)
            # let's have a fake cursor
            _cur_y, _cur_x = self.translate_cursor(self.cursor_position)
            #_cur_y += self.rely - self.start_display_at
            #assert _cur_y >= 0
            #_cur_x += self.relx - xdisplay_offset
            #char_under_cur = self.parent.curses_pad.inch(_cur_y, _cur_x)
            #self.parent.curses_pad.addch(_cur_y, _cur_x, char_under_cur, curses.A_STANDOUT)
            try:
                char_under_cur = self.safe_string(self.value[self.cursor_position])
                if char_under_cur == '\n':
                    char_under_cur = ' '
            except:
                char_under_cur = ' '
            
            if self.do_colors():
                self.parent.curses_pad.addstr(self.rely + _cur_y - self.start_display_at, _cur_x - xdisplay_offset + self.relx, char_under_cur, 
                                                self.parent.theme_manager.findPair(self) | curses.A_STANDOUT)
                
            else:
                self.parent.curses_pad.addstr(self.rely + _cur_y - self.start_display_at, _cur_x - xdisplay_offset + self.relx, char_under_cur, curses.A_STANDOUT)
            
    def _print_unicode_char(self, ch):
        # return the ch to print.  For python 3 this is just ch
        if self._force_ascii:
            return ch.encode('ascii', 'replace')
        elif sys.version_info[0] >= 3:
            return ch
        else:
            return ch.encode('utf-8', 'strict')

    def reformat_preserve_nl(self, *ignorethese):
        # Adapted from a script found at:
        #http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/148061
        #width=self.maximum_display_width
        #text = self.value
        #self.value = reduce(lambda line, word, width=width: '%s%s%s' %
        #          (line,
        #           ' \n'[(len(line)-line.rfind('\n')-1
        #             + len(word.split('\n',1)[0]
        #                  ) >= width)],
        #           word),
        #          text.split(' ')
        #         )
        
        width=self.maximum_display_width
        text = self.value
        lines = []
        for paragraph in text.split('\n'):
            line = []
            len_line = 0
            for word in paragraph.split(' '):
                len_word = len(word)
                if len_line + len_word <= width:
                    line.append(word)
                    len_line += len_word + 1
                else:
                    lines.append(' '.join(line))
                    line = [word]
                    len_line = len_word + 1
            lines.append(' '.join(line))
        self.value = '\n'.join(lines)
        return self.value



    def full_reformat(self, *args):
        w = DocWrapper(width=self.maximum_display_width)
        self.value = w.fill(self.value)
        
        
    #def handle_mouse_event(self, mouse_event):
        # unfinished
        #mouse_id, x, y, z, bstate = mouse_event
        #rel_mouse_x = x - self.relx
        #rel_mouse_y = y = self.rely
        #self.cursor_position = rel_mouse_x + self.begin_at
        #self.display()

        
    ######################################################################
    def set_up_handlers(self):
        super(MultiLineEdit, self).set_up_handlers()    
    
        # For OS X
        del_key = curses.ascii.alt('~')
        
        self.handlers.update({
                   curses.ascii.NL:    self.h_add_nl,
                   curses.ascii.CR:    self.h_add_nl,
                   curses.KEY_LEFT:    self.h_cursor_left,
                   curses.KEY_RIGHT:   self.h_cursor_right,
                   curses.KEY_UP:      self.h_line_up,
                   curses.KEY_DOWN:    self.h_line_down,
                   curses.KEY_DC:      self.h_delete_right,
                   curses.ascii.DEL:   self.h_delete_left,
                   curses.ascii.BS:    self.h_delete_left,
                   curses.KEY_BACKSPACE: self.h_delete_left,
                   "^R":           self.full_reformat,
                   # mac os x curses reports DEL as escape oddly
                   # no solution yet                   
                   #"^K":          self.h_erase_right,
                   #"^U":          self.h_erase_left,
            })

        self.complex_handlers.extend((
                    (self.t_input_isprint, self.h_addch),
                    # (self.t_is_ck, self.h_erase_right),
                    # (self.t_is_cu, self.h_erase_left),
                        ))

    
    def h_addch(self, inp):
        if self.editable:
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
        else:
            return False
        if self.autowrap:
            self.reformat_preserve_nl()
    
    def t_input_isprint(self, inp):
        if self._last_get_ch_was_unicode and inp not in '\n\t\r':
            return True
        if curses.ascii.isprint(inp) and \
        (chr(inp) not in '\n\t\r'): 
            return True
        
        else: return False

    def h_addch_disabled(self, input):
        """Add printable characters.  However, do NOT add newlines with this function"""
        if not self.editable: return False
        self.value = self.value[:self.cursor_position] + chr(input) \
            + self.value[self.cursor_position:]
        self.cursor_position += len(chr(input))
        
        if self.autowrap:
            self.reformat_preserve_nl()

    
    def h_line_down(self, input):
        end_this_line = self.value.find("\n", self.cursor_position) 
        if end_this_line == -1:
            if self.scroll_exit: 
                self.h_exit_down(None)
            else: 
                self.cursor_position = len(self.value)
        else:
            self.cursor_position = end_this_line + 1
            for x in range(self.cursorx):
                if self.cursor_position > len(self.value)-1:
                    break
                elif self.value[self.cursor_position] == "\n":
                    break
                else:
                    self.cursor_position += 1
            

    def h_line_up(self, input):
        end_last_line = self.value.rfind("\n", 0, self.cursor_position) 
        if end_last_line == -1:
            if self.scroll_exit: self.h_exit_up(None)
            else: self.cursor_position = 0
        else:
            start_last_line = self.value.rfind("\n", 0, end_last_line)
            if start_last_line == -1: start_last_line = 0
            else: start_last_line += 1
            if end_last_line - start_last_line <= self.cursorx:
                self.cursor_position = end_last_line
            else: 
                self.cursor_position = start_last_line + self.cursorx 
                if self.value[self.cursor_position] == "\n":
                    self.cursor_position += 1 
    # Bug somewhere here when dealing with empty lines.
    def h_add_nl(self, input):
        self.value = self.value[:self.cursor_position] + "\n" + self.value[self.cursor_position:]
        self.cursor_position += 1

    def h_cursor_left(self, input):
        if self.cursor_position > 0: 
            self.cursor_position -= 1
        

    def h_cursor_right(self, input):
        self.cursor_position += 1

    def h_delete_left(self, input):
        if self.editable and self.cursor_position > 0:
            self.value = self.value[:self.cursor_position-1] + self.value[self.cursor_position:]
        
        self.cursor_position -= 1

    def h_delete_right(self, input):
        if self.editable:
            self.value = self.value[:self.cursor_position] + self.value[self.cursor_position+1:]

class DocWrapper(textwrap.TextWrapper):
    """Wrap text in a document, processing each paragraph individually"""
    # Code from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/358228
    def wrap(self, text):
        """Override textwrap.TextWrapper to process 'text' properly when
        multiple paragraphs present"""
        para_edge = re.compile(r"(\n\s*\n)", re.MULTILINE)
        paragraphs = para_edge.split(text)
        wrapped_lines = []
        for para in paragraphs:
            if para.isspace():
                if not self.replace_whitespace:
                    # Do not take the leading and trailing newlines since
                    # joining the list with newlines (as self.fill will do)
                    # will put them back in.
                    if self.expand_tabs:
                        para = para.expandtabs()
                    wrapped_lines.append(para[1:-1])
                else:
                    # self.fill will end up putting in the needed newline to
                    # space out the paragraphs
                    wrapped_lines.append('')
            else:
                wrapped_lines.extend(textwrap.TextWrapper.wrap(self, para))
        return wrapped_lines

        
