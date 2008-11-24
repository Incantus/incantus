from Cost import ManaCost, Cost
from ActivatedAbility import ActivatedAbility
from game.Match import isCard
from game.GameEvent import DiscardCardEvent, CardCycledEvent
from Target import NoTarget

# A bit of a hack, but neccessary to make sure the event gets sent at the right time.

class CycleDiscard(Cost):
    def precompute(self, source, player): return True
    def compute(self, source, player): return str(source.zone) == "hand"
    def pay(self, source, player):
        self.payment = player.discard(source)
        if self.payment: self.payment.send(CardCycledEvent())
    def __str__(self): return "Discard this card"

def cycling(cost):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        yield cost + CycleDiscard()
        yield NoTarget()
        controller.draw()
        yield
    return ActivatedAbility(effects, None, "hand", txt="Cycling %s"%str(cost), keyword="cycling")

def typecycling(subtype, cost):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        yield cost + CycleDiscard()
        yield NoTarget()
        for card in controller.choose_from_zone(number=1, cardtype=isCard.with_condition(lambda c: c.subtypes == subtype), zone="library", action=subtype, required=False):
            card.move_to("hand")
        yield
    return ActivatedAbility(effects, None, "hand", txt="%scycling %s"%(subtype, str(cost)), keyword="cycling")

plains_cycling = lambda cost: typecycling("Plains", cost)
island_cycling = lambda cost: typecycling("Island", cost)
swamp_cycling = lambda cost: typecycling("Swamp", cost)
mountain_cycling = lambda cost: typecycling("Mountain", cost)
forest_cycling = lambda cost: typecycling("Forest", cost)
