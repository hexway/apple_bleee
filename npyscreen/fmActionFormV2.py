import operator
import weakref
from . import wgwidget as widget
from . import wgbutton
from . import fmForm

class ActionFormV2(fmForm.FormBaseNew):
    class OK_Button(wgbutton.MiniButtonPress):
        def whenPressed(self):
            return self.parent._on_ok()
    
    class Cancel_Button(wgbutton.MiniButtonPress):
        def whenPressed(self):
            return self.parent._on_cancel()
    
    OKBUTTON_TYPE = OK_Button
    CANCELBUTTON_TYPE = Cancel_Button
    CANCEL_BUTTON_BR_OFFSET = (2, 12)
    OK_BUTTON_TEXT          = "OK"
    CANCEL_BUTTON_TEXT      = "Cancel"
    def __init__(self, *args, **keywords):
        super(ActionFormV2, self).__init__(*args, **keywords)
        self._added_buttons = {}
        self.create_control_buttons()

    
    def create_control_buttons(self):
        self._add_button('ok_button', 
                        self.__class__.OKBUTTON_TYPE, 
                        self.__class__.OK_BUTTON_TEXT,
                        0 - self.__class__.OK_BUTTON_BR_OFFSET[0],
                        0 - self.__class__.OK_BUTTON_BR_OFFSET[1] - len(self.__class__.OK_BUTTON_TEXT),
                        None
                        )
                        
        self._add_button('cancel_button', 
                        self.__class__.CANCELBUTTON_TYPE, 
                        self.__class__.CANCEL_BUTTON_TEXT,
                        0 - self.__class__.CANCEL_BUTTON_BR_OFFSET[0],
                        0 - self.__class__.CANCEL_BUTTON_BR_OFFSET[1] - len(self.__class__.CANCEL_BUTTON_TEXT),
                        None
                        )
    
    def on_cancel(self):
        pass
    
    def on_ok(self):
        pass
    
    def _on_ok(self):
        self.editing = self.on_ok()
    
    def _on_cancel(self):
        self.editing = self.on_cancel() 
    
    def set_up_exit_condition_handlers(self):
        super(ActionFormV2, self).set_up_exit_condition_handlers()
        self.how_exited_handers.update({
            widget.EXITED_ESCAPE:   self.find_cancel_button
        })

    def find_cancel_button(self):
        self.editw = len(self._widgets__)-2
    
    def _add_button(self, button_name, button_type, button_text, button_rely, button_relx, button_function):
        tmp_rely, tmp_relx = self.nextrely, self.nextrelx
        this_button = self.add_widget(
                        button_type, 
                        name=button_text, 
                        rely=button_rely,
                        relx=button_relx,
                        when_pressed_function = button_function,
                        use_max_space=True,
                        )
        self._added_buttons[button_name] = this_button
        self.nextrely, self.nextrelx = tmp_rely, tmp_relx
    
    
    def pre_edit_loop(self):
        self._widgets__.sort(key=operator.attrgetter('relx'))
        self._widgets__.sort(key=operator.attrgetter('rely'))
        if not self.preserve_selected_widget:
            self.editw = 0
        if not self._widgets__[self.editw].editable: 
            self.find_next_editable()
        
    def post_edit_loop(self):
        pass        
    
    def _during_edit_loop(self):
        pass

class ActionFormExpandedV2(ActionFormV2):
    BLANK_LINES_BASE   = 1
    OK_BUTTON_BR_OFFSET = (1,6)
    CANCEL_BUTTON_BR_OFFSET = (1, 12)

class ActionFormMinimal(ActionFormV2):
        def create_control_buttons(self):
            self._add_button('ok_button',
                        self.__class__.OKBUTTON_TYPE,
                        self.__class__.OK_BUTTON_TEXT,
                        0 - self.__class__.OK_BUTTON_BR_OFFSET[0],
                        0 - self.__class__.OK_BUTTON_BR_OFFSET[1] - len(self.__class__.OK_BUTTON_TEXT),
                        None
                        )

