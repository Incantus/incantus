
class guiEvent(object):
    def __hash__(self):
        return hash(self.__class__)
    def __eq__(self, other):
        return self.__class__ == other.__class__

class FocusCard(guiEvent): pass
class HighlightTarget(guiEvent): pass
