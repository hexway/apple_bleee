#!/usr/bin/env pyton

from . import wgcheckbox
import weakref

class FormControlCheckbox(wgcheckbox.Checkbox):
    def __init__(self, *args, **keywords):
        super(FormControlCheckbox, self).__init__(*args, **keywords)
        self._visibleWhenSelected    = []
        self._notVisibleWhenSelected = []

    def addVisibleWhenSelected(self, w):
        """Add a widget to be visible only when this box is selected"""
        self._register(w, vws=True)
    
    def addInvisibleWhenSelected(self, w):
        self._register(w, vws=False)
        
    def _register(self, w, vws=True):
        if vws:
            working_list = self._visibleWhenSelected
        else:
            working_list = self._notVisibleWhenSelected
            
        if w in working_list:
            pass
        else:
            try:
                working_list.append(weakref.proxy(w))
            except TypeError:
                working_list.append(w)
        
        self.updateDependents()
    
    def updateDependents(self):
        # This doesn't yet work.
        if self.value:
            for w in self._visibleWhenSelected:
                w.hidden    = False
                w.editable  = True
            for w in self._notVisibleWhenSelected:
                w.hidden    =  True
                w.editable  =  False
        else:
            for w in self._visibleWhenSelected:
                w.hidden    = True
                w.editable  = False
            for w in self._notVisibleWhenSelected:
                w.hidden    =  False
                w.editable  =  True
        self.parent.display()

    def h_toggle(self, *args):
        super(FormControlCheckbox, self).h_toggle(*args)
        self.updateDependents()
        

        
