#!/usr/bin/env python
# encoding: utf-8

from . import apNPSApplicationManaged
from . import fmForm
import weakref

class NPSAppAdvanced(apNPSApplicationManaged.NPSAppManaged):
    """EXPERIMENTAL and NOT for use.  This class of application will eventually replace the 
    standard method of user input handling and deal with everything at the application level."""
    
    def _main_loop(self):
        pass