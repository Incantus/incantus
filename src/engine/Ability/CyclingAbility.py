from Cost import ManaCost, Cost
from ActivatedAbility import ActivatedAbility
from engine.Match import isCard, isBasicLandCard
from engine.GameEvent import DiscardCardEvent, CardCycledEvent, TimestepEvent
from engine.symbols import *
from Target import NoTarget

__all__ = ["cycling", "search_cycling", "basic_landcycling", 
            "plains_cycling", "island_cycling", "swamp_cycling",
            "forest_cycling", "mountain_cycling"]

# A bit of a hack, but neccessary to make sure the event gets sent at the right time.
class CycleDiscard(Cost):
    def precompute(self, source, player): return True
    def compute(self, source, player): return str(source.zone) == "hand"
    def pay(self, source, player):
        self.payment = player.discard(source)
        #XXX This is a bit of a hack - i don't like sending a timestep here
        source.send(TimestepEvent())
        if self.payment: self.payment.send(CardCycledEvent())
    def __str__(self): return "Discard this card"

def cycling(cost):
    def effects(controller, source):
        yield cost + CycleDiscard()
        yield NoTarget()
        controller.draw()
        yield
    return ActivatedAbility(effects, zone="hand", txt="Cycling %s"%str(cost), keyword="cycling")

def search_cycling(match, cost, typestr):
    def effects(controller, source):
        yield cost + CycleDiscard()
        yield NoTarget()
        for card in controller.choose_from_zone(number=1, cardtype=match, zone="library", action="put into your hand"):
            controller.reveal_cards(card)
            card.move_to("hand")
        yield
    return ActivatedAbility(effects, zone="hand", txt="%scycling %s"%(typestr, str(cost)), keyword="cycling")

basic_landcycling = lambda cost: search_cycling(isBasicLandCard, cost, "Basic land")

def typecycling(subtype, cost):
    return search_cycling(match=isCard.with_condition(lambda c: c.subtypes == subtype), cost=cost, typestr=subtype)

plains_cycling = lambda cost: typecycling(Plains, cost)
island_cycling = lambda cost: typecycling(Island, cost)
swamp_cycling = lambda cost: typecycling(Swamp, cost)
mountain_cycling = lambda cost: typecycling(Mountain, cost)
forest_cycling = lambda cost: typecycling(Forest, cost)
