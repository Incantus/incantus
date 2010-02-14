from ActivatedAbility import ActivatedAbility, ManaAbility
from TriggeredAbility import TriggeredAbility
from StaticAbility import *
from CastingAbility import CastInstantSpell, CastSorcerySpell
from Target import NoTarget, Target
from Cost import ManaCost
from CiPAbility import CiP, CiPAbility

__all__ = ["sorcery", "instant", "mana", 
           "activated", "triggered", "static_tracking",
           "static_tracking_conditional", "static",
           "attached", "enters_battlefield"]

# Decorators for effects of cards
def sorcery(txt="Play sorcery"):
    def make_spell(ability):
        effects = ability()
        return CastSorcerySpell(effects, txt=txt)
    return make_spell

def instant(txt="Play instant"):
    def make_spell(ability):
        effects = ability()
        return CastInstantSpell(effects, txt=txt)
    return make_spell

def mana(limit=None, zone='battlefield', txt=''):
    def make_ability(ability):
        effects = ability()
        return ManaAbility(effects, limit, zone, txt)
    return make_ability

def activated(limit=None, zone='battlefield', txt=''):
    def make_ability(ability):
        effects = ability()
        return ActivatedAbility(effects, limit, zone, txt)
    return make_ability

def triggered(zone='battlefield', txt=''):
    def make_triggered(ability):
        triggers, effects = ability()
        return TriggeredAbility(triggers, effects, zone=zone, txt=txt)
    return make_triggered

def static_tracking(events=[], tracking="battlefield", zone="battlefield", txt=''):
    def make_ability(ability):
        condition, effects = ability()
        return CardTrackingAbility(effects, condition, events, tracking, zone, txt)
    return make_ability

def static_tracking_conditional(events=[], tracking="battlefield", zone="battlefield", txt=''):
    def make_ability(ability):
        condition, conditional, effects = ability()
        return ConditionalTrackingAbility(effects, condition, conditional, events, tracking, zone, txt)
    return make_ability

def static(zone="battlefield", txt=''):
    def make_ability(ability):
        condition, effects = ability()
        if condition: return ConditionalStaticAbility(effects, condition, zone, txt)
        else: return CardStaticAbility(effects, zone, txt)
    return make_ability

def attached(zone="attached", txt=''):
    def make_ability(ability):
        condition, effects = ability()
        if condition:
            ability = ConditionalStaticAbility(effects, condition, zone, txt)
        else:
            ability = CardStaticAbility(effects, zone, txt)
        return ability
    return make_ability

def enters_battlefield(txt=''):
    def make_ability(ability):
        before, during = ability()
        def effects(source):
            yield CiP(source, during, before, txt=txt)
        return CiPAbility(effects, txt=txt)
    return make_ability
