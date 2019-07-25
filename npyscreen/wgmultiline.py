#!/usr/bin/python
import copy
from . import wgwidget       as widget
from . import wgtextbox      as textbox
import textwrap
import curses
from . import wgtitlefield   as titlefield
from . import fmPopup        as Popup
import weakref
import collections
import copy

MORE_LABEL = "- more -"  # string to tell user there are more options


class FilterPopupHelper(Popup.Popup):
    def create(self):
        super(FilterPopupHelper, self).create()
        self.filterbox = self.add(titlefield.TitleText, name='Find:', )
        self.nextrely += 1
        self.statusline = self.add(textbox.Textfield, color='LABEL', editable=False)

    def updatestatusline(self):
        self.owner_widget._filter = self.filterbox.value
        filtered_lines = self.owner_widget.get_filtered_indexes()
        len_f = len(filtered_lines)
        if self.filterbox.value == None or self.filterbox.value == '':
            self.statusline.value = ''
        elif len_f == 0:
            self.statusline.value = '(No Matches)'
        elif len_f == 1:
            self.statusline.value = '(1 Match)'
        else:
            self.statusline.value = '(%s Matches)' % len_f

    def adjust_widgets(self):
        self.updatestatusline()
        self.statusline.display()


class MultiLine(widget.Widget):
    _safe_to_display_cache = True
    """Display a list of items to the user.  By overloading the display_value method, this widget can be made to 
display different kinds of objects.  Given the standard definition, 
the same effect can be achieved by altering the __str__() method of displayed objects"""
    _MINIMUM_HEIGHT = 2  # Raise an error if not given this.
    _contained_widgets = textbox.Textfield
    _contained_widget_height = 1

    def __init__(self, screen, values=None, value=None,
                 slow_scroll=False, scroll_exit=False,
                 return_exit=False, select_exit=False,
                 exit_left=False,
                 exit_right=False,
                 widgets_inherit_color=False,
                 always_show_cursor=False,
                 allow_filtering=True,
                 cursor_line=0,
                 start_display_at=0,
                 custom_highlighting=False,
                 highlighting_arr_color_data=None,
                 **keywords):

        self.never_cache = False
        self.exit_left = exit_left
        self.exit_right = exit_right
        self.allow_filtering = allow_filtering
        self.widgets_inherit_color = widgets_inherit_color
        super(MultiLine, self).__init__(screen, **keywords)
        if self.height < self.__class__._MINIMUM_HEIGHT:
            raise widget.NotEnoughSpaceForWidget(
                "Height of %s allocated. Not enough space allowed for %s" % (self.height, str(self)))
        self.make_contained_widgets()

        self.value = value

        # does pushing return select and then leave the widget?
        self.return_exit = return_exit

        # does any selection leave the widget?
        self.select_exit = select_exit

        # Show cursor even when not editing?
        self.always_show_cursor = always_show_cursor

        self.slow_scroll = slow_scroll
        self.scroll_exit = scroll_exit

        self.start_display_at = start_display_at
        self.cursor_line = cursor_line
        self.values = values or []
        self._filter = None

        # These are just to do some optimisation tricks
        self._last_start_display_at = None
        self._last_cursor_line = None
        self._last_values = copy.copy(values)
        self._last_value = copy.copy(value)
        self._last_filter = None
        self._filtered_values_cache = []

        # override - it looks nicer.
        if self.scroll_exit:
            self.slow_scroll = True

        # custom highlightning
        self.custom_highlighting = custom_highlighting
        self.highlighting_arr_color_data = highlighting_arr_color_data

    def resize(self):
        super(MultiLine, self).resize()
        self.make_contained_widgets()
        self.reset_display_cache()
        self.display()

    def make_contained_widgets(self, ):
        self._my_widgets = []
        for h in range(self.height // self.__class__._contained_widget_height):
            self._my_widgets.append(
                self._contained_widgets(self.parent,
                                        rely=(h * self._contained_widget_height) + self.rely,
                                        relx=self.relx,
                                        max_width=self.width,
                                        max_height=self.__class__._contained_widget_height
                                        )
            )

    def display_value(self, vl):
        """Overload this function to change how values are displayed.  
Should accept one argument (the object to be represented), and return a string or the 
object to be passed to the contained widget."""
        try:
            return self.safe_string(str(vl))
        except ReferenceError:
            return "**REFERENCE ERROR**"

        try:
            return "Error displaying " + self.safe_string(repr(vl))
        except:
            return "**** Error ****"

    def calculate_area_needed(self):
        return 0, 0

    def reset_cursor(self):
        self.start_display_at = 0
        self.cursor_line = 0

    def reset_display_cache(self):
        self._last_values = False
        self._last_value = False

    def update(self, clear=True):
        if self.hidden and clear:
            self.clear()
            return False
        elif self.hidden:
            return False

        if self.values == None:
            self.values = []

        # clear = None is a good value for this widget
        display_length = len(self._my_widgets)
        # self._remake_filter_cache()
        self._filtered_values_cache = self.get_filtered_indexes()

        if self.editing or self.always_show_cursor:
            if self.cursor_line < 0: self.cursor_line = 0
            if self.cursor_line > len(self.values) - 1: self.cursor_line = len(self.values) - 1

            if self.slow_scroll:
                if self.cursor_line > self.start_display_at + display_length - 1:
                    self.start_display_at = self.cursor_line - (display_length - 1)

                if self.cursor_line < self.start_display_at:
                    self.start_display_at = self.cursor_line

            else:
                if self.cursor_line > self.start_display_at + (display_length - 2):
                    self.start_display_at = self.cursor_line

                if self.cursor_line < self.start_display_at:
                    self.start_display_at = self.cursor_line - (display_length - 2)
                    if self.start_display_at < 0: self.start_display_at = 0

        # What this next bit does is to not bother updating the screen if nothing has changed.
        no_change = False
        try:
            if (self._safe_to_display_cache and \
                self._last_value is self.value) and \
                    (self.values == self._last_values) and \
                    (self.start_display_at == self._last_start_display_at) and \
                    (clear != True) and \
                    (self._last_cursor_line == self.cursor_line) and \
                    (self._last_filter == self._filter) and \
                    self.editing:
                no_change = True

            else:
                no_change = False
        except:
            no_change = False
        if clear:
            no_change = False
        if not no_change or clear or self.never_cache:
            if clear is True:
                self.clear()

            if (self._last_start_display_at != self.start_display_at) \
                    and clear is None:
                self.clear()
            else:
                pass

            self._last_start_display_at = self.start_display_at

            self._before_print_lines()
            indexer = 0 + self.start_display_at
            for line in self._my_widgets[:-1]:
                self._print_line(line, indexer)
                line.task = "PRINTLINE"
                line.update(clear=True)
                indexer += 1

            # Now do the final line
            line = self._my_widgets[-1]

            if (len(
                    self.values) <= indexer + 1):  # or (len(self._my_widgets)*self._contained_widget_height)<self.height:
                self._print_line(line, indexer)
                line.task = "PRINTLINE"
                line.update(clear=False)
            elif len((self._my_widgets) * self._contained_widget_height) < self.height:
                self._print_line(line, indexer)
                line.task = "PRINTLINELASTOFSCREEN"
                line.update(clear=False)
                if self.do_colors():
                    self.parent.curses_pad.addstr(self.rely + self.height - 1, self.relx, MORE_LABEL,
                                                  self.parent.theme_manager.findPair(self, 'CONTROL'))
                else:
                    self.parent.curses_pad.addstr(self.rely + self.height - 1, self.relx, MORE_LABEL)
            else:
                # line.value = MORE_LABEL
                line.name = MORE_LABEL
                line.task = MORE_LABEL
                # line.highlight = False
                # line.show_bold = False
                line.clear()
                if self.do_colors():
                    self.parent.curses_pad.addstr(self.rely + self.height - 1, self.relx, MORE_LABEL,
                                                  self.parent.theme_manager.findPair(self, 'CONTROL'))
                else:
                    self.parent.curses_pad.addstr(self.rely + self.height - 1, self.relx, MORE_LABEL)

            if self.editing or self.always_show_cursor:
                self.set_is_line_cursor(self._my_widgets[(self.cursor_line - self.start_display_at)], True)
                self._my_widgets[(self.cursor_line - self.start_display_at)].update(clear=True)
            else:
                # There is a bug somewhere that affects the first line.  This cures it.
                # Without this line, the first line inherits the color of the form when not editing. Not clear why.
                self._my_widgets[0].update()

        self._last_start_display_at = self.start_display_at
        self._last_cursor_line = self.cursor_line
        self._last_values = copy.copy(self.values)
        self._last_value = copy.copy(self.value)

        # This will prevent the program crashing if the user has changed values, and the cursor 
        # is now on the bottom line.
        if (self._my_widgets[self.cursor_line - self.start_display_at].task in (MORE_LABEL, "PRINTLINELASTOFSCREEN")):
            if self.slow_scroll:
                self.start_display_at += 1
            else:
                self.start_display_at = self.cursor_line
            self.update(clear=clear)

    def _before_print_lines(self):
        # Provide a function for the Tree classes to override.
        pass

    def _print_line(self, line, value_indexer):
        if self.widgets_inherit_color and self.do_colors():
            line.color = self.color
        self._set_line_values(line, value_indexer)
        self._set_line_highlighting(line, value_indexer)

    def _set_line_values(self, line, value_indexer):
        try:
            _vl = self.values[value_indexer]
        except IndexError:
            self._set_line_blank(line)
            return False
        except TypeError:
            self._set_line_blank(line)
            return False
        line.value = self.display_value(_vl)
        line.hidden = False

    def _set_line_blank(self, line):
        line.value = None
        line.show_bold = False
        line.name = None
        line.hidden = True

    def _set_line_highlighting(self, line, value_indexer):

        if value_indexer in self._filtered_values_cache:
            self.set_is_line_important(line, True)
        else:
            self.set_is_line_important(line, False)

        if (value_indexer == self.value) and \
                (self.value is not None):
            self.set_is_line_bold(line, True)
        else:
            self.set_is_line_bold(line, False)
        self.set_is_line_cursor(line, False)

        # set custom
        if self.custom_highlighting:
            if value_indexer < len(self.highlighting_arr_color_data):
                self.set_custom_highlighting(line, self.highlighting_arr_color_data[value_indexer])

    def set_is_line_important(self, line, value):
        line.important = value

    def set_is_line_bold(self, line, value):
        line.show_bold = value

    def set_is_line_cursor(self, line, value):
        line.highlight = value

    def set_custom_highlighting(self, line, color_data):

        line.syntax_highlighting = True
        line._highlightingdata = color_data

    def get_filtered_indexes(self, force_remake_cache=False):
        if not force_remake_cache:
            try:
                if self._last_filter == self._filter and self._last_values == self.values:
                    return self._filtered_values_cache
            except ReferenceError:
                # Can happen if self.values was a list of weak references
                pass

        self._last_filter = self._filter
        self._last_values = copy.copy(self.values)
        if self._filter == None or self._filter == '':
            return []
        list_of_indexes = []
        for indexer in range(len(self.values)):
            if self.filter_value(indexer):
                list_of_indexes.append(indexer)
        return list_of_indexes

    def get_filtered_values(self):
        fvls = []
        for vli in self.get_filtered_indexes():
            fvls.append(self.values[vli])
        return fvls

    def _remake_filter_cache(self):
        self._filtered_values_cache = self.get_filtered_indexes(force_remake_cache=True)

    def filter_value(self, index):
        if self._filter in self.display_value(self.values[index]):
            return True
        else:
            return False

    def jump_to_first_filtered(self, ):
        self.h_cursor_beginning(None)
        self.move_next_filtered(include_this_line=True)

    def clear_filter(self):
        self._filter = None
        self.cursor_line = 0
        self.start_display_at = 0

    def move_next_filtered(self, include_this_line=False, *args):
        if self._filter == None:
            return False
        for possible in self._filtered_values_cache:
            if (possible == self.cursor_line and include_this_line == True):
                self.update()
                break
            elif possible > self.cursor_line:
                self.cursor_line = possible
                self.update()
                break
        try:
            if self.cursor_line - self.start_display_at > len(self._my_widgets) or \
                    self._my_widgets[self.cursor_line - self.start_display_at].task == MORE_LABEL:
                if self.slow_scroll:
                    self.start_display_at += 1
                else:
                    self.start_display_at = self.cursor_line
        except IndexError:
            self.cursor_line = 0
            self.start_display_at = 0

    def move_previous_filtered(self, *args):
        if self._filter == None:
            return False
        nextline = self.cursor_line
        _filtered_values_cache_reversed = copy.copy(self._filtered_values_cache)
        _filtered_values_cache_reversed.reverse()
        for possible in _filtered_values_cache_reversed:
            if possible < self.cursor_line:
                self.cursor_line = possible
                return True
                break

    def get_selected_objects(self):
        if self.value == None:
            return None
        else:
            return [self.values[x] for x in self.value]

    def handle_mouse_event(self, mouse_event):
        # unfinished
        # mouse_id, x, y, z, bstate = mouse_event
        # self.cursor_line = y - self.rely - self.parent.show_aty + self.start_display_at

        mouse_id, rel_x, rel_y, z, bstate = self.interpret_mouse_event(mouse_event)
        self.cursor_line = rel_y // self._contained_widget_height + self.start_display_at

        ##if self.cursor_line > len(self.values):
        ##    self.cursor_line = len(self.values)
        self.display()

    def set_up_handlers(self):
        super(MultiLine, self).set_up_handlers()
        self.handlers.update({
            curses.KEY_UP: self.h_cursor_line_up,
            ord('k'): self.h_cursor_line_up,
            curses.KEY_LEFT: self.h_cursor_line_up,
            curses.KEY_DOWN: self.h_cursor_line_down,
            ord('j'): self.h_cursor_line_down,
            curses.KEY_RIGHT: self.h_cursor_line_down,
            curses.KEY_NPAGE: self.h_cursor_page_down,
            curses.KEY_PPAGE: self.h_cursor_page_up,
            curses.ascii.TAB: self.h_exit_down,
            curses.ascii.NL: self.h_select_exit,
            curses.KEY_HOME: self.h_cursor_beginning,
            curses.KEY_END: self.h_cursor_end,
            ord('g'): self.h_cursor_beginning,
            ord('G'): self.h_cursor_end,
            ord('x'): self.h_select,
            # "^L":        self.h_set_filtered_to_selected,
            curses.ascii.SP: self.h_select,
            curses.ascii.ESC: self.h_exit_escape,
            curses.ascii.CR: self.h_select_exit,
        })

        if self.allow_filtering:
            self.handlers.update({
                ord('l'): self.h_set_filter,
                ord('L'): self.h_clear_filter,
                ord('n'): self.move_next_filtered,
                ord('N'): self.move_previous_filtered,
                ord('p'): self.move_previous_filtered,
                # "^L":        self.h_set_filtered_to_selected,

            })

        if self.exit_left:
            self.handlers.update({
                curses.KEY_LEFT: self.h_exit_left
            })

        if self.exit_right:
            self.handlers.update({
                curses.KEY_RIGHT: self.h_exit_right
            })

        self.complex_handlers = [
            # (self.t_input_isprint, self.h_find_char)
        ]

    def h_find_char(self, input):
        # The following ought to work, but there is a curses keyname bug
        # searchingfor = curses.keyname(input).upper()
        # do this instead:
        searchingfor = chr(input).upper()
        for counter in range(len(self.values)):
            try:
                if self.values[counter].find(searchingfor) is not -1:
                    self.cursor_line = counter
                    break
            except AttributeError:
                break

    def t_input_isprint(self, input):
        if curses.ascii.isprint(input):
            return True
        else:
            return False

    def h_set_filter(self, ch):
        if not self.allow_filtering:
            return None
        P = FilterPopupHelper()
        P.owner_widget = weakref.proxy(self)
        P.display()
        P.filterbox.edit()
        self._remake_filter_cache()
        self.jump_to_first_filtered()

    def h_clear_filter(self, ch):
        self.clear_filter()
        self.update()

    def h_cursor_beginning(self, ch):
        self.cursor_line = 0

    def h_cursor_end(self, ch):
        self.cursor_line = len(self.values) - 1
        if self.cursor_line < 0:
            self.cursor_line = 0

    def h_cursor_page_down(self, ch):
        self.cursor_line += (len(self._my_widgets) - 1)  # -1 because of the -more-
        if self.cursor_line >= len(self.values) - 1:
            self.cursor_line = len(self.values) - 1
        if not (self.start_display_at + len(self._my_widgets) - 1) > len(self.values):
            self.start_display_at += (len(self._my_widgets) - 1)
            if self.start_display_at > len(self.values) - (len(self._my_widgets) - 1):
                self.start_display_at = len(self.values) - (len(self._my_widgets) - 1)

    def h_cursor_page_up(self, ch):
        self.cursor_line -= (len(self._my_widgets) - 1)
        if self.cursor_line < 0:
            self.cursor_line = 0
        self.start_display_at -= (len(self._my_widgets) - 1)
        if self.start_display_at < 0: self.start_display_at = 0

    def h_cursor_line_up(self, ch):
        self.cursor_line -= 1
        if self.cursor_line < 0:
            if self.scroll_exit:
                self.cursor_line = 0
                self.h_exit_up(ch)
            else:
                self.cursor_line = 0

    def h_cursor_line_down(self, ch):
        self.cursor_line += 1
        if self.cursor_line >= len(self.values):
            if self.scroll_exit:
                self.cursor_line = len(self.values) - 1
                self.h_exit_down(ch)
                return True
            else:
                self.cursor_line -= 1
                return True

        if self._my_widgets[self.cursor_line - self.start_display_at].task == MORE_LABEL:
            if self.slow_scroll:
                self.start_display_at += 1
            else:
                self.start_display_at = self.cursor_line

    def h_exit(self, ch):
        self.editing = False
        self.how_exited = True

    def h_set_filtered_to_selected(self, ch):
        # This is broken on multiline
        if len(self._filtered_values_cache) < 2:
            self.value = self._filtered_values_cache
        else:
            # There is an error - trying to select too many things.
            curses.beep()

    def h_select(self, ch):
        self.value = self.cursor_line
        if self.select_exit:
            self.editing = False
            self.how_exited = True

    def h_select_exit(self, ch):
        self.h_select(ch)
        if self.return_exit or self.select_exit:
            self.editing = False
            self.how_exited = True

    def edit(self):
        self.editing = True
        self.how_exited = None
        # if self.value: self.cursor_line = self.value
        self.display()
        while self.editing:
            self.get_and_use_key_press()
            self.update(clear=None)
            ##          self.clear()
            ##          self.update(clear=False)
            self.parent.refresh()


##          curses.napms(10)
##          curses.flushinp()

class MultiLineAction(MultiLine):
    RAISE_ERROR_IF_EMPTY_ACTION = False

    def __init__(self, *args, **keywords):
        self.allow_multi_action = False
        super(MultiLineAction, self).__init__(*args, **keywords)

    def actionHighlighted(self, act_on_this, key_press):
        "Override this Method"
        pass

    def h_act_on_highlighted(self, ch):
        try:
            return self.actionHighlighted(self.values[self.cursor_line], ch)
        except IndexError:
            if self.RAISE_ERROR_IF_EMPTY_ACTION:
                raise
            else:
                pass

    def set_up_handlers(self):
        super(MultiLineAction, self).set_up_handlers()
        self.handlers.update({
            curses.ascii.NL: self.h_act_on_highlighted,
            curses.ascii.CR: self.h_act_on_highlighted,
            ord('x'): self.h_act_on_highlighted,
            curses.ascii.SP: self.h_act_on_highlighted,
        })


class MultiLineActionWithShortcuts(MultiLineAction):
    shortcut_attribute_name = 'shortcut'

    def set_up_handlers(self):
        super(MultiLineActionWithShortcuts, self).set_up_handlers()
        self.add_complex_handlers(((self.h_find_shortcut_action, self.h_execute_shortcut_action),))

    def h_find_shortcut_action(self, _input):
        _input_decoded = curses.ascii.unctrl(_input)
        for r in range(len(self.values)):
            if hasattr(self.values[r], self.shortcut_attribute_name):
                from . import utilNotify
                if getattr(self.values[r], self.shortcut_attribute_name) == _input \
                        or getattr(self.values[r], self.shortcut_attribute_name) == _input_decoded:
                    return r
        return False

    def h_execute_shortcut_action(self, _input):
        l = self.h_find_shortcut_action(_input)
        if l is False:
            return None
        self.cursor_line = l
        self.display()
        self.h_act_on_highlighted(_input)


class Pager(MultiLine):
    def __init__(self, screen, autowrap=False, center=False, **keywords):
        super(Pager, self).__init__(screen, **keywords)
        self.autowrap = autowrap
        self.center = center
        self._values_cache_for_wrapping = []

    def reset_display_cache(self):
        super(Pager, self).reset_display_cache()
        self._values_cache_for_wrapping = False

    def _wrap_message_lines(self, message_lines, line_length):
        lines = []
        for line in message_lines:
            if line.rstrip() == '':
                lines.append('')
            else:
                this_line_set = textwrap.wrap(line.rstrip(), line_length)
                if this_line_set:
                    lines.extend(this_line_set)
                else:
                    lines.append('')
        return lines

    def resize(self):
        super(Pager, self).resize()
        # self.values = [str(self.width), str(self._my_widgets[0].width),]
        if self.autowrap:
            self.setValuesWrap(list(self.values))
        if self.center:
            self.centerValues()

    def setValuesWrap(self, lines):
        if self.autowrap and (lines == self._values_cache_for_wrapping):
            return False
        try:
            lines = lines.split('\n')
        except AttributeError:
            pass
        self.values = self._wrap_message_lines(lines, self.width - 1)
        self._values_cache_for_wrapping = self.values

    def centerValues(self):
        self.values = [l.strip().center(self.width - 1) for l in self.values]

    def update(self, clear=True):
        # we look this up a lot. Let's have it here.
        if self.autowrap:
            self.setValuesWrap(list(self.values))

        if self.center:
            self.centerValues()

        display_length = len(self._my_widgets)
        values_len = len(self.values)

        if self.start_display_at > values_len - display_length:
            self.start_display_at = values_len - display_length
        if self.start_display_at < 0: self.start_display_at = 0

        indexer = 0 + self.start_display_at
        for line in self._my_widgets[:-1]:
            self._print_line(line, indexer)
            indexer += 1

        # Now do the final line
        line = self._my_widgets[-1]

        if values_len <= indexer + 1:
            self._print_line(line, indexer)
        else:
            line.value = MORE_LABEL
            line.highlight = False
            line.show_bold = False

        for w in self._my_widgets:
            # call update to avoid needless refreshes
            w.update(clear=True)
        # There is a bug somewhere that affects the first line.  This cures it.
        # Without this line, the first line inherits the color of the form when not editing. Not clear why.
        self._my_widgets[0].update()

    def edit(self):
        # Make sure a value never gets set.
        value = self.value
        super(Pager, self).edit()
        self.value = value

    def h_scroll_line_up(self, input):
        self.start_display_at -= 1
        if self.scroll_exit and self.start_display_at < 0:
            self.editing = False
            self.how_exited = widget.EXITED_UP

    def h_scroll_line_down(self, input):
        self.start_display_at += 1
        if self.scroll_exit and self.start_display_at >= len(self.values) - self.start_display_at + 1:
            self.editing = False
            self.how_exited = widget.EXITED_DOWN

    def h_scroll_page_down(self, input):
        self.start_display_at += len(self._my_widgets)

    def h_scroll_page_up(self, input):
        self.start_display_at -= len(self._my_widgets)

    def h_show_beginning(self, input):
        self.start_display_at = 0

    def h_show_end(self, input):
        self.start_display_at = len(self.values) - len(self._my_widgets)

    def h_select_exit(self, input):
        self.exit(self, input)

    def set_up_handlers(self):
        super(Pager, self).set_up_handlers()
        self.handlers = {
            curses.KEY_UP: self.h_scroll_line_up,
            curses.KEY_LEFT: self.h_scroll_line_up,
            curses.KEY_DOWN: self.h_scroll_line_down,
            curses.KEY_RIGHT: self.h_scroll_line_down,
            curses.KEY_NPAGE: self.h_scroll_page_down,
            curses.KEY_PPAGE: self.h_scroll_page_up,
            curses.KEY_HOME: self.h_show_beginning,
            curses.KEY_END: self.h_show_end,
            curses.ascii.NL: self.h_exit,
            curses.ascii.CR: self.h_exit,
            curses.ascii.SP: self.h_scroll_page_down,
            curses.ascii.TAB: self.h_exit,
            ord('j'): self.h_scroll_line_down,
            ord('k'): self.h_scroll_line_up,
            ord('x'): self.h_exit,
            ord('q'): self.h_exit,
            ord('g'): self.h_show_beginning,
            ord('G'): self.h_show_end,
            curses.ascii.ESC: self.h_exit_escape,
        }

        self.complex_handlers = [
        ]


class TitleMultiLine(titlefield.TitleText):
    _entry_type = MultiLine

    def get_selected_objects(self):
        return self.entry_widget.get_selected_objects()

    def get_values(self):
        if hasattr(self, 'entry_widget'):
            return self.entry_widget.values
        elif hasattr(self, '__tmp_value'):
            return self.__tmp_values
        else:
            return None

    def set_values(self, value):
        if hasattr(self, 'entry_widget'):
            self.entry_widget.values = value
        elif hasattr(self, '__tmp_value'):
            # probably trying to set the value before the textarea is initialised
            self.__tmp_values = value

    def del_values(self):
        del self.entry_widget.value

    values = property(get_values, set_values, del_values)


class TitlePager(TitleMultiLine):
    _entry_type = Pager


class BufferPager(Pager):
    DEFAULT_MAXLEN = None

    def __init__(self, screen, maxlen=False, *args, **keywords):
        super(BufferPager, self).__init__(screen, *args, **keywords)
        if maxlen is False:
            maxlen = self.DEFAULT_MAXLEN
        self.values = collections.deque(maxlen=maxlen)

    def clearBuffer(self):
        self.values.clear()

    def setValuesWrap(self, lines):
        if self.autowrap and (lines == self._values_cache_for_wrapping):
            return False
        try:
            lines = lines.split('\n')
        except AttributeError:
            pass

        self.clearBuffer()
        self.buffer(self._wrap_message_lines(lines, self.width - 1))
        self._values_cache_for_wrapping = copy.deepcopy(self.values)

    def buffer(self, lines, scroll_end=True, scroll_if_editing=False):
        "Add data to be displayed in the buffer."
        self.values.extend(lines)
        if scroll_end:
            if not self.editing:
                self.start_display_at = len(self.values) - len(self._my_widgets)
            elif scroll_if_editing:
                self.start_display_at = len(self.values) - len(self._my_widgets)


class TitleBufferPager(TitleMultiLine):
    _entry_type = BufferPager

    def clearBuffer(self):
        return self.entry_widget.clearBuffer()

    def buffer(self, *args, **values):
        return self.entry_widget.buffer(*args, **values)
