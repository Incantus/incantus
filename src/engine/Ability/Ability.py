import copy

__all__ = ["Ability"]

class Ability(object):
    def __init__(self, txt):
        self.txt = txt
        self.controller = None
        self._status_count = 0

    def enable(self, source):
        self.source = source
        self.toggle(True)
    def disable(self):
        self.toggle(False)
    def toggle(self, val):
        if val:
            self._status_count += 1
            if (self._status_count == 1): self._enable()
        else:
            self._status_count -= 1
            if (self._status_count == 0): self._disable()
    def _enable(self): pass
    def _disable(self): pass
    enabled = property(fget=lambda self: self._status_count > 0)

    def copy(self): return copy.copy(self)
    def __str__(self): return self.txt.replace("~", "%s"%self.source.name)
    def __repr__(self): return "<%s%s %o: %s>"%('**' if self.enabled else '', self.__class__.__name__, id(self), self.txt)

