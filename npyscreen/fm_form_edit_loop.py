#!/usr/bin/env python
# encoding: utf-8
"""
form_edit_loop.py

Created by Nicholas Cole on 2008-03-31.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

import sys
import os
import weakref

class FormNewEditLoop(object):
    "Edit Fields .editing = False"
    def pre_edit_loop(self):
        pass
    def post_edit_loop(self):
        pass
    def _during_edit_loop(self):
        pass
    
    def edit_loop(self):
        self.editing = True
        self.display()
        while not (self._widgets__[self.editw].editable and not self._widgets__[self.editw].hidden):
            self.editw += 1
            if self.editw > len(self._widgets__)-1: 
                self.editing = False
                return False
        
        while self.editing:
            if not self.ALL_SHOWN: self.on_screen()
            self.while_editing(weakref.proxy(self._widgets__[self.editw]))
            self._during_edit_loop()
            if not self.editing:
                break
            self._widgets__[self.editw].edit()
            self._widgets__[self.editw].display()

            self.handle_exiting_widgets(self._widgets__[self.editw].how_exited)

            if self.editw > len(self._widgets__)-1: self.editw = len(self._widgets__)-1
        
    def edit(self):
        self.pre_edit_loop()
        self.edit_loop()
        self.post_edit_loop()

class FormDefaultEditLoop(object):
    def edit(self):
        """Edit the fields until the user selects the ok button added in the lower right corner. Button will
        be removed when editing finishes"""
        # Add ok button. Will remove later
        tmp_rely, tmp_relx = self.nextrely, self.nextrelx
        my, mx = self.curses_pad.getmaxyx()
        ok_button_text = self.__class__.OK_BUTTON_TEXT
        my -= self.__class__.OK_BUTTON_BR_OFFSET[0]
        mx -= len(ok_button_text)+self.__class__.OK_BUTTON_BR_OFFSET[1]
        self.ok_button = self.add_widget(self.__class__.OKBUTTON_TYPE, name=ok_button_text, rely=my, relx=mx, use_max_space=True)
        ok_button_postion = len(self._widgets__)-1
        self.ok_button.update()
        # End add buttons 
        self.editing=True
        if self.editw < 0: self.editw=0
        if self.editw > len(self._widgets__)-1:
            self.editw = len(self._widgets__)-1
        if not self.preserve_selected_widget:
            self.editw = 0
        if not self._widgets__[self.editw].editable: self.find_next_editable()


        self.display()

        while not (self._widgets__[self.editw].editable and not self._widgets__[self.editw].hidden):
            self.editw += 1
            if self.editw > len(self._widgets__)-1: 
                self.editing = False
                return False

        while self.editing:
            if not self.ALL_SHOWN: self.on_screen()
            self.while_editing(weakref.proxy(self._widgets__[self.editw]))
            if not self.editing:
                break
            self._widgets__[self.editw].edit()
            self._widgets__[self.editw].display()

            self.handle_exiting_widgets(self._widgets__[self.editw].how_exited)

            if self.editw > len(self._widgets__)-1: self.editw = len(self._widgets__)-1
            if self.ok_button.value:
                self.editing = False

        self.ok_button.destroy()
        del self._widgets__[ok_button_postion]
        del self.ok_button
        self.nextrely, self.nextrelx = tmp_rely, tmp_relx
        self.display()
        
        #try:
        #    self.parentApp._FORM_VISIT_LIST.pop()
        #except:
        #    pass
        

        self.editing = False
        self.erase()
    
    def move_ok_button(self):
        if hasattr(self, 'ok_button'):
            my, mx = self.curses_pad.getmaxyx()
            my -= self.__class__.OK_BUTTON_BR_OFFSET[0]
            mx -= len(self.__class__.OK_BUTTON_TEXT)+self.__class__.OK_BUTTON_BR_OFFSET[1]
            self.ok_button.relx = mx
            self.ok_button.rely = my


    
