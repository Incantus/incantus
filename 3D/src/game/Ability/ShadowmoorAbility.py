from Ability import Ability
from StaticAbility import GlobalStaticAbility
from TriggeredAbility import TriggeredAbility
from Target import Target
from game.Match import SelfMatch
from game.GameEvent import CounterAddedEvent
from game.CardRoles import Creature
from Trigger import EnterFromTrigger
from Effect import MultipleEffects, ChangeZoneToPlay, AddPowerToughnessCounter, OverrideGlobal
from Counters import PowerToughnessCounter
from game.stacked_function import logical_and

def persist(subrole, card):
    persist = TriggeredAbility(card, trigger = EnterFromTrigger(from_zone="play", to_zone="graveyard"),
            match_condition=SelfMatch(card, condition=lambda card: not any([True for counter in card.counters if counter.ctype == "-1-1"])),
            ability=Ability(card, target=Target(targeting="self"),
                effects=MultipleEffects(ChangeZoneToPlay("graveyard"), AddPowerToughnessCounter(-1,-1))))

    subrole.triggered_abilities.append(persist)
    def remove_persist():
        persist.leavingPlay()
        subrole.triggered_abilities.remove(persist)
    return remove_persist

def wither(subrole, card):
    subrole.keywords.add("wither")
    return lambda: subrole.keywords.remove("wither")

def wither_orig(subrole, card):
    def assignWither(self, amt, source, combat=False):
        continue_chain = True
        if source == card:
            for counter in [PowerToughnessCounter(-1, -1) for i in range(amt)]:
                self.card.counters.append(counter)
                self.send(CounterAddedEvent(), counter=counter)
                source.send(DealsDamageEvent(), to=self.card, amount=amt)
                self.send(ReceivesDamageEvent(), source=source, amount=amt)
            continue_chain = False
        return continue_chain
    wither_damage = GlobalStaticAbility(card,
            effects=OverrideGlobal(assignWither, "assignDamage", Creature, reverse=True, combiner=logical_and, expire=False))
    subrole.static_abilities.append(wither_damage)

    def remove_wither():
        subrole.static_abilities.remove(wither_damage)
    return remove_wither
