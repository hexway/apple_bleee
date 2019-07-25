#!/usr/bin/env python

import curses
import curses.panel
#import curses.wrapper
from . import npyspmfuncs as pmfuncs
import os
from . import npysThemeManagers as ThemeManagers


# For more complex method of getting the size of screen
try:
    import fcntl, termios, struct, sys
except:
    # Win32 platforms do not have fcntl
    pass


APPLICATION_THEME_MANAGER = None

def setTheme(theme):
    global APPLICATION_THEME_MANAGER
    APPLICATION_THEME_MANAGER = theme()

def getTheme():
    return APPLICATION_THEME_MANAGER



class ScreenArea(object):
    BLANK_LINES_BASE   =0
    BLANK_COLUMNS_RIGHT=0
    DEFAULT_NEXTRELY=2
    DEFAULT_LINES      = 0
    DEFAULT_COLUMNS    = 0
    SHOW_ATX           = 0
    SHOW_ATY           = 0
    
    """A screen area that can be safely resized.  But this is a low-level class, not the
    object you are looking for."""

    def __init__(self, lines=0, columns=0, 
            minimum_lines = 24,
            minimum_columns = 80,
            show_atx = 0, 
            show_aty = 0,
             **keywords):

        
    # Putting a default in here will override the system in _create_screen. For testing?
        if not lines:
            lines = self.__class__.DEFAULT_LINES
        if not columns:
            columns = self.__class__.DEFAULT_COLUMNS
            
        if lines:   minimum_lines   = lines
        if columns: minimum_columns = columns

        self.lines = lines #or 25
        self.columns = columns #or 80

        self.min_l = minimum_lines
        self.min_c = minimum_columns

        # Panels can be bigger than the screen area. These two variables
        # set which bit of the panel should be visible.
        # ie. They are about the virtual, not the physical, screen.
        self.show_from_y = 0
        self.show_from_x = 0
        self.show_atx = show_atx or self.__class__.SHOW_ATX
        self.show_aty = show_aty or self.__class__.SHOW_ATY
        self.ALL_SHOWN = False
        
        global APPLICATION_THEME_MANAGER
        if APPLICATION_THEME_MANAGER is None:
            self.theme_manager = ThemeManagers.ThemeManager()
        else:
            self.theme_manager = APPLICATION_THEME_MANAGER
        
        self.keypress_timeout = None
        

        self._create_screen()

    def _create_screen(self):
    
        try:
            if self.lines_were_auto_set: self.lines = None
            if self.cols_were_auto_set: self.columns = None
        except: pass

        
        if not self.lines: 
            self.lines = self._max_physical()[0]+1
            self.lines_were_auto_set = True
        if not self.columns: 
            self.columns = self._max_physical()[1]+1
            self.cols_were_auto_set = True

        if self.min_l > self.lines:
            self.lines = self.min_l

        if self.min_c > self.columns:
            self.columns = self.min_c

        #self.area = curses.newpad(self.lines, self.columns)
        self.curses_pad = curses.newpad(self.lines, self.columns)
        #self.max_y, self.max_x = self.lines, self.columns
        self.max_y, self.max_x = self.curses_pad.getmaxyx()

    def _max_physical(self):
        "How big is the physical screen?"
        # On OS X newwin does not correctly get the size of the screen.
        # let's see how big we could be: create a temp screen
        # and see the size curses makes it.  No good to keep, though
        try:
            mxy, mxx = struct.unpack('hh', fcntl.ioctl(sys.stderr.fileno(), termios.TIOCGWINSZ, 'xxxx'))
            if (mxy, mxx) == (0,0):
                raise ValueError
        except (ValueError, NameError):
            mxy, mxx = curses.newwin(0,0).getmaxyx()

        # return safe values, i.e. slightly smaller.
        return (mxy-1, mxx-1)

    def useable_space(self, rely=0, relx=0):
       mxy, mxx = self.lines, self.columns
       return (mxy-rely, mxx-1-relx) # x - 1 because can't use last line bottom right.

    def widget_useable_space(self, rely=0, relx=0):
        #Slightly misreports space available.
        #mxy, mxx = self.lines, self.columns-1
        mxy, mxx = self.useable_space(rely=rely, relx=relx)
        return (mxy-self.BLANK_LINES_BASE, mxx-self.BLANK_COLUMNS_RIGHT)
    
    def refresh(self):
        pmfuncs.hide_cursor()
        _my, _mx = self._max_physical()
        self.curses_pad.move(0,0)
        
        # Since we can have pannels larger than the screen
        # let's allow for scrolling them
        
        # Getting strange errors on OS X, with curses sometimes crashing at this point. 
        # Suspect screen size not updated in time. This try: seems to solve it with no ill effects.
        try:
            self.curses_pad.refresh(self.show_from_y,self.show_from_x,self.show_aty,self.show_atx,_my,_mx)
        except curses.error:
            pass
        if self.show_from_y is 0 and \
        self.show_from_x is 0 and \
        (_my >= self.lines) and \
        (_mx >= self.columns):
            self.ALL_SHOWN = True

        else:
            self.ALL_SHOWN = False
    
    def erase(self):
        self.curses_pad.erase()
        self.refresh()

