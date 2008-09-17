from TriggeredAbility import TriggeredAbility, source_match
from StaticAbility import CardStaticAbility
from Target import NoTarget
from Trigger import EnterFromTrigger
from Counters import PowerToughnessCounter
from CreatureAbility import keyword_effect
from PermanentAbility import CiP

def persist():
    def condition(source, card):
        return source_match(source, card) and card.num_counters("-1-1") == 0
    def enterWithCounters(self):
        print repr(self)
        self.add_counters(PowerToughnessCounter(-1, -1))
        print self._counters
    def persist_effect(controller, source, card):
        yield NoTarget()
        print repr(source), repr(card), condition(source, card), source.is_LKI
        # XXX this is broken because the source/card is LKI and can't move
        if condition(source, card):
            expire = CiP(source, enterWithCounters, txt='%s - enter play with a -1/-1 counter')
            # Now move to play
            source._cardtmpl.move_to(source.owner.play)
            expire()
        yield

    return TriggeredAbility(EnterFromTrigger(from_zone="play", to_zone="graveyard"),
            condition = condition,
            effects = persist_effect,
            keyword="persist")

def wither(): return CardStaticAbility(effects=keyword_effect, zone="all", keyword="wither")

# XXX
#from game.GameEvent import CounterAddedEvent, ReceivesDamageFromEvent
#from game.CardRoles import Creature
#from game.stacked_function import logical_and
#def wither_as_override(card):
#    # This doesn't let me return the amount of damage done, since the override code uses the return value
#    # to indicate whether to process further overrides
#    def assignWither(self, amt, source, combat=False):
#        continue_chain = True
#        if source == card:
#            self.perm.add_counters(PowerToughnessCounter(-1, -1), amt)
#            self.send(ReceivesDamageEvent(), source=source, amount=amt)
#            continue_chain = False
#        return continue_chain
#    return GlobalStaticAbility(card,
#            effects=OverrideGlobal(assignWither, "assignDamage", Creature, combiner=logical_and, expire=False), txt="wither")
