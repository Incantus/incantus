from game.Match import isPermanent, isCreature, isLand, isArtifact
from game.stacked_function import override, replace, logical_or
from game.LazyInt import LazyInt
from game.characteristics import all_characteristics
import new

def landwalk(subrole, landtype):
    keyword = landtype.lower()+"walk"
    def canBeBlocked(self):
        other_play = self.card.controller.opponent.play
        return (len(other_play.get(isLand.with_condition(lambda land: landtype in land.subtypes))) == 0)
    return override(subrole, "canBeBlocked", canBeBlocked)

def plainswalk(subrole): return landwalk(subrole, "Plains")
def swampwalk(subrole): return landwalk(subrole, "Swamp")
def forestwalk(subrole): return landwalk(subrole, "Forest")
def islandwalk(subrole): return landwalk(subrole, "Island")
def mountainwalk(subrole): return landwalk(subrole, "Mountain")

def legendary_landwalk(subrole):
    keyword = "legendary landwalk"
    def canBeBlocked(self):
        other_play = self.card.controller.opponent.play
        return (len(other_play.get(isLand.with_condition(lambda land: "Legendary" in land.supertype))) == 0)
    return override(subrole, "canBeBlocked", canBeBlocked)
def nonbasic_landwalk(subrole):
    keyword = "Nonbasic landwalk"
    def canBeBlocked(self):
        other_play = self.card.controller.opponent.play
        return (len(other_play.get(isLand.with_condition(lambda land: not "Basic" in land.supertype))) == 0)
    return override(subrole, "canBeBlocked", canBeBlocked)

def flying(subrole):
    attr = set(["flying", "reach"])
    def canBeBlockedBy(self, blocker):
        return not (len(attr.intersection(blocker.keywords)) == 0)
    return override(subrole, "canBeBlockedBy", canBeBlockedBy) #keyword="flying"

def only_block(subrole):
    def canBlockAttacker(self, attacker):
        return keyword in attacker.keywords
    return override(subrole, "canBlockAttacker", canBlockAttacker)

def haste(subrole):
    def continuouslyInPlay(self): return True
    return override(subrole, "continuouslyInPlay", continuouslyInPlay, combiner=logical_or) #keyword="haste"

def must_attack(subrole):
    def checkAttack(self, attackers, not_attacking):
        return self.card in attackers or not self.canAttack()
    return override(subrole, "checkAttack", checkAttack)

def defender(subrole):
    def canAttack(self): return False
    return override(subrole, "canAttack", canAttack) #, keyword="defender")

def shroud(subrole):
    def canBeTargetedBy(self, targetter): return False
    return override(subrole, "canBeTargetedBy", canBeTargetedBy) #, keyword="shroud")

def reach(card):
    card.keywords.add("reach")
    return lambda: card.keywords.remove("reach")

def double_strike(card):
    card.keywords.add("double-strike")
    return lambda: card.keywords.remove("double-strike")
def first_strike(card):
    card.keywords.add("first-strike")
    return lambda: card.keywords.remove("first-strike")
def trample(card):
    card.keywords.add("trample")
    return lambda: card.keywords.remove("trample")


# XXX I don't like the way these are overriden - there must be a better way
def vigilance(subrole):
    def setAttacking(self):
        from game.GameEvent import AttackerDeclaredEvent
        self.setCombat(True)
        self.attacking = True
        self.send(AttackerDeclaredEvent())
        return False
    return override(subrole, "setAttacking", setAttacking) # keyword="vigilance")

# 502.68b If a permanent has multiple instances of lifelink, each triggers separately.
# XXX Lifelink is broken when you have to split the damage
def lifelink(subrole, card=None):
    from Ability import Ability
    from Effect import ChangeLife
    from TriggeredAbility import TriggeredAbility
    from Trigger import DealDamageTrigger
    # XXX This won't work because for a card with lifelink, the subrole won't have been assigned to a card
    # XXX Fix this when i move abilities to the card
    if not card:
        card = subrole.card
        in_play = True
    else: in_play = False
    card.keywords.add("lifelink")
    trigger = DealDamageTrigger(sender=card)
    life_link = TriggeredAbility(card, trigger = trigger,
            match_condition = lambda sender: True,
            ability = Ability(card, effects=ChangeLife(lambda life, t=trigger: life+t.amount)))
    subrole.triggered_abilities.append(life_link)
    if in_play: life_link.enteringPlay()
    def remove_lifelink():
        card.keywords.remove("lifelink")
        life_link.leavingPlay()
        subrole.triggered_abilities.remove(life_link)
    return remove_lifelink

def fear(subrole):
    def canBeBlockedBy(self, blocker):
        return (blocker.color == "B" or (blocker.type == "Artifact" and blocker.type=="Creature"))
    return override(subrole ,"canBeBlockedBy", canBeBlockedBy) #, keyword="fear")

