from game.GameObjects import MtGObject
from game.Match import isPermanent
from Trigger import Trigger, EnterTrigger, LeaveTrigger, CardTrigger
from game.GameEvent import CardControllerChanged, AddSubRoleEvent, RemoveSubRoleEvent

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
    def __init__(self, card, enter_condition, leave_condition, effects=[]):
        super(PermanentTrackingAbility, self).__init__(card, effects)
        self.enter_condition = enter_condition
        self.leave_condition = leave_condition
        self.enter_trigger = EnterTrigger("play", any=True)
        self.leave_trigger = LeaveTrigger("play", any=True)
        #self.controller_trigger = CardTrigger(CardControllerChanged())
        self.add_subrole_trigger = CardTrigger(event=AddSubRoleEvent())
        self.remove_subrole_trigger = CardTrigger(event=RemoveSubRoleEvent())
        self.effect_tracking = {}
    def enteringPlay(self):
        self.enter_trigger.setup_trigger(self,self.entered,self.enter_condition)
        self.leave_trigger.setup_trigger(self,self.left,self.leave_condition)
        self.add_subrole_trigger.setup_trigger(self,self.entered,self.enter_condition)
        self.remove_subrole_trigger.setup_trigger(self,self.left,self.leave_condition)
        #self.controller_trigger.setup_trigger(self,self.controllerChanged,self.enter_condition)
        # Get All Permanents
        permanents = self.card.controller.play.get(self.enter_condition)
        permanents.extend(self.card.controller.opponent.play.get(self.enter_condition))
        for perm in permanents:
            effect_removal = []
            for effect in self.effects: effect_removal.append(effect(self.card, perm))
            self.effect_tracking[perm] = effect_removal
    def leavingPlay(self):
        self.enter_trigger.clear_trigger()
        self.leave_trigger.clear_trigger()
        #self.controller_trigger.clear_trigger()
        self.add_subrole_trigger.clear_trigger()
        self.remove_subrole_trigger.clear_trigger()
        for perm, removal in self.effect_tracking.items():
            for remove in removal: remove()
        self.effect_tracking.clear()
    def controllerChanged(self):
        perm = self.controller_trigger.matched_card
        effect_removal = []
        for effect in self.effects: effect_removal.append(effect(self.card, perm))
        self.effect_tracking[perm] = effect_removal
    def entered(self, trigger):
        # This is called everytime something triggers
        perm = trigger.matched_card
        if not perm in self.effect_tracking:
            effect_removal = []
            for effect in self.effects: effect_removal.append(effect(self.card, perm))
            self.effect_tracking[perm] = effect_removal
    def left(self, trigger):
        perm = trigger.matched_card
        # The perm might already be removed if both this card and the perm left play at the same time
        if perm in self.effect_tracking:
            removal = self.effect_tracking[perm]
            for remove in removal: remove()
            del self.effect_tracking[perm]

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
