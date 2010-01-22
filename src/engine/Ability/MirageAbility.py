from StaticAbility import CardStaticAbility
from EffectsUtilities import do_override

__all__ = ["flash"]

def flash():
    def timing(self):
        return True
    def effects(source):
        yield do_override(source, "_playable_timing", timing)
    return CardStaticAbility(effects, keyword="flash", zone="non-battlefield")

