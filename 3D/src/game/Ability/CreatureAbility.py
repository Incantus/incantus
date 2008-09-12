from functools import partial
from game.Match import isCreature, isLand, isArtifact
from StaticAbility import CardStaticAbility
from Target import NoTarget
from TriggeredAbility import TriggeredAbility
from Trigger import DealDamageTrigger
from Effects import do_override, do_replace, logical_or

def keyword_effect(target):
    yield lambda: None

def landwalk(landtype):
    keyword = landtype.lower()+"walk"
    def canBeBlocked(self):
        other_play = self.controller.opponent.play
        return (len(other_play.get(isLand.with_condition(lambda land: land.subtypes == landtype))) == 0)
    return CardStaticAbility(effects=do_override("canBeBlocked", canBeBlocked), keyword=keyword)

plainswalk = partial(landwalk, "Plains")
swampwalk = partial(landwalk, "Swamp")
forestwalk = partial(landwalk, "Forest")
islandwalk = partial(landwalk, "Island")
mountainwalk = partial(landwalk, "Mountain")

def legendary_landwalk():
    keyword = "legendary landwalk"
    def canBeBlocked(self):
        other_play = self.controller.opponent.play
        return (len(other_play.get(isLand.with_condition(lambda land: land.supertypes == "Legendary"))) == 0)
    return CardStaticAbility(effects=do_override("canBeBlocked", canBeBlocked), keyword=keyword)

def nonbasic_landwalk():
    keyword = "Nonbasic landwalk"
    def canBeBlocked(self):
        other_play = self.controller.opponent.play
        return (len(other_play.get(isLand.with_condition(lambda land: not land.supertypes == "Basic"))) == 0)
    return CardStaticAbility(effects=do_override("canBeBlocked", canBeBlocked), keyword=keyword)

def flying():
    keyword = "flying"
    def canBeBlockedBy(self, blocker):
        return ("flying" in blocker.abilities or "reach" in blocker.abilities)
    return CardStaticAbility(effects=do_override("canBeBlockedBy", canBeBlockedBy), keyword=keyword)

def haste():
    keyword = "haste"
    def continuouslyInPlay(self): return True
    return CardStaticAbility(effects=do_override("continuouslyInPlay", continuouslyInPlay, combiner=logical_or), keyword=keyword)

def defender():
    keyword = "defender"
    def canAttack(self): return False
    return CardStaticAbility(effects=do_override("canAttack", canAttack), keyword=keyword)

def shroud():
    keyword = "shroud"
    def canBeTargetedBy(self, targetter): return False
    return CardStaticAbility(effects=do_override("canBeTargetedBy", canBeTargetedBy), keyword=keyword)

def reach():
    keyword = "reach"
    return CardStaticAbility(effects=keyword_effect, keyword=keyword)
def double_strike():
    keyword = "double strike"
    return CardStaticAbility(effects=keyword_effect, keyword=keyword)
def first_strike():
    keyword = "first strike"
    return CardStaticAbility(effects=keyword_effect, keyword=keyword)
def trample():
    keyword = "trample"
    return CardStaticAbility(effects=keyword_effect, keyword=keyword)

def vigilance():
    keyword = "vigilance"
    def setAttacking(self):
        from game.GameEvent import AttackerDeclaredEvent
        self.setCombat(True)
        self.attacking = True
        self.send(AttackerDeclaredEvent())
        return False
    return CardStaticAbility(effects=do_override("setAttacking", setAttacking), keyword=keyword)

def fear():
    keyword = "fear"
    def canBeBlockedBy(self, blocker):
        return (blocker.color == "B" or (blocker.types == "Artifact" and blocker.types =="Creature"))
    return CardStaticAbility(effects=do_override("canBeBlockedBy", canBeBlockedBy), keyword=keyword)

# Not sure how to do this one yet
def protection(attribute_match):
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
    return CardStaticAbility(effects=[give_keyword(keyword), Override(func1), Override(func2), Override(func3), Override(func4)], txt=keyword)

protection_from_black = partial(protection, attribute_match = lambda other: other.color == "B")
protection_from_blue = partial(protection, attribute_match = lambda other: other.color == "U")
protection_from_white = partial(protection, attribute_match = lambda other: other.color == "W")
protection_from_red = partial(protection, attribute_match = lambda other: other.color == "R")
protection_from_green = partial(protection, attribute_match = lambda other: other.color == "G")
protection_from_ge_cmc = lambda n: protection(attribute_match = lambda other: other.cost >= n)
protection_from_le_cmc = lambda n: protection(attribute_match = lambda other: other.cost <= n)
protection_from_artifacts = partial(protection, attribute_match = lambda other: isArtifact(other))

