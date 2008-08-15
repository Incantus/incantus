from game.pydispatch import dispatcher
from game.CardEnvironment import *
from game.abilities import stacked_abilities

def until_end_of_turn(restore):
    dispatcher.connect(restore, signal=CleanupEvent(), weak=False, expiry=1)
    return restore

def change_controller(target, new_controller):
    if not isPlayer(new_controller): raise Exception()
    if not isPermanent(target): raise Exception()
    old_controller, target.controller = target.controller, new_controller
    def restore():
        if str(target.zone) == "play": target.controller = old_controller
    return restore

def add_mana(player, amount):
    if not isPlayer(player): raise Exception()
    # XXX Do some sanity checking
    if type(amount) == tuple: amount = amount[0]
    player.manapool.add(amount)

def augment_power_toughness(target, power, toughness):
    PT = PowerToughnessModifier(power, toughness)
    return target.PT_other_modifiers.add(PT)
def augment_power_toughness_static(target, power, toughness):
    PT = PowerToughnessModifier(power, toughness)
    return target.PT_static_modifiers.add(PT)
def set_power_toughness(target, power, toughness):
    PT = PowerToughnessSetter(power, toughness)
    return target.PT_other_modifiers.add(PT)
def set_power(target, power):
    PT = PowerSetter(power, None)
    return target.PT_other_modifiers.add(PT)
def set_toughness(target, toughness):
    PT = ToughnessSetter(None, toughness)
    return target.PT_other_modifiers.add(PT)
def switch_power_toughness(target):
    PT = PowerToughnessSwitcher()
    return target.PT_switch_modifiers.add(PT)

def add_activated(target, effects, is_mana=False):
    if not hasattr(target.abilities, "stacked"): stacked_ability = stacked_abilities(target)
    else: stacked_ability = target.abilities
    if not is_mana: ability_cls = ActivatedAbility
    else: ability_cls = ManaAbility
    return stacked_ability.add_abilities(ability_cls(target, effects))
