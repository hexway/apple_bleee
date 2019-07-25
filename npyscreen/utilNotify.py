from . import fmPopup
from . import wgmultiline
from . import fmPopup
import curses
import textwrap

class ConfirmCancelPopup(fmPopup.ActionPopup):
    def on_ok(self):
        self.value = True
    def on_cancel(self):
        self.value = False

class YesNoPopup(ConfirmCancelPopup):
    OK_BUTTON_TEXT = "Yes"
    CANCEL_BUTTON_TEXT = "No"
    
def _prepare_message(message):
    if isinstance(message, list) or isinstance(message, tuple):
        return "\n".join([ s.rstrip() for s in message])
        #return "\n".join(message)
    else:
        return message

def _wrap_message_lines(message, line_length):
    lines = []
    for line in message.split('\n'):
        lines.extend(textwrap.wrap(line.rstrip(), line_length))
    return lines
    
def notify(message, title="Message", form_color='STANDOUT', 
            wrap=True, wide=False,
            ):
    message = _prepare_message(message)
    if wide:
        F = fmPopup.PopupWide(name=title, color=form_color)
    else:
        F   = fmPopup.Popup(name=title, color=form_color)
    F.preserve_selected_widget = True
    mlw = F.add(wgmultiline.Pager,)
    mlw_width = mlw.width-1
    if wrap:
        message = _wrap_message_lines(message, mlw_width)
    mlw.values = message
    F.display()
    
def notify_confirm(message, title="Message", form_color='STANDOUT', wrap=True, wide=False,
                    editw = 0,):
    message = _prepare_message(message)
    if wide:
        F = fmPopup.PopupWide(name=title, color=form_color)
    else:
        F   = fmPopup.Popup(name=title, color=form_color)
    F.preserve_selected_widget = True
    mlw = F.add(wgmultiline.Pager,)
    mlw_width = mlw.width-1
    if wrap:
        message = _wrap_message_lines(message, mlw_width)
    else:
        message = message.split("\n")
    mlw.values = message
    F.editw = editw
    F.edit()

def notify_wait(*args, **keywords):
    notify(*args, **keywords)
    curses.napms(3000)
    curses.flushinp()    
    
    
def notify_ok_cancel(message, title="Message", form_color='STANDOUT', wrap=True, editw = 0,):
    message = _prepare_message(message)
    F   = ConfirmCancelPopup(name=title, color=form_color)
    F.preserve_selected_widget = True
    mlw = F.add(wgmultiline.Pager,)
    mlw_width = mlw.width-1
    if wrap:
        message = _wrap_message_lines(message, mlw_width)
    mlw.values = message
    F.editw = editw
    F.edit()
    return F.value

def notify_yes_no(message, title="Message", form_color='STANDOUT', wrap=True, editw = 0,):
    message = _prepare_message(message)
    F   = YesNoPopup(name=title, color=form_color)
    F.preserve_selected_widget = True
    mlw = F.add(wgmultiline.Pager,)
    mlw_width = mlw.width-1
    if wrap:
        message = _wrap_message_lines(message, mlw_width)
    mlw.values = message
    F.editw = editw
    F.edit()
    return F.value

    