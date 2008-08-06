from game.GameObjects import MtGObject
from game.Match import SelfMatch

class TriggeredAbility(MtGObject):
    def __init__(self, card, trigger, match_condition, ability, expiry=-1, zone="play"):
        self.card = card
        self.trigger = trigger
        self.match_condition = match_condition
        self.ability = ability
        self.expiry = expiry
        self.zone = zone
    #def can_be_countered(self):
    #    return False
    def enteringZone(self):
        self.trigger.setup_trigger(self,self.playAbility,self.match_condition,self.expiry)
    def leavingZone(self):
        self.trigger.clear_trigger(wait=False)
    def playAbility(self, trigger=None): # We don't care about the trigger
        Play(self.card, self.ability.copy())
    def copy(self, card=None):
        if not card: card = self.card
        return TriggeredAbility(card, self.trigger.copy(), self.match_condition, self.ability.copy(card))
    def __str__(self):
        return "When %s, do %s"%(self.trigger, self.ability)

def Play(card, ability):
    # This is identical to Action.PlaySpell - there's probably a way to combine them
    ability.controller = card.controller
    if ability.needs_stack(): ability.controller.stack.add_triggered(ability)
    else: ability.controller.stack.stackless(ability)
    return True
