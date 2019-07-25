from . import fmFileSelector
from . import wgcombobox

class FilenameCombo(wgcombobox.ComboBox):
    def __init__(self, screen,
    # The following are all options taken from the FileSelector
    select_dir=False, #Select a dir, not a file
    must_exist=False, #Selected File must already exist
    confirm_if_exists=False,
    sort_by_extension=True,
    *args, **keywords):
        self.select_dir = select_dir
        self.must_exist = must_exist
        self.confirm_if_exists = confirm_if_exists
        self.sort_by_extension = sort_by_extension
        
        super(FilenameCombo, self).__init__(screen, *args, **keywords)
        
    def _print(self):
        if self.value == None:
            printme = '- Unset -'
        else:
            try:
                printme = self.display_value(self.value)
            except IndexError:
                printme = '-error-'
        if self.do_colors():
            self.parent.curses_pad.addnstr(self.rely, self.relx, printme, self.width, self.parent.theme_manager.findPair(self))
        else:
            self.parent.curses_pad.addnstr(self.rely, self.relx, printme, self.width)

    
    
    def h_change_value(self, *args, **keywords):
        self.value = fmFileSelector.selectFile(
            starting_value = self.value,
            select_dir = self.select_dir,
            must_exist = self.must_exist,
            confirm_if_exists = self.confirm_if_exists,
            sort_by_extension = self.sort_by_extension
        )
        if self.value == '':
            self.value = None
        self.display()
        

class TitleFilenameCombo(wgcombobox.TitleCombo):
    _entry_type = FilenameCombo