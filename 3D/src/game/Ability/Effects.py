from game.pydispatch import dispatcher
from game.CardEnvironment import *
from game.abilities import stacked_abilities

def delay(source, delayed_trigger):
    delayed_trigger.enable(source)
    def expire(): delayed_trigger.disable()
    return expire

def until_end_of_turn(*restores):
    for restore in restores: dispatcher.connect(restore, signal=CleanupEvent(), weak=False, expiry=1)

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
