from characteristics import characteristic, all_characteristics, no_characteristic, additional_characteristic
from stacked_function import override, replace, logical_or, logical_and
from Player import Player
from GameKeeper import Keeper
from CardRoles import *
from Planeswalker import Planeswalker
from Match import *
from LazyInt import LazyInt, X
from GameEvent import *

from Ability.ActivatedAbility import ActivatedAbility, ManaAbility
from Ability.TriggeredAbility import TriggeredAbility
from Ability.StaticAbility import *
from Ability.CastingAbility import *
from Ability.Target import *
from Ability.Trigger import *
from Ability.Cost import *
from Ability.Counters import *
from Ability.Effects import *
#from Ability.CreatureAbility import *
#from Ability.PermanentAbility import *
#from Ability.CyclingAbility import *
#from Ability.LorwynAbility import *
#from Ability.MorningtideAbility import *
#from Ability.ShadowmoorAbility import *
#from Ability.EventideAbility import *
from Ability.MemoryVariable import *

damage_tracker = DamageTrackingVariable()
graveyard_tracker = ZoneMoveVariable(from_zone="play", to_zone="graveyard")

def play_permanent(cost):
    global play_spell
    if type(cost) == str: cost = ManaCost(cost)
    def effects(source):
        yield cost
        yield NoTarget()
        yield
    return CastPermanentSpell(effects, txt="Play spell")

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
        def modal_effects(source):
            indices = source.controller.getSelection([(mode.__doc__,i) for i, mode in enumerate(modes)], choose, idx=False, msg='Select %d mode(s):'%choose)
            if hasattr(indices, "__len__"): chosen = tuple((modes[i](source) for i in indices))
            else: chosen = (modes[indices](source), )
            # get the costs
            costs = tuple((mode.next() for mode in chosen))
            payment = yield effects(source).next()

            # get the targets
            targets = yield tuple((mode.send(payment) for mode in chosen))
            if not hasattr(targets, "__len__"): targets = (targets, )
            yield tuple((mode.send(t) for t, mode in zip(targets, chosen)))

        return modal_effects
    return make_modal

def modal_triggered(*modes, **kw):
    choose = kw['choose']
    def make_modal(effects):
        def modal_effects(source):
            indices = source.controller.getSelection([(mode.__doc__,i) for i, mode in enumerate(modes)], choose, idx=False, msg='Select %d mode(s):'%choose)
            if hasattr(indices, "__len__"): chosen = tuple((modes[i](source) for i in indices))
            else: chosen = (modes[indices](source), )
            # get the targets
            targets = yield tuple((mode.next() for mode in chosen))
            if not hasattr(targets, "__len__"): targets = (targets, )
            yield tuple((mode.send(t) for t, mode in zip(targets, chosen)))

        return modal_effects
    return make_modal

def mana(limit=None, zone='play', txt=''):
    def make_ability(effects):
        return ManaAbility(effects, limit, zone, txt)
    return make_ability

def activated(limit=None, zone='play', txt=''):
    def make_ability(effects):
       return ActivatedAbility(effects, limit, zone, txt)
    return make_ability

def triggered(triggers, expiry=-1, zone="play", txt=''):
    if not (type(triggers) == list or type(triggers) == tuple): triggers=[triggers]
    def make_triggered(ability):
        condition, effects = ability()
        return TriggeredAbility(triggers, condition, effects, expiry, zone, txt)
    return make_triggered

def static_tracking(events=[], tracking="play", zone="play", txt=''):
    def make_ability(ability):
        condition, effects = ability()
        return CardTrackingAbility(effects, condition, events, tracking, zone, txt)
    return make_ability
