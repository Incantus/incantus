from TriggeredAbility import TriggeredAbility, self_condition
from StaticAbility import CardStaticAbility
from Target import NoTarget
from Trigger import EnterFromTrigger
from Counters import PowerToughnessCounter
from CreatureAbility import keyword_effect
from game.stacked_function import override, do_all
from game.pydispatch import dispatcher
from game.GameEvent import TimestepEvent

def persist():
    def condition(source, card):
        return self_condition(source, card) and card.num_counters("-1-1") == 0
    def persist_effect(controller, source, card):
        yield NoTarget()
        if condition(source, card):

            # XXX Fix for LKI
            remove_entering = override(source.in_play_role, "enteringZone", lambda self, zone: self.add_counters(PowerToughnessCounter(-1, -1)), combiner=do_all)
            # Now move to play
            source.move_to(source.owner.play)
            dispatcher.connect(remove_entering, signal=TimestepEvent(), weak=False)
        yield

    return TriggeredAbility(EnterFromTrigger(from_zone="play", to_zone="graveyard"),
            condition = condition,
            effects = persist_effect,
            keyword="persist")

def wither(): return CardStaticAbility(effects=keyword_effect, zone="all", keyword="wither")

# XXX
from game.GameEvent import CounterAddedEvent, ReceivesDamageEvent
from game.CardRoles import Creature
from game.stacked_function import logical_and
def wither_as_override(card):
    # This doesn't let me return the amount of damage done, since the override code uses the return value
    # to indicate whether to process further overrides
    def assignWither(self, amt, source, combat=False):
        continue_chain = True
        if source == card:
            self.perm.add_counters(PowerToughnessCounter(-1, -1), amt)
            self.send(ReceivesDamageEvent(), source=source, amount=amt)
            continue_chain = False
        return continue_chain
    return GlobalStaticAbility(card,
            effects=OverrideGlobal(assignWither, "assignDamage", Creature, combiner=logical_and, expire=False), txt="wither")
