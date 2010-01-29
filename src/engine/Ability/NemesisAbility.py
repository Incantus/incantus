from CiPAbility import CiP, CiPAbility
from TriggeredAbility import TriggeredAbility
from Target import NoTarget
from Trigger import PhaseTrigger
from engine.GameEvent import UpkeepStepEvent

__all__ = ["fading"]

def fading(value):
    txt = "Fading %d"%value
    def enterBattlefieldWith(self):
        self.add_counters('fade', value)
    def fading_1(source):
        yield CiP(source, enterBattlefieldWith, txt=txt)
    fading_CiP = CiPAbility(fading_1, txt=txt, keyword='fading')

    def condition(source, player):
        return player == source.controller
    def fading_2(controller, source, player):
        target = yield NoTarget()
        if source.num_counters("fade") > 0:
            source.remove_counters("fade")
        else:
            controller.sacrifice(source)
        yield
    fading_Triggered = TriggeredAbility(PhaseTrigger(UpkeepStepEvent(),condition=condition),
            effects=fading_2)
    return fading_CiP, fading_Triggered
