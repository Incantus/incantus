from game.Match import isCreature
from Cost import ManaCost
from TriggeredAbility import TriggeredAbility
from Target import NoTarget
from Trigger import EnterFromTrigger

def recover(cost):
    if type(cost) == str: cost = ManaCost(cost)
    def condition(source, card):
        return isCreature(card)

    def recover(controller, source):
        target = yield NoTarget()
        if controller.you_may_pay(source, cost):
            source.move_to("hand")
        else:
            source.move_to("removed")
        yield

    return TriggeredAbility(EnterFromTrigger("graveyard", "play", player="you"),
            condition=condition,
            effects=effects,
            zone="graveyard",
            txt="Recover %s"%cost,
            keyword="recover")
