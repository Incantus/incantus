from game.Match import isPermanent, isCreature, isLand
from game.stacked_function import stacked_function, logical_or, logical_and, replacement_stacked_function, replacement
from game.LazyInt import LazyInt
from game.characteristics import all_characteristics
import new

# XXX Some of these that take subroles are broken (vigilance, berserker) since they are bound (im_self) to the original subrole, while a copy is made when the card becomes a permanent.

def override(subrole, name, func, keyword=None, combiner=logical_and, reverse=True, new_func_gen=new.instancemethod):
    if keyword: subrole.keywords.add(keyword)
    obj = subrole
    cls = subrole.__class__

    is_derived = False
    # Check if we've overriden this before
    if not name in obj.__dict__:
        # Bind the call to the class function (since we are an object)
        orig_func = new.instancemethod(lambda self, *args, **named: getattr(cls, name).__call__(self, *args,**named), obj, cls)
        if not combiner == replacement: stacked_func = stacked_function(orig_func, combiner=combiner, reverse=reverse)
        else: stacked_func = replacement_stacked_function(obj, name, reverse)
        setattr(obj, name, stacked_func)
    else:
        stacked_func = getattr(obj, name)

    new_func = new_func_gen(func, obj, cls)
    stacked_func.add_func(new_func)
    def restore(stacked_func=stacked_func):
        stacked_func.remove_func(new_func)
        if not stacked_func.stacking():
            if name in obj.__dict__: del obj.__dict__[name]
        if keyword: obj.keywords.remove(keyword)
    func.expire = restore
    return restore

def override_replace(subrole, name, func, condition=None, keyword=None, txt=''):
    if condition == None: condition = lambda *args, **kw: True
    new_func_gen = lambda func, obj, cls: [False, new.instancemethod(func,obj,cls), txt, condition]
    return override(subrole, name, func, keyword, combiner=replacement, reverse=False, new_func_gen=new_func_gen)

# XXX Landwalk is broken - because the self for canBeBlocked refers to the in_play_role
def landwalk(subrole, landtype):
    keyword = landtype.lower()+"walk"
    def canBeBlocked(self):
        other_play = self.card.controller.opponent.play
        return (len(other_play.get(isLand.with_condition(lambda c: landtype in c.subtypes))) == 0)
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
    # XXX Haste broke after I split apart permanents from their roles
    def continuouslyInPlay(self): return True
    return override(subrole,"continuouslyInPlay",continuouslyInPlay, keyword="haste", combiner=logical_or)

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
        self.setCombat(True)
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
        card = self.card
        target.get(card)
        card.controller.stack.announce(Ability(card, target=target, effects=AugmentPowerToughness(power=num, toughness=num)))
        return True
    return override(subrole, "setBlocked", setBlocked, keyword="berserker", combiner=logical_or)

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

def indestructible(permanent):
    def shouldDestroy(self): return False
    def destroy(self, skip=False): pass
    remove1 = override(permanent,"shouldDestroy", shouldDestroy)
    remove2 = override(permanent,"destroy", destroy)
    def remove_indestructible():
        for remove in [remove1, remove2]: remove()
    return remove_indestructible

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


# XXX The next 3 don't work with the stacked_functions because they can replace the new function
# with the original within the new function - maybe they don't need to be stacked because they are never
# externally removed, they either expire naturally or from being called
# XXX Actually, they are replacement effects, which are slightly different (since two replacement effects looking
# for the same event can be ordered by the player affected by the event), and usually once one finishes the other won't
# be relevant
# XXX Fixed 03/01/08

def prevent_damage(subrole, amt, txt=None, condition=None, next=True):
    if txt == None:
        if amt == -1: amtstr = 'all'
        else: amtstr = str(amt)
        if next == True: nextstr = "the next"
        else: nextstr = ""
        txt = 'Prevent %s %s damage'%(nextstr, amtstr)
    def shieldDamage(self, amt, source, combat=False):
        if shieldDamage.curr_amt != -1:
            if next:
                shielded = min([amt,shieldDamage.curr_amt])
                shieldDamage.curr_amt -= amt
                if shieldDamage.curr_amt <= 0:
                    self.assignDamage(-1*shieldDamage.curr_amt, source, combat)
                    shieldDamage.curr_amt = 0
                    shieldDamage.expire()
            else:
                shielded = shieldDamage.curr_amt
                amt -= shieldDamage.curr_amt
                if amt > 0:
                    self.assignDamage(amt, source, combat)
        else: shielded = amt
        #self.send(DamagePreventedEvent(),amt=shielded)
    shieldDamage.curr_amt = amt
    restore = override_replace(subrole, "assignDamage", shieldDamage, txt=txt, condition=condition)
    return restore
def regenerate(subrole, txt="Regenerate", condition=None):
    def canDestroy(self):
        if self.perm.canBeTapped(): self.perm.tap()
        if isCreature(self.perm.card):
            self.clearDamage()
            self.clearCombatState()
        # expire it
        canDestroy.expire()
        #self.send(RegenerationEvent())
        return False # This is to the caller of canDestroy() (usually GameKeeper)
    restore = override_replace(subrole, "canDestroy", canDestroy, txt=txt, condition=condition)
    return restore
def redirect_damage(from_target, to_target, amt, txt=None, next=True, condition=None):
    if txt == None:
        if amt == -1: amtstr = 'all'
        else: amtstr = str(amt)
        if next == True: nextstr = "the next"
        else: nextstr = ""
        txt = 'Redirect %s %s damage from %s to %s'%(nextstr, amtstr, from_target, to_target)
    def redirectDamage(self, amt, source, combat=False):
        #print "redirecting from ", from_target, "to", to_target
        if redirectDamage.curr_amt != -1:
            if next:
                redirected = min([amt,redirectDamage.curr_amt])
                redirectDamage.curr_amt -= amt
                if redirectDamage.curr_amt <= 0:
                    self.assignDamage(-1*redirectDamage.curr_amt, source, combat)
                    redirectDamage.curr_amt = 0
                    redirectDamage.expire()
            else:
                redirected = redirectDamage.curr_amt
                amt -= redirectDamage.curr_amt
                if amt > 0:
                    self.assignDamage(amt, source, combat)
        else:
            redirected = amt
        # XXX Make sure the target is in play, otherwise the damage isn't redirected
        to_target.assignDamage(redirected, source, combat)
        #self.send(DamageRedirectedEvent(),amt=redirected)
    redirectDamage.curr_amt = amt
    restore = override_replace(from_target, "assignDamage", redirectDamage, txt=txt, condition=condition)
    return restore

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

def morph(permanent, cost="0"):
    # XXX Not implemented
    # You may play this face down as a 2/2 creature for 3. Turn it face up any time for its morph cost.
    pass
