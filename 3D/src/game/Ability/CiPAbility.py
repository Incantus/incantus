from game.pydispatch import dispatcher
from game.GameEvent import TimestepEvent
from game.CardRoles import Permanent
from EffectsUtilities import do_override, do_replace, do_all, role_method
from StaticAbility import SimpleStaticAbility

class CiPAbility(SimpleStaticAbility):
    def __init__(self, effects, txt='', keyword=''):
        super(CiPAbility, self).__init__(effects, zone="all", txt=txt, keyword=keyword)
    def copy(self): return self.__class__(self.effect_generator, self.txt, self.keyword)

def attach_on_enter():
    attaching_to = [None]
    def before(source):
        # Ask to select target
        if source.attach_on_enter:
            card = source.attach_on_enter
        else:
            if not source.target_zone == "play": where = " in %s"%source.target_zone
            else: where = ''
            # XXX Need to make sure there is a valid attachment
            card = source.controller.getTarget(source.target_type, zone=source.target_zone, required=False, prompt="Select %s%s to attach %s"%(source.target_type, where, source))
        if card:
            attaching_to[0] = card
            return True
        else: return False
    def during(self):
        self.attach(attaching_to[0])
    def effects(source):
        yield CiP(source, during, before=before, txt="Attach to card")
    return CiPAbility(effects, txt="")

def comes_into_play_tapped(txt):
    def effects(source):
        yield CiP(source, enter_play_tapped, no_before, txt=txt)
    return CiPAbility(effects, txt=txt)

# Comes into play functionality
def enter_play_tapped(self):
    '''Card comes into play tapped'''
    self.tapped = True

@role_method
def move_to_play_tapped(card, txt):
    expire = CiP(card, enter_play_tapped, txt=txt)
    card.move_to("play")
    expire()

no_before = lambda source: True
def CiP(obj, during, before=no_before, condition=None, txt=''):
    if not txt and hasattr(during, "__doc__"): msg = during.__doc__
    else: msg = txt

    def move_to(self, zone, position="top"):
        # Now move to play
        if before(self):
            perm = self.move_to(zone, position)
            # At this point the card hasn't actually moved (it will on the next timestep event), so we can modify it's enteringZone function. This basically relies on the fact that entering play is batched and done on the timestep.
            if isinstance(perm, Permanent):
                remove_entering = do_override(perm, "modifyEntering", lambda self: during(self), combiner=do_all)
                # XXX There might be timing issue, since we want to remove the override after the card is put into play, but because of ordering the card isn't put into play until the TimestepEvent
                #dispatcher.connect(remove_entering, signal=TimestepEvent(), weak=False, expiry=1)
            return perm
        else:
            # Don't actually move the card
            return self

    play_condition = lambda self, zone, position="top": str(zone) == "play"
    if condition: cond = lambda self, zone, position="top": play_condition(self,zone,position) and condition(self,zone,position)
    else: cond = play_condition

    return do_replace(obj, "move_to", move_to, msg=msg, condition=cond)
