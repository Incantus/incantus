from functools import partial
from engine.pydispatch.dispatcher import CONTINUOUS_PRIORITY
from engine.GameEvent import ControllerChanged, TimestepEvent
from engine.MtGObject import MtGObject
from Ability import Ability
from Trigger import Trigger, EnterTrigger, LeaveTrigger, all_match
from EffectsUtilities import combine

__all__ = ["SimpleStaticAbility", "CardStaticAbility", "ConditionalStaticAbility", "CardTrackingAbility", "ConditionalTrackingAbility"]

# Static abilities always function while the permanent is in the relevant zone
class StaticAbility(Ability):
    def __init__(self, effects, zone="battlefield", txt='', keyword=''):
        self.effect_generator = effects
        self.effect_tracking = None
        self.zone = zone
        self.keyword = keyword
        if keyword and not txt: txt = keyword.capitalize()
        super(StaticAbility, self).__init__(txt)
    def copy(self): return self.__class__(self.effect_generator, self.zone, self.txt, self.keyword)

class CardTrackingAbility(StaticAbility):
    def __init__(self, effects, condition, events = [], tracking="battlefield", zone="battlefield", txt=''):
        super(CardTrackingAbility, self).__init__(effects, zone, txt)
        self.enter_trigger = EnterTrigger(tracking, condition, player="any")
        self.leave_trigger = LeaveTrigger(tracking, player="any")
        self.control_changed = Trigger(ControllerChanged(), sender="source")  # card with ability changed controller
        if isinstance(events, tuple): events = list(events)
        elif not isinstance(events, list): events = [events]
        self.other_triggers = [Trigger(event) for event in [ControllerChanged()] + events] # triggers for tracked cards
        if not condition: condition = all_match
        self.condition = condition
        self.tracking = tracking
        self.events = events
    def get_current(self):
        controller = self.source.controller
        zone_condition = partial(self.condition, self.source)
        if self.tracking == "battlefield":
            cards = controller.battlefield.get(zone_condition, all=True)
        else:
            zone = getattr(controller, self.tracking)
            cards = zone.get(zone_condition)
            for opponent in controller.opponents:
                opp_zone = getattr(opponent, self.tracking)
                cards.extend(opp_zone.get(zone_condition))
        return cards
    def _enable(self):
        super(CardTrackingAbility, self)._enable()
        self.effect_tracking = {}
        # Get all cards in the tracked zone
        for card in self.get_current(): self.add_effects(card)

        self.enter_trigger.setup_trigger(self.source, self.entering, priority=CONTINUOUS_PRIORITY)
        self.leave_trigger.setup_trigger(self.source, self.leaving, priority=CONTINUOUS_PRIORITY)
        self.control_changed.setup_trigger(self.source, self.new_controller, priority=CONTINUOUS_PRIORITY)
        for trigger in self.other_triggers: trigger.setup_trigger(self.source, self.card_changed, priority=CONTINUOUS_PRIORITY)
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
        # The card might already be removed if the tracked card is removed and this card leaves the battlefield
        # XXX Don't remove the effect since it's part of LKI
        #if card in self.effect_tracking: self.remove_effects(card)
        if card in self.effect_tracking: del self.effect_tracking[card]
    def add_effects(self, card):
        self.effect_tracking[card] = True  # this is to prevent recursion when the effect is called
        self.effect_tracking[card] = [combine(*removal_func) if isinstance(removal_func, tuple) 
                else removal_func for removal_func in self.effect_generator(self.source, card)]
    def remove_effects(self, card):
        for remove in self.effect_tracking[card]: remove()
        del self.effect_tracking[card]   # necessary to prevent recursion
    def card_changed(self, sender):
        tracking = sender in self.effect_tracking
        pass_condition = self.condition(self.source, sender)
        # If card is already tracked, but doesn't pass the condition, remove it
        # XXX Note the condition can't rely on any trigger data
        if not tracking and pass_condition: self.add_effects(sender)
        elif tracking and not pass_condition and not self.effect_tracking[sender] == True: self.remove_effects(sender)
    def copy(self):
        return self.__class__(self.effect_generator, self.condition, self.events, self.tracking, self.zone, self.txt)

class SimpleStaticAbility(StaticAbility):
    def _enable(self):
        super(SimpleStaticAbility, self)._enable()
        self.effect_tracking = [combine(*removal_func) if isinstance(removal_func, tuple) else removal_func for removal_func in self.effect_generator(self.source)]
    def _disable(self):
        super(SimpleStaticAbility, self)._disable()
        for remove in self.effect_tracking: remove()
        self.effect_tracking = []

class CardStaticAbility(StaticAbility):
    def __init__(self, effects, zone="battlefield", txt='', keyword=''):
        super(CardStaticAbility, self).__init__(effects, zone=zone, txt=txt, keyword=keyword)
        # XXX The zone is not quite right, for attached static abilities that can 
        # attach to something out of the battlefield
        self.control_changed = Trigger(ControllerChanged(), sender="source")  # card with ability changed controller
    def _enable(self):
        super(CardStaticAbility, self)._enable()
        self.control_changed.setup_trigger(self.source, self.new_controller, priority=CONTINUOUS_PRIORITY)
        self.effect_tracking = [combine(*removal_func) if isinstance(removal_func, tuple) else removal_func for removal_func in self.effect_generator(self.source)]
    def _disable(self):
        super(CardStaticAbility, self)._disable()
        self.control_changed.clear_trigger()
        for remove in self.effect_tracking: remove()
        self.effect_tracking = []
    def leaving(self, card):
        # XXX Don't remove the effect since it's part of LKI
        self.effect_tracking = []
    def new_controller(self, original):
        for remove in self.effect_tracking: remove()
        self.effect_tracking = [combine(*removal_func) if isinstance(removal_func, tuple) else removal_func for removal_func in self.effect_generator(self.source)]

# The condition is checked every timestep
class Conditional(MtGObject):
    def init_conditional(self, conditional=lambda source: True):
        self.conditional = conditional
        self.__enabled = False
    def _enable(self):
        self.register(self.check_conditional, event=TimestepEvent())
        self.check_conditional()
    def _disable(self):
        self.unregister(self.check_conditional, event=TimestepEvent())
        if self.__enabled:
            self.__enabled = False
            super(Conditional, self)._disable()
    def check_conditional(self):
        pass_condition = self.conditional(self.source)
        if not self.__enabled and pass_condition:
            super(Conditional, self)._enable()
            self.__enabled = True
        elif self.__enabled and not pass_condition:
            super(Conditional, self)._disable()
            self.__enabled = False

class ConditionalStaticAbility(Conditional, CardStaticAbility):
    def __init__(self, effects, conditional, zone="battlefield", txt='', keyword=''):
        super(ConditionalStaticAbility, self).__init__(effects, zone, txt, keyword)
        self.init_conditional(conditional)
    def copy(self): return self.__class__(self.effect_generator, self.conditional, self.zone, self.txt, self.keyword)

class ConditionalTrackingAbility(Conditional, CardTrackingAbility):
    def __init__(self, effects, condition, conditional, events = [], tracking="battlefield", zone="battlefield", txt=''):
        super(ConditionalTrackingAbility, self).__init__(effects, condition, events, tracking, zone, txt)
        self.init_conditional(conditional)
    def copy(self):
        return self.__class__(self.effect_generator, self.condition, self.conditional, self.events, self.tracking, self.zone, self.txt)
