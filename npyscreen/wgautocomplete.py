#!/usr/bin/env python
import curses
from . import wgtextbox    as textbox
from . import wgmultiline  as multiline
from . import wgtitlefield as titlefield
import os
from . import fmForm as Form
from . import fmPopup as Popup

class Autocomplete(textbox.Textfield):
    """This class is fairly useless, but override auto_complete to change that.  See filename class for example"""
    def set_up_handlers(self):
        super(Autocomplete, self).set_up_handlers()
        
        self.handlers.update({curses.ascii.TAB: self.auto_complete})

    def auto_complete(self, input):
        curses.beep()

    def get_choice(self, values):
        # If auto_complete needs the user to select from a list of values, this function lets them do that.
        
        #tmp_window = Form.TitleForm(name=self.name, framed=True)
        tmp_window = Popup.Popup(name=self.name, framed=True)
        sel = tmp_window.add_widget(multiline.MultiLine, 
                values=values, 
                value=self.value,
                return_exit=True, select_exit=True)
        #sel = multiline.MultiLine(tmp_window, values=values, value=self.value)
        tmp_window.display()
        sel.value=0
        sel.edit()
        return sel.value


class Filename(Autocomplete):
    def auto_complete(self, input):
        # expand ~
        self.value = os.path.expanduser(self.value)

        for i in range(1):
            dir, fname = os.path.split(self.value)
            # Let's have absolute paths.
            dir = os.path.abspath(dir)
    
            if self.value == '': 
                self.value=dir
                break
    
            try: 
                flist = os.listdir(dir)
            except:
                self.show_brief_message("Can't read directory!")
                break

            flist = [os.path.join(dir, x) for x in flist]
            possibilities = list(filter(
                (lambda x: os.path.split(x)[1].startswith(fname)), flist
                ))

            if len(possibilities) is 0:
                # can't complete
                curses.beep()
                break

            if len(possibilities) is 1:
                if self.value != possibilities[0]:
                    self.value = possibilities[0]
                if os.path.isdir(self.value) \
                    and not self.value.endswith(os.sep):
                    self.value = self.value + os.sep
                else:
                    if not os.path.isdir(self.value):
                        self.h_exit_down(None)
                    break

            if len(possibilities) > 1:
                filelist = possibilities
            else:
                filelist = flist #os.listdir(os.path.dirname(self.value))
    
            filelist = list(map((lambda x: os.path.normpath(os.path.join(self.value, x))), filelist))
            files_only = []
            dirs_only = []

            if fname.startswith('.'):
                filelist = list(filter((lambda x: os.path.basename(x).startswith('.')), filelist))
            else:
                filelist = list(filter((lambda x: not os.path.basename(x).startswith('.')), filelist))

            for index1 in range(len(filelist)):
                if os.path.isdir(filelist[index1]) and not filelist[index1].endswith(os.sep):
                    filelist[index1] = filelist[index1] + os.sep

                if os.path.isdir(filelist[index1]):
                    dirs_only.append(filelist[index1])
            
                else:
                    files_only.append(filelist[index1])
    
            dirs_only.sort()
            files_only.sort()
            combined_list = dirs_only + files_only
            combined_list.insert(0, self.value)
            self.value = combined_list[self.get_choice(combined_list)]
            break

            # Can't complete
            curses.beep()
        #os.path.normpath(self.value)
        os.path.normcase(self.value)
        self.cursor_position=len(self.value)

class TitleFilename(titlefield.TitleText):
    _entry_type = Filename


