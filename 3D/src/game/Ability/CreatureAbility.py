from game.Match import isPermanent, isCreature, isLand, isArtifact
from game.stacked_function import override, replace, logical_or
from game.LazyInt import LazyInt
from game.characteristics import all_characteristics
from Ability import Ability
from StaticAbility import CardStaticAbility
from Effect import GiveKeyword, Override, ChangeLife
from TriggeredAbility import TriggeredAbility
from Trigger import DealDamageTrigger

def flash(card):
    from Limit import Unlimited, SorceryLimit, MultipleLimits
    casting_ability = card.play_spell
    if isinstance(casting_ability.limit, SorceryLimit):
        casting_ability.limit = Unlimited(card)
    elif isinstance(casting_ability.limit, MultipleLimits):
        for i, limit in enumerate(casting_ability.limit):
            if isinstance(limit, SorceryLimit): break
        casting_ability.limit.limits.pop(i)

def landwalk(card, landtype):
    keyword = landtype.lower()+"walk"
    def canBeBlocked(self):
        other_play = self.card.controller.opponent.play
        return (len(other_play.get(isLand.with_condition(lambda land: landtype in land.subtypes))) == 0)
    func = lambda subrole: override(subrole, "canBeBlocked", canBeBlocked)
    return CardStaticAbility(card, effects=GiveKeyword(keyword, func), txt=keyword)

plainswalk = lambda card: landwalk(card, "Plains")
swampwalk = lambda card: landwalk(card, "Swamp")
forestwalk = lambda card: landwalk(card, "Forest")
islandwalk = lambda card: landwalk(card, "Island")
mountainwalk = lambda card: landwalk(card, "Mountain")

def legendary_landwalk(card):
    keyword = "legendary landwalk"
    def canBeBlocked(self):
        other_play = self.card.controller.opponent.play
        return (len(other_play.get(isLand.with_condition(lambda land: "Legendary" in land.supertype))) == 0)
    func = lambda subrole: override(subrole, "canBeBlocked", canBeBlocked)
    return CardStaticAbility(card, effects=GiveKeyword(keyword, func), txt=keyword)

def nonbasic_landwalk(card):
    keyword = "Nonbasic landwalk"
    def canBeBlocked(self):
        other_play = self.card.controller.opponent.play
        return (len(other_play.get(isLand.with_condition(lambda land: not "Basic" in land.supertype))) == 0)
    func = lambda subrole: override(subrole, "canBeBlocked", canBeBlocked)
    return CardStaticAbility(card, effects=GiveKeyword(keyword, func), txt=keyword)

def flying(card):
    keyword = "flying"
    attr = set(["flying", "reach"])
    def canBeBlockedBy(self, blocker):
        return not (len(attr.intersection(blocker.keywords)) == 0)
    func = lambda subrole: override(subrole, "canBeBlockedBy", canBeBlockedBy)
    return CardStaticAbility(card, effects=GiveKeyword(keyword, func), txt=keyword)

def haste(card):
    keyword = "haste"
    def continuouslyInPlay(self): return True
    func = lambda subrole: override(subrole, "continuouslyInPlay", continuouslyInPlay, combiner=logical_or)
    return CardStaticAbility(card, effects=GiveKeyword(keyword, func), txt=keyword)

def defender(card):
    keyword = "defender"
    def canAttack(self): return False
    func = lambda subrole: override(subrole, "canAttack", canAttack)
    return CardStaticAbility(card, effects=GiveKeyword(keyword, func), txt=keyword)

def shroud(card):
    keyword = "shroud"
    def canBeTargetedBy(self, targetter): return False
    func = lambda subrole: override(subrole, "canBeTargetedBy", canBeTargetedBy)
    return CardStaticAbility(card, effects=GiveKeyword(keyword, func), txt=keyword)

def reach(card):
    keyword = "reach"
    return CardStaticAbility(card, effects=GiveKeyword(keyword), txt=keyword)
def double_strike(card):
    keyword = "double-strike"
    return CardStaticAbility(card, effects=GiveKeyword(keyword), txt=keyword)
def first_strike(card):
    keyword = "first-strike"
    return CardStaticAbility(card, effects=GiveKeyword(keyword), txt=keyword)
def trample(card):
    keyword = "trample"
    return CardStaticAbility(card, effects=GiveKeyword(keyword), txt=keyword)

