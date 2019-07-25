import curses
from . import npysThemeManagers as ThemeManagers

class DefaultTheme(ThemeManagers.ThemeManager):
    default_colors = {
        'DEFAULT'     : 'WHITE_BLACK',
        'FORMDEFAULT' : 'WHITE_BLACK',
        'NO_EDIT'     : 'BLUE_BLACK',
        'STANDOUT'    : 'CYAN_BLACK',
        'CURSOR'      : 'WHITE_BLACK',
        'CURSOR_INVERSE': 'BLACK_WHITE',
        'LABEL'       : 'GREEN_BLACK',
        'LABELBOLD'   : 'WHITE_BLACK',
        'CONTROL'     : 'YELLOW_BLACK',
        'WARNING'     : 'RED_BLACK',
        'CRITICAL'    : 'BLACK_RED',
        'GOOD'        : 'GREEN_BLACK',
        'GOODHL'      : 'GREEN_BLACK',
        'VERYGOOD'    : 'BLACK_GREEN',
        'CAUTION'     : 'YELLOW_BLACK',
        'CAUTIONHL'   : 'BLACK_YELLOW',
    }
    
class ElegantTheme(ThemeManagers.ThemeManager):
    default_colors = {
        'DEFAULT'     : 'WHITE_BLACK',
        'FORMDEFAULT' : 'WHITE_BLACK',
        'NO_EDIT'     : 'BLUE_BLACK',
        'STANDOUT'    : 'CYAN_BLACK',
        'CURSOR'      : 'CYAN_BLACK',
        'CURSOR_INVERSE': 'BLACK_CYAN',
        'LABEL'       : 'GREEN_BLACK',
        'LABELBOLD'   : 'WHITE_BLACK',
        'CONTROL'     : 'YELLOW_BLACK',
        'WARNING'     : 'RED_BLACK',
        'CRITICAL'    : 'BLACK_RED',
        'GOOD'        : 'GREEN_BLACK',
        'GOODHL'      : 'GREEN_BLACK',
        'VERYGOOD'    : 'BLACK_GREEN',
        'CAUTION'     : 'YELLOW_BLACK',
        'CAUTIONHL'   : 'BLACK_YELLOW',
    }


class ColorfulTheme(ThemeManagers.ThemeManager):
    default_colors = {
        'DEFAULT'     : 'RED_BLACK',
        'FORMDEFAULT' : 'YELLOW_BLACK',
        'NO_EDIT'     : 'BLUE_BLACK',
        'STANDOUT'    : 'CYAN_BLACK',
        'CURSOR'      : 'WHITE_BLACK',
        'CURSOR_INVERSE': 'BLACK_WHITE',
        'LABEL'       : 'BLUE_BLACK',
        'LABELBOLD'   : 'YELLOW_BLACK',
        'CONTROL'     : 'GREEN_BLACK',
        'WARNING'     : 'RED_BLACK',
        'CRITICAL'    : 'BLACK_RED',
        'GOOD'        : 'GREEN_BLACK',
        'GOODHL'      : 'GREEN_BLACK',
        'VERYGOOD'    : 'BLACK_GREEN',
        'CAUTION'     : 'YELLOW_BLACK',
        'CAUTIONHL'   : 'BLACK_YELLOW',
        }

class BlackOnWhiteTheme(ThemeManagers.ThemeManager):
    default_colors = {
        'DEFAULT'     : 'BLACK_WHITE',
        'FORMDEFAULT' : 'BLACK_WHITE',
        'NO_EDIT'     : 'BLUE_WHITE',
        'STANDOUT'    : 'CYAN_WHITE',
        'CURSOR'      : 'BLACK_WHITE',
        'CURSOR_INVERSE': 'WHITE_BLACK',
        'LABEL'       : 'RED_WHITE',
        'LABELBOLD'   : 'BLACK_WHITE',
        'CONTROL'     : 'BLUE_WHITE',
        'WARNING'     : 'RED_WHITE',
        'CRITICAL'    : 'BLACK_RED',
        'GOOD'        : 'GREEN_BLACK',
        'GOODHL'      : 'GREEN_WHITE',
        'VERYGOOD'    : 'WHITE_GREEN',
        'CAUTION'     : 'YELLOW_WHITE',
        'CAUTIONHL'   : 'BLACK_YELLOW',
    }

