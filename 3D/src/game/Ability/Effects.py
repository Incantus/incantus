from game.pydispatch import dispatcher
from game.GameEvent import CleanupEvent
from game.GameObjects import GameObject
from game import CardDatabase

def delay(source, delayed_trigger):
    delayed_trigger.enable(source)
    def expire(): delayed_trigger.disable()
    return expire

def combine(*restores):
    def expire():
        for restore in restores: restore()
    return expire

def until_end_of_turn(*restores):
    dispatcher.connect(combine(*restores), signal=CleanupEvent(), weak=False, expiry=1)


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
    reverse = [getattr(role, attr).set_copy(getattr(obj, "base_"+attr)) for attr in ("name", "text", "color", "types", "subtypes", "supertypes", "abilities")]
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
