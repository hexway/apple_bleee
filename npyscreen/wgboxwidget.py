import curses
import weakref
from .wgwidget import Widget
from .wgmultiline import MultiLine


class BoxBasic(Widget):
    def __init__(self, screen, footer=None, *args, **keywords):
        super(BoxBasic, self).__init__(screen, *args, **keywords)
        self.footer = footer
        if 'color' in keywords:
            self.color = keywords['color'] or 'LABEL'
        else:
            self.color = 'LABEL'

    def update(self, clear=True):
        if clear: self.clear()
        if self.hidden:
            self.clear()
            return False
        HEIGHT = self.height - 1
        WIDTH = self.width - 1
        # draw box.
        self.parent.curses_pad.hline(self.rely, self.relx, curses.ACS_HLINE, WIDTH)
        self.parent.curses_pad.hline(self.rely + HEIGHT, self.relx, curses.ACS_HLINE, WIDTH)
        self.parent.curses_pad.vline(self.rely, self.relx, curses.ACS_VLINE, self.height)
        self.parent.curses_pad.vline(self.rely, self.relx + WIDTH, curses.ACS_VLINE, HEIGHT)

        # draw corners
        self.parent.curses_pad.addch(self.rely, self.relx, curses.ACS_ULCORNER, )
        self.parent.curses_pad.addch(self.rely, self.relx + WIDTH, curses.ACS_URCORNER, )
        self.parent.curses_pad.addch(self.rely + HEIGHT, self.relx, curses.ACS_LLCORNER, )
        self.parent.curses_pad.addch(self.rely + HEIGHT, self.relx + WIDTH, curses.ACS_LRCORNER, )

        # draw title
        if self.name:
            if isinstance(self.name, bytes):
                name = self.name.decode(self.encoding, 'replace')
            else:
                name = self.name
            name = self.safe_string(name)
            name = " " + name + " "
            if isinstance(name, bytes):
                name = name.decode(self.encoding, 'replace')
            name_attributes = curses.A_NORMAL
            if self.do_colors() and not self.editing:
                name_attributes = name_attributes | self.parent.theme_manager.findPair(self,
                                                                                       self.color)  # | curses.A_BOLD
            elif self.editing:
                name_attributes = name_attributes | self.parent.theme_manager.findPair(self, 'HILIGHT')
            else:
                name_attributes = name_attributes  # | curses.A_BOLD

            if self.editing:
                name_attributes = name_attributes | curses.A_BOLD

            self.add_line(self.rely, self.relx + 4, name,
                          self.make_attributes_list(name, name_attributes),
                          self.width - 8)
            # end draw title

            # draw footer
        if hasattr(self, 'footer') and self.footer:
            footer_text = self.footer
            if isinstance(footer_text, bytes):
                footer_text = footer_text.decode(self.encoding, 'replace')
            footer_text = self.safe_string(footer_text)
            footer_text = " " + footer_text + " "
            if isinstance(footer_text, bytes):
                footer_text = footer_text.decode(self.encoding, 'replace')

            footer_attributes = self.get_footer_attributes(footer_text)
            if len(footer_text) <= self.width - 4:
                placing = self.width - 4 - len(footer_text)
            else:
                placing = 4

            self.add_line(self.rely + HEIGHT, self.relx + placing, footer_text,
                          footer_attributes,
                          self.width - placing - 2)

    def get_footer_attributes(self, footer_text):
        footer_attributes = curses.A_NORMAL
        if self.do_colors() and not self.editing:
            footer_attributes = footer_attributes | self.parent.theme_manager.findPair(self,
                                                                                       self.color)  # | curses.A_BOLD
        elif self.editing:
            footer_attributes = footer_attributes | self.parent.theme_manager.findPair(self, 'HILIGHT')
        else:
            footer_attributes = footer_attributes  # | curses.A_BOLD

        if self.editing:
            footer_attributes = footer_attributes | curses.A_BOLD
        # footer_attributes = self.parent.theme_manager.findPair(self, self.color)
        return self.make_attributes_list(footer_text, footer_attributes)


class BoxTitle(BoxBasic):
    _contained_widget = MultiLine

    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super(BoxTitle, self).__init__(screen, *args, **keywords)
        if contained_widget_arguments:
            self.make_contained_widget(contained_widget_arguments=contained_widget_arguments)
        else:
            self.make_contained_widget()
        if 'editable' in keywords:
            self.entry_widget.editable = keywords['editable']
        if 'value' in keywords:
            self.value = keywords['value']
        if 'values' in keywords:
            self.values = keywords['values']
        if 'scroll_exit' in keywords:
            self.entry_widget.scroll_exit = keywords['scroll_exit']
        if 'slow_scroll' in keywords:
            self.entry_widget.scroll_exit = keywords['slow_scroll']

        if 'always_show_cursor' in keywords:
            self.entry_widget.always_show_cursor = keywords['always_show_cursor']
        if 'cursor_line' in keywords:
            self.entry_widget.cursor_line = keywords['cursor_line']
        if 'start_display_at' in keywords:
            self.entry_widget.start_display_at = keywords['start_display_at']

        if 'custom_highlighting' in keywords:
            self.entry_widget.custom_highlighting = keywords['custom_highlighting']
        if 'highlighting_arr_color_data' in keywords:
            self.entry_widget.highlighting_arr_color_data = keywords['highlighting_arr_color_data']

    def make_contained_widget(self, contained_widget_arguments=None):
        self._my_widgets = []
        if contained_widget_arguments:
            self._my_widgets.append(self._contained_widget(self.parent,
                                                           rely=self.rely + 1, relx=self.relx + 2,
                                                           max_width=self.width - 4, max_height=self.height - 2,
                                                           **contained_widget_arguments
                                                           ))

        else:
            self._my_widgets.append(self._contained_widget(self.parent,
                                                           rely=self.rely + 1, relx=self.relx + 2,
                                                           max_width=self.width - 4, max_height=self.height - 2,
                                                           ))
        self.entry_widget = weakref.proxy(self._my_widgets[0])
        self.entry_widget.parent_widget = weakref.proxy(self)

    def update(self, clear=True):
        if self.hidden and clear:
            self.clear()
            return False
        elif self.hidden:
            return False
        super(BoxTitle, self).update(clear=clear)
        for w in self._my_widgets:
            w.update(clear=clear)

    def resize(self):
        super(BoxTitle, self).resize()
        self.entry_widget.resize()

    def edit(self):
        self.editing = True
        self.display()
        self.entry_widget.edit()
        # self.value = self.textarea.value
        self.how_exited = self.entry_widget.how_exited
        self.editing = False
        self.display()

    def get_value(self):
        if hasattr(self, 'entry_widget'):
            return self.entry_widget.value
        elif hasattr(self, '__tmp_value'):
            return self.__tmp_value
        else:
            return None

    def set_value(self, value):
        if hasattr(self, 'entry_widget'):
            self.entry_widget.value = value
        else:
            # probably trying to set the value before the textarea is initialised
            self.__tmp_value = value

    def del_value(self):
        del self.entry_widget.value

    value = property(get_value, set_value, del_value)

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

    def get_editable(self):
        if hasattr(self, 'entry_widget'):
            return self.entry_widget.editable
        else:
            return None

    def set_editable(self, value):
        if hasattr(self, 'entry_widget'):
            self.entry_widget.editable = value
        elif hasattr(self, '__tmp_value'):
            # probably trying to set the value before the textarea is initialised
            self.__tmp_values = value

    def del_editable(self):
        del self.entry_widget.editable

    editable = property(get_editable, set_editable, del_editable)
