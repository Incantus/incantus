from game.GameObjects import MtGObject
from game.Match import SelfMatch

# Triggered abilities don't have costs, and only come into play when the card is in play
class TriggeredAbility(MtGObject):
    def __init__(self, card, trigger, match_condition, ability, always_on=False, expiry=-1):
        self.card = card
        self.trigger = trigger
        self.match_condition = match_condition
        self.ability = ability
        self.expiry = expiry
        # If the card is tracking something while it is outside of play then it should always be on
        # Maybe I could have a graveyard/removed role (since that's the only other time it could track something)
        # Actually, not true - since prowl can be triggered while in hand
        self.always_on = always_on
        if self.always_on: self.trigger.setup_trigger(self,self.playAbility,self.match_condition,self.expiry)
    #def can_be_countered(self):
    #    return False
    def enteringPlay(self):
        if not self.always_on:
            self.trigger.setup_trigger(self,self.playAbility,self.match_condition,self.expiry)
    def leavingPlay(self):
        if not self.always_on:
            self.trigger.clear_trigger(wait=True)
    def playAbility(self, trigger=None): # We don't care about the trigger
        Play(self.card, self.ability.copy())
    def copy(self):
        ability = self.ability.copy()
        return TriggeredAbility(self.card, self.trigger, self.match_condition, ability, self.always_on)

def Play(card, ability):
    # This is identical to Action.PlaySpell - there's probably a way to combine them
    ability.controller = card.controller
    if ability.needs_stack(): ability.controller.stack.add_triggered(ability)
    else: ability.controller.stack.stackless(ability)
    return True
