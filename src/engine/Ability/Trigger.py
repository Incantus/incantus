import copy
from engine.MtGObject import MtGObject
from engine.GameEvent import DealsDamageEvent, DealsDamageToEvent, ReceivesDamageEvent, CardEnteredZone, CardLeftZone, CardEnteringZoneFrom, UpkeepStepEvent
from engine.pydispatch.dispatcher import Any, LOWEST_PRIORITY
from EffectsUtilities import robustApply

__all__ = ["Trigger",
           "PhaseTrigger", "YourUpkeepTrigger",
           "SpellPlayedTrigger",
           "DealDamageTrigger", "DealDamageToTrigger", "ReceiveDamageTrigger",
           "EnterTrigger", "LeaveTrigger", "EnterFromTrigger",
           "all_match", "source_match", "sender_match", "attached_match", "controller_match"]

all_match = lambda *args: True
source_match = lambda source, card: source == card
sender_match = lambda source, sender: source == sender
attached_match = lambda source, card: source.attached_to == card
controller_match = lambda source, player: source.controller == player

class Trigger(MtGObject):
    def __init__(self, event=None, condition=None, sender=None):
        self.trigger_event = event
        self.trigger_sender = sender
        self.activated = False
        if condition: self.condition = condition
        else: self.condition = all_match
    def check_expiry():
        return (self.expiry == -1 or self.count < self.expiry)
    def setup_trigger(self, source, trigger_function, expiry=-1, priority=LOWEST_PRIORITY):
        self.source = source
        self.count = 0
        self.expiry = expiry
        self.trigger_function = trigger_function
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
            del self.expiry
            del self.count
    def filter(self, sender, **keys):
        keys["source"] = self.source
        keys["sender"] = sender
        if self.check_expiry() and robustApply(self.condition, **keys):
            robustApply(self.trigger_function, **keys)
            self.count += 1
    def __str__(self): return self.__class__.__name__
    def copy(self):
        return copy.copy(self)

class PhaseTrigger(Trigger):
    def filter(self, sender, player):
        keys = {'player': player, 'source': self.source}
        if self.check_expiry() and robustApply(self.condition, **keys):
            robustApply(self.trigger_function, **keys)
            self.count += 1

class YourUpkeepTrigger(PhaseTrigger):
    def __init__(self):
        super(PhaseTrigger, self).__init__(UpkeepStepEvent(), condition=controller_match)

class SpellPlayedTrigger(Trigger):
    def __init__(self, condition=None, sender=None):
        super(SpellPlayedTrigger, self).__init__(event=SpellPlayedEvent(), condition=condition, sender=sender)


class DealDamageTrigger(Trigger):
    def __init__(self, condition=None, sender=None):
        super(DealDamageTrigger, self).__init__(event=DealsDamageEvent(), condition=condition, sender=sender)
class DealDamageToTrigger(Trigger):
    def __init__(self, condition=None, sender=None):
        super(DealDamageToTrigger, self).__init__(event=DealsDamageToEvent(), condition=condition, sender=sender)
class ReceiveDamageTrigger(Trigger):
    def __init__(self, condition=None, sender=None):
        super(ReceiveDamageTrigger, self).__init__(event=ReceivesDamageEvent(), condition=condition, sender=sender)

# The next triggers are for events that pertain to cards but aren't sent by the card itself (ie zone changes, spells of abilities of cards)

class MoveTrigger(Trigger):
    def __init__(self, event, zone, condition=None, player="you"):
        super(MoveTrigger, self).__init__(event=event, condition=condition)
        self.zone = zone
        self.player = player
    def check_player(self, sender, card):
        player_cmp = card.controller  # Out of battlefield defaults to owner

        if self.player == "you" and player_cmp == self.source.controller: return True
        elif self.player == "opponent" and player_cmp in self.source.controller.opponents: return True
        elif self.player == "any": return True
        else: return False
    def filter(self, sender, card):
        keys = {"sender": sender, "source": self.source, "card":card}
        if (self.zone == str(sender) and self.check_player(sender, card) and
            robustApply(self.condition, **keys) and self.check_expiry())):
            robustApply(self.trigger_function, **keys)
            self.count += 1

class EnterTrigger(MoveTrigger):
    def __init__(self, zone, condition=None, player="you"):
        super(EnterTrigger,self).__init__(event=CardEnteredZone(), zone=zone, condition=condition, player=player)
class LeaveTrigger(MoveTrigger):
    def __init__(self, zone, condition=None, player="you"):
        super(LeaveTrigger,self).__init__(event=CardLeftZone(), zone=zone, condition=condition, player=player)

class EnterFromTrigger(Trigger):
    # We need to keep track of all zone changes, to make sure that we catch the right sequence of events
    def __init__(self, to_zone, from_zone, condition=None, player="you"):
        super(EnterFromTrigger,self).__init__(event=None, condition=condition)
        self.from_zone = from_zone
        self.to_zone = to_zone
        self.player = player
    def setup_trigger(self, source, trigger_function, expiry=-1, priority=LOWEST_PRIORITY):
        self.count = 0
        self.expiry = expiry
        self.source = source
        self.trigger_function = trigger_function
        self.register(self.filter, event=CardEnteringZoneFrom(), priority=priority)
        self.activated = True
    def clear_trigger(self):
        if self.activated:
            self.unregister(self.filter, event=CardEnteringZoneFrom())
            self.activated = False
    def check_player(self, sender, card):
        player_cmp = card.controller  # Out of battlefield defaults to owner

        if self.player == "you" and player_cmp == self.source.controller: return True
        elif self.player == "opponent" and player_cmp in self.source.controller.opponents: return True
        elif self.player == "any": return True
        else: return False
    def filter(self, sender, from_zone, oldcard, newcard):
        keys = {"source": self.source, "card": oldcard, "newcard": newcard}
        if ((str(sender) == self.to_zone and str(from_zone) == self.from_zone) and 
             self.check_player(sender, oldcard) and 
             robustApply(self.condition, **keys) and 
             self.check_expiry()):
            robustApply(self.trigger_function, **keys)
            self.count += 1
