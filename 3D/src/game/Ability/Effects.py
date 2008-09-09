from game.pydispatch import dispatcher
from game.CardEnvironment import *
from game.abilities import stacked_abilities
from game.GameObjects import GameObject
from game import CardDatabase

def delay(source, delayed_trigger):
    delayed_trigger.enable(source)
    def expire(): delayed_trigger.disable()
    return expire

def until_end_of_turn(*restores):
    for restore in restores: dispatcher.connect(restore, signal=CleanupEvent(), weak=False, expiry=1)

def clone(card, cloned):
    # XXX This is ugly,
    role = card.current_role
    for subrole in role.subroles: subrole.leavingPlay()
    reverse = CiP_as_cloned(card, cloned)
    for subrole in role.subroles: subrole.enteringPlay(role)
    def reversal():
        for subrole in role.subroles: subrole.leavingPlay()
        reverse()
        for subrole in role.subroles: subrole.enteringPlay(role)
    return reversal

def CiP_as_cloned(card, cloned):
    text = cloned.text
    obj = CardDatabase.execCode(GameObject(card.controller), text)
    role = card.current_role
    role.name = obj.base_name
    role.cost = obj.base_cost
    role.text = obj.base_text
    reverse = [getattr(role, attr).set_copy(getattr(obj, "base_"+attr)) for attr in ("color", "type", "subtypes", "supertype", "abilities")]
    # XXX Instead of this, i should reset the power/toughness value that the creature subrole will refer to
    # That way i keep the same subrole
    role.subroles = obj.in_play_role.subroles
    def reversal():
        role.name = card.base_name
        role.cost = card.base_cost
        role.text = card.base_text
        for r in reverse: r()
        role.subroles = card.in_play_role.subroles
    return reversal

def add_mana(player, amount):
    if not isPlayer(player): raise Exception()
    # XXX fix this to make a selection
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
