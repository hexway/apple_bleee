import weakref
import textwrap
import datetime

from . import fmForm
from . import fmPopup
from . import wgtitlefield
from . import wgannotatetextbox
from . import wgmultiline
from . import wgselectone
from . import wgmultiselect
from . import wgeditmultiline
from . import wgcheckbox
from . import wgfilenamecombo
from . import wgdatecombo

class SimpleOptionForm(fmForm.Form):
    def create(self,):
        self.wOptionList = self.add(OptionListDisplay, )
    
    def beforeEditing(self, ):
        try:
            self.wOptionList.values = self.value.options
        except AttributeError:
            pass
    
    def afterEditing(self):
        if self.value.filename:
            self.value.write_to_file()
        self.parentApp.switchFormPrevious()

class OptionListDisplayLine(wgannotatetextbox.AnnotateTextboxBase):
    ANNOTATE_WIDTH = 25   
    def getAnnotationAndColor(self):
        return (self.value.get_name_user(), 'LABEL')
    
    def display_value(self, vl):
        return vl.get_for_single_line_display()
        
class OptionListDisplay(wgmultiline.MultiLineAction):
    _contained_widgets = OptionListDisplayLine
    def actionHighlighted(self, act_on_this, key_press):
        rtn = act_on_this.change_option()
        self.display()
        return rtn
    
    def display_value(self, vl):
        return vl

class OptionChanger(fmPopup.ActionPopupWide):
    def on_ok(self,):
        self.OPTION_TO_CHANGE.set_from_widget_value(self.OPTION_WIDGET.value)

class OptionList(object):
    def __init__(self, filename=None):
        self.options  = []
        self.filename = filename
        self.define_serialize_functions()
    
    def define_serialize_functions(self):
        self.SERIALIZE_FUNCTIONS = {
            OptionFreeText:         self.save_text,
            OptionSingleChoice:     self.save_text,
            OptionMultiChoice:      self.save_multi_text,
            OptionMultiFreeText:    self.save_text,
            OptionBoolean:          self.save_bool,
            OptionFilename:         self.save_text,
            OptionDate:             self.save_date,
            OptionMultiFreeList:    self.save_list,
        }
    
        self.UNSERIALIZE_FUNCTIONS = {
            OptionFreeText:         self.reload_text,
            OptionSingleChoice:     self.reload_text,
            OptionMultiChoice:      self.load_multi_text,
            OptionMultiFreeText:    self.reload_text,
            OptionBoolean:          self.load_bool,
            OptionFilename:         self.reload_text,
            OptionDate:             self.load_date,
            OptionMultiFreeList:    self.load_list,
        }
    
    def get(self, name):
        for o in self.options:
            if o.get_real_name() == name:
                return o
    
    
    
    def write_to_file(self, fn=None, exclude_defaults=True):
        fn = fn or self.filename
        if not fn:
            raise ValueError("Must specify a filename.")
        with open(fn, 'w', encoding="utf-8") as f:
            for opt in self.options:
                if opt.default != opt.get():
                    f.write('%s=%s\n' % (opt.get_real_name(), self.serialize_option_value(opt)))
    
    def reload_from_file(self, fn=None):
        fn = fn or self.filename
        with open(fn, 'r', encoding="utf-8") as f:
            for line in f.readlines():
                 line = line.strip()
                 name, value = line.split("=", maxsplit=1)
                 for option in self.options:
                     if option.get_real_name() == name:
                         option.set(self.deserialize_option_value(option, value.encode('ascii')))
    
    def serialize_option_value(self, option):
        return self.SERIALIZE_FUNCTIONS[option.__class__](option)
    
    def deserialize_option_value(self, option, serialized):
        return self.UNSERIALIZE_FUNCTIONS[option.__class__](serialized)
    
    def _encode_text_for_saving(self, txt):
        return txt.encode('unicode-escape').decode('ascii')
    
    def _decode_text_from_saved(self, txt):
        return txt.decode('unicode-escape')
        
    def save_text(self, option):
        s = option.get()
        if not s:
            s = ''
        return self._encode_text_for_saving(s)
    
    def reload_text(self, txt):
        return self._decode_text_from_saved(txt)
    
    def save_bool(self, option):
        if option.get():
            return 'True'
        else:
            return 'False'
            
    def load_bool(self, txt):
        txt = txt.decode()
        if txt in ('True', ):
            return True
        elif txt in ('False', ):
            return False
        else:
            raise ValueError("Could not decode %s" % txt)
    
    def save_multi_text(self, option):
        line = []
        opt = option.get()
        if not opt:
            return ''
        for text_part in opt:
            line.append(text_part.encode('unicode-escape').decode('ascii'))
        return "\t".join(line)
    
    def load_multi_text(self, text):
        parts = text.decode('ascii').split("\t")
        rtn = []
        for p in parts:
            rtn.append(p.encode('ascii').decode('unicode-escape'))
        return rtn
        
    def save_list(self, lst):
        pts_to_save = []
        for p in lst.get():
            pts_to_save.append(self._encode_text_for_saving(p))
        return "\t".join(pts_to_save)
    
    def load_list(self, text):
        parts = text.decode('ascii').split("\t")
        parts_to_return = []
        for p in parts:
            parts_to_return.append(self._decode_text_from_saved(p.encode('ascii')))
        return parts_to_return
    
    def save_date(self, option):
        if option.get():
            return option.get().ctime()
        else:
            return None
    
    def load_date(self, txt):
        if txt:
            return datetime.datetime.strptime(txt.decode(), "%a %b %d %H:%M:%S %Y")
        else:
            return None
    
    
            
