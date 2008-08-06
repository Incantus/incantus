from game.GameObjects import MtGObject
from game.Match import SelfMatch

# Triggered abilities don't have costs, and only come into play when the card is in play
class TriggeredAbility(MtGObject):
    def __init__(self, card, trigger, match_condition, ability, expiry=-1):
        self.card = card
        self.trigger = trigger
        self.match_condition = match_condition
        self.ability = ability
        self.expiry = expiry
    #def can_be_countered(self):
    #    return False
    def enteringPlay(self):
        self.trigger.setup_trigger(self,self.playAbility,self.match_condition,self.expiry)
    def leavingPlay(self):
        self.trigger.clear_trigger(wait=False)
    def playAbility(self, trigger=None): # We don't care about the trigger
        Play(self.card, self.ability.copy())
    def copy(self, card=None):
        if not card: card = self.card
        return TriggeredAbility(card, self.trigger.copy(), self.match_condition, self.ability.copy(card))

def Play(card, ability):
    # This is identical to Action.PlaySpell - there's probably a way to combine them
    ability.controller = card.controller
    if ability.needs_stack(): ability.controller.stack.add_triggered(ability)
    else: ability.controller.stack.stackless(ability)
    return True
