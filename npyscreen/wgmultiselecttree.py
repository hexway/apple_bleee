from . import wgmultilinetree as multilinetree
from . import wgcheckbox      as checkbox
import weakref
import curses

class MultiSelectTree(multilinetree.SelectOneTree):
    _contained_widgets = checkbox.Checkbox

    def set_up_handlers(self):
        super(MultiSelectTree, self).set_up_handlers()
        self.handlers.update({
                    ord("x"):    self.h_select_toggle,
                    curses.ascii.SP: self.h_select_toggle,
                    ord("X"):    self.h_select,
                    "^U":        self.h_select_none,
                })
    
    def h_select_none(self, input):
        self.value = []
    
    def h_select_toggle(self, input):
        try:
            working_with = weakref.proxy(self.values[self.cursor_line])
        except TypeError:
            working_with = self.values[self.cursor_line]
        if working_with in self.value:
            self.value.remove(working_with)
        else:
            self.value.append(working_with)
            
    def h_set_filtered_to_selected(self, ch):
        self.value = self.get_filtered_values()
    
    def h_select_exit(self, ch):
        try:
            working_with = weakref.proxy(self.values[self.cursor_line])
        except TypeError:
            working_with = self.values[self.cursor_line]
        
        if not working_with in self.value:
            self.value.append(working_with)
        if self.return_exit:
            self.editing = False
            self.how_exited=True
