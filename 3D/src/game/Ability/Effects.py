from game.pydispatch import dispatcher
from game.GameEvent import CleanupEvent
from game.GameObjects import GameObject
from game import CardDatabase
from Counters import *

def delay(source, delayed_trigger):
    delayed_trigger.enable(source)
    def expire(): delayed_trigger.disable()
    return expire

def until_end_of_turn(*restores):
    def expire():
        for restore in restores: restore()
    dispatcher.connect(expire, signal=CleanupEvent(), weak=False, expiry=1)

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
    role.cost = obj.base_cost
    reverse = [getattr(role, attr).set_copy(getattr(obj, "base_"+attr)) for attr in ("name", "text", "color", "type", "subtypes", "supertype", "abilities")]
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
    if type(amount) == tuple:
        amount = player.getSelection(amount, 1, prompt="Select mana to add")
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

def add_creature_type(target, power, toughness):
    target.current_role.base_power.cda(0)
    target.current_role.base_toughness.cda(0)
    reverse = [target.type.add("Creature"), set_power_toughness(target, power, toughness)]
    def restore():
        for r in reverse: r()
    return restore
