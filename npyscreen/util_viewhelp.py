import textwrap


def view_help(message, title="Message", form_color="STANDOUT", scroll_exit=False, autowrap=False):
    from . import fmForm
    from . import wgmultiline
    F = fmForm.Form(name=title, color=form_color)
    mlw = F.add(wgmultiline.Pager, scroll_exit=True, autowrap=autowrap)
    mlw_width = mlw.width-1
    
    message_lines = []
    for line in message.splitlines():
        line = textwrap.wrap(line, mlw_width)
        if line == []:
            message_lines.append('')
        else:
            message_lines.extend(line)
    mlw.values = message_lines
    F.edit()
    del mlw
    del F
    
