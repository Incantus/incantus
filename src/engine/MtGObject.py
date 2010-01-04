from pydispatch import dispatcher

class MtGObject(object):
    #Universal dispatcher
    # this class is for all objects that can send and receive signals
    #_lock = False
    #_holding = False
    def send(self, event, *args, **named):
        #send event to dispatcher
        dispatcher.send(event, self, *args, **named)
        #if not MtGObject._lock: dispatcher.send(event, self, *args, **named)
        #else: MtGObject._holding.append(lambda: dispatcher.send(event, self, *args, **named))
    def register(self, callback, event, sender=dispatcher.Any, weak=True, expiry=-1, priority=dispatcher.LOWEST_PRIORITY):
        # register to receive events
        # if expiry == -1, then it is continuous, otherwise number is the number of times
        # that the callback is processed
        # XXX Major python problem - each callback must be a separate function (or wrapped in a lambda)
        # which makes it hard to disconnect it
        dispatcher.connect(callback, signal=event, sender=sender,weak=weak,expiry=expiry,priority=priority)
    def unregister(self, callback, event, sender=dispatcher.Any, weak=True):
        dispatcher.disconnect(callback, signal=event, sender=sender, weak=weak)
    #@staticmethod
    #def lock():
    #    MtGObject._lock = True
    #    MtGObject._holding = []
    #@staticmethod
    #def release():
    #    MtGObject._lock = False
    #    # Call the sends that were held
    #    for func in MtGObject._holding: func()

