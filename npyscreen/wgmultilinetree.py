#!/usr/bin/python
import curses
import weakref

from . import wgmultiline    as multiline
from . import wgtextbox      as textbox
from .compatibility_code import npysNPSTree as NPSTree
from .npysTree import TreeData


class TreeLine(textbox.TextfieldBase):
    def __init__(self, *args, **keywords):
        self._tree_real_value   = None
        self._tree_ignore_root  = None
        self._tree_depth        = False
        self._tree_sibling_next = False
        self._tree_has_children = False
        self._tree_expanded     = True
        self._tree_last_line    = False
        self._tree_depth_next   = False
        self.safe_depth_display = False
        self.show_v_lines       = True
        super(TreeLine, self).__init__(*args, **keywords)

    ##########################################################################
    # Methods to enable this class to work with NPSTree and newer tree classes
    ##########################################################################

    def _get_content_for_display(self, vl):
        try:
            return vl.get_content_for_display()
        except AttributeError:
            return vl.getContentForDisplay()


    # End Compatibility Methods
    ##########################################################################





    #EXPERIMENTAL
    def _print(self, left_margin=0):
        self.left_margin = left_margin
        self.parent.curses_pad.bkgdset(' ',curses.A_NORMAL)
        self.left_margin += self._print_tree(self.relx)
        if self.highlight:
            self.parent.curses_pad.bkgdset(' ',curses.A_STANDOUT)
        super(TreeLine, self)._print()
        
    def _print_tree(self, real_x):
        if hasattr(self._tree_real_value, 'find_depth') or hasattr(self._tree_real_value, 'findDepth'):
            control_chars_added = 0
            this_safe_depth_display = self.safe_depth_display or ((self.width // 2) + 1)
            if self._tree_depth_next:
                _tree_depth_next = self._tree_depth_next
            else:
                _tree_depth_next = 0
            dp = self._tree_depth
            if self._tree_ignore_root:
                dp -= 1
            if dp: # > 0:
                if dp < this_safe_depth_display:                    
                    for i in range(dp-1):
                        if (i < _tree_depth_next) and (not self._tree_last_line): # was i+1 < # and not (_tree_depth_next==1):
                            if self.show_v_lines:
                                self.parent.curses_pad.addch(self.rely, real_x, curses.ACS_VLINE, curses.A_NORMAL)
                                if self.height > 1:
                                    for h in range(self.height-1):
                                        self.parent.curses_pad.addch(self.rely+h+1, real_x, curses.ACS_VLINE, curses.A_NORMAL)
                            else:
                                self.parent.curses_pad.addch(self.rely, real_x, ' ', curses.A_NORMAL)
                                
                        else:
                            if self.show_v_lines:
                                self.parent.curses_pad.addch(self.rely, real_x, curses.ACS_BTEE, curses.A_NORMAL)
                                
                            else:
                                self.parent.curses_pad.addch(self.rely, real_x, ' ', curses.A_NORMAL)
                                
                        real_x +=1
                        self.parent.curses_pad.addch(self.rely, real_x, ord(' '), curses.A_NORMAL)
                        real_x +=1
                    
                    
                    
                    if self._tree_sibling_next or _tree_depth_next > self._tree_depth:
                        self.parent.curses_pad.addch(self.rely, real_x, curses.ACS_LTEE, curses.A_NORMAL)
                        if self.height > 1:
                            for h in range(self.height-1):
                                self.parent.curses_pad.addch(self.rely+h+1, real_x, curses.ACS_VLINE, curses.A_NORMAL)
                    
                    else:
                        self.parent.curses_pad.addch(self.rely, real_x, curses.ACS_LLCORNER, curses.A_NORMAL)
                    real_x += 1
                    self.parent.curses_pad.addch(self.rely, real_x, curses.ACS_HLINE, curses.A_NORMAL)
                    real_x += 1
                else:
                    self.parent.curses_pad.addch(self.rely, real_x, curses.ACS_HLINE, curses.A_NORMAL)
                    real_x += 1
                    self.parent.curses_pad.addstr(self.rely, real_x, "[ %s ]" % (str(dp)), curses.A_NORMAL)
                    real_x += len(str(dp)) + 4
                    self.parent.curses_pad.addch(self.rely, real_x, curses.ACS_RTEE, curses.A_NORMAL)
                    real_x += 1
                    
            if self._tree_has_children:
                if self._tree_expanded:
                    self.parent.curses_pad.addch(self.rely, real_x, curses.ACS_TTEE, curses.A_NORMAL)
                    if self.height > 1:
                        for h in range(self.height-1):
                            self.parent.curses_pad.addch(self.rely+h+1, real_x, curses.ACS_VLINE, curses.A_NORMAL)
                    
                else:   
                    self.parent.curses_pad.addch(self.rely, real_x, curses.ACS_RARROW, curses.A_NORMAL)
                real_x +=1
            else:
                real_x +=1
            control_chars_added += real_x - self.relx
            margin_needed = control_chars_added + 1
        else:
            margin_needed = 0
        return margin_needed
        
        
    def display_value(self, vl):
        try:
            return self.safe_string(self._get_content_for_display(self._tree_real_value))
        except:
            # Catch the times this is None.
            return self.safe_string(vl)
            
    

class TreeLineAnnotated(TreeLine):
    ## Experimental.
    _annotate = "   ?   "
    _annotatecolor = 'CONTROL'

    def getAnnotationAndColor(self):
        # This is actually the api.  Override this function to return the correct string and colour name as a tuple.
        self.setAnnotateString()
        return (self._annotate, self._annotatecolor)

    def setAnnotateString(self):
        # This was an experimental function it was the original way to set the string and annotation.
        self._annotate = "   ?   "
        self._annotatecolor = 'CONTROL'

    def annotationColor(self, real_x):
        # Must return the "Margin" needed before the entry begins
         # historical reasons.
        _annotation, _color = self.getAnnotationAndColor()
        self.parent.curses_pad.addstr(self.rely, real_x, _annotation, self.parent.theme_manager.findPair(self, _color))
        return len(_annotation)

    def annotationNoColor(self, real_x):
        # Must return the "Margin" needed before the entry begins
        #self.parent.curses_pad.addstr(self.rely, real_x, 'xxx')
        #return 3
        _annotation, _color = self.getAnnotationAndColor()
        self.parent.curses_pad.addstr(self.rely, real_x, _annotation)
        return len(_annotation)

    def _print(self):
        self.left_margin = 0
        self.parent.curses_pad.bkgdset(' ',curses.A_NORMAL)
        self.left_margin += self._print_tree(self.relx)
        if self.do_colors():    
            self.left_margin += self.annotationColor(self.left_margin+self.relx)
        else:
            self.left_margin += self.annotationNoColor(self.left_margin+self.relx)
        if self.highlight:
            self.parent.curses_pad.bkgdset(' ',curses.A_STANDOUT)
        super(TreeLine, self)._print()


class MLTree(multiline.MultiLine):
    # Experimental
    
    #_contained_widgets = TreeLineAnnotated
    _contained_widgets = TreeLine

    ##########################################################################
    # Methods to enable this class to work with NPSTree and newer tree classes
    ##########################################################################

    def _find_depth(self, vl):
        try:
            return vl.find_depth()
        except AttributeError:
            return vl.findDepth()

    def _has_children(self, vl):
        try:
            return vl.has_children()
        except AttributeError:
            return vl.hasChildren()

    def _get_content(self, vl):
        try:
            return vl.get_content()
        except AttributeError:
            return vl.getContent()

    def _get_ignore_root(self, vl):
        try:
            return vl.ignore_root
        except AttributeError:
            return vl.ignoreRoot

    def _get_tree_as_list(self, vl):
        try:
            return vl.get_tree_as_list()
        except AttributeError:
            return vl.getTreeAsList()

    def _walk_tree(self, root, only_expanded=True, ignore_root=True, sort=None, sort_function=None):
        try:
            return root.walk_tree(only_expanded=only_expanded, ignore_root=ignore_root, sort=sort, sort_function=sort_function)
        except AttributeError:
            return root.walkTree(onlyExpanded=only_expanded, ignoreRoot=ignore_root, sort=sort, sort_function=sort_function)

    # End Compatibility Methods
    ##########################################################################

    def _setMyValues(self, tree):
        if tree == [] or tree == None:
            self._myFullValues = TreeData() #NPSTree.NPSTreeData()
        elif not (isinstance(tree, TreeData) or isinstance(tree, NPSTree.NPSTreeData)):
            tree = self.convertToTree(tree)
            self._myFullValues = tree
            if not (isinstance(tree, TreeData) or isinstance(tree, NPSTree.NPSTreeData)):
                raise TypeError("MultiLineTree widget can only contain a TreeData or NPSTreeData object in its values attribute")
        else:
            self._myFullValues = tree
    
    def convertToTree(self, tree):
        "Override this function to convert a set of values to a tree."
        return None
        
    def resize(self):
        super(MLTree, self).resize()
        self.clearDisplayCache()
        self.update(clear=True)
        self.display()
    
    def clearDisplayCache(self):
        self._cached_tree = None
        self._cached_sort = None
        self._cached_tree_as_list = None
    
    def _getApparentValues(self):
        try:
            if self._cached_tree is weakref.proxy(self._myFullValues) and \
            (self._cached_sort == (self._myFullValues.sort, self._myFullValues.sort_function)):
                return self._cached_tree_as_list
        except:
            pass
        self._cached_tree = weakref.proxy(self._myFullValues)
        self._cached_sort = (self._myFullValues.sort, self._myFullValues.sort_function)
        self._cached_tree_as_list = self._get_tree_as_list(self._myFullValues)
        return self._cached_tree_as_list
    
    def _walkMyValues(self):
        return self._walk_tree(self._myFullValues)
    
    def _delMyValues(self):
        self._myFullValues = None
    
    values = property(_getApparentValues, _setMyValues, _delMyValues)
    
    def filter_value(self, index):
        if self._filter in self._get_content(self.display_value(self.values[index])):
            return True
        else:
            return False
    
    def display_value(self, vl):
        return vl
    
    def set_up_handlers(self):
        super(MLTree, self).set_up_handlers()
        self.handlers.update({
                ord('<'): self.h_collapse_tree,
                ord('>'): self.h_expand_tree,
                ord('['): self.h_collapse_tree,
                ord(']'): self.h_expand_tree,
                ord('{'): self.h_collapse_all,
                ord('}'): self.h_expand_all,
                ord('h'): self.h_collapse_tree,
                ord('l'): self.h_expand_tree,                
        })

    
    def _before_print_lines(self):
        pass
    
    def _set_line_values(self, line, value_indexer):
        line._tree_real_value   = None
        line._tree_depth        = False
        line._tree_sibling_next = False
        line._tree_has_children = False
        line._tree_expanded     = False
        line._tree_last_line    = False
        line._tree_depth_next   = False
        line._tree_ignore_root  = None
        try:
            line.value = self.display_value(self.values[value_indexer])
            line._tree_real_value = self.values[value_indexer]
            line._tree_ignore_root = self._get_ignore_root(self._myFullValues)
            try:
                line._tree_depth        = self._find_depth(self.values[value_indexer])
                line._tree_has_children = self._has_children(self.values[value_indexer])
                line._tree_expanded     = self.values[value_indexer].expanded
            except:
                line._tree_depth        = False
                line._tree_has_children = False
                line._tree_expanded     = False
            try:
                if line._tree_depth == self._find_depth(self.values[value_indexer+1]):
                    line._tree_sibling_next = True
                else:
                    line._tree_sibling_next = False
    
            except:
                line._sibling_next = False
                line._tree_last_line = True
            try:
                line._tree_depth_next = self._find_depth(self.values[value_indexer+1])
            except:
                line._tree_depth_next = False
            line.hidden = False
        except IndexError:
            self._set_line_blank(line)
        except TypeError:
            self._set_line_blank(line)
            
    def h_collapse_tree(self, ch):
        if self.values[self.cursor_line].expanded and self._has_children(self.values[self.cursor_line]):
            self.values[self.cursor_line].expanded = False
        else:
            look_for_depth = self._find_depth(self.values[self.cursor_line]) - 1
            cursor_line = self.cursor_line - 1
            while cursor_line >= 0:
                if look_for_depth == self._find_depth(self.values[cursor_line]):
                    self.cursor_line = cursor_line
                    self.values[cursor_line].expanded = False
                    break
                else:
                    cursor_line -= 1
        self._cached_tree = None
        self.display()

    def h_expand_tree(self, ch):
        if not self.values[self.cursor_line].expanded:
            self.values[self.cursor_line].expanded = True
        else:
            for v in self._walk_tree(self.values[self.cursor_line], only_expanded=False):
                v.expanded = True
        self._cached_tree = None
        self.display()
    
    def h_collapse_all(self, ch):
        for v in self._walk_tree(self._myFullValues, only_expanded=True):
            v.expanded = False
        self._cached_tree = None
        self.cursor_line = 0
        self.display()
    
    def h_expand_all(self, ch):
        for v in self._walk_tree(self._myFullValues, only_expanded=False):
            v.expanded    = True
        self._cached_tree = None
        self.cursor_line  = 0
        self.display()
    
class MLTreeAnnotated(MLTree):
    _contained_widgets = TreeLineAnnotated

class MLTreeAction(MLTree, multiline.MultiLineAction):
    pass

class MLTreeAnnotatedAction(MLTree, multiline.MultiLineAction):
    _contained_widgets = TreeLineAnnotated













