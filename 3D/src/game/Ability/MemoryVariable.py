from game.GameObjects import MtGObject
from game.GameEvent import *

class MemoryVariable(MtGObject):
    def __init__(self):
        self.register(self.reset, event=EndTurnEvent())
    def value(self): pass
    def reset(self): pass
    def __int__(self):
        return int(self.value())
    def __long__(self):
        return long(self.value())
    def __str__(self):
        return str(self.value())

class DamageTrackingVariable(MemoryVariable):
    def __init__(self):
        self.reset()
        self.register(self.damage_received, event=DealsDamageEvent())
        super(DamageTrackingVariable, self).__init__()
    def reset(self):
        self.dealing = {}
    def damage_dealt(self, sender, to, amount):
        if not sender in self.dealing: self.dealing[sender] = {}
        if not to in self.dealing[sender]: self.dealing[sender][to] = 0
        self.dealing[sender][to] += amount
    def dealt(self, source, to=None):
        return source in self.dealing and (to == None or to in self.dealing[source])
    def received(self, to, source=None):
        if source: return self.dealt(source, to)
        else: return any([True for dealing in self.dealing.values() if to in dealing])

class PlaySpellVariable(MemoryVariable):
    def __init__(self, condition):
        self.was_played = False
        self.condition = condition
        self.register(self.played, event=PlaySpellEvent())
        super(PlaySpellVariable, self).__init__()
    def played(self, sender, card):
        if self.condition(card):
            self.was_played = True
    def value(self): return self.was_played
    def reset(self): self.was_played = False