def protection(subrole, attribute_match):
    #subrole.keywords.add("protection")
    # DEBT is an acronym. It stands for Damage, Enchantments/Equipment, Blocking, and Targeting
    def canBeDamagedBy(self, damager):
        return not attribute_match(damager)
    def canBeAttachedBy(self, attachment):
        return not attribute_match(attachment)
    def canBeBlockedBy(self, blocker):
        return not attribute_match(blocker)
    def canBeTargetedBy(self, targeter):
        return not attribute_match(targeter)
    remove1 = override(subrole, "canBeDamagedBy", canBeDamagedBy)
    remove2 = override(subrole, "canBeAttachedBy", canBeAttachedBy)
    remove3 = override(subrole, "canBeBlockedBy", canBeBlockedBy)
    remove4 = override(subrole, "canBeTargetedBy", canBeTargetedBy)
    def remove_protection():
        for remove in [remove1, remove2, remove3, remove4]: remove()
    return remove_protection

protection_from_black = lambda subrole: protection(subrole, attribute_match = lambda other: other.color == "B")
protection_from_blue = lambda subrole: protection(subrole, attribute_match = lambda other: other.color == "U")
protection_from_white = lambda subrole: protection(subrole, attribute_match = lambda other: other.color == "W")
protection_from_red = lambda subrole: protection(subrole, attribute_match = lambda other: other.color == "R")
protection_from_green = lambda subrole: protection(subrole, attribute_match = lambda other: other.color == "G")
protection_from_ge_cmc = lambda subrole, n: protection(subrole, attribute_match = lambda other: other.cost.converted_cost() >= n)
protection_from_le_cmc = lambda subrole, n: protection(subrole, attribute_match = lambda other: other.cost.converted_cost() <= n)
protection_from_artifacts = lambda subrole: protection(subrole, attribute_match = lambda other: isArtifact(other))

# These are additional ones that aren't actually keywords, but the structure is the same
def unblockable(subrole):
    def canBeBlocked(self): return False
    return override(subrole, "canBeBlocked", canBeBlocked)

def indestructible(permanent):
    def shouldDestroy(self): return False
    def destroy(self, skip=False): return False
    remove1 = override(permanent, "shouldDestroy", shouldDestroy)
    remove2 = override(permanent, "destroy", destroy)
    def remove_indestructible():
        for remove in [remove1, remove2]: remove()
    return remove_indestructible


# Replacement effects for damage
def prevent_damage(subrole, amt, next=True, txt=None, condition=None):
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
                    if not shieldDamage.curr_amt == 0:
                        self.assignDamage(-1*shieldDamage.curr_amt, source, combat)
                    shieldDamage.expire()
            else:
                shielded = shieldDamage.curr_amt
                amt -= shieldDamage.curr_amt
                if amt > 0: self.assignDamage(amt, source, combat)
        else: shielded = amt
        #self.send(DamagePreventedEvent(),amt=shielded)
    shieldDamage.curr_amt = amt
    return replace(subrole, "assignDamage", shieldDamage, msg=txt, condition=condition)
def regenerate(permanent, txt="Regenerate", condition=None):
    def canDestroy(self):
        if self.canBeTapped(): self.tap()
        if isCreature(self.card):
            self.clearDamage()
            self.clearCombatState()
        # expire it
        canDestroy.expire()
        #self.send(RegenerationEvent())
        return False
    return replace(subrole, "canDestroy", canDestroy, msg=txt, condition=condition)
def redirect_damage(from_target, to_target, amt, next=True, txt=None, condition=None):
    if txt == None:
        if amt == -1: amtstr = 'all'
        else: amtstr = str(amt)
        if next == True: nextstr = "the next"
        else: nextstr = ""
        txt = 'Redirect %s %s damage from %s to %s'%(nextstr, amtstr, from_target, to_target)
    def redirectDamage(self, amt, source, combat=False):
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
                if amt > 0: self.assignDamage(amt, source, combat)
        else:
            redirected = amt
        # XXX Make sure the target is in play, otherwise the damage isn't redirected
        to_target.assignDamage(redirected, source, combat)
        #self.send(DamageRedirectedEvent(),amt=redirected)
    redirectDamage.curr_amt = amt
    return replace(from_target, "assignDamage", redirectDamage, msg=txt, condition=condition)

def flash(card):
    from Limit import Unlimited, SorceryLimit, MultipleLimits
    casting_ability = card.out_play_role.abilities[0]
    if isinstance(casting_ability.limit, SorceryLimit):
        casting_ability.limit = Unlimited(card)
    elif isinstance(casting_ability.limit, MultipleLimits):
        for i, limit in enumerate(casting_ability.limit):
            if isinstance(limit, SorceryLimit): break
        casting_ability.limit.limits.pop(i)

def morph(permanent, cost="0"):
    # XXX Not implemented
    # You may play this face down as a 2/2 creature for 3. Turn it face up any time for its morph cost.
    pass

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
