from engine.Match import isCard, isCreature, isLand, isPermanent
from engine.GameEvent import UntapStepEvent, UpkeepStepEvent
from engine.CardRoles import permanent_method
from ActivatedAbility import ActivatedAbility
from StaticAbility import CardStaticAbility
from Target import NoTarget, Target
from Trigger import PhaseTrigger
from EffectsUtilities import do_override, override_effect, do_when, combine
from Limit import no_limit, sorcery_limit
from Cost import ManaCost

__all__ = ["attach_artifact", "equip", "fortify", "enchant",
           "optionally_untap", "this_card_doesnt_untap",
           "doesnt_untap_controllers_next_untap_step",
           "doesnt_untap_your_next_untap_step",
           "draw_card_next_upkeep",
           "this_card_is_indestructible"]

def attach_artifact(cost, keyword, limit=no_limit):
    if isinstance(cost, str): cost = ManaCost(cost)
    def effects(controller, source):
        yield cost
        target = yield Target(source.target_type, player='you')
        source.attach(target)
        yield
    return ActivatedAbility(effects, limit=limit+sorcery_limit, txt='%s %s'%(keyword, cost), keyword=keyword)

equip = lambda cost, limit=no_limit: attach_artifact(cost, "Equip", limit)
fortify = lambda cost, limit=no_limit: attach_artifact(cost, "Fortify", limit)

def enchant(target_type, zone="battlefield", player=None):
    def effects(source):
        source.target_type = target_type
        source.target_zone = zone
        source.target_player = player
        source.attach_on_enter = None
        yield lambda: None
    return CardStaticAbility(effects, keyword="Enchant %s in %s"%(target_type, zone), zone="all")

# Untapping abilities
@permanent_method
def optionally_untap(target):
    return do_override(target, "canUntapDuringUntapStep", 
            lambda self: self.canUntap() and self.controller.getIntention("Untap %s"%self))
@permanent_method
def doesnt_untap_controllers_next_untap_step(target):
    def canUntap(self):
        canUntap.expire()
        return False
    do_override(target, "canUntapDuringUntapStep", canUntap)
@permanent_method
def doesnt_untap_your_next_untap_step(target):
    # This is different than doesnt_untap_controllers_next_untap_step because it specifies
    # YOU, not controller
    # So we don't set it up until the start of your turn, after which it will expire
    controller = target.controller # save the current controller
    def canUntap(self):
        canUntap.expire()
        return False
    do_when(lambda: do_override(target, "canUntapDuringUntapStep", canUntap), UntapStepEvent(), lambda player: player==controller)

def this_card_doesnt_untap():
    return CardStaticAbility(effects=override_effect("canUntapDuringUntapStep", lambda self: False), txt="~ doesn't untap during your untap step.")

# draw a card at the beginning of the next turn's upkeep
def draw_card_next_upkeep():
    def effects(controller, source):
        '''Draw a card at the beginning of the next turn's upkeep'''
        target = yield NoTarget()
        controller.draw(1)
        yield
    return PhaseTrigger(UpkeepStepEvent()), effects

@permanent_method
def indestructible(target):
    def shouldDestroy(self): return False
    def destroy(self, regenerate=True): return False
    return combine(do_override(target, "shouldDestroy", shouldDestroy), do_override(target, "destroy", destroy))

def this_card_is_indestructible():
    def indestructible_effect(target):
        yield target.indestructible()
    return CardStaticAbility(effects=indestructible_effect, txt="~ is indestructible.")

#class ThresholdAbility(ActivatedAbility):
#    def __init__(self, card, cost="0", target=None, effects=[], copy_targets=True, limit=None, zone="battlefield"):
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
#    def draw_single(self):
#        if self.getIntention("Would you like to dredge %s?"%card, "Dredge %s"%card):
#            top_N = self.library.top(number)
#            for c in top_N: c.move_to("graveyard")
#            card.move_to("hand")
#        else:
#            self.draw_single()
#
#    dredge_ability = GlobalStaticAbility(card,
#      effects=ReplacementEffect(draw_single, "draw_single", txt='%s - dredge?'%card, expire=False, condition=condition), zone="graveyard")
#    card.abilities.add(dredge_ability)
