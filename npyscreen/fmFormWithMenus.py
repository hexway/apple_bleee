#!/usr/bin/env python
# encoding: utf-8
import curses
from . import fmForm
from . import fmActionForm
from . import fmActionFormV2
from . import wgNMenuDisplay

class FormBaseNewWithMenus(fmForm.FormBaseNew, wgNMenuDisplay.HasMenus):
    """The FormBaseNew class, but with a handling system for menus as well.  See the HasMenus class for details."""
    def __init__(self, *args, **keywords):
        super(FormBaseNewWithMenus, self).__init__(*args, **keywords)
        self.initialize_menus()
    
    def display_menu_advert_at(self):
        return self.lines-1, 1
    
    def draw_form(self):
        super(FormBaseNewWithMenus, self).draw_form()
        menu_advert = " " + self.__class__.MENU_KEY + ": Menu "
        if isinstance(menu_advert, bytes):
            menu_advert = menu_advert.decode('utf-8', 'replace')
        y, x = self.display_menu_advert_at()
        self.add_line(y, x, 
            menu_advert, 
            self.make_attributes_list(menu_advert, curses.A_NORMAL),
            self.columns - x - 1
            )
    

class FormWithMenus(fmForm.Form, wgNMenuDisplay.HasMenus):
    """The Form class, but with a handling system for menus as well.  See the HasMenus class for details."""
    def __init__(self, *args, **keywords):
        super(FormWithMenus, self).__init__(*args, **keywords)
        self.initialize_menus()
    
    def display_menu_advert_at(self):
        return self.lines-1, 1
    
    def draw_form(self):
        super(FormWithMenus, self).draw_form()
        menu_advert = " " + self.__class__.MENU_KEY + ": Menu "
        y, x = self.display_menu_advert_at()
        if isinstance(menu_advert, bytes):
            menu_advert = menu_advert.decode('utf-8', 'replace')
        self.add_line(y, x, 
            menu_advert, 
            self.make_attributes_list(menu_advert, curses.A_NORMAL),
            self.columns - x - 1
            )

# The following class does not inherit from FormWithMenus and so some code is duplicated.  
# The pig is getting to inherit edit() from ActionForm, but draw_form from FormWithMenus
class ActionFormWithMenus(fmActionForm.ActionForm, wgNMenuDisplay.HasMenus):
    def __init__(self, *args, **keywords):
        super(ActionFormWithMenus, self).__init__(*args, **keywords)
        self.initialize_menus()
    
    def display_menu_advert_at(self):
        return self.lines-1, 1

    def draw_form(self):
        super(ActionFormWithMenus, self).draw_form()
        menu_advert = " " + self.__class__.MENU_KEY + ": Menu "
        y, x = self.display_menu_advert_at()
        
        if isinstance(menu_advert, bytes):
            menu_advert = menu_advert.decode('utf-8', 'replace')
        self.add_line(y, x, 
            menu_advert, 
            self.make_attributes_list(menu_advert, curses.A_NORMAL),
            self.columns - x - 1
            )

class ActionFormV2WithMenus(fmActionFormV2.ActionFormV2, wgNMenuDisplay.HasMenus):
    def __init__(self, *args, **keywords):
        super(ActionFormV2WithMenus, self).__init__(*args, **keywords)
        self.initialize_menus()


        
class SplitFormWithMenus(fmForm.SplitForm, FormWithMenus):
    """Just the same as the Title Form, but with a horizontal line"""
    def draw_form(self):
        super(SplitFormWithMenus, self).draw_form()

