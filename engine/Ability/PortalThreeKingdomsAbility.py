from StaticAbility import CardStaticAbility
from engine.GameEvent import DeclareAttackersEvent, NewTurnEvent
from EffectsUtilities import override_effect
from Limit import Limit, TurnLimit

class PortalLimit(TurnLimit):
    def __init__(self):
        self.register(self.attacked, event=DeclareAttackersEvent())
        self.register(self.new_turn, event=NewTurnEvent())
        self.active_player = None
        self.attackers_declared = False
    def attacked(self, sender, attackers):
        self.attackers_declared = True
    def new_turn(self, sender, player):
        self.attackers_declared = False
        self.active_player = player
    def __call__(self, card):
        return (self.active_player == card.controller and not self.attackers_declared)

portal_limit = PortalLimit()

def horsemanship():
    keyword = "horsemanship"
    return CardStaticAbility(effects=override_effect("canBeBlockedBy", lambda self, blocker: keyword in blocker.abilities), keyword=keyword)
