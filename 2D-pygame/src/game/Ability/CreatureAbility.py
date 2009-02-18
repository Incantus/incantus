from game.Match import isPermanent, isCreature, isLand
from game.stacked_function import stacked_function, logical_or, logical_and
from game.LazyInt import LazyInt
from game.characteristics import all_characteristics
import new

def override(subrole, attribute, func, keyword=None, combiner=logical_and):
    if keyword: subrole.keywords.add(keyword)
    orig_func = getattr(subrole, attribute)
    if not hasattr(orig_func, "stacked"):
        stacked_func = stacked_function(orig_func, combiner=combiner)
        setattr(subrole, attribute, stacked_func)
    else: stacked_func = orig_func
    new_func = new.instancemethod(func, subrole, subrole.__class__)
    stacked_func.add_func(new_func)
    def _restore():
        stacked_func.remove_func(new_func)
        #if not stacked_func.stacking():
        #    setattr(subrole, attribute, stacked_func.funcs[0])
        #    del stacked_func
        if keyword: subrole.keywords.remove(keyword)
    return _restore

def landwalk(subrole, landtype):
    keyword = landtype.lower()+"walk"
    def canBeBlocked(self):
        other_play = self.card.controller.opponent.play
        return (len(other_play.get(isLand.with(lambda c: landtype in c.subtypes))) == 0)
    return override(subrole, "canBeBlocked", canBeBlocked, keyword=keyword)

def plainswalk(subrole): return landwalk(subrole, "Plains")
def swampwalk(subrole): return landwalk(subrole, "Swamp")
def forestwalk(subrole): return landwalk(subrole, "Forest")
def islandwalk(subrole): return landwalk(subrole, "Island")
def mountainwalk(subrole): return landwalk(subrole, "Mountain")

def flying(subrole):
    attr = set(["flying", "reach"])
    def canBeBlockedBy(self, blocker):
        return not (len(attr.intersection(blocker.current_role.keywords)) == 0)
    return override(subrole,"canBeBlockedBy",canBeBlockedBy,keyword="flying")

def only_block(subrole, keyword):
    def canBlockAttacker(self, attacker):
        return keyword in attacker.current_role.keywords
    return override(subrole,"canBlockAttacker",canBlockAttacker)

def haste(subrole):
    subrole.keywords.add("haste")
    subrole.continuously_in_play = True
    return lambda: subrole.keywords.remove("haste")

def must_attack(subrole):
    def mustAttack(self): return True
    return override(subrole, "mustAttack", mustAttack, combiner=logical_or)

def defender(subrole):
    def canAttack(self): return False
    return override(subrole, "canAttack", canAttack, keyword="defender")

def shroud(subrole):
    def canBeTargetedBy(self, targetter): return False
    return override(subrole, "canBeTargetedBy", canBeTargetedBy, keyword="shroud")

def reach(subrole):
    subrole.keywords.add("reach")
    return lambda: subrole.keywords.remove("reach")

def double_strike(subrole):
    subrole.keywords.add("double-strike")
    return lambda: subrole.keywords.remove("double-strike")
def first_strike(subrole):
    subrole.keywords.add("first-strike")
    return lambda: subrole.keywords.remove("first-strike")
def trample(subrole):
    subrole.keywords.add("trample")
    return lambda: subrole.keywords.remove("trample")

def vigilance(subrole):
    def setAttacking(self):
        from game.GameEvent import AttackerDeclaredEvent
        self.attacking = True
        self.card.send(AttackerDeclaredEvent())
        return True
    return override(subrole, "setAttacking", setAttacking, keyword="vigilance", combiner=logical_or)
def berserker(subrole):
    def setBlocked(self, blockers):
        from Target import Target
        from Ability import Ability
        from Effect import AugmentPowerToughness
        num = len(blockers)
        target = Target(targeting="self")
        target.get(self.card)
        self.card.controller.stack.push(Ability(self.card, target=target, effects=AugmentPowerToughness(power=num, toughness=num)))
        return True
    return override(subrole, "setBlocked", setBlocked)

# 502.68b If a permanent has multiple instances of lifelink, each triggers separately.
# XXX This is broken with trample, since the trigger only has the last amount of damage done
def lifelink(subrole, in_play=False):
    from Ability import Ability
    from Effect import ChangeLife
    from TriggeredAbility import TriggeredAbility
    from Trigger import DealDamageTrigger
    subrole.keywords.add("lifelink")
    card = subrole.card
    trigger = DealDamageTrigger(sender=card)
    lifelink = TriggeredAbility(card, trigger = trigger,
            match_condition = lambda sender: True,
            ability = Ability(card, effects=ChangeLife(lambda life, t=trigger: life+t.amount)))
    subrole.triggered_abilities.append(lifelink)
    if in_play: lifelink.enteringPlay()
    def remove_lifelink():
        subrole.keywords.remove("lifelink")
        lifelink.leavingPlay()
        subrole.triggered_abilities.remove(lifelink)
    return remove_lifelink

def fear(subrole):
    def canBeBlockedBy(self, blocker):
        return (blocker.color == "B" or (blocker.type == "Artifact" and blocker.type=="Creature"))
    return override(subrole,"canBeBlockedBy",canBeBlockedBy, keyword="fear")

