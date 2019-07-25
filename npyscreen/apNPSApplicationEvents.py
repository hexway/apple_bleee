import collections
import weakref
from .apNPSApplicationManaged import NPSAppManaged
from .eveventhandler import EventHandler

class NPSEventQueue(object):
    def __init__(self):
        self.interal_queue = collections.deque()
    
    def get(self, maximum=None):
        if maximum is None:
            maximum = -1
        counter = 1
        while counter != maximum:
            try:
                yield self.interal_queue.pop()
            except IndexError:
                pass
                #raise StopIteration
            counter += 1
    
    def put(self, event):
        self.interal_queue.append(event)
        
class StandardApp(NPSAppManaged, EventHandler):
    MAINQUEUE_TYPE = NPSEventQueue
    keypress_timeout_default = 2
    max_events_per_queue = 50
    """This class adds event queue functionality to the existing NPSAppManaged.  The name reflects the fact that future applications
    are expected to use this class as standard.  However, it is currently an experimental class.  The API is unlikely to change, but
    no promises are made at this time.
    """
    def __init__(self):
        super(StandardApp, self).__init__()
        self.event_directory = {}
        self.event_queues = {}
        self.initalize_application_event_queues()
        self.initialize_event_handling()
    
    def _internal_while_waiting(self):
        # Parent NPSAppManaged does not define this, so no need to call.
        self.process_event_queues(max_events_per_queue=self.max_events_per_queue)
    
        
    def initalize_application_event_queues(self):
        # in the standard application the event queue is not threaded so...
        main_queue = self.MAINQUEUE_TYPE()
        self.event_queues['MAINQUEUE'] = main_queue
    
    def process_event_queues(self, max_events_per_queue=None):
        for queue in self.event_queues.values():
            for event in queue.get(maximum=max_events_per_queue):
                try:
                    self.process_event(event)
                except:
                    pass
    
    def register_for_event(self, registering_object, event_name):
        if event_name not in self.event_directory:
            self.event_directory[event_name] = weakref.WeakSet()
        self.event_directory[event_name].add(registering_object)
        
    def queue_event(self, event, queue='MAINQUEUE'):
        self.event_queues[queue].put(event)
        
    def process_event(self, event):
        discard_list = []
        if event.name not in self.event_directory:
            return True
        if not self.event_directory[event.name]:
            del self.event_directory[event.name]
            return True
        for registered_object in self.event_directory[event.name]:
            result = registered_object.handle_event(event)
            if result is False:
                discard_list.append(registered_object)
                
        for registered_object in discard_list:
            self.event_directory[event.name].discard(registered_object)