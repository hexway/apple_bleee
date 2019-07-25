import weakref

class Event(object):
    # a basic event class
    def __init__(self, name, payload=None):
        self.name = name
        self.payload = payload


class EventHandler(object):
    # This partial base class provides the framework to handle events.
    
    def initialize_event_handling(self):
        self.event_handlers = {}
        
    def add_event_hander(self, event_name, handler):
        if not event_name in self.event_handlers:
            self.event_handlers[event_name] = set() # weakref.WeakSet() #Why doesn't the WeakSet work?
        self.event_handlers[event_name].add(handler)
        
        parent_app = self.find_parent_app()
        if parent_app:
            parent_app.register_for_event(self, event_name)
        else:
            # Probably are the parent App!
            # but could be a form outside a proper application environment
            try:
                self.register_for_event(self, event_name)
            except AttributeError:
                pass
                
    def remove_event_handler(self, event_name, handler):
        if event_name in self.event_handlers:
            self.event_handlers[event_name].remove(handler)
        if not self.event_handlers[event_name]:
            self.event_handlers.pop({})
            
    
    def handle_event(self, event):
        "return True if the event was handled.  Return False if the application should stop sending this event."
        if event.name not in self.event_handlers:
            return False
        else:
            remove_list = []
            for handler in self.event_handlers[event.name]:
                try:
                    handler(event)
                except weakref.ReferenceError:
                    remove_list.append(handler)
            for dead_handler in remove_list:
                self.event_handlers[event.name].remove(handler)
            return True
    
    def find_parent_app(self):
        if hasattr(self, "parentApp"):
            return self.parentApp
        elif hasattr(self, "parent") and hasattr(self.parent, "parentApp"):
            return self.parent.parentApp
        else:
            return None
            
