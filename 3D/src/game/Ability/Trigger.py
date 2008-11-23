import copy
from game.GameObjects import MtGObject
from game.GameEvent import DealsDamageEvent, DealsDamageToEvent, ReceivesDamageEvent, CardEnteredZone, CardLeftZone, CardEnteringZoneFrom
from game.pydispatch.dispatcher import Any, LOWEST_PRIORITY
from EffectsUtilities import robustApply

class Trigger(MtGObject):
    def __init__(self, event=None, sender=None):
        self.trigger_event = event
        self.trigger_sender = sender
        self.activated = False
    def setup_trigger(self, source, trigger_function, match_condition=None, expiry=-1, priority=LOWEST_PRIORITY):
        self.source = source
        self.count = 0
        self.expiry = expiry
        self.trigger_function = trigger_function
        if match_condition: self.match_condition = match_condition
        else: self.match_condition = lambda *args: True
        if self.trigger_sender == "source": sender = self.source
        else: sender=Any
        self.register(self.filter, event=self.trigger_event, sender=sender, priority=priority)
        self.activated = True
    def clear_trigger(self):
        if self.activated:
            if self.trigger_sender == "source": sender = self.source
            else: sender=Any
            self.unregister(self.filter, event=self.trigger_event, sender=sender)
            self.activated = False
    def filter(self, sender, **keys):
        keys["source"] = self.source
        keys["sender"] = sender
        if (self.expiry == -1 or self.count < self.expiry) and robustApply(self.match_condition, **keys):
            robustApply(self.trigger_function, **keys)
            self.count += 1
    def __str__(self): return self.__class__.__name__
    def copy(self):
        return copy.copy(self)

class PhaseTrigger(Trigger):
    def filter(self, sender, player):
        keys = {'player': player, 'source': self.source}
        if (self.expiry == -1 or self.count < self.expiry) and robustApply(self.match_condition, **keys):
            robustApply(self.trigger_function, **keys)
            self.count += 1

class DealDamageTrigger(Trigger):
    def __init__(self, sender=None):
        super(DealDamageTrigger, self).__init__(event=DealsDamageEvent(), sender=sender)
class DealDamageToTrigger(Trigger):
    def __init__(self, sender=None):
        super(DealDamageToTrigger, self).__init__(event=DealsDamageToEvent(), sender=sender)
class ReceiveDamageTrigger(Trigger):
    def __init__(self, sender=None):
        super(ReceiveDamageTrigger, self).__init__(event=ReceivesDamageEvent(), sender=sender)

# The next triggers are for events that pertain to cards but aren't sent by the card itself (ie zone changes, spells of abilities of cards)
class CardTrigger(Trigger): pass

class MoveTrigger(Trigger):
    def __init__(self, event, zone, player="controller"):
        super(MoveTrigger, self).__init__(event=event)
        self.zone = zone
        self.player = player
    def check_player(self, sender, card):
        if self.zone == "play": player_cmp = card.controller
        else: player_cmp = card.owner

        if self.player == "controller" and player_cmp == self.source.controller: return True
        elif self.player == "opponent" and player_cmp in self.source.controller.opponents: return True
        elif self.player == "any": return True
        else: return False
    def filter(self, sender, card):
        keys = {"sender": sender, "source": self.source, "card":card}
        if (self.zone == str(sender) and self.check_player(sender, card) and
            robustApply(self.match_condition, **keys) and (self.expiry == -1 or self.count < self.expiry)):
            robustApply(self.trigger_function, **keys)
            self.count += 1

class EnterTrigger(MoveTrigger):
    def __init__(self, zone=None, player="controller"):
        super(EnterTrigger,self).__init__(event=CardEnteredZone(), zone=zone, player=player)
class LeaveTrigger(MoveTrigger):
    def __init__(self, zone=None, player="controller"):
        super(LeaveTrigger,self).__init__(event=CardLeftZone(), zone=zone, player=player)

class EnterFromTrigger(Trigger):
    # We need to keep track of all zone changes, to make sure that we catch the right sequence of events
    def __init__(self, to_zone, from_zone, player="any"):
        super(EnterFromTrigger,self).__init__(event=None)
        self.from_zone = from_zone
        self.to_zone = to_zone
        self.player = player
    def setup_trigger(self, source, trigger_function, match_condition=None, expiry=-1, priority=LOWEST_PRIORITY):
        self.count = 0
        self.expiry = expiry
        self.source = source
        self.trigger_function = trigger_function
        if match_condition: self.match_condition = match_condition
        else: self.match_condition = lambda *args: True
        self.register(self.filter, event=CardEnteringZoneFrom(), priority=priority)
        self.activated = True
    def clear_trigger(self):
        if self.activated:
            self.unregister(self.filter, event=CardEnteringZoneFrom())
            self.activated = False
    def check_player(self, sender, card):
        if self.to_zone == "play": player_cmp = card.controller
        else: player_cmp = card.owner

        if self.player == "controller" and player_cmp == self.source.controller: return True
        elif self.player == "opponent" and player_cmp in self.source.controller.opponents: return True
        elif self.player == "any": return True
        else: return False
    def filter(self, sender, from_zone, oldcard, newcard):
        keys = {"source": self.source, "card": oldcard, "newcard": newcard}
        if ((str(sender) == self.to_zone and str(from_zone) == self.from_zone) and 
             self.check_player(sender, oldcard) and 
             robustApply(self.match_condition, **keys) and 
             (self.expiry == -1 or self.count < self.expiry)):
            robustApply(self.trigger_function, **keys)
            self.count += 1
