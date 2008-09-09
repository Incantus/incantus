from Cost import ManaCost, DiscardCost
from ActivatedAbility import ActivatedAbility
from game.Match import isCard
from game.GameEvent import CardCycledEvent
from Target import NoTarget

def cycling(cost):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        yield cost + DiscardCost()
        yield NoTarget()
        controller.draw()
        source.send(CardCycledEvent())
        yield
    return ActivatedAbility(effects, None, "hand", "Cycling %s"%str(cost))

def typecycling(subtype, cost):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        yield cost + DiscardCost()
        yield NoTarget()
        for card in controller.choose_from_zone(number=1, cardtype=isCard.with_condition(lambda c: c.subtypes == subtype), zone="library", action=subtype, required=False):
            card.move_to(card.owner.hand)
            source.send(CardCycledEvent())
        yield
    return ActivatedAbility(effects, None, "hand", "%scycling %s"%(subtype, str(cost)))

plains_cycling = lambda cost: typecycling("Plains", cost)
island_cycling = lambda cost: typecycling("Island", cost)
swamp_cycling = lambda cost: typecycling("Swamp", cost)
mountain_cycling = lambda cost: typecycling("Mountain", cost)
forest_cycling = lambda cost: typecycling("Forest", cost)
