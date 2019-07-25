#!/usr/bin/env python
# encoding: utf-8
import curses
from . import wgwidget   as widget
from . import wgtextbox  as textbox


class SimpleGrid(widget.Widget):
    _contained_widgets    = textbox.Textfield
    default_column_number = 4
    additional_y_offset   = 0
    additional_x_offset   = 0
    def __init__(self, screen, columns = None, 
            column_width = None, col_margin=1, row_height = 1, 
            values = None,
            always_show_cursor = False,
            select_whole_line = False,
            on_select_callback = None,
            **keywords):
        super(SimpleGrid, self).__init__(screen, **keywords)
        self.col_margin = col_margin
        self.always_show_cursor = always_show_cursor
        self.columns_requested = columns
        self.column_width_requested = column_width
        self.row_height = row_height
        self.make_contained_widgets()
        
        self.begin_row_display_at = 0
        self.begin_col_display_at = 0
        self.on_empty_display = ''
        self.select_whole_line = select_whole_line
        
        self.edit_cell = None
        
        if not values:
            self.values = None
        else:
            self.values = values

        self.on_select_callback = on_select_callback
            
    def set_grid_values_from_flat_list(self, new_values, max_cols=None, reset_cursor=True):
        if not max_cols:
            max_cols = self.columns
        grid_values = [ [], ]
        col_number        = 0
        row_number        = 0
        for f in new_values:
            if col_number >= max_cols:
                col_number = 0
                grid_values.append([])
                row_number += 1
            grid_values[row_number].append(f)    
            col_number += 1
        self.values = grid_values
        if reset_cursor:
            self.edit_cell = [0,0]
        
    def resize(self):
        self.make_contained_widgets()

    def make_contained_widgets(self):
        if self.column_width_requested:
            # don't need a margin for the final column
            self.columns = (self.width + self.col_margin) // (self.column_width_requested + self.col_margin)
        elif self.columns_requested:
            self.columns = self.columns_requested
        else:
            self.columns = self.default_column_number
        self._my_widgets = []
        column_width = (self.width + self.col_margin - self.additional_x_offset) // self.columns
        column_width -= self.col_margin
        self._column_width = column_width
        if column_width < 1: raise Exception("Too many columns for space available")
        for h in range( (self.height - self.additional_y_offset) // self.row_height ):
            h_coord = h * self.row_height
            row = []
            for cell in range(self.columns):
                x_offset = cell * (self._column_width + self.col_margin)
                row.append(self._contained_widgets(self.parent, rely=h_coord+self.rely + self.additional_y_offset, relx = self.relx + x_offset + self.additional_x_offset, width=column_width, height=self.row_height))
            self._my_widgets.append(row)
    
    def display_value(self, vl):
        """Overload this function to change how values are displayed.  
Should accept one argument (the object to be represented), and return a string."""
        return str(vl)
    
        
    def calculate_area_needed(self):
        return 0,0

    def update(self, clear=True):
        if clear == True:
            self.clear()
        if self.begin_col_display_at < 0:
            self.begin_col_display_at = 0
        if self.begin_row_display_at < 0:
            self.begin_row_display_at = 0
        if (self.editing or self.always_show_cursor) and not self.edit_cell:
            self.edit_cell = [0,0]
        row_indexer = self.begin_row_display_at
        for widget_row in self._my_widgets:
            column_indexer = self.begin_col_display_at
            for cell in widget_row:
                cell.grid_current_value_index = (row_indexer, column_indexer)
                self._print_cell(cell, )
                column_indexer += 1
            row_indexer += 1
    
    def _print_cell(self, cell,):
        row_indexer, column_indexer = cell.grid_current_value_index
        try:
            cell_value = self.display_value(self.values[row_indexer][column_indexer])
        except IndexError:
            cell_value = self.on_empty_display
            cell.grid_current_value_index = -1
        except TypeError:
            cell_value = self.on_empty_display
            cell.grid_current_value_index = -1
            
        cell.grid_current_value_index
        self._cell_widget_show_value(cell, cell_value)        
        
        if self.value:
            if cell.grid_current_value_index in self.value or cell.grid_current_value_index == self.value:
                self._cell_widget_show_value_selected(cell, True)
            else:
                self._cell_widget_show_value_selected(cell, False)
        else:
            self._cell_widget_show_value_selected(cell, False)
        
        if (self.editing or self.always_show_cursor) and cell.grid_current_value_index != -1:
            if self.select_whole_line:
                if (self.edit_cell[0] == cell.grid_current_value_index[0]):
                    self._cell_show_cursor(cell, True)
                    cell.highlight_whole_widget = True
                else:
                    self._cell_show_cursor(cell, False)
            elif ((self.edit_cell[0] == cell.grid_current_value_index[0]) and (self.edit_cell[1] == cell.grid_current_value_index[1])):
                self._cell_show_cursor(cell, True)
            else:
                self._cell_show_cursor(cell, False)
        else:
            self._cell_show_cursor(cell, False)
            
        self.custom_print_cell(cell, cell_value)
        
        cell.update() # <-------------------- WILL NEED TO OPTIMIZE THIS
        
    def custom_print_cell(self, actual_cell, cell_display_value):
        pass
        
        
        
    def _cell_widget_show_value(self, cell, value):
        cell.value = value
    
    def _cell_widget_show_value_selected(self, cell, yes_no):
        cell.show_bold = yes_no
    
    def _cell_show_cursor(self, cell, yes_no):
        cell.highlight = yes_no
        
    def handle_mouse_event(self, mouse_event):
        # unfinished
        for row in self._my_widgets:
            for c in row:
                if c.intersted_in_mouse_event(mouse_event):
                    if c.grid_current_value_index != -1:
                        self.edit_cell = list(c.grid_current_value_index)
        self.display()

        
    def set_up_handlers(self):
        super(SimpleGrid, self).set_up_handlers()
        self.handlers = {
                    curses.KEY_UP:      self.h_move_line_up,
                    curses.KEY_LEFT:    self.h_move_cell_left,
                    curses.KEY_DOWN:    self.h_move_line_down,
                    curses.KEY_RIGHT:   self.h_move_cell_right,
                    "k":                self.h_move_line_up,
                    "h":                self.h_move_cell_left,
                    "j":                self.h_move_line_down,
                    "l":                self.h_move_cell_right,
                    curses.KEY_NPAGE:   self.h_move_page_down,
                    curses.KEY_PPAGE:   self.h_move_page_up,
                    curses.KEY_HOME:    self.h_show_beginning,
                    curses.KEY_END:     self.h_show_end,
                    ord('g'):           self.h_show_beginning,
                    ord('G'):           self.h_show_end,
                    curses.ascii.TAB:   self.h_exit,
                    curses.KEY_BTAB:     self.h_exit_up,
                    '^P':               self.h_exit_up,
                    '^N':               self.h_exit_down,
                    #curses.ascii.NL:    self.h_exit,
                    #curses.ascii.SP:    self.h_exit,
                    #ord('x'):       self.h_exit,
                    ord('q'):       self.h_exit,
                    curses.ascii.ESC:   self.h_exit,
                    curses.KEY_MOUSE:    self.h_exit_mouse,
                }

        self.complex_handlers = [
                    ]
    
    def getValuesFlatList(self):
        output_list = []
        for row in self.values:
            for col in row:
                output_list.append(col)
        return output_list
    
    
    def ensure_cursor_on_display_down_right(self, inpt=None):
        while self.begin_row_display_at  + len(self._my_widgets) - 1 < self.edit_cell[0]:
            self.h_scroll_display_down(inpt)
        while self.edit_cell[1] > self.begin_col_display_at + self.columns - 1:
            self.h_scroll_right(inpt)
    
    def ensure_cursor_on_display_up(self, inpt=None):
        while self.begin_row_display_at  >  self.edit_cell[0]:
            self.h_scroll_display_up(inpt)
        
    def h_show_beginning(self, inpt):
        self.begin_col_display_at = 0
        self.begin_row_display_at = 0
        self.edit_cell = [0, 0]
        self.on_select(inpt)
    
    def h_show_end(self, inpt):
        self.edit_cell = [len(self.values) - 1 , len(self.values[-1]) - 1]
        self.ensure_cursor_on_display_down_right()
        self.on_select(inpt)
        
    def h_move_cell_left(self, inpt):
        if self.edit_cell[1] > 0:
            self.edit_cell[1] -= 1
        
        if self.edit_cell[1] < self.begin_col_display_at:
            self.h_scroll_left(inpt)
        self.on_select(inpt)
    
    def h_move_cell_right(self, inpt):
        if self.edit_cell[1] <= len(self.values[self.edit_cell[0]]) -2:   # Only allow move to end of current line
            self.edit_cell[1] += 1
        
        if self.edit_cell[1] > self.begin_col_display_at + self.columns - 1:
            self.h_scroll_right(inpt)
        self.on_select(inpt)
    
    def h_move_line_down(self, inpt):
        if self.edit_cell[0] <= (len(self.values) -2) \
        and (len(self.values[self.edit_cell[0]+1]) > self.edit_cell[1]):
            self.edit_cell[0] += 1
        if self.begin_row_display_at  + len(self._my_widgets) - 1 < self.edit_cell[0]:
            self.h_scroll_display_down(inpt)
        self.on_select(inpt)
    
    def h_move_line_up(self, inpt):
        if self.edit_cell[0] > 0:
            self.edit_cell[0] -= 1
            
        if self.edit_cell[0] < self.begin_row_display_at:
            self.h_scroll_display_up(inpt)
        self.on_select(inpt)
    
    def h_scroll_right(self, inpt):
        if self.begin_col_display_at + self.columns < len(self.values[self.edit_cell[0]]):
            self.begin_col_display_at += self.columns
        self.on_select(inpt)
        
    def h_scroll_left(self, inpt):
        if self.begin_col_display_at > 0:
            self.begin_col_display_at -= self.columns
        
        if self.begin_col_display_at < 0:
            self.begin_col_display_at = 0
        self.on_select(inpt)

    def h_scroll_display_down(self, inpt):
        if self.begin_row_display_at + len(self._my_widgets) < len(self.values):
            self.begin_row_display_at += len(self._my_widgets)
        self.on_select(inpt)
        
    def h_scroll_display_up(self, inpt):
        if self.begin_row_display_at > 0:
            self.begin_row_display_at -= len(self._my_widgets)
        if self.begin_row_display_at < 0:
            self.begin_row_display_at = 0
        self.on_select(inpt)
    
    def h_move_page_up(self, inpt):
        self.edit_cell[0] -= len(self._my_widgets)
        if self.edit_cell[0] < 0:
             self.edit_cell[0] = 0
        self.ensure_cursor_on_display_up()
        self.on_select(inpt)
             
    def h_move_page_down(self, inpt):
        self.edit_cell[0] += len(self._my_widgets)
        if self.edit_cell[0] > len(self.values) - 1:
             self.edit_cell[0] = len(self.values) -1
        
        self.ensure_cursor_on_display_down_right()
        self.on_select(inpt)

    def on_select(self, input):
        if self.on_select_callback:
            self.on_select_callback()

    def h_exit(self, ch):
        self.editing = False
        self.how_exited = True

    def selected_row(self):
        try:
            return self.values[self.edit_cell[0]]
        except KeyError:
            pass

    
    
    