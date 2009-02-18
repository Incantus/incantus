from game.GameObjects import MtGObject
from game.Match import SelfMatch

# Triggered abilities don't have costs, and only come into play when the card is in play
class TriggeredAbility(MtGObject):
    def __init__(self, card, trigger, match_condition, ability, always_on=False):
        self.card = card
        self.trigger = trigger
        self.match_condition = match_condition
        self.ability = ability
        # If the card is tracking something while it is outside of play then it should always be on
        # Maybe I could have a graveyard/removed role (since that's the only other time it could track something)
        self.always_on = always_on
        if self.always_on: self.trigger.setup_trigger(self,self.playAbility,self.match_condition)
    #def can_be_countered(self):
    #    return False
    def enteringPlay(self):
        if not self.always_on:
            self.trigger.setup_trigger(self,self.playAbility,self.match_condition)
    def leavingPlay(self):
        if not self.always_on:
            self.trigger.clear_trigger()
    def playAbility(self, trigger):
        Play(self.card, self.ability.copy())

def Play(card, ability):
    # This is identical to Action.PlaySpell - there's probably a way to combine them
    player = card.controller
    success = True
    if hasattr(ability, "cost"):
        success = ability.compute_cost()
        if success and ability.needs_target(): success = ability.get_target()
        if success: success = ability.pay_cost()
    else:
        if ability.needs_target(): success = ability.get_target()

    if success:
        if ability.needs_stack():
            # Add it to the stack
            card.current_role.onstack = True
            player.stack.add_triggered(ability)
        else:
            ability.played()
            if ability.resolve(): ability.resolved()
            else: ability.countered()
            ability.cleanup()
            del ability
    return success
