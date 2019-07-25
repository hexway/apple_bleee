#!/usr/bin/python
# encoding: utf-8

from . import fmForm
from . import fmActionFormV2
import curses


class Popup(fmForm.Form):
    DEFAULT_LINES      = 12
    DEFAULT_COLUMNS    = 60
    SHOW_ATX           = 10
    SHOW_ATY           = 2
        
class ActionPopup(fmActionFormV2.ActionFormV2):
    DEFAULT_LINES      = 12
    DEFAULT_COLUMNS    = 60
    SHOW_ATX           = 10
    SHOW_ATY           = 2
    
    
class MessagePopup(Popup):
    def __init__(self, *args, **keywords):
        from . import wgmultiline as multiline 
        super(MessagePopup, self).__init__(*args, **keywords)
        self.TextWidget = self.add(multiline.Pager, scroll_exit=True, max_height=self.widget_useable_space()[0]-2)
        
class PopupWide(Popup):
    DEFAULT_LINES      = 14
    DEFAULT_COLUMNS    = None
    SHOW_ATX           = 0
    SHOW_ATY           = 0
        
class ActionPopupWide(fmActionFormV2.ActionFormV2):
    DEFAULT_LINES      = 14
    DEFAULT_COLUMNS    = None
    SHOW_ATX           = 0
    SHOW_ATY           = 0
