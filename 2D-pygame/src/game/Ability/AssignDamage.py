from game.GameEvent import DealsCombatDamageEvent, ReceivesCombatDamageEvent
from game.Match import isPlayer, isCreature
from Ability import Ability

class AssignDamage(Ability):
    def __init__(self, damages, txt = "Combat Damages"):
        self.damages = damages
        self.txt = txt
    def needs_stack(self): return True
    def can_be_countered(self): return False
    def resolve(self):
        # 310.4a Combat damage is dealt as it was originally assigned even if the creature dealing damage is no longer in play, its power has changed, or the creature receiving damage has left combat.
        # 310.4b The source of the combat damage is the creature as it currently exists, if it's still in play. If it's no longer in play, its last known information is used to determine its characteristics.
        # 310.4c If a creature that was supposed to receive combat damage is no longer in play or is no longer a creature, the damage assigned to it isn't dealt.
        for damager, damage_assn in self.damages:
            if damager.canDealDamage():
                for damagee, amt in damage_assn.iteritems():
                    if isPlayer(damagee): damager.dealDamage(damagee, amt, combat=True)
                    elif isCreature(damagee) and damagee.in_combat: damager.dealDamage(damagee, amt, combat=True)
                    if amt > 0:
                        damager.send(DealsCombatDamageEvent(),to=damagee,amount=amt)
                        damagee.send(ReceivesCombatDamageEvent(),source=damager,amount=amt)

            # Each target should trigger if it receives combat damage - handled by the target
            # XXX is this different than other damage?
        return True
    def resolved(self): pass
    def cleanup(self): pass
    def __str__(self):
        return self.txt
