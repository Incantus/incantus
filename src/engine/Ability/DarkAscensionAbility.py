from TriggeredAbility import TriggeredAbility
from Target import NoTarget
from Trigger import EnterFromTrigger, source_match
from Counters import PowerToughnessCounter
from CiPAbility import CiP

__all__ = ["undying"]

def undying():
    def condition(source, card):
        return source_match(source, card) and card.num_counters("+1+1") == 0
    def enterWithCounters(self):
        self.add_counters(PowerToughnessCounter(1, 1))
    def undying_effect(controller, source, card, newcard):
        yield NoTarget()
        if condition(source, card):
            expire = CiP(newcard, enterWithCounters, txt="%s - enter the battlefield with a +1/+1 counter"%newcard)
            newcard.move_to("battlefield")
            expire()
        yield

    return TriggeredAbility(EnterFromTrigger(from_zone="battlefield", to_zone="graveyard", condition=condition),
            effects = undying_effect,
            keyword="undying")
