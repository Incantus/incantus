from EffectsUtilities import do_override, do_replace
from StaticAbility import SimpleStaticAbility

__all__ = ["CiPAbility", "attach_on_enter", "enters_battlefield_with",
            "enters_battlefield_tapped", "enter_tapped", 
            "CiP", "no_before"]

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
            if not source.target_zone == "battlefield": where = " in %s"%source.target_zone
            else: where = ''
            # XXX Need to make sure there is a valid attachment
            card = source.controller.getTarget(source.target_type, zone=source.target_zone, required=False, prompt="Select %s%s to attach %s"%(source.target_type, where, source))
        if card:
            attaching_to[0] = card
            return True
        else: return False
    def during(self):
        self.attach(attaching_to[0], during=True)
    def effects(source):
        yield CiP(source, during, before=before, txt="Attach to card")
    return CiPAbility(effects, txt="")

# Comes onto battlefield functionality
def enters_battlefield_with(func, txt=""):
    def effects(source):
        yield CiP(source, func, no_before, txt=txt)
    return CiPAbility(effects, txt=txt)

def enter_tapped(self):
    '''Enters the battlefield tapped'''
    self.tapped = True

def enters_battlefield_tapped():
    return enters_battlefield_with(enter_tapped, '~ enters the battlefield tapped.')

no_before = lambda source: True
def CiP(obj, during, before=no_before, condition=None, txt=''):
    if not txt and hasattr(during, "__doc__"): msg = during.__doc__
    else: msg = txt

    def move_to(self, zone, position="top"):
        # Now move to the battlefield
        if before(self):
            perm = self.move_to(zone, position)
            # At this point the card hasn't actually moved (it will on the next timestep event), so we can modify it's enteringZone function. This basically relies on the fact that entering battlefield is batched and done on the timestep.
            if not perm == self: # We weren't prevented from moving
                remove_entering = do_override(perm, "modifyEntering", lambda self: during(self))
            return perm
        else:
            # Don't actually move the card
            return self

    battlefield_condition = lambda self, zone, position="top": str(zone) == "battlefield"
    if condition: cond = lambda self, zone, position="top": battlefield_condition(self,zone,position) and condition(self,zone,position)
    else: cond = battlefield_condition

    return do_replace(obj, "move_to", move_to, msg=msg, condition=cond)
