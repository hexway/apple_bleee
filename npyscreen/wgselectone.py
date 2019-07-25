from . import wgmultiline  as multiline
from . import wgcheckbox   as checkbox

class SelectOne(multiline.MultiLine):
    _contained_widgets = checkbox.RoundCheckBox
    
    def update(self, clear=True):
        if self.hidden:
            self.clear()
            return False
        # Make sure that self.value is a list
        if not hasattr(self.value, "append"):
            if self.value is not None:
                self.value = [self.value, ]
            else:
                self.value = []
                
        super(SelectOne, self).update(clear=clear)

    def h_select(self, ch):
        self.value = [self.cursor_line,]

    def _print_line(self, line, value_indexer):
        try:
            display_this = self.display_value(self.values[value_indexer])
            line.value = display_this
            line.hide = False
            if hasattr(line, 'selected'):
                if (value_indexer in self.value and (self.value is not None)):
                    line.selected = True
                else:
                    line.selected = False
            # Most classes in the standard library use this
            else:
                if (value_indexer in self.value and (self.value is not None)):
                    line.show_bold = True
                    line.name = display_this
                    line.value = True
                else:
                    line.show_bold = False
                    line.name = display_this
                    line.value = False
                    
            if value_indexer in self._filtered_values_cache:
                line.important = True
            else:
                line.important = False
            
            
        except IndexError:
            line.name = None
            line.hide = True

        line.highlight= False
        
class TitleSelectOne(multiline.TitleMultiLine):
    _entry_type = SelectOne
    