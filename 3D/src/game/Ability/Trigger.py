import copy
from game.GameObjects import MtGObject
from game.GameEvent import DealsDamageEvent, ReceivesDamageEvent, CardEnteredZone, CardLeftZone, CardEnteringZone, CardLeavingZone, TimestepEvent
from game.pydispatch.dispatcher import Any
from game.pydispatch.robustapply import function

def robustApply(receiver, **named):
    """Call receiver with arguments and an appropriate subset of named
    """
    receiver, codeObject, startIndex = function(receiver)
    acceptable = codeObject.co_varnames[startIndex:codeObject.co_argcount]
    if not (codeObject.co_flags & 8):
        # fc does not have a **kwds type parameter, therefore
        # remove unacceptable arguments.
        for arg in named.keys():
            if arg not in acceptable:
                del named[arg]
    return receiver(**named)

class Trigger(MtGObject):
    def __init__(self, event=None, sender=None):
        self.trigger_event = event
        self.trigger_sender = sender
        self.activated = False
    def setup_trigger(self, source, trigger_function, match_condition=None, expiry=-1):
        self.source = source
        self.count = 0
        self.expiry = expiry
        self.trigger_function = trigger_function
        if match_condition: self.match_condition = match_condition
        else: self.match_condition = lambda *args: True
        if self.trigger_sender == "source": sender = self.source
        else: sender=Any
        self.register(self.filter, event=self.trigger_event, sender=sender)
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
        if robustApply(self.match_condition, **keys) and (self.expiry == -1 or self.count < self.expiry):
            robustApply(self.trigger_function, **keys)
            self.count += 1
    def __str__(self): return self.__class__.__name__
    def copy(self):
        return copy.copy(self)

class PhaseTrigger(Trigger):
    def filter(self, sender):
        keys = {'player': sender.curr_player, 'source': self.source}
        if robustApply(self.match_condition, **keys) and (self.expiry == -1 or self.count < self.expiry):
            robustApply(self.trigger_function, **keys)
            self.count += 1

class DealDamageTrigger(Trigger):
    def __init__(self, sender=None):
        super(DealDamageTrigger, self).__init__(event=DealsDamageEvent(), sender=sender)
class DealDamageToTrigger(Trigger):
    def __init__(self, sender=None):
        super(DealDamageTrigger, self).__init__(event=DealsDamageToEvent(), sender=sender)
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
        elif self.player == "opponent" and not player_cmp == self.source.controller: return True
        elif self.player == "any": return True
        else: return False
    def filter(self, sender, card):
        keys = {"sender": sender, "source": self.source, "card":card}
        if (robustApply(self.match_condition, **keys) and (self.expiry == -1 or self.count < self.expiry) and
           self.zone == str(sender) and self.check_player(sender, card)):
            robustApply(self.trigger_function, **keys)
            self.count += 1

class EnterTrigger(MoveTrigger):
    def __init__(self, zone=None, player="controller"):
        super(EnterTrigger,self).__init__(event=CardEnteredZone(), zone=zone, player=player)
class LeaveTrigger(MoveTrigger):
    def __init__(self, zone=None, player="controller"):
        super(LeaveTrigger,self).__init__(event=CardLeftZone(), zone=zone, player=player)
class EnteringTrigger(MoveTrigger):
    def __init__(self, zone=None, player="controller"):
        super(EnteringTrigger,self).__init__(event=CardEnteringZone(), zone=zone, player=player)
class LeavingTrigger(MoveTrigger):
    def __init__(self, zone=None, player="controller"):
        super(LeavingTrigger,self).__init__(event=CardLeavingZone(), zone=zone, player=player)

class EnterFromTrigger(Trigger):
    # We need to keep track of all zone changes, to make sure that we catch the right sequence of events
    def __init__(self, to_zone, from_zone, player="any"):
        super(EnterFromTrigger,self).__init__(event=None)
        self.from_zone = from_zone
        self.to_zone = to_zone
        self.player = player
    def setup_trigger(self, source, trigger_function, match_condition=None, expiry=-1):
        self.entering = set()
        self.count = 0
        self.expiry = expiry
        self.source = source
        self.trigger_function = trigger_function
        if match_condition: self.match_condition = match_condition
        else: self.match_condition = lambda *args: True
        self.events_senders = [(CardEnteringZone(), self.filter_entering), (CardLeavingZone(), self.filter_leaving)]
        for event, filter in self.events_senders: self.register(filter, event=event)
        self.activated = True
    def clear_trigger(self):
        if self.activated:
            # closures are not bound properly in loops, so have to define an external function
            def unregister(event, filter):
                return lambda: self.unregister(filter, event=event)
            for event, filter in self.events_senders:
                # XXX We want to wait because of the nature of the events we are catching
                # If I get rid of this, then i'll have to entering ordered zones so that removing from
                # the previous zone happens exactly before adding to the new zone
                self.register(unregister(event, filter), event=TimestepEvent(), weak=False, expiry=1)
            self.activated = False
    def check_player(self, sender, card):
        if self.to_zone == "play": player_cmp = card.controller
        else: player_cmp = card.owner

        if self.player == "controller" and player_cmp == self.source.controller: return True
        elif self.player == "opponent" and not player_cmp == self.source.controller: return True
        elif self.player == "any": return True
        else: return False
    def filter_entering(self, sender, card):
        keys = {"source": self.source, "card": card}
        if robustApply(self.match_condition, **keys) and str(sender) == self.to_zone and self.check_player(sender, card):
            self.entering.add(card)
    def filter_leaving(self, sender, card):
        keys = {"source": self.source, "card": card}
        if card in self.entering:
            self.entering.remove(card)
            if str(sender) == self.from_zone and (self.expiry == -1 or self.count < self.expiry):
                robustApply(self.trigger_function, **keys)
                self.count += 1
