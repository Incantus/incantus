from CiPAbility import CiP, CiPAbility
from TriggeredAbility import TriggeredAbility
from Target import NoTarget
from Trigger import Trigger, PhaseTrigger
from engine.GameEvent import UpkeepStepEvent, CounterRemovedEvent

__all__ = ["vanishing"]

# Thanks to Ozin for writing the base code here; I just fixed it up slightly
# to better match proper templating. -MageKing17

def vanishing(value=None):
    if value:
        txt = "Vanishing %d"%value
        def enterBattlefieldWith(self):
            self.add_counters('time', value)
        def vanishing_1(source):
            yield CiP(source, enterBattlefieldWith, txt=txt)
        vanishing_CiP = CiPAbility(vanishing_1, txt=txt, keyword='vanishing')
    def condition_2(source, player):
        return player == source.controller and source.num_counters("time") > 0
    def vanishing_2(controller, source):
        target = yield NoTarget()
        source.remove_counters("time")
        yield
    vanishing_Triggered_1 = TriggeredAbility(PhaseTrigger(UpkeepStepEvent(), condition=condition_2), effects=vanishing_2, txt="At the beginning of your upkeep, if this permanent has a time counter on it, remove a time counter from it.")
    def condition_3(source, sender, counter):
        return source == sender and counter.ctype == "time" and source.num_counters("time") == 0
    def vanishing_3(controller, source):
        target = yield NoTarget()
        controller.sacrifice(source)
        yield
    vanishing_Triggered_2 = TriggeredAbility(Trigger(CounterRemovedEvent(), condition=condition_3), effects=vanishing_3, txt="When the last time counter is removed from this permanent, sacrifice it.")
    if value: return vanishing_CiP, vanishing_Triggered_1, vanishing_Triggered_2
    else: return vanishing_Triggered_1, vanishing_Triggered_2
