from Ability import Ability
from StaticAbility import GlobalStaticAbility
from TriggeredAbility import TriggeredAbility
from Target import Target
from game.Match import SelfMatch
from game.GameEvent import CounterAddedEvent, DealsDamageEvent, ReceivesDamageEvent
from game.CardRoles import Creature
from Trigger import EnterFromTrigger
from Effect import MultipleEffects, ChangeZoneToPlay, AddPowerToughnessCounter, OverrideGlobal
from Counters import PowerToughnessCounter
from game.stacked_function import logical_and

def persist(card):
    card.keywords.add("persist")
    persist = TriggeredAbility(card, trigger = EnterFromTrigger(from_zone="play", to_zone="graveyard"),
            match_condition=SelfMatch(card, condition=lambda card: not any([True for counter in card.counters if counter.ctype == "-1-1"])),
            ability=Ability(card, target=Target(targeting="self"),
                effects=MultipleEffects(ChangeZoneToPlay("graveyard"), AddPowerToughnessCounter(-1,-1))),
            txt="persist")

    remove = card.abilities.add(persist)
    def remove_persist():
        card.keywords.remove("persist")
        remove()
    return remove_persist

def wither(card):
    card.keywords.add("wither")
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
            effects=OverrideGlobal(assignWither, "assignDamage", Creature, combiner=logical_and, expire=False), txt="wither")
    remove = card.abilities.add(wither_damage)
    def remove_wither():
        card.keywords.remove("wither")
        remove()
    return remove_wither