def protection(subrole, attribute_match):
    #subrole.keywords.add("protection")
    # XXX I'm not sure if I should use canBeDamagedBy or assignDamage, since it is a prevention effect
    def canBeDamagedBy(self, damager):
        return not attribute_match(damager)
    def canBeTargetedBy(self, targeter):
        return not attribute_match(targeter)
    def canBeBlockedBy(self, blocker):
        return not attribute_match(blocker)
    remove1 = override(subrole,"canBeDamagedBy", canBeDamagedBy)
    remove2 = override(subrole,"canBeTargetedBy", canBeTargetedBy)
    remove3 = override(subrole,"canBeBlockedBy", canBeBlockedBy)
    def remove_protection():
        for remove in [remove1, remove2, remove3]: remove()
    return remove_protection

protection_from_black = lambda subrole: protection(subrole, attribute_match = lambda other: other.color == "B")
protection_from_blue = lambda subrole: protection(subrole, attribute_match = lambda other: other.color == "U")
protection_from_white = lambda subrole: protection(subrole, attribute_match = lambda other: other.color == "W")
protection_from_red = lambda subrole: protection(subrole, attribute_match = lambda other: other.color == "R")
protection_from_green = lambda subrole: protection(subrole, attribute_match = lambda other: other.color == "G")

# These are additional ones that aren't actually keywords, but the structure is the same
def unblockable(subrole):
    def canBeBlocked(self): return False
    return override(subrole,"canBeBlocked",canBeBlocked)


# XXX The next two don't work with the stacked_functions because they can replace the new function
# with the original within the new function - maybe they don't need to be stacked because they are never
# externally removed, they either expire naturally or from being called
# XXX Actually, they are replacement effects, which are slightly different (since two replacement effects looking
# for the same event can be ordered by the player affected by the event), and usually once one finishes the other won't
# be relevant

#def override(subrole, attribute, func, keyword=None):
#    if keyword: subrole.keywords.add(keyword)
#    orig_func = getattr(subrole, attribute)
#    setattr(subrole, attribute, new.instancemethod(func, subrole, Creature))
#    return restore_original(subrole, attribute, orig_func, keyword)
def restore_original(role, attribute, orig_func, keyword=None):
    def _restore():
        setattr(role,attribute, orig_func)
        if keyword: role.keywords.remove(keyword)
    return _restore

def regenerate(subrole):
    orig_func = subrole.canDestroy
    def canDestroy(self):
        # expire it
        self.canDestroy = orig_func
        if self.canBeTapped(): self.tap()
        if isCreature(self.card):
            self.clearDamage()
            self.clearCombatState()
        #self.send(RegenerationEvent())
        return False # This is to the caller of canDestroy() (usually GameKeeper)
    subrole.canDestroy = new.instancemethod(canDestroy,subrole,subrole.__class__)
    return restore_original(subrole,"canDestroy",orig_func)
def prevent_damage(subrole, amt):
    orig_func = subrole.assignDamage
    def shieldDamage(self, amt, source, combat=False):
        if shieldDamage.curr_amt != -1:
            shielded = min([amt,shieldDamage.curr_amt])
            shieldDamage.curr_amt -= amt
            if shieldDamage.curr_amt <= 0:
                orig_func(-1*shieldDamage.curr_amt, source)
                shieldDamage.curr_amt = 0
                self.assignDamage = orig_func
        else: shielded = amt
        #self.send(DamagePreventedEvent(),amt=shielded)
    shieldDamage.curr_amt = amt
    subrole.assignDamage = new.instancemethod(shieldDamage,subrole,subrole.__class__)
    return restore_original(subrole,"assignDamage",orig_func)
def redirect_damage(from_target, to_target, amt):
    orig_func = from_target.assignDamage
    def assignDamage(self, amt, source, combat=False):
        if assignDamage.curr_amt != -1:
            redirected = min([amt,assignDamage.curr_amt])
            assignDamage.curr_amt -= amt
            if assignDamage.curr_amt <= 0:
                orig_func(-1*assignDamage.curr_amt, source)
                assignDamage.curr_amt = 0
                self.assignDamage = orig_func
        else:
            redirected = amt
        # XXX Make sure the target is in play, otherwise the damage isn't redirected
        to_target.assignDamage(redirected, source, combat)
        #self.send(DamageRedirectedEvent(),amt=shielded)
    assignDamage.curr_amt = amt
    from_target.assignDamage = new.instancemethod(assignDamage,from_target,from_target.__class__)
    return restore_original(from_target,"assignDamage",orig_func)

# XXX This works with blockers blocking multiple attackers, but not with the current damage calculation
# since we don't compute a total combat_damage array
def trample_old(subrole):
    subrole.keywords.add("trample")
    def trample(self, blockers, damage_assn, combat_damage):
        total_damage = self.power
        total_applied = 0
        not_enough = False
        for b in blockers:
            # if total assigned damage is lethal
            # lethal_damage will never be less than 1
            lethal_damage = b.toughness-b.currentDamage()
            assert lethal_damage >= 1, "Error in damage calculation"
            if combat_damage[b] >= lethal_damage:
                # find out how much we contributed to it
                if damage_assn[b] > lethal_damage:
                    combat_damage[b] -= (damage_assn[b]-lethal_damage)
                    damage_assn[b] = lethal_damage
                total_applied += damage_assn[b]
            else:
                not_enough = True
                break
        if not_enough: return 0
        else: return total_damage - total_applied
    # There is no original function
    subrole.trample = new.instancemethod(trample,subrole,subrole.__class__)
    def remove_trample():
        del subrole.trample
        subrole.remove("trample")
    return remove_trample

def flash(card):
    from game.Action import PlayInstant
    card.play_action = PlayInstant
