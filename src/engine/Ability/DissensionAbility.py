from Counters import PowerToughnessCounter
from CiPAbility import CiP, CiPAbility
from TriggeredAbility import TriggeredAbility
from Target import NoTarget
from Trigger import EnterTrigger
from engine.Match import isCreature

__all__ = ["graft"]

def graft(value):
    txt = "Graft %d"%value
    def enterBattlefieldWith(self):
        self.add_counters(PowerToughnessCounter(1,1), number=value)
    def graft_1(source):
        yield CiP(source, enterBattlefieldWith, txt=txt)
    graft_CiP = CiPAbility(graft_1, txt=txt, keyword='graft')

    def condition(source, card):
        return isCreature(card) and not source == card and source.num_counters("+1+1") > 0
    def graft_2(controller, source, card):
        yield NoTarget()
        if source.num_counters("+1+1") > 0:
            if controller.you_may("move a +1/+1 counter from %s to %s"%(source, card)):
                source.remove_counters("+1+1")
                card.add_counters(PowerToughnessCounter(1,1))
        yield
    graft_Triggered = TriggeredAbility(EnterTrigger("battlefield", condition, player="any"),
            effects=graft_2,
            txt=txt)
    return graft_CiP, graft_Triggered