# 502.68b If a permanent has multiple instances of lifelink, each triggers separately.
def lifelink():
    def lifelink_effect(controller, source, amount):
        yield NoTarget()
        source.controller.life += amount
        yield

    return TriggeredAbility(DealDamageTrigger(sender="source"),
        condition = None,
        effects = lifelink_effect,
        keyword = "lifelink")

# These are additional ones that aren't actually keyword abilities, but the structure is the same
def must_attack():
    def checkAttack(self, attackers, not_attacking):
        # XXX LKI fix
        return self.card in attackers or not self.canAttack()
    return CardStaticAbility(effects=do_override("checkAttack", checkAttack), txt="must attack")

def only_block(keyword):
    def canBlockAttacker(self, attacker):
        return keyword in attacker.abilities
    return CardStaticAbility(effects=do_override("canBlockAttacker", canBlockAttacker), txt="only block %s"%keyword)

def unblockable():
    def canBeBlocked(self): return False
    return CardStaticAbility(effects=do_override("canBeBlocked", canBeBlocked), txt="unblockable")

def indestructible():
    def shouldDestroy(self): return False
    def destroy(self, skip=False): return False
    func1 = lambda permanent: override(permanent, "shouldDestroy", shouldDestroy)
    func2 = lambda permanent: override(permanent, "destroy", destroy)
    return CardStaticAbility(effects=[Override(func1), Override(func2)], txt="indestructible")

def prevent_damage(target, amt, next=True, txt=None, condition=None):
    if txt == None:
        if amt == -1: amtstr = 'all'
        else: amtstr = str(amt)
        if next == True: nextstr = "the next"
        else: nextstr = ""
        txt = 'Prevent %s %s damage'%(nextstr, amtstr)
    def shieldDamage(self, amt, source, combat=False):
        dmg = 0
        if shieldDamage.curr_amt != -1:
            if next:
                shielded = min([amt,shieldDamage.curr_amt])
                shieldDamage.curr_amt -= amt
                if shieldDamage.curr_amt <= 0:
                    if not shieldDamage.curr_amt == 0:
                        dmg = self.assignDamage(-1*shieldDamage.curr_amt, source, combat)
                    shieldDamage.expire()
            else:
                shielded = shieldDamage.curr_amt
                amt -= shieldDamage.curr_amt
                if amt > 0: dmg = self.assignDamage(amt, source, combat)
        else: shielded = amt
        #self.send(DamagePreventedEvent(),amt=shielded)
        return dmg
    shieldDamage.curr_amt = amt
    return do_replace(target, "assignDamage", shieldDamage, msg=txt, condition=condition)
def regenerate(target, txt="Regenerate", condition=None):
    def canDestroy(self):
        if self.canBeTapped(): self.tap()
        # XXX LKI fix
        if isCreature(self.card):
            self.clearDamage()
            self.clearCombatState()
        # expire it
        canDestroy.expire()
        #self.send(RegenerationEvent())
        return False
    return do_replace(target, "canDestroy", canDestroy, msg=txt, condition=condition)
def redirect_damage(from_target, to_target, amt, next=True, txt=None, condition=None):
    if txt == None:
        if amt == -1: amtstr = 'all'
        else: amtstr = str(amt)
        if next == True: nextstr = "the next"
        else: nextstr = ""
        txt = 'Redirect %s %s damage from %s to %s'%(nextstr, amtstr, from_target, to_target)
    def redirectDamage(self, amt, source, combat=False):
        dmg = 0
        if redirectDamage.curr_amt != -1:
            if next:
                redirected = min([amt,redirectDamage.curr_amt])
                redirectDamage.curr_amt -= amt
                if redirectDamage.curr_amt <= 0:
                    dmg = self.assignDamage(-1*redirectDamage.curr_amt, source, combat)
                    redirectDamage.curr_amt = 0
                    redirectDamage.expire()
            else:
                redirected = redirectDamage.curr_amt
                amt -= redirectDamage.curr_amt
                if amt > 0: dmg = self.assignDamage(amt, source, combat)
        else:
            redirected = amt
        # XXX Make sure the target is in play, otherwise the damage isn't redirected
        dmg += to_target.assignDamage(redirected, source, combat)
        #self.send(DamageRedirectedEvent(),amt=redirected)
        return dmg
    redirectDamage.curr_amt = amt
    return do_replace(from_target, "assignDamage", redirectDamage, msg=txt, condition=condition)

# XXX This works with blockers blocking multiple attackers, but not with the current damage calculation
# since we don't compute a total combat_damage array
def trample_old(target):
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
    target.trample = new.instancemethod(trample,target,target.__class__)
    def remove_trample():
        del target.trample
    return remove_trample