class Option(object):
    DEFAULT = ''
    def __init__(self, name, 
                    value=None, 
                    documentation=None, 
                    short_explanation=None,
                    option_widget_keywords = None,
                    default = None,
                    ):
        self.name = name
        self.default = default or self.DEFAULT
        self.set(value or self.default)
        self.documentation = documentation
        self.short_explanation = short_explanation
        self.option_widget_keywords = option_widget_keywords or {}
        self.default = default or self.DEFAULT
    
    def when_set(self):
        pass
    
    def get(self,):
        return self.value
    
    def get_for_single_line_display(self):
        return repr(self.value)
    
    def set_from_widget_value(self, vl):
        self.set(vl)
    
    def set(self, value):
        self.value = value
        self.when_set()
    
    def get_real_name(self):
        # This might be for internal use
        return self.name
    
    def get_name_user(self):
        # You could do translation here.
        return self.name
    
    def _set_up_widget_values(self, option_form, main_option_widget):
        main_option_widget.value = self.value
    
    def change_option(self):
        option_changing_form = OptionChanger()
        option_changing_form.OPTION_TO_CHANGE = weakref.proxy(self)
        if self.documentation:
            explanation_widget = option_changing_form.add(wgmultiline.Pager, 
                                                        editable=False, value=None,
                                                        max_height=(option_changing_form.lines - 3) // 2,
                                                        autowrap=True,
                                                        )
            option_changing_form.nextrely += 1
            explanation_widget.values = self.documentation
            
        
        option_widget = option_changing_form.add(self.WIDGET_TO_USE, 
                                                    name=self.get_name_user(),
                                                    **self.option_widget_keywords 
                                                )
        option_changing_form.OPTION_WIDGET = option_widget
        self._set_up_widget_values(option_changing_form, option_widget)        
        option_changing_form.edit()
    

class OptionLimitedChoices(Option):
    def __init__(self, name, choices=None, *args, **keywords):
        super(OptionLimitedChoices, self).__init__(name, *args, **keywords)
        choices = choices or []
        self.setChoices(choices)
    
    def setChoices(self, choices):
        self.choices = choices
    
    def getChoices(self,):
        return self.choices
    
    def _set_up_widget_values(self, option_form, main_option_widget):
        main_option_widget.value  = []
        main_option_widget.values = self.getChoices()
        for x in range(len(main_option_widget.values)):
            if self.value and main_option_widget.values[x] in self.value:
                main_option_widget.value.append(x)
    
    def set_from_widget_value(self, vl):
        value = []
        for v in vl:
            value.append(self.choices[v])
        self.set(value)
        
class OptionFreeText(Option):
    WIDGET_TO_USE = wgtitlefield.TitleText

class OptionSingleChoice(OptionLimitedChoices):
    WIDGET_TO_USE = wgselectone.TitleSelectOne

class OptionMultiChoice(OptionLimitedChoices):
    DEFAULT = []
    WIDGET_TO_USE = wgmultiselect.TitleMultiSelect

class OptionMultiFreeText(Option):
    WIDGET_TO_USE = wgeditmultiline.MultiLineEdit

class OptionMultiFreeList(Option):
    WIDGET_TO_USE = wgeditmultiline.MultiLineEdit
    DEFAULT = []
    def _set_up_widget_values(self, option_form, main_option_widget):
        main_option_widget.value = "\n".join(self.get())
    
    def set_from_widget_value(self, vl):
        self.set(vl.split("\n"))

class OptionBoolean(Option):
    WIDGET_TO_USE = wgcheckbox.Checkbox

class OptionFilename(Option):
    DEFAULT = ''
    WIDGET_TO_USE = wgfilenamecombo.FilenameCombo
    
class OptionDate(Option):
    DEFAULT = None
    WIDGET_TO_USE = wgdatecombo.DateCombo