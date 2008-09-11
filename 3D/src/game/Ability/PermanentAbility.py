#from Ability import Ability
from ActivatedAbility import ManaAbility
#from StaticAbility import GlobalStaticAbility
from Target import NoTarget
from Cost import TapCost
#from TriggeredAbility import TriggeredAbility
#from Trigger import PlayerTrigger, Trigger
#from Counters import Counter
#from Limit import ThresholdLimit, SorceryLimit
#from game.GameEvent import UpkeepStepEvent, CounterRemovedEvent, EndTurnEvent
#from game.Match import SelfMatch, isCreature

def basic_mana_ability(subtype, subtype_to_mana=dict(Forest='G',Island='U',Plains='W',Mountain='R',Swamp='B')):
    color = subtype_to_mana[subtype]
    def effects(controller, source):
        payment = yield TapCost()
        yield NoTarget()
        controller.add_mana(color)
        yield
    return ManaAbility(effects, txt="T: Add %s"%color)

def equip(cost, target_type=isCreature, limit=None, txt=''):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        yield cost
        target = yield Target(target_type)
        source.set_target_type(target_type)
        source.attach(target)
        yield
    if not txt: txt="Equip creature"
    if not limit: limit = SorceryLimit()
    else: limit += SorceryLimit()
    return ActivatedAbility(effects, limit=limit, txt=txt)

#class ThresholdAbility(ActivatedAbility):
#    def __init__(self, card, cost="0", target=None, effects=[], copy_targets=True, limit=None, zone="play"):
#        if limit: limit += ThresholdLimit(card)
#        else: limit = ThresholdLimit(card)
#        super(ThresholdAbility,self).__init__(card, cost=cost, target=target, effects=effects, copy_targets=copy_targets, limit=limit, zone=zone)
#
#def vanishing(card, number):
#    for i in range(number): card.counters.append(Counter("time"))
#    remove_counter = TriggeredAbility(card, trigger=PlayerTrigger(event=UpkeepStepEvent()),
#                        match_condition = lambda player, card=card: player == card.controller,
#                        ability=Ability(card, target=Target(targeting="self"), effects=RemoveCounter("time")))
#    def check_time(sender, counter):
#        counters = [c for c in sender.counters if c == "time"]
#        print sender, counter, len(counters)
#        return sender == card and counter == "time" and len(counters) == 0
#
#    sacrifice = TriggeredAbility(card, trigger=Trigger(event=CounterRemovedEvent()),
#                        match_condition = check_time,
#                        ability=Ability(card, effects=SacrificeSelf()))
#    return card.abilities.add([remove_counter, sacrifice])
#
#def dredge(card, number):
#    condition = lambda self: len(self.graveyard) >= number
#    def draw(self):
#        if self.getIntention("Would you like to dredge %s?"%card, "Dredge %s"%card):
#            top_N = self.library.top(number)
#            for c in top_N: c.move_to(self.graveyard)
#            card.move_to(self.hand)
#        else:
#            self.draw()
#
#    dredge_ability = GlobalStaticAbility(card,
#      effects=ReplacementEffect(draw, "draw", txt='%s - dredge?'%card, expire=False, condition=condition), zone="graveyard")
#    card.abilities.add(dredge_ability)

#def suspend(card, number):
#    pass

#def echo(card, cost="0"):
#    #At the beginning of your upkeep, if this came under your control since the beginning of your last upkeep, sacrifice it unless you pay its echo cost.
#    # XXX This doesn't work when the controller is changed
#    # need to reset the triggered ability somehow or implement the intervening if properly
#    echo_ability = [TriggeredAbility(card,
#                       trigger = PlayerTrigger(event=UpkeepStepEvent()),
#                       match_condition = lambda player: player == card.controller,
#                       ability = Ability(card,
#                                        target=Target(targeting="you"),
#                                        effects=DoOr(PayExtraCost(cost), failed=SacrificeSelf())),
#                       expiry=1)]
#    return card.abilities.add(echo_ability)
