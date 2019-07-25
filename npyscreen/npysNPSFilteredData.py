class NPSFilteredDataBase(object):
    def __init__(self, values=None):
        self._values  = None
        self._filter  = None
        self._filtered_values = None
        self.set_values(values)

    def set_values(self, value):
        self._values = value

    def get_all_values(self):
        return self._values

    def set_filter(self, this_filter):
        self._filter = this_filter
        self._apply_filter()

    def filter_data(self):
        # should set self._filtered_values to the filtered values
        raise Exception("You need to define the way the filter operates")
    
    def get(self):
        self._apply_filter()
        return self._filtered_values

    def _apply_filter(self):
        # Could do some caching here - but the default definition does not.
        self._filtered_values = self.filter_data()
            
class NPSFilteredDataList(NPSFilteredDataBase):
    def filter_data(self):
        if self._filter and self.get_all_values():
            return [x for x in self.get_all_values() if self._filter in x]
        else:
            return self.get_all_values()
    
    