class TransparentThemeDarkText(ThemeManagers.ThemeManager):
    _colors_to_define = ( 
    ('BLACK_WHITE',      curses.COLOR_BLACK,      curses.COLOR_WHITE),
    ('BLUE_BLACK',       curses.COLOR_BLUE,       curses.COLOR_BLACK),
    ('CYAN_BLACK',       curses.COLOR_CYAN,       curses.COLOR_BLACK),
    ('GREEN_BLACK',      curses.COLOR_GREEN,      curses.COLOR_BLACK),
    ('MAGENTA_BLACK',    curses.COLOR_MAGENTA,    curses.COLOR_BLACK),
    ('RED_BLACK',        curses.COLOR_RED,        curses.COLOR_BLACK),
    ('YELLOW_BLACK',     curses.COLOR_YELLOW,     curses.COLOR_BLACK),
    ('BLACK_RED',        curses.COLOR_BLACK,      curses.COLOR_RED),
    ('BLACK_GREEN',      curses.COLOR_BLACK,      curses.COLOR_GREEN),
    ('BLACK_YELLOW',     curses.COLOR_BLACK,      curses.COLOR_YELLOW),

    ('BLUE_WHITE',       curses.COLOR_BLUE,       curses.COLOR_WHITE),
    ('CYAN_WHITE',       curses.COLOR_CYAN,       curses.COLOR_WHITE),
    ('GREEN_WHITE',      curses.COLOR_GREEN,      curses.COLOR_WHITE),
    ('MAGENTA_WHITE',    curses.COLOR_MAGENTA,    curses.COLOR_WHITE),
    ('RED_WHITE',        curses.COLOR_RED,        curses.COLOR_WHITE),
    ('YELLOW_WHITE',     curses.COLOR_YELLOW,     curses.COLOR_WHITE),
     
    ('BLACK_ON_DEFAULT',   curses.COLOR_BLACK,      -1),
    ('WHITE_ON_DEFAULT',   curses.COLOR_WHITE,      -1),
    ('BLUE_ON_DEFAULT',    curses.COLOR_BLUE,       -1),
    ('CYAN_ON_DEFAULT',    curses.COLOR_CYAN,       -1),
    ('GREEN_ON_DEFAULT',   curses.COLOR_GREEN,      -1),
    ('MAGENTA_ON_DEFAULT', curses.COLOR_MAGENTA,    -1),
    ('RED_ON_DEFAULT',     curses.COLOR_RED,        -1),
    ('YELLOW_ON_DEFAULT',  curses.COLOR_YELLOW,     -1),
    )

    default_colors = {
        'DEFAULT'     : 'BLACK_ON_DEFAULT',
        'FORMDEFAULT' : 'BLACK_ON_DEFAULT',
        'NO_EDIT'     : 'BLUE_ON_DEFAULT',
        'STANDOUT'    : 'CYAN_ON_DEFAULT',
        'CURSOR'      : 'BLACK_WHITE',
        'CURSOR_INVERSE': 'WHITE_BLACK',
        'LABEL'       : 'RED_ON_DEFAULT',
        'LABELBOLD'   : 'BLACK_ON_DEFAULT',
        'CONTROL'     : 'BLUE_ON_DEFAULT',
        'WARNING'     : 'RED_WHITE',
        'CRITICAL'    : 'BLACK_RED',
        'GOOD'        : 'GREEN_BLACK',
        'GOODHL'      : 'GREEN_WHITE',
        'VERYGOOD'    : 'WHITE_GREEN',
        'CAUTION'     : 'YELLOW_WHITE',
        'CAUTIONHL'   : 'BLACK_YELLOW',
    }


    def __init__(self, *args, **keywords):
        curses.use_default_colors()
        super(TransparentThemeDarkText, self).__init__(*args, **keywords)
        
class TransparentThemeLightText(TransparentThemeDarkText):
    default_colors = {
        'DEFAULT'     : 'WHITE_ON_DEFAULT',
        'FORMDEFAULT' : 'WHITE_ON_DEFAULT',
        'NO_EDIT'     : 'BLUE_ON_DEFAULT',
        'STANDOUT'    : 'CYAN_ON_DEFAULT',
        'CURSOR'      : 'WHITE_BLACK',
        'CURSOR_INVERSE': 'BLACK_WHITE',
        'LABEL'       : 'RED_ON_DEFAULT',
        'LABELBOLD'   : 'BLACK_ON_DEFAULT',
        'CONTROL'     : 'BLUE_ON_DEFAULT',
        'WARNING'     : 'RED_BLACK',
        'CRITICAL'    : 'BLACK_RED',
        'GOOD'        : 'GREEN_BLACK',
        'GOODHL'      : 'GREEN_BLACK',
        'VERYGOOD'    : 'BLACK_GREEN',
        'CAUTION'     : 'YELLOW_BLACK',
        'CAUTIONHL'   : 'BLACK_YELLOW',
    }
    
