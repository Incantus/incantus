from Ability import Ability
from StaticAbility import GlobalStaticAbility, CardStaticAbility
from TriggeredAbility import TriggeredAbility
from Target import Target
from game.Match import SelfMatch
from game.GameEvent import CounterAddedEvent, ReceivesDamageEvent
from game.CardRoles import Creature
from Trigger import EnterFromTrigger
from Effect import MultipleEffects, ChangeZoneToPlay, AddPowerToughnessCounter, OverrideGlobal, GiveKeyword
from Counters import PowerToughnessCounter
from game.stacked_function import logical_and

def persist(card):
    return TriggeredAbility(card, trigger = EnterFromTrigger(from_zone="play", to_zone="graveyard"),
            match_condition=SelfMatch(card, condition=lambda card: not any([True for counter in card.counters if counter.ctype == "-1-1"])),
            ability=Ability(card, target=Target(targeting="self"),
                effects=MultipleEffects(ChangeZoneToPlay("graveyard"), AddPowerToughnessCounter(-1,-1))),
            txt="persist")

def wither(card):
    keyword = "wither"
    return CardStaticAbility(card, effects=GiveKeyword(keyword), zone="all", txt=keyword)

def wither_as_override(card):
    # This doesn't let me return the amount of damage done, since the override code uses the return value
    # to indicate whether to process further overrides
    def assignWither(self, amt, source, combat=False):
        continue_chain = True
        if source == card:
            for counter in [PowerToughnessCounter(-1, -1) for i in range(amt)]:
                self.card.counters.append(counter)
                self.send(CounterAddedEvent(), counter=counter)
            self.send(ReceivesDamageEvent(), source=source, amount=amt)
            continue_chain = False
        return continue_chain
    return GlobalStaticAbility(card,
            effects=OverrideGlobal(assignWither, "assignDamage", Creature, combiner=logical_and, expire=False), txt="wither")
