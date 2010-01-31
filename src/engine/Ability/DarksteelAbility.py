from engine.Match import isArtifactCreature
from TriggeredAbility import TriggeredAbility
from Trigger import EnterFromTrigger, source_match
from Target import Target
from CiPAbility import CiP, CiPAbility
from Counters import PowerToughnessCounter

__all__ = ["modular"]

def modular(n):
    txt = "Modular %d"%n
    def enterBattlefieldWith(self):
        self.add_counters(PowerToughnessCounter(1,1), number=n)
    def effects(source):
        yield CiP(source, enterBattlefieldWith, txt=txt)
    cip = CiPAbility(effects, txt=txt, keyword="modular")

    def effects(controller, source):
        target = yield Target(isArtifactCreature, msg="Target Artifact Creature for %s"%source)
        if controller.you_may("move all +1/+1 counters from %s to target"%source.name):
            target.add_counters(PowerToughnessCounter(1,1), number=source.num_counters("+1+1"))
        yield
    triggered = TriggeredAbility(EnterFromTrigger("graveyard", "battlefield", source_match, player="any"),
            effects=effects,
            txt='')
    return (cip, triggered)
