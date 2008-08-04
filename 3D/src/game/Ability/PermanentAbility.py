from Ability import Ability
from ActivatedAbility import ActivatedAbility
from StaticAbility import GlobalStaticAbility
from Effect import RemoveCounter, SacrificeSelf, PayExtraCost, AttachToPermanent, DoOr, ReplacementEffect
from Target import Target
from TriggeredAbility import TriggeredAbility
from Trigger import PlayerTrigger, Trigger
from Counters import Counter
from Limit import ThresholdLimit, SorceryLimit
from game.GameEvent import UpkeepStepEvent, CounterRemovedEvent, EndTurnEvent
from game.Match import SelfMatch, isCreature

class EquipAbility(ActivatedAbility):
    def __init__(self, card, cost="0"):
        super(EquipAbility,self).__init__(card, cost=cost, target=Target(target_types=isCreature), effects=AttachToPermanent(), limit=SorceryLimit(card))

class ThresholdAbility(ActivatedAbility):
    def __init__(self, card, cost="0", target=None, effects=[], copy_targets=True, limit=None, zone="play"):
        if limit: limit += ThresholdLimit(card)
        else: limit = ThresholdLimit(card)
        super(ThresholdAbility,self).__init__(card, cost=cost, target=target, effects=effects, copy_targets=copy_targets, limit=limit, zone=zone)

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

def dredge(out_play_role, card, number):
    def condition(self): 
        return len(self.graveyard) >= number
    def draw(self):
        if self.getIntention("Would you like to dredge %s?"%card, "Dredge %s"%card):
            top_N = self.library.top(number)
            for c in top_N: c.move_to(self.graveyard)
            card.move_to(self.hand)
        else:
            self.draw()

    dredge_ability = GlobalStaticAbility(card,
      effects=ReplacementEffect(draw, "draw", txt='%s - dredge?'%card, expire=False, condition=condition))
    out_play_role.graveyard_abilities.append(dredge_ability)

def suspend(subrole, card, number):
    pass

def echo(permanent, subrole, cost="0"):
    card = permanent.card
    #At the beginning of your upkeep, if this came under your control since the beginning of your last upkeep, sacrifice it unless you pay its echo cost.
    # XXX This doesn't work when the controller is changed
    # need to reset the triggered ability somehow or implement the intervening if properly
    echo_ability = [TriggeredAbility(card,
                       trigger = PlayerTrigger(event=UpkeepStepEvent()),
                       match_condition = lambda player: player == card.controller,
                       ability = Ability(card,
                                        target=Target(targeting="you"),
                                        effects=DoOr(PayExtraCost(cost), failed=SacrificeSelf())),
                       expiry=1)]
    subrole.triggered_abilities.extend(echo_ability)
    return None
