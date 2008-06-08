
from pydispatch import dispatcher
from GameEvent import HasPriorityEvent, TimestepEvent

class LazyInt:
    def __init__(self, func, finalize=False, event=HasPriorityEvent()): #TimestepEvent()):
        if not callable(func): raise Exception("Argument to LazyInt init must be a function")
        self._func = func
        self._final_value = None
        self.finalize = finalize
        def reset(self=self): self._final_value = None
        if self.finalize: dispatcher.connect(reset, signal=event, weak=False)
    def value(self):
        if self.finalize:
            if not self._final_value: self._final_value = self._func()
            return self._final_value
        else: return self._func()
    def __coerce__(self, other):
        return (self.value(), other)
    def __neg__(self):
        return LazyInt(lambda : -1 * self.value())
    def __long__(self):
        return long(self.value())
    def __int__(self):
        return int(self.value())
    def __str__(self):
        return str(self.value())


class X(LazyInt):
    def __init__(self, card):
        self.card = card
        func = lambda: card.controller.getX()
        LazyInt.__init__(self, func, finalize=False)
    def value(self):
        if not self._final_value: self._final_value = self._func()
        else: return self._final_value
