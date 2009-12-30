from engine.Match import isCreature
from TriggeredAbility import TriggeredAbility
from Target import NoTarget
from Trigger import EnterFromTrigger

def recover(cost):
    def condition(source, card):
        return isCreature(card)

    def effects(controller, source):
        target = yield NoTarget()
        if controller.you_may_pay(source, cost):
            source.move_to("hand")
        else:
            source.move_to("exile")
        yield

    return TriggeredAbility(EnterFromTrigger("graveyard", "play", player="you"),
            condition=condition,
            effects=effects,
            zone="graveyard",
            txt="Recover %s"%cost,
            keyword="recover")
