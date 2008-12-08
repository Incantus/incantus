from ActivatedAbility import ActivatedAbility, ManaAbility
from TriggeredAbility import TriggeredAbility, attached_match
from StaticAbility import *
from CastingAbility import CastPermanentSpell, CastInstantSpell, CastSorcerySpell
from Target import NoTarget, Target
from Cost import ManaCost
from CiPAbility import CiP, CiPAbility
from EffectsUtilities import robustApply

def play_permanent():
    def effects(controller, source):
        yield source.cost
        yield NoTarget()
        yield
    return CastPermanentSpell(effects, txt="Play spell")

def play_aura():
    def effects(controller, source):
        yield source.cost
        target = yield Target(source.target_type, zone=source.target_zone, player=source.target_player)
        source.attach_on_enter = target
        yield
    return CastPermanentSpell(effects)

# Decorators for effects of cards
def play_sorcery():
    def make_spell(effects):
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
            selected = controller.make_selection([(mode.__doc__,mode) for mode in modes], choose, prompt='Select %d mode(s):'%choose)
            if choose > 1: chosen = tuple((mode(controller, source) for mode in selected))
            else: chosen = (selected(controller, source), )
            # get the costs
            costs = tuple((mode.next() for mode in chosen))
            payment = yield effects(controller, source).next()

            # get the targets
            targets = yield tuple((mode.send(payment) for mode in chosen))
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

def static(zone="play", txt=''):
    def make_ability(ability):
        condition, effects = ability()
        if condition: return ConditionalStaticAbility(effects, condition, zone, txt)
        else: return CardStaticAbility(effects, zone, txt)
    return make_ability

def attached(zone="attached", controller_dependent=False, txt=''):
    def make_ability(ability):
        condition, effects = ability()
        if controller_dependent:
            ability = ControllerChangeCardStatic(effects, zone, txt)
        elif condition:
            ability = ConditionalStaticAbility(effects, condition, zone, txt)
        else:
            ability = CardStaticAbility(effects, zone, txt)
        ability.LKI_condition = attached_match
        return ability
    return make_ability

def comes_into_play(txt=''):
    def make_ability(ability):
        before, during = ability()
        def effects(source):
            yield CiP(source, during, before, txt=txt)
        return CiPAbility(effects, txt=txt)
    return make_ability
