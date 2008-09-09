from characteristics import characteristic, all_characteristics, no_characteristic, additional_characteristic
from stacked_function import override, replace, logical_or, logical_and, do_all
from Player import Player
from GameKeeper import Keeper
#from Planeswalker import Planeswalker
from Match import *
from LazyInt import LazyInt
from GameEvent import *

from Ability.ActivatedAbility import ActivatedAbility, ManaAbility
from Ability.TriggeredAbility import TriggeredAbility
from Ability.StaticAbility import *
from Ability.CastingAbility import *
from Ability.Target import *
from Ability.Trigger import *
from Ability.Cost import *
from Ability.Counters import *
from Ability.Limit import *
from Ability.Effects import *
from Ability.MemoryVariable import *

from Ability.CreatureAbility import *
#from Ability.PermanentAbility import *
#from Ability.CyclingAbility import *
#from Ability.LorwynAbility import *
#from Ability.MorningtideAbility import *
from Ability.ShadowmoorAbility import *
from Ability.EventideAbility import *

damage_tracker = DamageTrackingVariable()
graveyard_tracker = ZoneMoveVariable(from_zone="play", to_zone="graveyard")
nan = float("NaN")

def play_permanent(cost):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        yield cost
        yield NoTarget()
        yield
    return CastPermanentSpell(effects, txt="Play spell")

def play_aura(cost, target_type):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        yield cost
        target = yield Target(target_type)
        yield
    return EnchantAbility(effects, target_type, txt="Enchant %s"%target_type)

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

# Decorators for effects of cards
def play_sorcery():
    def make_spell(effects):
        global play_spell
        return CastSorcerySpell(effects, txt="Play spell")
    return make_spell

def play_instant():
    def make_spell(effects):
        return CastInstantSpell(effects, txt="Play spell")
    return make_spell

def modal(*modes, **kw):
    choose = kw['choose']
    def make_modal(effects):
        def modal_effects(controller, source):
            indices = controller.getSelection([(mode.__doc__,i) for i, mode in enumerate(modes)], choose, idx=False, msg='Select %d mode(s):'%choose)
            if hasattr(indices, "__len__"): chosen = tuple((modes[i](controller, source) for i in indices))
            else: chosen = (modes[indices](source), )
            # get the costs
            costs = tuple((mode.next() for mode in chosen))
            payment = yield effects(controller, source).next()

            # get the targets
            targets = yield tuple((mode.send(payment) for mode in chosen))
            if not hasattr(targets, "__len__"): targets = (targets, )
            yield tuple((mode.send(t) for t, mode in zip(targets, chosen)))

        return modal_effects
    return make_modal

def modal_triggered(*modes, **kw):
    choose = kw['choose']
    def make_modal(effects):
        def modal_effects(controller, source):
            indices = controller.getSelection([(mode.__doc__,i) for i, mode in enumerate(modes)], choose, idx=False, msg='Select %d mode(s):'%choose)
            if hasattr(indices, "__len__"): chosen = tuple((modes[i](controller, source) for i in indices))
            else: chosen = (modes[indices](source), )
            # get the targets
            targets = yield tuple((mode.next() for mode in chosen))
            if not hasattr(targets, "__len__"): targets = (targets, )
            yield tuple((mode.send(t) for t, mode in zip(targets, chosen)))

        return modal_effects
    return make_modal

def mana(limit=None, zone='play', txt=''):
    def make_ability(ability):
        effects = ability()
        return ManaAbility(effects, limit, zone, txt)
    return make_ability

def activated(limit=None, zone='play', txt=''):
    def make_ability(ability):
        effects = ability()
        return ActivatedAbility(effects, limit, zone, txt)
    return make_ability

def triggered(triggers, expiry=-1, zone="play", txt=''):
    def make_triggered(ability):
        condition, effects = ability()
        return TriggeredAbility(triggers, condition, effects, expiry, zone, txt)
    return make_triggered

delayed_trigger = triggered

def static_tracking(events=[], tracking="play", zone="play", txt=''):
    def make_ability(ability):
        condition, effects = ability()
        return CardTrackingAbility(effects, condition, events, tracking, zone, txt)
    return make_ability

no_condition = None

def static(zone="play", txt=''):
    def make_ability(ability):
        condition, effects = ability()
        if condition: return ConditionalStaticAbility(effects, condition, zone, txt)
        else: return CardStaticAbility(effects, zone, txt)
    return make_ability

def attached(zone="attached", txt=''):
    def make_ability(ability):
        condition, effects = ability()
        if condition: return ConditionalAttachedAbility(effects, condition, zone, txt)
        else: return AttachedAbility(effects, zone, txt)
    return make_ability

no_before = lambda source: None
def comes_into_play(txt=''):
    def make_ability(ability):
        def effects(source):
            yield CiP(source, ability, txt=txt)
        return CardStaticAbility(effects, zone="all", txt=txt)
    return make_ability

def CiP(obj, ability, condition=None, txt=''):
    before, during = ability()
    if not txt and hasattr(during, "__doc__"): msg = during.__doc__
    else: msg = txt
    def move_to(self, zone, position="top"):
        # Add the entering function to the in_play_role
        remove_entering = override(self.in_play_role, "enteringZone", lambda self, zone: during(self), combiner=do_all)
        # Now move to play
        before(self)
        print "Moving %s with %s"%(self, msg)
        self.move_to(zone, position)
        # Remove the entering function from the in_play_role
        # XXX There might be timing issue, since we want to remove the override after the card is put into play
        dispatcher.connect(remove_entering, signal=TimestepEvent(), weak=False)
    play_condition = lambda self, zone, position="top": str(zone) == "play"
    if condition: cond = lambda self, zone, position="top": play_condition(self,zone,position) and condition(self,zone,position)
    else: cond = play_condition

    return replace(obj, "move_to", move_to, msg=msg, condition=cond)
