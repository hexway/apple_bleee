import curses
from . import wgtextbox as textbox

class TextfieldCtrlChars(textbox.Textfield):
    "Implements a textfield, but which can be prefixed with special curses graphics.  Currently unfinished. Not for use."
    def __init__(self, *args, **keywords):
        self.ctr_chars = []
        super(TextfieldCtrlChars, self).__init__(*args, **keywords)
    
    def _get_maximum_string_length(self):
        if self.on_last_line:
            _maximum_string_length = self.width - 1
        else:   
            _maximum_string_length = self.width
        
        _maximum_string_length -= (len(self.ctr_chars) + 1)
        
        return _maximum_string_length
    
    def _set_maxiumum_string_length(self, *args):
        pass
    
    def _del_maxiumum_string_length(self):
        pass
    
    maximum_string_length = property(_get_maximum_string_length, _set_maxiumum_string_length, _del_maxiumum_string_length)
    
    
