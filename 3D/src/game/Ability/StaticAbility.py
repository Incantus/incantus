from game.GameObjects import MtGObject
from game.Match import isPermanent
from Trigger import Trigger, EnterTrigger, LeaveTrigger, CardTrigger, robustApply
from game.GameEvent import ControllerChanged, SubroleModifiedEvent, TimestepEvent

# Static abilities always function while the permanent is in play
class StaticAbility(MtGObject):
    def __init__(self, card, effects=[]):
        self.card = card
        if not (type(effects) == list or type(effects) == tuple):
            self.effects = [effects]
        else: self.effects = effects
    def enteringPlay(self): pass
    def leavingPlay(self): pass

class CardStaticAbility(StaticAbility):
    # Target is by default the card itself
    def __init__(self, card, effects=[]):
        super(CardStaticAbility, self).__init__(card, effects)
        self.effect_tracking = None
    def enteringPlay(self):
        effect_removal = []
        for effect in self.effects: effect_removal.append(effect(self.card, self.card))
        self.effect_tracking = effect_removal
    def leavingPlay(self):
        for remove in self.effect_tracking: remove()
        self.effect_tracking = None

class GlobalStaticAbility(StaticAbility):
    # Target is by default the cards controller
    def __init__(self, card, effects=[]):
        super(GlobalStaticAbility, self).__init__(card, effects)
        self.effect_tracking = None
    def enteringPlay(self):
        effect_removal = []
        for effect in self.effects: effect_removal.append(effect(self.card, self.card.controller))
        self.effect_tracking = effect_removal
    def leavingPlay(self):
        for remove in self.effect_tracking: remove()
        self.effect_tracking = None

class PermanentTrackingAbility(StaticAbility):
    def __init__(self, card, condition, events = [], effects=[]):
        super(PermanentTrackingAbility, self).__init__(card, effects)
        self.condition = condition
        self.enter_trigger = EnterTrigger("play", player="any")
        self.leave_trigger = LeaveTrigger("play", player="any")
        if not type(events) == list: events = [events]
        self.other_triggers = [Trigger(event) for event in [SubroleModifiedEvent(), ControllerChanged()] + events]
        self.effect_tracking = {}
    def enteringPlay(self):
        # Get All Permanents
        permanents = self.card.controller.play.get(self.condition)
        permanents.extend(self.card.controller.opponent.play.get(self.condition))
        for perm in permanents: self.add_effects(perm)

        self.enter_trigger.setup_trigger(self, self.entering, self.condition)
        self.leave_trigger.setup_trigger(self, self.leaving)
        for trigger in self.other_triggers: trigger.setup_trigger(self,self.event_triggered)
    def leavingPlay(self):
        self.enter_trigger.clear_trigger(wait=False)
        self.leave_trigger.clear_trigger(wait=False)
        for trigger in self.other_triggers: trigger.clear_trigger(wait=False)

        for perm in self.effect_tracking.keys(): self.remove_effects(perm)
        self.effect_tracking.clear()
    def entering(self, trigger):
        # This is called everytime a permanent that matches condition enters play
        perm = trigger.matched_card
        #print "%s triggered %s in %s, currently tracked %s"%(perm, trigger.trigger_event, self.card, perm in self.effect_tracking)
        if not perm in self.effect_tracking: self.add_effects(perm)
    def leaving(self, trigger):
        # This is called everytime a permanent leaves play
        perm = trigger.matched_card
        # The perm might already be removed if both this card and the perm left play at the same time
        if perm in self.effect_tracking: self.remove_effects(perm)
    def add_effects(self, perm):
        self.effect_tracking[perm] = True  # this is to prevent recursion when the effect is called
        effect_removal = []
        for effect in self.effects: effect_removal.append(effect(self.card, perm))
        self.effect_tracking[perm] = effect_removal
    def remove_effects(self, perm):
        removal = self.effect_tracking[perm]
        for remove in removal: remove()
        del self.effect_tracking[perm]   # necessary to prevent recursion
    def event_triggered(self, trigger):
        if hasattr(trigger, "card"): perm = trigger.card
        else: perm = trigger.sender
        tracking = perm in self.effect_tracking
        pass_condition = self.condition(perm)
        #print "%s triggered %s in %s, currently tracked %s, valid %s"%(perm, trigger.trigger_event, self.card, tracking, pass_condition)
        # If perm is already tracked, but doesn't pass the condition, remove it
        # Note the condition can't rely on any trigger data
        if not tracking and pass_condition: self.add_effects(perm)
        elif tracking and not pass_condition and not self.effect_tracking[perm] == True: self.remove_effects(perm)

class AttachedStaticAbility(StaticAbility):
    def __init__(self, card, effects=[]):
        super(AttachedStaticAbility, self).__init__(card, effects)
        self.effect_tracking = None
    def enteringPlay(self):
        perm = self.card.attached_to
        effect_removal = []
        for effect in self.effects: effect_removal.append(effect(self.card, perm))
        self.effect_tracking = effect_removal
    def leavingPlay(self):
        #if isPermanent(self.card.attached_to):
        #    for remove in self.effect_tracking: remove()
        for remove in self.effect_tracking: remove()
        self.effect_tracking = None

# If the attachment target is destroyed, the aura will be destroyed, and the target is no longer valid
class AuraStaticAbility(AttachedStaticAbility): pass
class EquipmentStaticAbility(AttachedStaticAbility): pass

class Conditional(MtGObject):
    def init_condition(self, condition=lambda card: True):
        self.condition = condition
        self.activated = False
    def enteringPlay(self):
        self.register(self.check_condition, event=TimestepEvent())
    def leavingPlay(self):
        self.unregister(self.check_condition, event=TimestepEvent())
    def check_condition(self):
        pass_condition = self.condition(self.card)
        if not self.activated and pass_condition:
            super(Conditional, self).enteringPlay()
            self.activated = True
        elif self.activated and not pass_condition:
            super(Conditional, self).leavingPlay()
            self.activated = False

class ConditionalAttachedStaticAbility(Conditional, AttachedStaticAbility):
    def __init__(self, card, effects, condition):
        super(ConditionalAttachedStaticAbility, self).__init__(card, effects)
        self.init_condition(condition)

class ConditionalStaticAbility(Conditional, CardStaticAbility):
    def __init__(self, card, effects, condition):
        super(ConditionalStaticAbility, self).__init__(card, effects)
        self.init_condition(condition)
