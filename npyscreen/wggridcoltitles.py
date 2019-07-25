#!/usr/bin/env python
# encoding: utf-8
import curses
from . import wggrid    as grid
from . import wgtextbox as textbox

class GridColTitles(grid.SimpleGrid):
    additional_y_offset   = 2
    _col_widgets = textbox.Textfield
    def __init__(self, screen, col_titles = None, *args, **keywords):
        if col_titles:
            self.col_titles = col_titles
        else:
            self.col_titles = []
        super(GridColTitles, self).__init__(screen, *args, **keywords)
    
    def make_contained_widgets(self):
        super(GridColTitles, self).make_contained_widgets()
        self._my_col_titles = []
        for title_cell in range(self.columns):
            x_offset = title_cell * (self._column_width+self.col_margin)
            self._my_col_titles.append(self._col_widgets(self.parent, rely=self.rely, relx = self.relx + x_offset, width=self._column_width, height=1))
            
            
    def update(self, clear=True):
        super(GridColTitles, self).update(clear = True)
        
        _title_counter = 0
        for title_cell in self._my_col_titles:
            try:
                title_text = self.col_titles[self.begin_col_display_at+_title_counter]
            except IndexError:
                title_text = None
            self.update_title_cell(title_cell, title_text)
            _title_counter += 1
            
        self.parent.curses_pad.hline(self.rely+1, self.relx, curses.ACS_HLINE, self.width)
    
    def update_title_cell(self, cell, cell_title):
        cell.value = cell_title
        cell.update()
        
