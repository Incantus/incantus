from Ability import Ability
from ActivatedAbility import DoOrAbility
from Effect import RemoveCounter, SacrificeSelf, TriggerEffect, PayExtraCost
from Target import Target
from TriggeredAbility import TriggeredAbility
from Trigger import PlayerTrigger, Trigger
from Counters import Counter
from game.GameEvent import UpkeepStepEvent, CounterRemovedEvent, EndTurnEvent
from game.Match import SelfMatch

def vanishing(permanent, subrole, number):
    card = permanent.card
    for i in range(number): permanent.counters.append(Counter("time"))
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

def echo(permanent, subrole, cost="0"):
    card = permanent.card
    #At the beginning of your upkeep, if this came under your control since the beginning of your last upkeep, sacrifice it unless you pay its echo cost.
    echo_ability = [TriggeredAbility(card,
                       trigger = PlayerTrigger(event=UpkeepStepEvent()),
                       match_condition = lambda player: player == card.controller,
                       ability = DoOrAbility(card, cost="0",
                                        target=Target(targeting="controller"),
                                        failure_target=Target(targeting="controller"),
                                        effects=PayExtraCost(cost),
                                        failed=SacrificeSelf()),
                       expiry=1)]
    subrole.triggered_abilities.extend(echo_ability)
    return None