def vigilance(card):
    keyword = "vigilance"
    def setAttacking(self):
        from game.GameEvent import AttackerDeclaredEvent
        self.setCombat(True)
        self.attacking = True
        self.send(AttackerDeclaredEvent())
        return False
    func = lambda subrole: override(subrole, "setAttacking", setAttacking)
    return CardStaticAbility(card, effects=GiveKeyword(keyword, func), txt=keyword)

def fear(card):
    keyword = "fear"
    def canBeBlockedBy(self, blocker):
        return (blocker.color == "B" or (blocker.type == "Artifact" and blocker.type=="Creature"))
    func = lambda subrole: override(subrole ,"canBeBlockedBy", canBeBlockedBy)
    return CardStaticAbility(card, effects=GiveKeyword(keyword, func), txt=keyword)

# Not sure how to do this one yet
def protection(card, attribute_match):
    keyword = "protection"
    # DEBT is an acronym. It stands for Damage, Enchantments/Equipment, Blocking, and Targeting
    def canBeDamagedBy(self, damager):
        return not attribute_match(damager)
    def canBeAttachedBy(self, attachment):
        return not attribute_match(attachment)
    def canBeBlockedBy(self, blocker):
        return not attribute_match(blocker)
    def canBeTargetedBy(self, targeter):
        return not attribute_match(targeter)
    func1 = lambda subrole: override(subrole, "canBeDamagedBy", canBeDamagedBy)
    func2 = lambda subrole: override(subrole, "canBeAttachedBy", canBeAttachedBy)
    func3 = lambda subrole: override(subrole, "canBeBlockedBy", canBeBlockedBy)
    func4 = lambda subrole: override(subrole, "canBeTargetedBy", canBeTargetedBy)
    return CardStaticAbility(card, effects=[GiveKeyword(keyword), Override(func1), Override(func2), Override(func3), Override(func4)], txt=keyword)

protection_from_black = lambda card: protection(card, attribute_match = lambda other: other.color == "B")
protection_from_blue = lambda card: protection(card, attribute_match = lambda other: other.color == "U")
protection_from_white = lambda card: protection(card, attribute_match = lambda other: other.color == "W")
protection_from_red = lambda card: protection(card, attribute_match = lambda other: other.color == "R")
protection_from_green = lambda card: protection(card, attribute_match = lambda other: other.color == "G")
protection_from_ge_cmc = lambda card, n: protection(card, attribute_match = lambda other: other.cost.converted_cost() >= n)
protection_from_le_cmc = lambda card, n: protection(card, attribute_match = lambda other: other.cost.converted_cost() <= n)
protection_from_artifacts = lambda card: protection(card, attribute_match = lambda other: isArtifact(other))

# 502.68b If a permanent has multiple instances of lifelink, each triggers separately.
# XXX Lifelink is broken when you have to split the damage
def lifelink(card):
    # This ability doesn't actually add lifelink to the keywords
    #card.keywords.add(keyword)
    trigger = DealDamageTrigger(sender=card)
    life_link = TriggeredAbility(card, trigger = trigger,
            match_condition = lambda sender: True,
            ability = Ability(card, effects=ChangeLife(lambda life, t=trigger: life+t.amount)),
            txt="lifelink")
    return life_link

# These are additional ones that aren't actually keywords, but the structure is the same
def must_attack(card):
    def checkAttack(self, attackers, not_attacking):
        return self.card in attackers or not self.canAttack()
    func = lambda subrole: override(subrole, "checkAttack", checkAttack)
    return CardStaticAbility(card, effects=Override(func), txt="must attack")

def only_block(card, keyword):
    def canBlockAttacker(self, attacker):
        return keyword in attacker.keywords
    func = lambda subrole: override(subrole, "canBlockAttacker", canBlockAttacker)
    return CardStaticAbility(card, effects=Override(func), txt="only block %s"%keyword)

def unblockable(card):
    def canBeBlocked(self): return False
    func = lambda subrole: override(subrole, "canBeBlocked", canBeBlocked)
    return CardStaticAbility(card, effects=Override(func), txt="unblockable")

def indestructible(card): #permanent):
    def shouldDestroy(self): return False
    def destroy(self, skip=False): return False
    func1 = lambda permanent: override(permanent, "shouldDestroy", shouldDestroy)
    func2 = lambda permanent: override(permanent, "destroy", destroy)
    return CardStaticAbility(card, effects=[Override(func1, attr="permanent"), Override(func2, attr="permanent")], txt="indestructible")


# Replacement effects for damage
# XXX I think these are broken right now
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
def regenerate(subrole, txt="Regenerate", condition=None):
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

def morph(card, cost="0"):
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
