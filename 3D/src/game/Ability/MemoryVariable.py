from game.GameObjects import MtGObject
from game.GameEvent import *

class MemoryVariable(MtGObject):
    def __init__(self):
        self.register(self.reset, event=EndTurnEvent())
    def value(self): raise NotImplementedError()
    def reset(self): pass
    def __int__(self):
        return int(self.value())
    def __long__(self):
        return long(self.value())
    def __str__(self):
        return str(self.value())

class ZoneMoveVariable(MemoryVariable):
    def __init__(self, from_zone, to_zone):
        self.from_zone = from_zone
        self.to_zone = to_zone
        self.moved = set()
        self.entering = set()
        self.events_senders = [(CardEnteringZone(), self.filter_entering), (CardLeavingZone(), self.filter_leaving)]
        for event, filter in self.events_senders: self.register(filter, event=event)
        super(ZoneMoveVariable, self).__init__()
    def reset(self):
        self.moved.clear()
        self.entering.clear()
    def filter_entering(self, sender, card):
        # If we are already tracking the card, reset
        if card in self.moved: self.moved.remove(card)
        if str(sender) == self.to_zone: self.entering.add(card)
    def filter_leaving(self, sender, card):
        if card in self.entering:
            self.entering.remove(card)
            if str(sender) == self.from_zone: self.moved.add(card)
    def __len__(self): return len(self.moved)
    def value(self): return len(self)
    def __contains__(self, card): return card in self.moved
    def get(self, match=lambda c:True):
        return (card for card in self.moved if match(card))
    def __iter__(self): return iter(self.get())

class ZoneMoveCountVariable(MemoryVariable):
    def __init__(self, from_zone, to_zone, match):
        self.from_zone = from_zone
        self.to_zone = to_zone
        self.match = match
        self.move_count = 0
        self.entering = set()
        self.events_senders = [(CardEnteringZone(), self.filter_entering), (CardLeavingZone(), self.filter_leaving)]
        for event, filter in self.events_senders: self.register(filter, event=event)
        super(ZoneMoveCounterVariable, self).__init__()
    def reset(self):
        self.move_count = 0
        self.entering.clear()
    def filter_entering(self, sender, card):
        if str(sender) == self.to_zone and self.match(card): self.entering.add(card)
    def filter_leaving(self, sender, card):
        if card in self.entering:
            self.entering.remove(card)
            if str(sender) == self.from_zone: self.move_count += 1
    def value(self): return self.move_count

class DamageTrackingVariable(MemoryVariable):
    def __init__(self):
        self.reset()
        self.register(self.damage, event=DealsDamageToEvent())
        super(DamageTrackingVariable, self).__init__()
    def reset(self):
        self.dealing = {}
    def value(self): return 0
    def damage(self, sender, to, amount):
        if not sender in self.dealing: self.dealing[sender] = {}
        if not to in self.dealing[sender]: self.dealing[sender][to] = 0
        self.dealing[sender][to] += amount
    def dealt(self, source, to=None):
        return source in self.dealing and (to == None or to in self.dealing[source])
    def received(self, to, source=None):
        if source: return self.dealt(source, to)
        else: return any([True for dealing in self.dealing.values() if to in dealing])
    def amount_dealt(self, source, to=None):
        if not source in self.dealing: return 0
        elif to == None: return sum(self.dealing[source].values())
        else: return self.dealing[source][to]
    def amount_received(self, to, source=None):
        if source: return self.dealt[source][to]
        else: return sum([dealing[to] for dealing in self.dealing.values if to in dealing])

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
