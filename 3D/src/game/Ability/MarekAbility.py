from game.Match import isCard, isCreature
from Cost import ManaCost
from TriggeredAbility import TriggeredAbility
from Trigger import EnterFromTrigger
from Target import Target, NoTarget

def recover(cost):
    if type(cost) == str: cost = ManaCost(cost)
    # condition
    def condition(source, card):
        return isCreature(card)
    # effects
    def effects(controller, source):
        target = yield NoTarget()
        # Code for effect
        if controller.you_may_pay(source, cost):
            source.move_to("hand")
        else:
            source.move_to("removed")
        yield
    return TriggeredAbility(EnterFromTrigger("graveyard", "play", player="you"),
            condition=condition,
            effects=effects,
            zone="graveyard",
            txt="Recover %s"%cost)

def soulshift(n):
    def effects(source):
        target = yield Target(isCard.with_condition(lambda c: c.subtypes == "Spirit" and c.cost
.converted_mana_cost() <= 3), zone = "graveyard", player = "you")
        # Code for effect
        if controller.you_may("return target to your hand"):
            target.move_to("hand")
        yield
    return TriggeredAbility(EnterFromTrigger("graveyard", "play", player="you"),
            condition=condition,
            effects=effects,
            txt="Soulshift %s"%n)
