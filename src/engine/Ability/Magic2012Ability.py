from StaticAbility import CardStaticAbility
from EffectsUtilities import override_effect

def hexproof():
    keyword = "hexproof"
    def canBeTargetedBy(self, targetter): return not targetter.controller in self.controller.opponents
    return CardStaticAbility(effects=override_effect("canBeTargetedBy", canBeTargetedBy), keyword=keyword)
