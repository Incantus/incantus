from game.pydispatch import dispatcher
from game.CardEnvironment import *
from game.characteristics import _find_stacked

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
def set_power(target, toughness):
    PT = ToughnessSetter(None, toughness)
    return target.PT_other_modifiers.add(PT)
def switch_power_toughness(target):
    PT = PowerToughnessSwitcher()
    return target.PT_switch_modifiers.add(PT)

def set_color(target, color):
    characteristic = _find_stacked(target, "color", ColorModifiedEvent())
    return characteristic.set_characteristic(color)

def set_subtype(target, subtype):
    characteristic = _find_stacked(target, "subtypes", SubtypeModifiedEvent())
    return characteristic.set_characteristic(subtype)

def add_counter(): pass
