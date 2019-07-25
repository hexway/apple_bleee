#!/usr/bin/env python
from . import wgtextbox     as textbox
from . import wgtitlefield  as titlefield
from . import wgmonthbox    as monthbox
from . import fmPopup       as Popup
from . import fmForm        as Form
import datetime
import curses


class DateCombo(textbox.Textfield, monthbox.DateEntryBase):
    def __init__(self, screen, allowPastDate=True, allowTodaysDate=True, allowClear=True, **keywords):
        super(DateCombo, self).__init__(screen, **keywords)
        self.allow_date_in_past = allowPastDate
        self.allow_todays_date  = allowTodaysDate
        self.allow_clear        = allowClear

    def update(self, **keywords):
        keywords.update({'cursor': False})
        super(DateCombo, self).update(**keywords)

    def edit(self):
        #We'll just use the widget one
        super(textbox.Textfield, self).edit()

    def display_value(self, vl):
        if self.value:
            try:
                # in python 2.4 this will raise ValueError if date is before 1900
                #return self.value.strftime("%a, %d %B, %Y")
                return self.value.strftime("%d %B, %Y")
            except ValueError:
                return self.value.isoformat()
            except AttributeError:
                return "-error-"
        else:
            return "-unset-"
            
    def _print(self):
        if self.do_colors():
            self.parent.curses_pad.addnstr(self.rely, self.relx, self.display_value(self.value), self.width, self.parent.theme_manager.findPair(self,))
        else:
            self.parent.curses_pad.addnstr(self.rely, self.relx, self.display_value(self.value), self.width)
            
    def h_change_value(self, *arg):
        # Remember to leave extra space at the end of the popup, or the clear function can't work properly.
        _old_date = self.value
        F = Popup.Popup(name = self.name,
                        columns = (monthbox.MonthBox.DAY_FIELD_WIDTH * 7) + 4, 
                        lines=13,
                        )
        #F = Form.Form()
        m = F.add(monthbox.MonthBox,
                    allowPastDate   = self.allow_date_in_past,
                    allowTodaysDate = self.allow_todays_date,
                    use_max_space   = True,
                    use_datetime    = self.use_datetime,
                    allowClear      = self.allow_clear,
        )
        try:
            # Is it a date, do we think?
            self.value.isoformat()
            m.value = self.value
        except:
            # if not, we could do worse than today
            m.value = self.date_or_datetime().today()
            # But make sure that that is acceptable
            m._check_today_validity()
        F.display()
        m.edit()
        self.value = m.value
        # The following is perhaps confusing.
        #if self.value == _old_date:
        #   self.h_exit_down('')
    
    def set_up_handlers(self):
        super(textbox.Textfield, self).set_up_handlers()
        self.handlers.update({curses.ascii.SP:  self.h_change_value,
                      #curses.ascii.TAB: self.h_change_value,
                      curses.ascii.CR:  self.h_change_value,
                      curses.ascii.NL:  self.h_change_value,
                      ord('x'):         self.h_change_value,
                      ord('j'): self.h_exit_down,
                      ord('k'): self.h_exit_up,
                      })
    
class TitleDateCombo(titlefield.TitleText):
    _entry_type = DateCombo



        

