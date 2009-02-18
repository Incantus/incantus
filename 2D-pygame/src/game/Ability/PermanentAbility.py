from Ability import Ability
from Effect import RemoveCounter, SacrificeSelf
from Target import Target
from TriggeredAbility import TriggeredAbility
from Trigger import PlayerTrigger, Trigger
from Counters import Counter
from game.GameEvent import UpkeepStepEvent, CounterRemovedEvent
from game.Match import SelfMatch

def vanishing(subrole, card, number):
    for i in range(number): subrole.counters.append(Counter("time"))
    remove_counter = TriggeredAbility(card, trigger=PlayerTrigger(event=UpkeepStepEvent()),
                        match_condition = lambda player, card=card: player == card.controller,
                        ability=Ability(card, target=Target(targeting="self"), effects=RemoveCounter("time")))
    def check_time(sender, counter):
        counters = [c for c in sender.counters if c == "time"]
        print sender, counter, len(counters)
        return sender == card and counter == "time" and len(counters) == 0
    
    sacrifice = TriggeredAbility(card, trigger=Trigger(event=CounterRemovedEvent()),
                        match_condition = check_time,
                        ability=Ability(card, effects=SacrificeSelf()))
    subrole.triggered_abilities.extend([remove_counter, sacrifice])
    def remove_vanishing():
        remove_counter.leavingPlay()
        sacrifice.leavingPlay()
        subrole.triggered_abilities.remove(remove_counter)
        subrole.triggered_abilities.remove(sacrifice)
    return remove_vanishing

def suspend(subrole, card, number):
    pass
