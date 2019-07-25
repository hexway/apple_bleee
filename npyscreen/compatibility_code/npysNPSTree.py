#!/usr/bin/env python
import weakref
import collections
import operator

class NPSTreeData(object):
    CHILDCLASS = None
    def __init__(self, content=None, parent=None, selected=False, selectable=True,
                    highlight=False, expanded=True, ignoreRoot=True, sort_function=None):
        self.setParent(parent)
        self.setContent(content)
        self.selectable = selectable
        self.selected   = selected
        self.highlight  = highlight
        self.expanded   = expanded
        self._children  = []
        self.ignoreRoot = ignoreRoot
        self.sort       = False
        self.sort_function = sort_function
        self.sort_function_wrapper = True
        
    
    def getContent(self):
        return self.content
        
    def getContentForDisplay(self):
        return str(self.content)
    
    def setContent(self, content):
        self.content = content
    
    def isSelected(self):
        return self.selected
    
    def isHighlighted(self):
        return self.highlight
    
    def setParent(self, parent):
        if parent == None:
            self._parent = None
        else:
            self._parent = weakref.proxy(parent)
    
    def getParent(self):
        return self._parent
        
    
    def findDepth(self, d=0):
        depth = d
        parent = self.getParent()
        while parent:
            d += 1
            parent = parent.getParent()
        return d
        # Recursive
        #if self._parent == None:
        #    return d
        #else:
        #    return(self._parent.findDepth(d+1))
    
    def isLastSibling(self):
        if self.getParent():
            if list(self.getParent().getChildren())[-1] == self:
                return True
            else:
                return False
        else:
            return None
    
    def hasChildren(self):
        if len(self._children) > 0:
            return True
        else:
            return False
    
    def getChildren(self):
        for c in self._children:
            try:
                yield weakref.proxy(c)
            except:
                yield c
                
    def getChildrenObjects(self):
        return self._children[:]
    
    def _getChildrenList(self):
        return self._children
    
    def newChild(self, *args, **keywords):
        if self.CHILDCLASS:
            cld = self.CHILDCLASS
        else:
            cld = type(self)
        c = cld(parent=self, *args, **keywords)
        self._children.append(c)
        return weakref.proxy(c)
        
    def removeChild(self, child):
        new_children = []
        for ch in self._children:
            # do it this way because of weakref equality bug.
            if not ch.getContent() == child.getContent():
                new_children.append(ch)
            else:
                ch.setParent(None)
        self._children = new_children
    
        
    def create_wrapped_sort_function(self, this_function):
        def new_function(the_item):
            if the_item:
                the_real_item = the_item.getContent()
                return this_function(the_real_item)
            else:
                return the_item        
        return new_function

    def walkParents(self):
        p = self.getParent()
        while p:
            yield p
            p = p.getParent()
            
    def walkTree(self, onlyExpanded=True, ignoreRoot=True, sort=None, sort_function=None):
        #Iterate over Tree        
        if sort is None:
            sort = self.sort
        
        if sort_function is None:
            sort_function = self.sort_function
        
        # example sort function # sort = True
        # example sort function # def sort_function(the_item):
        # example sort function #     import email.utils
        # example sort function #     if the_item:
        # example sort function #         if the_item.getContent():
        # example sort function #             frm = the_item.getContent().get('from')
        # example sort function #             try:
        # example sort function #                 frm = email.utils.parseaddr(frm)[0]
        # example sort function #             except:
        # example sort function #                 pass
        # example sort function #             return frm
        # example sort function #     else:
        # example sort function #         return the_item
        #key = operator.methodcaller('getContent',)
                    
        if self.sort_function_wrapper and sort_function:
           # def wrapped_sort_function(the_item):
           #     if the_item:
           #         the_real_item = the_item.getContent()
           #         return sort_function(the_real_item)
           #     else:
           #         return the_item        
           # _this_sort_function = wrapped_sort_function
           _this_sort_function = self.create_wrapped_sort_function(sort_function)
        else:
            _this_sort_function = sort_function
        
        key = _this_sort_function
        if not ignoreRoot:
            yield self
        nodes_to_yield = collections.deque() # better memory management than a list for pop(0)
        if self.expanded or not onlyExpanded:
            if sort:
                # This and the similar block below could be combined into a nested function
                if key:
                    nodes_to_yield.extend(sorted(self.getChildren(), key=key,))
                else:
                    nodes_to_yield.extend(sorted(self.getChildren()))
            else:
                nodes_to_yield.extend(self.getChildren())
            while nodes_to_yield:
                child = nodes_to_yield.popleft()
                if child.expanded or not onlyExpanded:
                    # This and the similar block above could be combined into a nested function
                    if sort:
                        if key:
                            # must be reverse because about to use extendleft() below.
                            nodes_to_yield.extendleft(sorted(child.getChildren(), key=key, reverse=True)) 
                        else:
                            nodes_to_yield.extendleft(sorted(child.getChildren(), reverse=True))
                    else:
                        #for node in child.getChildren():
                        #    if node not in nodes_to_yield:
                        #        nodes_to_yield.appendleft(node)
                        yield_these = list(child.getChildren())
                        yield_these.reverse()
                        nodes_to_yield.extendleft(yield_these)
                        del yield_these
                yield child

    def _walkTreeRecursive(self,onlyExpanded=True, ignoreRoot=True,):
        #This is an old, recursive version
        if (not onlyExpanded) or (self.expanded):
            for child in self.getChildren():
                for node in child.walkTree(onlyExpanded=onlyExpanded, ignoreRoot=False):
                    yield node
        
    def getTreeAsList(self, onlyExpanded=True, sort=None, key=None):
        _a = []
        for node in self.walkTree(onlyExpanded=onlyExpanded, ignoreRoot=self.ignoreRoot, sort=sort):
            try:
                _a.append(weakref.proxy(node))
            except:
                _a.append(node)
        return _a

