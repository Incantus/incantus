import copy
from game.GameObjects import MtGObject
from game.Match import isPermanent
from Trigger import Trigger, EnterTrigger, LeaveTrigger, CardTrigger, robustApply
from game.GameEvent import ControllerChanged, SubroleModifiedEvent, TimestepEvent

# Static abilities always function while the permanent is in the relevant zone
class StaticAbility(object):
    def __init__(self, card, effects=[], zone="play", txt=''):
        self.card = card
        if not (type(effects) == list or type(effects) == tuple):
            self.effects = [effects]
        else: self.effects = effects
        self.zone = zone
        self.txt = txt
        self.effect_tracking = None
    def enteringZone(self): pass
    def leavingZone(self): pass
    def copy(self, card=None):
        newcopy = copy.copy(self)
        if not card: card = self.card
        newcopy.card = card
        return newcopy
    def __str__(self): return self.txt

class CardTrackingAbility(StaticAbility):
    def __init__(self, card, condition, events = [], effects=[], tracking_zone="play", zone="play", txt=''):
        super(CardTrackingAbility, self).__init__(card, effects, zone, txt)
        self.condition = condition
        self.enter_trigger = EnterTrigger(tracking_zone, player="any")
        self.leave_trigger = LeaveTrigger(tracking_zone, player="any")
        if not type(events) == list: events = [events]
        self.tracking_zone = tracking_zone
        self.other_triggers = [Trigger(event) for event in [SubroleModifiedEvent(), ControllerChanged()] + events]
    def enteringZone(self):
        self.effect_tracking = {}
        # Get all cards in the tracked zone
        zone = getattr(self.card.controller, self.tracking_zone)
        opp_zone = getattr(self.card.controller.opponent, self.tracking_zone)
        cards = zone.get(self.condition) + opp_zone.get(self.condition)

        for card in cards: self.add_effects(card)

        self.enter_trigger.setup_trigger(self, self.entering, self.condition)
        self.leave_trigger.setup_trigger(self, self.leaving)
        for trigger in self.other_triggers: trigger.setup_trigger(self,self.event_triggered)
    def leavingZone(self):
        self.enter_trigger.clear_trigger()
        self.leave_trigger.clear_trigger()
        for trigger in self.other_triggers: trigger.clear_trigger()

        for card in self.effect_tracking.keys(): self.remove_effects(card)
        self.effect_tracking.clear()
    def entering(self, trigger):
        # This is called everytime a card that matches condition enters the tracking zone
        card = trigger.matched_card
        if not card in self.effect_tracking: self.add_effects(card)
    def leaving(self, trigger):
        # This is called everytime a card that matches condition leaves the tracking zone
        card = trigger.matched_card
        # The card might already be removed if the tracked card is removed and this card leaves play
        if card in self.effect_tracking: self.remove_effects(card)
    def add_effects(self, card):
        self.effect_tracking[card] = True  # this is to prevent recursion when the effect is called
        effect_removal = []
        for effect in self.effects: effect_removal.append(effect(self.card, card))
        self.effect_tracking[card] = effect_removal
    def remove_effects(self, card):
        removal = self.effect_tracking[card]
        for remove in removal: remove()
        del self.effect_tracking[card]   # necessary to prevent recursion
    def event_triggered(self, trigger):
        if hasattr(trigger, "card"): card = trigger.card
        else: card = trigger.sender
        tracking = card in self.effect_tracking
        pass_condition = self.condition(card)
        # If card is already tracked, but doesn't pass the condition, remove it
        # Note the condition can't rely on any trigger data
        if not tracking and pass_condition: self.add_effects(card)
        elif tracking and not pass_condition and not self.effect_tracking[card] == True: self.remove_effects(card)

class PermanentTrackingAbility(CardTrackingAbility):
    def __init__(self, card, condition, events = [], effects=[], zone="play", txt=''):
        super(PermanentTrackingAbility, self).__init__(card, condition, events, effects, "play", zone, txt)

class CardStaticAbility(StaticAbility):
    # Target is the card itself
    def enteringZone(self):
        effect_removal = []
        for effect in self.effects: effect_removal.append(effect(self.card, self.card))
        self.effect_tracking = effect_removal
    def leavingZone(self):
        for remove in self.effect_tracking: remove()
        self.effect_tracking = None

class GlobalStaticAbility(StaticAbility):
    # Target is the cards controller
    def enteringZone(self):
        effect_removal = []
        for effect in self.effects: effect_removal.append(effect(self.card, self.card.controller))
        self.effect_tracking = effect_removal
    def leavingZone(self):
        for remove in self.effect_tracking: remove()
        self.effect_tracking = None

class AttachedStaticAbility(StaticAbility):
    # Target is the card which is attached
    def enteringZone(self):
        effect_removal = []
        for effect in self.effects: effect_removal.append(effect(self.card, self.card.attached_to))
        self.effect_tracking = effect_removal
    def leavingZone(self):
        for remove in self.effect_tracking: remove()
        self.effect_tracking = None

# If the attachment target is destroyed, the aura will be destroyed, and the target is no longer valid
class AuraStaticAbility(AttachedStaticAbility): pass
class EquipmentStaticAbility(AttachedStaticAbility): pass

class Conditional(MtGObject):
    def init_condition(self, condition=lambda card: True):
        self.condition = condition
        self.activated = False
    def enteringZone(self):
        self.register(self.check_condition, event=TimestepEvent())
        self.check_condition()
    def leavingZone(self):
        self.unregister(self.check_condition, event=TimestepEvent())
        if self.activated:
            self.activated = False
            super(Conditional, self).leavingZone()
    def check_condition(self):
        pass_condition = self.condition(self.card)
        if not self.activated and pass_condition:
            super(Conditional, self).enteringZone()
            self.activated = True
        elif self.activated and not pass_condition:
            super(Conditional, self).leavingZone()
            self.activated = False

class ConditionalAttachedStaticAbility(Conditional, AttachedStaticAbility):
    def __init__(self, card, effects, condition, zone="play", txt=''):
        super(ConditionalAttachedStaticAbility, self).__init__(card, effects, zone, txt)
        self.init_condition(condition)

class ConditionalStaticAbility(Conditional, CardStaticAbility):
    def __init__(self, card, effects, condition, zone="play", txt=''):
        super(ConditionalStaticAbility, self).__init__(card, effects, zone, txt)
        self.init_condition(condition)
