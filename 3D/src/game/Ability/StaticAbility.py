import copy
from functools import partial
from game.GameObjects import MtGObject
from Trigger import Trigger, EnterTrigger, LeaveTrigger, CardTrigger
from game.GameEvent import ControllerChanged, SubroleModifiedEvent, TimestepEvent

# Static abilities always function while the permanent is in the relevant zone
class StaticAbility(object):
    enabled = property(fget=lambda self: self._status_count > 0)
    def __init__(self, effects, zone="play", txt='', keyword=''):
        self.effect_generator = effects
        self.zone = zone
        if keyword: self.txt = keyword.title()
        else: self.txt = txt
        self.keyword = keyword
        self.effect_tracking = None
        self._status_count = 0
    def enable(self, source):
        self.source = source
        self._status_count += 1
        if self._status_count == 1: self._enable()
    def disable(self):
        self._status_count -= 1
        if self._status_count == 0: self._disable()
    def _enable(self): pass
    def _disable(self): pass
    def copy(self): return copy.copy(self)
    def __str__(self): return self.txt

class CardTrackingAbility(StaticAbility):
    def __init__(self, effects, condition, events = [], tracking="play", zone="play", txt=''):
        super(CardTrackingAbility, self).__init__(effects, zone, txt)
        self.enter_trigger = EnterTrigger(tracking, player="any")
        self.leave_trigger = LeaveTrigger(tracking, player="any")
        self.control_changed = Trigger(ControllerChanged(), sender="source")
        if not type(events) == list: events = [events]
        self.other_triggers = [Trigger(event) for event in [SubroleModifiedEvent(), ControllerChanged()] + events]
        self.condition = condition
        self.tracking = tracking
    def get_current(self):
        zone_condition = partial(self.condition, self.source)
        if self.tracking == "play":
            zone = getattr(self.source.controller, self.tracking)
            cards = zone.get(zone_condition, all=True)
        else:
            zone = getattr(self.source.controller, self.tracking)
            opp_zone = getattr(self.source.controller.opponent, self.tracking)
            cards = zone.get(zone_condition) + opp_zone.get(zone_condition)
        return cards
    def _enable(self):
        super(CardTrackingAbility, self)._enable()
        self.effect_tracking = {}
        # Get all cards in the tracked zone
        for card in self.get_current(): self.add_effects(card)

        self.enter_trigger.setup_trigger(self.source, self.entering, self.condition)
        self.leave_trigger.setup_trigger(self.source, self.leaving)
        self.control_changed.setup_trigger(self.source, self.new_controller)
        for trigger in self.other_triggers: trigger.setup_trigger(self.source, self.card_changed)
    def _disable(self):
        super(CardTrackingAbility, self)._disable()
        self.enter_trigger.clear_trigger()
        self.leave_trigger.clear_trigger()
        self.control_changed.clear_trigger()
        for trigger in self.other_triggers: trigger.clear_trigger()

        for card in self.effect_tracking.keys(): self.remove_effects(card)
        self.effect_tracking.clear()
    def new_controller(self, original):
        # Check all current cards, to see if they should be added or removed from the current set
        new_cards, old_cards = set(self.get_current()), set(self.effect_tracking)
        for card in new_cards-old_cards:
            self.add_effects(card)
        for card in old_cards-new_cards:
            self.remove_effects(card)
    def entering(self, card):
        # This is called everytime a card that matches condition enters the tracking zone
        if not card in self.effect_tracking: self.add_effects(card)
    def leaving(self, card):
        # This is called everytime a card that matches condition leaves the tracking zone
        # The card might already be removed if the tracked card is removed and this card leaves play
        # XXX Don't remove the effect since it's part of LKI
        #if card in self.effect_tracking: self.remove_effects(card)
        if card in self.effect_tracking: del self.effect_tracking[card]
    def add_effects(self, card):
        self.effect_tracking[card] = True  # this is to prevent recursion when the effect is called
        self.effect_tracking[card] = [removal_func for removal_func in self.effect_generator(self.source, card)]
    def remove_effects(self, card):
        for remove in self.effect_tracking[card]: remove()
        del self.effect_tracking[card]   # necessary to prevent recursion
    def card_changed(self, sender):
        tracking = sender in self.effect_tracking
        pass_condition = self.condition(self.source, sender)
        # If card is already tracked, but doesn't pass the condition, remove it
        # Note the condition can't rely on any trigger data
        if not tracking and pass_condition: self.add_effects(sender)
        elif tracking and not pass_condition and not self.effect_tracking[sender] == True: self.remove_effects(sender)

class CardStaticAbility(StaticAbility):
    def _enable(self):
        super(CardStaticAbility, self)._enable()
        self.effect_tracking = [removal_func for removal_func in self.effect_generator(self.source)]
    def _disable(self):
        super(CardStaticAbility, self)._disable()
        for remove in self.effect_tracking: remove()
        self.effect_tracking = None

class AttachedAbility(StaticAbility):
    def _enable(self):
        super(AttachedAbility, self)._enable()
        self.effect_tracking = [removal_func for removal_func in self.effect_generator(self.source, self.source.attached_to)]
    def _disable(self):
        super(AttachedAbility, self)._disable()
        for remove in self.effect_tracking: remove()
        self.effect_tracking = None

# The condition is checked every timestep
class Conditional(MtGObject):
    def init_condition(self, condition=lambda source: True):
        self.condition = condition
        self.__enabled = False
    def _enable(self):
        self.register(self.check_condition, event=TimestepEvent())
        self.check_condition()
    def _disable(self):
        self.unregister(self.check_condition, event=TimestepEvent())
        if self.__enabled:
            self.__enabled = False
            super(Conditional, self)._disable()
    def check_condition(self):
        pass_condition = self.condition(self.source)
        if not self.__enabled and pass_condition:
            super(Conditional, self)._enable()
            self.__enabled = True
        elif self.__enabled and not pass_condition:
            super(Conditional, self)._disable()
            self.__enabled = False

class ConditionalStaticAbility(Conditional, CardStaticAbility):
    def __init__(self, effects, condition, zone="play", txt=''):
        super(ConditionalStaticAbility, self).__init__(effects, zone, txt)
        self.init_condition(condition)

class ConditionalAttachedAbility(Conditional, AttachedAbility):
    def __init__(self, effects, condition, zone="play", txt=''):
        super(ConditionalAttachedAbility, self).__init__(effects, zone, txt)
        self.init_condition(condition)
