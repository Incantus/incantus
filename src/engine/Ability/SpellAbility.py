from StaticAbility import CardStaticAbility
from EffectsUtilities import do_override
from Cost import ManaCost

__all__ = ["additional_cost", "alternative_cost"]

def additional_cost(cost, txt=''):
    if isinstance(cost, str): cost = ManaCost(cost)
    def effects(card):
        yield do_override(card, "_get_additional_costs", lambda self: cost)
    return CardStaticAbility(effects, zone="stack", txt=txt)

def alternative_cost(cost, txt=''):
    if isinstance(cost, str): cost = ManaCost(cost)
    def effects(card):
        yield do_override(card, "_get_alternative_costs", lambda self: [cost])
    return CardStaticAbility(effects, zone="stack", txt=txt)
