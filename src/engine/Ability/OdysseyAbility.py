from StaticAbility import CardStaticAbility
from Cost import ManaCost, SpecialCost
from EffectsUtilities import override, replace

__all__ = ["flashback"]

class FlashbackCost(SpecialCost):
    def __init__(self, cost):
        if isinstance(cost, str): cost = ManaCost(cost)
        self.cost = cost
    def precompute(self, source, player):
        if super(FlashbackCost, self).precompute(source, player):
            source.flashbacked = True
        return source.flashbacked
    def compute(self, source, player):
        source.flashbacked = super(FlashbackCost, self).compute(source, player)
        return source.flashbacked
    def pay(self, source, player):
        super(FlashbackCost, self).pay(source, player)
    def payment(self):
        return self.cost.payment
    payment = property(fget=payment)

def flashback(cost):
    cost = FlashbackCost(cost)
    def flashback_effects(card):
        def modifyNewRole(self, new, zone):
            if str(zone) == "stack":
                new.set_casting_cost(cost)
        def play_from_graveyard(self):
            if self.controller.you_may("Play %s with flashback for %s"%(self, cost)):
                override(self, "modifyNewRole", modifyNewRole)
                return True
            else:
                return False
        yield override(card, "_playable_zone", play_from_graveyard)
    def exile_not_graveyard(card):
        def move_to(self, zone, position="top"):
            return self.move_to("exile")
        yield replace(card, "move_to", move_to, msg="Flashback - Exile this card instead of putting it anywhere else any time it would leave the stack.", condition=lambda self, zone, position="top": not str(zone) == 'exile' and self.flashbacked)
    return CardStaticAbility(effects=flashback_effects, zone="graveyard", txt="Flashback %s"%cost, keyword="flashback"), CardStaticAbility(effects=exile_not_graveyard, zone="stack")

