#!/usr/bin/env python
# encoding: utf-8
import curses
import _curses
#import curses.wrapper
import locale
import os
#import pty
import subprocess
import sys
import warnings

_NEVER_RUN_INITSCR = True
_SCREEN = None

def wrapper_basic(call_function):
    #set the locale properly
    locale.setlocale(locale.LC_ALL, '')
    return curses.wrapper(call_function)

#def wrapper(call_function):
#   locale.setlocale(locale.LC_ALL, '')
#   screen = curses.initscr()
#   curses.noecho()
#   curses.cbreak()
#   
#   return_code = call_function(screen)
#   
#   curses.nocbreak()
#   curses.echo()
#   curses.endwin()

def wrapper(call_function, fork=None, reset=True):
    global _NEVER_RUN_INITSCR
    if fork:
        wrapper_fork(call_function, reset=reset)
    elif fork == False:
        wrapper_no_fork(call_function)
    else:
        if _NEVER_RUN_INITSCR:
            wrapper_no_fork(call_function)
        else:
            wrapper_fork(call_function, reset=reset)

def wrapper_fork(call_function, reset=True):
    pid = os.fork()
    if pid:
        # Parent
        os.waitpid(pid, 0)
        if reset:
            external_reset()
    else:
        locale.setlocale(locale.LC_ALL, '')
        _SCREEN = curses.initscr()
        try:
            curses.start_color()
        except:
            pass
        _SCREEN.keypad(1)
        curses.noecho()
        curses.cbreak()
        curses.def_prog_mode()
        curses.reset_prog_mode()
        return_code = call_function(_SCREEN)
        _SCREEN.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        sys.exit(0)

def external_reset():
    subprocess.call(['reset', '-Q'])
    
def wrapper_no_fork(call_function, reset=False):
    global _NEVER_RUN_INITSCR
    if not _NEVER_RUN_INITSCR:
        warnings.warn("""Repeated calls of endwin may cause a memory leak. Use wrapper_fork to avoid.""")
    global _SCREEN
    return_code = None
    if _NEVER_RUN_INITSCR:
        _NEVER_RUN_INITSCR = False
        locale.setlocale(locale.LC_ALL, '')
        _SCREEN = curses.initscr()
        try:
            curses.start_color()
        except:
            pass
        curses.noecho()
        curses.cbreak()
        _SCREEN.keypad(1)

    curses.noecho()
    curses.cbreak()
    _SCREEN.keypad(1)
    
    try:
        return_code = call_function(_SCREEN)    
    finally:
        _SCREEN.keypad(0)
        curses.echo()
        curses.nocbreak()
        # Calling endwin() and then refreshing seems to cause a memory leak.
        curses.endwin()
        if reset:
            external_reset()
    return return_code  
