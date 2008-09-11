from game.pydispatch import dispatcher
from game.GameEvent import CleanupEvent, TimestepEvent
from game.GameObjects import GameObject
from game.stacked_function import override, replace, do_all
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

def enter_play_tapped(self):
    '''Card comes into play tapped'''
    self.tapped = True

no_before = lambda source: None
def CiP(obj, during, before=no_before, condition=None, txt=''):
    if not txt and hasattr(during, "__doc__"): msg = during.__doc__
    else: msg = txt
    def move_to(self, zone, position="top"):
        # Add the entering function to the in_play_role
        remove_entering = override(self.in_play_role, "enteringZone", lambda self, zone: during(self), combiner=do_all)
        # Now move to play
        before(self)
        print "Moving %s with %s"%(self, msg)
        self.move_to(zone, position)
        # Remove the entering function from the in_play_role
        # XXX There might be timing issue, since we want to remove the override after the card is put into play
        dispatcher.connect(remove_entering, signal=TimestepEvent(), weak=False)
    play_condition = lambda self, zone, position="top": str(zone) == "play"
    if condition: cond = lambda self, zone, position="top": play_condition(self,zone,position) and condition(self,zone,position)
    else: cond = play_condition

    return replace(obj, "move_to", move_to, msg=msg, condition=cond)

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
