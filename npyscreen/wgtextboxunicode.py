from . import wgtextbox

import unicodedata
import curses



class TextfieldUnicode(wgtextbox.Textfield):
    width_mapping = {'F':2, 'H': 1, 'W': 2, 'Na': 1, 'N': 1}
    def find_apparent_cursor_position(self, ):
        string_to_print = self.display_value(self.value)[self.begin_at:self.maximum_string_length+self.begin_at-self.left_margin]
        cursor_place_in_visible_string = self.cursor_position - self.begin_at
        counter = 0
        columns = 0
        while counter < cursor_place_in_visible_string:
             columns += self.find_width_of_char(string_to_print[counter])
             counter += 1
        return columns
    
    def find_width_of_char(self, char):
        return 1
        w = unicodedata.east_asian_width(char)
        if w == 'A':
            # Abiguous - allow 1, but be aware that this could well be wrong
            return 1
        else:
            return self.__class__.width_mapping[w]
    
            
    
        
    
