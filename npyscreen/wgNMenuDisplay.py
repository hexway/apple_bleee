#!/usr/bin/env python
# encoding: utf-8
from . import muNewMenu    as NewMenu
from . import fmForm       as Form
from . import wgmultiline  as multiline
from . import wgannotatetextbox
from . import utilNotify
import weakref
import curses

class MenuViewerController(object):
    def __init__(self, menu=None):
        self.setMenu(menu)
        self.create()
        self._menuStack = []
        self._editing = False

    def create(self):
        pass
        
    def setMenu(self, mnu):
        self._menuStack = []
        self._setMenuWithoutResettingStack(mnu)
    
    def _setMenuWithoutResettingStack(self, mnu):
        self._menu = mnu
        self._DisplayArea._menuListWidget.value = None
        
    def _goToSubmenu(self, mnu):
        self._menuStack.append(self._menu)
        self._menu = mnu

    def _returnToPrevious(self):
        self._menu = self._menuStack.pop()


    def _executeSelection(self, sel):
        self._editing = False
        return sel()
        
    def edit(self):
        try:
            if self._menu is None:
                raise ValueError("No Menu Set")
        except AttributeError:
            raise ValueError("No Menu Set")
        self._editing = True
        while self._editing:
            if self._menu is not None:
                self._DisplayArea.name = self._menu.name
            if hasattr(self._menu, 'do_pre_display_function'):
                self._menu.do_pre_display_function()
            self._DisplayArea.display()
            self._DisplayArea._menuListWidget.value = None
            self._DisplayArea._menuListWidget.cursor_line = 0
            _menulines = []
            _actionsToTake = []
            if len(self._menuStack) > 0:
                _menulines.append(PreviousMenu())
                _returnToPreviousSet = True
                _actionsToTake.append((self._returnToPrevious, ))
            else:
                _returnToPreviousSet = False
            
            for itm in self._menu.getItemObjects():
                if isinstance(itm, NewMenu.MenuItem):
                    _menulines.append(itm)
                    _actionsToTake.append((self._executeSelection, itm.do))
                elif isinstance(itm, NewMenu.NewMenu):
                    _menulines.append(itm)
                    _actionsToTake.append((self._goToSubmenu, itm))
                else:
                    raise ValueError("menu %s contains objects I don't know how to handle." % self._menu.name)
            
            
            self._DisplayArea._menuListWidget.values = _menulines
            self._DisplayArea.display()
            self._DisplayArea._menuListWidget.edit()
            _vlu = self._DisplayArea._menuListWidget.value
            if _vlu is None:
                self.editing = False
                return None
            try:
                _fctn = _actionsToTake[_vlu][0]
                _args = _actionsToTake[_vlu][1:]
            except IndexError:
                try:
                    _fctn = _actionsToTake[_vlu]
                    _args = []
                except IndexError:
                    # Menu must be empty.
                    return False
            _return_value = _fctn(*_args)
        
        return _return_value
            

class PreviousMenu(NewMenu.NewMenu):
    pass


class MenuDisplay(MenuViewerController):
    def __init__(self, color='CONTROL', lines=15, columns=39, show_atx=5, show_aty=2, *args, **keywords):
        self._DisplayArea = MenuDisplayScreen(lines=lines, 
                                    columns=columns, 
                                    show_atx=show_atx, 
                                    show_aty=show_aty, 
                                    color=color)
        super(MenuDisplay, self).__init__(*args, **keywords)

class MenuDisplayFullScreen(MenuViewerController):
    def __init__(self, *args, **keywords):
        self._DisplayArea = MenuDisplayScreen()
        super(MenuDisplayFullScreen, self).__init__(*args, **keywords)



class wgMenuLine(wgannotatetextbox.AnnotateTextboxBaseRight):
    ANNOTATE_WIDTH = 3
    def getAnnotationAndColor(self,):
        try:
            if self.value.shortcut:
                return (self.safe_string(self.value.shortcut), 'LABEL')
            else:
                return ('', 'LABEL')
        except AttributeError:
            return ('', 'LABEL')
    
    def display_value(self, vl):
        # if this function raises an exception, it gets masked.
        # this is a bug.
        if not vl:
            return None
        if isinstance(vl, PreviousMenu):
            return '<-- Back'
        elif isinstance(vl, NewMenu.NewMenu):
            return ('%s -->' % self.safe_string(self.value.name))
        elif isinstance(vl, NewMenu.MenuItem):
            return self.safe_string(self.value.getText())
        else:
            return self.safe_string(str(self.value))
            

class wgMenuListWithSortCuts(multiline.MultiLineActionWithShortcuts):
    _contained_widgets = wgMenuLine
    def __init__(self, screen,  allow_filtering=False, *args, **keywords):
        return super(wgMenuListWithSortCuts, self).__init__(screen, allow_filtering=allow_filtering, *args, **keywords)
    
    #def actionHighlighted(self, act_on_this, key_press):
    #    if isinstance(act_on_this, MenuItem):
    #        return act_on_this.do()
    #    else:
    #        return act_on_this
    def actionHighlighted(self, act_on_this, key_press):
        return self.h_select_exit(key_press)
    
    def display_value(self, vl):
        return vl

class MenuDisplayScreen(Form.Form):
    def __init__(self, *args, **keywords):
        super(MenuDisplayScreen, self).__init__(*args, **keywords)
        #self._menuListWidget = self.add(multiline.MultiLine, return_exit=True)
        self._menuListWidget = self.add(wgMenuListWithSortCuts, return_exit=True)
        self._menuListWidget.add_handlers({
            ord('q'):       self._menuListWidget.h_exit_down,
            ord('Q'):       self._menuListWidget.h_exit_down,
            ord('x'):       self._menuListWidget.h_select_exit,
            curses.ascii.SP:    self._menuListWidget.h_select_exit,
        })
        
class HasMenus(object):
    MENU_KEY          = "^X"
    MENU_DISPLAY_TYPE = MenuDisplay
    MENU_WIDTH        = None
    def initialize_menus(self):
        if self.MENU_WIDTH:
            self._NMDisplay = self.MENU_DISPLAY_TYPE(columns=self.MENU_WIDTH)
        else:
            self._NMDisplay = self.MENU_DISPLAY_TYPE()
        if not hasattr(self, '_NMenuList'):
            self._NMenuList = []
        self._MainMenu  = NewMenu.NewMenu
        self.add_handlers({self.__class__.MENU_KEY: self.root_menu})
        
    def new_menu(self, name=None, *args, **keywords):
        if not hasattr(self, '_NMenuList'):
            self._NMenuList = []
        _mnu = NewMenu.NewMenu(name=name, *args, **keywords)
        self._NMenuList.append(_mnu)
        return weakref.proxy(_mnu)
    
    def add_menu(self, *args, **keywords):
        return self.new_menu(*args, **keywords)
        
    def root_menu(self, *args):
        if len(self._NMenuList) == 1:
            self._NMDisplay.setMenu(self._NMenuList[0])
            self._NMDisplay.edit()
        else:    
            _root_menu = NewMenu.NewMenu(name="Menus")
            for mnu in self._NMenuList:
                _root_menu.addSubmenu(mnu)            
            self._NMDisplay.setMenu(_root_menu)
            self._NMDisplay.edit()
        self.DISPLAY()
    
    def use_existing_menu(self, _mnu):
        if not hasattr(self, '_NMenuList'):
            self._NMenuList = []
        self._NMenuList.append(_mnu)
        return weakref.proxy(_mnu)
    
        
    def popup_menu(self, menu):
        self._NMDisplay.setMenu(menu)
        self._NMDisplay.edit()



        
