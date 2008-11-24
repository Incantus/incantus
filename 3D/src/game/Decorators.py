from Ability.ActivatedAbility import ActivatedAbility, ManaAbility
from Ability.TriggeredAbility import TriggeredAbility
from Ability.StaticAbility import CardStaticAbility, ConditionalStaticAbility, CardTrackingAbility, CiPAbility
from Ability.CastingAbility import CastPermanentSpell, CastInstantSpell, CastSorcerySpell
from Ability.Target import NoTarget, Target
from Ability.Cost import ManaCost
from Ability.PermanentAbility import CiP
from Ability.EffectsUtilities import robustApply

def play_permanent(cost):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        yield cost
        yield NoTarget()
        yield
    return CastPermanentSpell(effects, txt="Play spell")

def play_aura(cost):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        yield cost
        target = yield Target(source.target_type, zone=source.target_zone)
        source._attaching_to = target
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
            indices = controller.getSelection([(mode.__doc__,i) for i, mode in enumerate(modes)], choose, idx=False, msg='Select %d mode(s):'%choose)
            if hasattr(indices, "__len__"): chosen = tuple((modes[i](controller, source) for i in indices))
            else: chosen = (modes[indices](controller, source), )
            # get the costs
            costs = tuple((mode.next() for mode in chosen))
            payment = yield effects(controller, source).next()

            # get the targets
            targets = yield tuple((mode.send(payment) for mode in chosen))
            if not hasattr(targets, "__len__"): targets = (targets, )
            yield tuple((mode.send(t) for t, mode in zip(targets, chosen)))

        return modal_effects
    return make_modal

def modal_triggered_effects(*modes, **kw):
    choose = kw['choose']
    def modal_effects(**keys):
        controller = keys['controller']
        source = keys['source']
        indices = controller.getSelection([(mode.__doc__,i) for i, mode in enumerate(modes)], choose, idx=False, msg='Select %d mode(s):'%choose)
        if hasattr(indices, "__len__"): chosen = tuple((robustApply(modes[i], **keys) for i in indices))
        else: chosen = (robustApply(modes[indices], **keys), )
        # get the targets
        targets = yield tuple((mode.next() for mode in chosen))
        if not hasattr(targets, "__len__"): targets = (targets, )
        yield tuple((mode.send(t) for t, mode in zip(targets, chosen)))

    return modal_effects

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

def attached(zone="attached", txt=''):
    return static(zone, txt)

def comes_into_play(txt=''):
    def make_ability(ability):
        before, during = ability()
        def effects(source):
            yield CiP(source, during, before, txt=txt)
        return CiPAbility(effects, txt=txt)
    return make_ability
