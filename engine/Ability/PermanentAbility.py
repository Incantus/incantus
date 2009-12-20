from engine.Match import isCard, isCreature, isLand
from engine.symbols import Forest, Island, Plains, Mountain, Swamp
from ActivatedAbility import ActivatedAbility, ManaAbility
from CastingAbility import CastPermanentSpell, CastAuraSpell
from StaticAbility import CardStaticAbility
from Target import NoTarget, Target
from Cost import TapCost
from EffectsUtilities import do_override, override_effect
from Limit import no_limit, sorcery_limit

def basic_mana_ability(subtype, subtype_to_mana=dict(zip([Plains,Island,Swamp,Mountain,Forest], "WUBRG"))):
    color = subtype_to_mana[subtype]
    def effects(controller, source):
        payment = yield TapCost()
        yield NoTarget()
        controller.add_mana(color)
        yield
    return ManaAbility(effects, txt="T: Add %s to your mana pool"%color)

def cast_permanent():
    return CastPermanentSpell()

def cast_aura():
    return CastAuraSpell()

def attach_artifact(cost, keyword, limit=no_limit):
    def effects(controller, source):
        yield cost
        target = yield Target(source.target_type, player='you')
        source.attach(target)
        yield
    return ActivatedAbility(effects, limit=limit+sorcery_limit, txt='%s %s'%(keyword, cost))

equip = lambda cost, limit=no_limit: attach_artifact(cost, "Equip", limit)
fortify = lambda cost, limit=no_limit: attach_artifact(cost, "Fortify", limit)

def enchant(target_type, zone="play", player=None):
    def effects(source):
        source.target_type = target_type
        source.target_zone = zone
        source.target_player = player
        source.attach_on_enter = None
        yield lambda: None
    return CardStaticAbility(effects, keyword="Enchant %s in %s"%(target_type, zone), zone="all")

# Untapping abilities
optionallyUntap = lambda self: self.canUntap() and self.controller.getIntention("Untap %s"%self)
def optionally_untap(target):
    return do_override(target, "canUntapDuringUntapStep", optionallyUntap)
def doesnt_untap_controllers_next_untap_step(target):
    def cantUntap(self):
        cantUntap.expire()
        return False
    return do_override(target, "canUntapDuringUntapStep", cantUntap)
def doesntUntapAbility(txt):
    return CardStaticAbility(effects=override_effect("canUntapDuringUntapStep", lambda self: False), txt=txt)

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

#def suspend(card, number):
#    pass

#def flash(card):
#    casting_ability = card.play_spell
#    if isinstance(casting_ability.limit, SorceryLimit):
#        casting_ability.limit = Unlimited(card)
#    elif isinstance(casting_ability.limit, MultipleLimits):
#        for i, limit in enumerate(casting_ability.limit):
#            if isinstance(limit, SorceryLimit): break
#        casting_ability.limit.limits.pop(i)

def flash():  # Essentially a noop
    def effects(source):
        yield lambda: None
    return CardStaticAbility(effects, keyword="flash", zone="nonplay")

