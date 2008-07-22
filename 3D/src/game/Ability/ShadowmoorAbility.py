from Ability import Ability
from TriggeredAbility import TriggeredAbility
from Target import Target
from game.Match import SelfMatch
from Trigger import EnterFromTrigger
from Effect import MultipleEffects, ChangeZoneToPlay, AddPowerToughnessCounter

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
