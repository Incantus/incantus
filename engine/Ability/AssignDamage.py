from engine.GameEvent import DealsDamageEvent
from engine.Match import isPlayer
from Ability import Ability
from Target import MultipleTargets

class AssignDamage(Ability):
    # XXX These two are very hacky, and are only here to support the GUI
    source = property(fget=lambda self: "Assign Damage")
    def targets():
        def fget(self):
            targets = set()
            for damager, damage_assn in self.damages:
                for d in damage_assn.keys():
                    if not isPlayer(d) and not d.is_LKI: continue
                    targets.add(d)
            target = MultipleTargets(len(targets), None)
            target.target = targets
            return [target]
        return locals()
    targets = property(**targets())


    def __init__(self, damages, txt = "Combat Damages"):
        self.damages = []
        for damager, damage_assn in damages:
            self.damages.append((damager, damage_assn))

        self.txt = txt
    def resolve(self):
        # 310.4a Combat damage is dealt as it was originally assigned even if the creature dealing damage is no longer in play, its power has changed, or the creature receiving damage has left combat.
        # 310.4b The source of the combat damage is the creature as it currently exists, if it's still in play. If it's no longer in play, its last known information is used to determine its characteristics.
        # 310.4c If a creature that was supposed to receive combat damage is no longer in play or is no longer a creature, the damage assigned to it isn't dealt.
        for damager, damage_assn in self.damages:
            total = 0
            for damagee, amt in damage_assn.iteritems():
                total += damager.deal_damage(damagee, amt, combat=True)
    def __str__(self): return self.txt
