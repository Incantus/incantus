from engine.symbols import Artifact, Creature
from StaticAbility import CardStaticAbility
from EffectsUtilities import override_effect

def intimidate():
    keyword = "intimidate"
    def canBeBlockedBy(self, blocker):
        return (any([blocker.color == color for color in self.color]) or (blocker.types == Artifact and blocker.types == Creature))
    return CardStaticAbility(effects=override_effect("canBeBlockedBy", canBeBlockedBy), keyword=keyword)
