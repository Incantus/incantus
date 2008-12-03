
from pydispatch import dispatcher

# Can't use properties, because that requires it derives from object and then __coerce__ won't work
class LazyInt:
    def __init__(self, func, reset_event=None):
        if not callable(func): raise Exception("Argument to LazyInt init must be a function")
        self._func = func
        if reset_event:
            self.value = self.finalize_value
            self.reset()
            dispatcher.connect(self.reset, signal=reset_event)
        else:
            self.value = self.recomp_value
    def reset(self): self._final_value = None
    def recomp_value(self): return self._func()
    def finalize_value(self):
        if not self._final_value: self._final_value = self._func()
        return self._final_value
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

