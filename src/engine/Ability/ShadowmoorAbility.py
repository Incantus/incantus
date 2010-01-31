from TriggeredAbility import TriggeredAbility
from StaticAbility import CardStaticAbility
from Target import NoTarget
from Trigger import EnterFromTrigger, source_match
from Counters import PowerToughnessCounter
from CreatureAbility import KeywordOnlyAbility
from CiPAbility import CiP

__all__ = ["persist", "wither"]

def persist():
    def condition(source, card):
        return source_match(source, card) and card.num_counters("-1-1") == 0
    def enterWithCounters(self):
        self.add_counters(PowerToughnessCounter(-1, -1))
    def persist_effect(controller, source, card, newcard):
        yield NoTarget()
        if condition(source, card):
            expire = CiP(newcard, enterWithCounters, txt='%s - enter the battlefield with a -1/-1 counter'%newcard)
            # Now move to the battlefield
            newcard.move_to("battlefield")
            expire()
        yield

    return TriggeredAbility(EnterFromTrigger(from_zone="battlefield", to_zone="graveyard", condition = condition),
            effects = persist_effect,
            keyword="persist")

def wither(): return KeywordOnlyAbility("wither")

# XXX
#from engine.GameEvent import CounterAddedEvent
#from engine.CardRoles import Creature
#from engine.stacked_function import logical_and
#def wither_as_override(card):
#    # This doesn't let me return the amount of damage done, since the override code uses the return value
#    # to indicate whether to process further overrides
#    def assignWither(self, amt, source, combat=False):
#        continue_chain = True
#        if source == card:
#            self.perm.add_counters(PowerToughnessCounter(-1, -1), amt)
#            continue_chain = False
#        return continue_chain
#    return GlobalStaticAbility(card,
#            effects=OverrideGlobal(assignWither, "assignDamage", Creature, combiner=logical_and, expire=False), txt="wither")
