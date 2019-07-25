#!/usr/bin/env python
# encoding: utf-8
import weakref


class NewMenu(object):
    """docstring for NewMenu"""
    def __init__(self, name=None, shortcut=None, preDisplayFunction=None, pdfuncArguments=None, pdfuncKeywords=None):
        self.name      = name
        self._menuList = []
        self.enabled   = True
        self.shortcut  = shortcut
        self.pre_display_function = preDisplayFunction
        self.pdfunc_arguments= pdfuncArguments or ()
        self.pdfunc_keywords = pdfuncKeywords  or {}
    
    def addItemsFromList(self, item_list):
        for l in item_list:
            if isinstance(l, MenuItem):
                self.addNewSubmenu(*l)
            else:
                self.addItem(*l)

    def addItem(self, *args, **keywords):
        _itm = MenuItem(*args, **keywords)
        self._menuList.append(_itm)
    
    def addSubmenu(self, submenu):
        "Not recommended. Use addNewSubmenu instead"
        _itm = submenu
        self._menuList.append(submenu)
    
    def addNewSubmenu(self, *args, **keywords):
        _mnu = NewMenu(*args, **keywords)
        self._menuList.append(_mnu)
        return weakref.proxy(_mnu)
    
    def getItemObjects(self):
        return [itm for itm in self._menuList if itm.enabled]
    
    def do_pre_display_function(self):
        if self.pre_display_function:
            return self.pre_display_function(*self.pdfunc_arguments, **self.pdfunc_keywords)

class MenuItem(object):
    """docstring for MenuItem"""
    def __init__(self, text='', onSelect=None, shortcut=None, document=None, arguments=None, keywords=None):
        self.setText(text)
        self.setOnSelect(onSelect)
        self.setDocumentation(document)
        self.shortcut = shortcut
        self.enabled = True
        self.arguments = arguments or ()
        self.keywords = keywords or {}
        
    def setText(self, text):
        self._text = text
        
    def getText(self):
        return self._text
    
    def setOnSelect(self, onSelect):
        self.onSelectFunction = onSelect
        
    def setDocumentation(self, document):
        self._help = document
    
    def getDocumentation(self):
        return self._help
    
    def getHelp(self):
        return self._help
    
    def do(self):
        if self.onSelectFunction:
            return self.onSelectFunction(*self.arguments, **self.keywords)
