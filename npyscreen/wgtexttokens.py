import curses
import sys
from . import wgwidget
from . import wgtextbox
from . import wgtitlefield

class TextTokens(wgtextbox.Textfield,wgwidget.Widget):
    """This is an experiemental widget"""
    
    # NB IT DOES NOT CURRENTLY SUPPORT THE HIGHLIGHTING COLORS
    # OF THE TEXTFIELD CLASS.
    
    
    def __init__(self, *args, **keywords):        
        super(TextTokens, self).__init__(*args, **keywords)
        self.begin_at        = 0 # which token to begin display with
        self.maximum_string_length = self.width - 2
        self.left_margin     = 0
        self.cursor_position = 0
        
        self.important = False
        self.highlight = False
        self.show_bold = False

    def find_cursor_offset_on_screen(self, position):
        index  = self.begin_at 
        offset = 0
        while index < position:
            offset += len(self.decode_token(self.value[index]))
            index  += 1
        return offset - self.begin_at # I don't quite understand
                                      # why the - self.begin_at is needed
                                      # but without it the cursor and screen
                                      # get out of sync
    
    def decode_token(self, tk):
        r = ''.join(tk)
        if len(r) > 1:
            r = ' [' + r + '] '
        if isinstance(r, bytes):
            r = r.decode(self.encoding, 'replace')
        return r
    
    # text and highlighting generator.
    def get_literal_text_and_highlighting_generator(self, start_at=0,):
        # could perform initialization here.
        index = start_at
        string_length = 0
        output = ''
        while string_length <= self.maximum_string_length and len(self.value) > index:
            token_output = self.decode_token(self.value[index])
            if isinstance(token_output, bytes):
                token_output = token_output.decode(self.encoding, 'replace')
            highlighting = [curses.A_NORMAL for c in token_output]
            yield(token_output, highlighting)
            index += 1
    
    def get_literal_text_to_display(self, start_at=0,):
        g = self.get_literal_text_and_highlighting_generator(start_at=start_at)
        txt = []
        highlighting = []
        for i in g:
            txt += i[0]
            highlighting += i[1]
        return txt, highlighting
            
                
    def update(self, clear=True, cursor=True):
        if clear: self.clear()
        if self.begin_at    < 0: self.begin_at = 0
        if self.left_margin >= self.maximum_string_length:
            raise ValueError
            
        if self.cursor_position < 0:
            self.cursor_position = 0
        if self.cursor_position > len(self.value):
            self.cursor_position = len(self.value)
        
        if self.cursor_position < self.begin_at:
            self.begin_at = self.cursor_position
        
        while self.find_cursor_offset_on_screen(self.cursor_position) > \
                 self.find_cursor_offset_on_screen(self.begin_at) + \
                 self.maximum_string_length - self.left_margin -1: # -1:
            self.begin_at += 1
    

        text, highlighting = self.get_literal_text_to_display(start_at=self.begin_at)
        if self.do_colors():
            if self.important:
                color = self.parent.theme_manager.findPair(self, 'IMPORTANT') | curses.A_BOLD            
            else:
                color = self.parent.theme_manager.findPair(self, self.color)
            if self.show_bold:
                color = color | curses.A_BOLD
            if self.highlight:
                if not self.editing:
                    color = color | curses.A_STANDOUT
                else:
                    color = color | curses.A_UNDERLINE
            highlighting = [color for c in highlighting if c == curses.A_NORMAL]
        else:
            color = curses.A_NORMAL
            if self.important or self.show_bold:
                color = color | curses.A_BOLD
            if self.important:
                color = color | curses.A_UNDERLINE
            if self.highlight:
                if not self.editing:
                    color = color | curses.A_STANDOUT
                else:
                    color = color | curses.A_UNDERLINE
            highlighting = [color for c in highlighting if c == curses.A_NORMAL]
        
        self._print(text, highlighting)
        
        if self.editing and cursor:
            self.print_cursor()
        

    def _print(self, text, highlighting):
        self.add_line(self.rely, 
                      self.relx + self.left_margin,
                      text,
                      highlighting,
                      self.maximum_string_length - self.left_margin
                      )
    def print_cursor(self):
        _cur_loc_x = self.cursor_position - self.begin_at + self.relx + self.left_margin
        try:
            char_under_cur = self.decode_token(self.value[self.cursor_position]) #use the real value
            char_under_cur = self.safe_string(char_under_cur)
        except IndexError:
            char_under_cur = ' '
        
        if isinstance(char_under_cur, bytes):
            char_under_cur = char_under_cur.decode(self.encoding, 'replace')
        
        offset = self.find_cursor_offset_on_screen(self.cursor_position)
        if self.do_colors():
            ATTR_LIST = self.parent.theme_manager.findPair(self) | curses.A_STANDOUT
        else:
            ATTR_LIST = curses.A_STANDOUT
    
        self.add_line(self.rely, 
             self.begin_at + self.relx + self.left_margin + offset,
            char_under_cur, 
            self.make_attributes_list(char_under_cur, ATTR_LIST),
            # I don't understand why the "- self.begin_at" is needed in the following line
            # but it is or the cursor can end up overrunning the end of the widget.
            self.maximum_string_length+1 - self.left_margin - offset - self.begin_at,
            )

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
            self.value = self.value[:self.cursor_position] + [ch_adding,] \
                + self.value[self.cursor_position:]
            self.cursor_position += len(ch_adding)
    
    def display_value(self, vl):
        return vl
    
    
    def calculate_area_needed(self):
        "Need one line of screen, and any width going"
        return 1,0
        


class TitleTextTokens(wgtitlefield.TitleText):
    _entry_type = TextTokens

    