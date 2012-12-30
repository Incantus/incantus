from functools import partial
from engine.symbols import *
from engine.Match import isPlayer, isCreature, isLand, isArtifact
from engine.GameEvent import BlockerDeclaredEvent, AttackerDeclaredEvent
from engine.CardRoles import permanent_method
from StaticAbility import CardStaticAbility
from Target import NoTarget
from TriggeredAbility import TriggeredAbility
from Trigger import Trigger, DealsDamageTrigger
from EffectsUtilities import until_end_of_turn, do_override, do_replace, combine, override_effect

__all__ = ["keyword_effect", "KeywordOnlyAbility",
           "reach", "double_strike", "first_strike",
           "trample", "lifelink", "deathtouch",
           "landwalk", "basic_landwalk",
           "plainswalk", "swampwalk", "forestwalk", "islandwalk", "mountainwalk",
           "legendary_landwalk", "nonbasic_landwalk", "flying",
           "shadow", "haste", "defender", "shroud", "vigilance",
           "fear", "absorb", "flanking",
           "protection", "protection_from_black", "aura_protection",
           "protection_from_blue", "protection_from_white",
           "protection_from_red", "protection_from_green",
           "protection_from_ge_cmc", "protection_from_le_cmc",
           "protection_from_artifacts", "protection_from_everything",
           "protection_from_multicolored", "protection_from_monocolored",
           "this_card_must_attack", "this_card_can_only_block", "this_card_is_unblockable",
           "this_card_cant_block", "prevent_damage", "redirect_damage", "fight"]

def keyword_effect(target):
    yield lambda: None

class KeywordOnlyAbility(CardStaticAbility):
    def __init__(self, keyword):
        super(KeywordOnlyAbility, self).__init__(effects=keyword_effect, zone="all", keyword=keyword)

def reach(): return KeywordOnlyAbility("reach")
def double_strike(): return KeywordOnlyAbility("double strike")
def first_strike(): return KeywordOnlyAbility("first strike")
def trample(): return KeywordOnlyAbility("trample")
def lifelink(): return KeywordOnlyAbility("lifelink")
def deathtouch(): return KeywordOnlyAbility("deathtouch")

def landwalk(condition, keyword):
    def canBeBlocked(self):
        if isPlayer(self.opponent): other_battlefield = self.opponent.battlefield
        else: other_battlefield = self.opponent.controller.battlefield # planeswalker
        return len(other_battlefield.get(isLand.with_condition(condition))) == 0
    return CardStaticAbility(effects=override_effect("canBeBlocked", canBeBlocked), keyword=keyword)

def basic_landwalk(landtype):
    condition = lambda land: land.subtypes == landtype
    return landwalk(condition, keyword=str(landtype).lower()+"walk")

plainswalk = partial(basic_landwalk, Plains)
swampwalk = partial(basic_landwalk, Swamp)
forestwalk = partial(basic_landwalk, Forest)
islandwalk = partial(basic_landwalk, Island)
mountainwalk = partial(basic_landwalk, Mountain)

def legendary_landwalk():
    keyword = "legendary landwalk"
    condition = lambda land: land.supertypes == Legendary
    return landwalk(condition, keyword)

def nonbasic_landwalk():
    keyword = "Nonbasic landwalk"
    condition = lambda land: not land.supertypes == Basic
    return landwalk(condition, keyword)

def flying():
    keyword = "flying"
    def canBeBlockedBy(self, blocker):
        return ("flying" in blocker.abilities or "reach" in blocker.abilities)
    return CardStaticAbility(effects=override_effect("canBeBlockedBy", canBeBlockedBy), keyword=keyword)

def shadow():
    keyword = "shadow"
    def canBeBlockedBy(self, blocker):
        return keyword in blocker.abilities
    def canBlockAttacker(self, attacker):
        return keyword in attacker.abilities
    def shadow_effects(source):
        yield do_override(source, "canBeBlockedBy", canBeBlockedBy), do_override(source, "canBlockAttacker", canBlockAttacker)
    return CardStaticAbility(effects=shadow_effects, keyword=keyword)

def haste():
    keyword = "haste"
    def continuouslyOnBattlefield(self): return True
    return CardStaticAbility(effects=override_effect("continuouslyOnBattlefield", continuouslyOnBattlefield), keyword=keyword)

def defender():
    keyword = "defender"
    def canAttack(self): return False
    return CardStaticAbility(effects=override_effect("canAttack", canAttack), keyword=keyword)

def shroud():
    keyword = "shroud"
    def canBeTargetedBy(self, targetter): return False
    return CardStaticAbility(effects=override_effect("canBeTargetedBy", canBeTargetedBy), keyword=keyword)

def vigilance():
    keyword = "vigilance"
    def setAttacking(self):
        self.setCombat(True)
        self.attacking = True
        self.send(AttackerDeclaredEvent())
        return False
    return CardStaticAbility(effects=override_effect("setAttacking", setAttacking), keyword=keyword)

def fear():
    keyword = "fear"
    def canBeBlockedBy(self, blocker):
        return (blocker.color == Black or (blocker.types == Artifact and blocker.types == Creature))
    return CardStaticAbility(effects=override_effect("canBeBlockedBy", canBeBlockedBy), keyword=keyword)

def protection(condition, attribute):
    keyword = "protection from %s"%attribute
    # DEBT is an acronym. It stands for Damage, Enchantments/Equipment, Blocking, and Targeting
    prevent_condition = lambda self, amt, source, combat=False: condition(source)
    def canBeAttachedBy(self, targeter):
        return not condition(targeter)
    def canBeBlockedBy(self, blocker):
        return not condition(blocker)
    def canBeTargetedBy(self, targeter):
        return not condition(targeter)

    def protection_effect(target):
        yield combine(prevent_damage(target, -1, txt="Protection effect", condition=prevent_condition),
                      do_override(target, "canBeAttachedBy", canBeAttachedBy),
                      do_override(target, "canBeBlockedBy", canBeBlockedBy),
                      do_override(target, "canBeTargetedBy", canBeTargetedBy))

    return CardStaticAbility(effects=protection_effect, keyword=keyword)

protection_from_black = partial(protection, condition = lambda other: other.color == Black, attribute="black")
protection_from_blue = partial(protection, condition = lambda other: other.color == Blue, attribute="blue")
protection_from_white = partial(protection, condition = lambda other: other.color == White, attribute="white")
protection_from_red = partial(protection, condition = lambda other: other.color == Red, attribute="red")
protection_from_green = partial(protection, condition = lambda other: other.color == Green, attribute="green")
protection_from_ge_cmc = lambda n: protection(condition = lambda other: other.cost >= n, attribute="converted mana cost %d or greater"%n)
protection_from_le_cmc = lambda n: protection(condition = lambda other: other.cost <= n, attribute="converted mana cost %d or less"%n)
protection_from_artifacts = partial(protection, condition = lambda other: isArtifact(other), attribute="artifacts")
protection_from_monocolored = partial(protection, condition = lambda other: len(other.color) == 1, attribute="monocolored")
protection_from_multicolored = partial(protection, condition = lambda other: len(other.color) > 1, attribute="multicolored")
protection_from_everything = partial(protection, condition = lambda other: True, attribute="everything")

def absorb(value):
    def absorb_effects(source):
        yield prevent_damage(source, value, False)
    return CardStaticAbility(effects=absorb_effects, txt="Absorb %d"%value, keyword="absorb")

def flanking():
    def condition(source, sender, attacker):
        return source == attacker and not "flanking" in sender.abilities
    def effects(controller, source, sender):
        yield NoTarget()
        until_end_of_turn(sender.augment_power_toughness(-1, -1))
        yield
    return TriggeredAbility(Trigger(BlockerDeclaredEvent(), condition), effects, keyword='flanking')

# This is for auras which say "Enchanted creature gains protection from <attribute>. This protection does not remove CARDNAME."
def aura_protection(aura, condition, attribute):
    keyword = "protection from %s"%attribute
    # DEBT is an acronym. It stands for Damage, Enchantments/Equipment, Blocking, and Targeting
    prevent_condition = lambda self, amt, source, combat=False: condition(source)
    def mk_override(cond):
        return lambda self, by: not cond(by)

    def effects(target):
        yield combine(*[do_override(target, func_name, mk_override(cond)) for func_name, cond in [("canBeAttachedBy", lambda o: not o==aura and condition(o)), ("canBeBlockedBy", condition), ("canBeTargetedBy", condition)]]+[prevent_damage(target, -1, txt="Protection effect", condition=prevent_condition)])

    return CardStaticAbility(effects=effects, keyword=keyword)

# These are additional ones that aren't actually keyword abilities, but the structure is the same
def this_card_must_attack():
    def checkAttack(self, attackers, not_attacking):
        return self in attackers or not self.canAttack()
    return CardStaticAbility(effects=override_effect("checkAttack", checkAttack), txt="~ must attack each turn if able.")

def this_card_cant_block():
    def canBlock(self):
        return False
    return CardStaticAbility(effects=override_effect("canBlock", canBlock), txt="~ can't block.")

def this_card_can_only_block(keyword):
    def canBlockAttacker(self, attacker):
        return keyword in attacker.abilities
    return CardStaticAbility(effects=override_effect("canBlockAttacker", canBlockAttacker), txt="~ can only block creatures with %s."%keyword)

@permanent_method
def unblockable(target):
    def canBeBlocked(self): return False
    return do_override(target, "canBeBlocked", canBeBlocked)

def this_card_is_unblockable():
    def unblockable_effect(target):
        yield target.unblockable()
    return CardStaticAbility(effects=unblockable_effect, txt="~ is unblockable.")

def prevent_damage(target, amount, next=True, txt='', condition=None):
    if not txt:
        txt = 'Prevent %s%s damage'%("the next " if next else '', str(amount) if amount > -1 else "all")
    def shieldDamage(self, amt, source, combat=False):
        dmg = 0
        if shieldDamage.curr_amt != -1:
            if next:
                shielded = min([amt,shieldDamage.curr_amt])
                shieldDamage.curr_amt -= amt
                if shieldDamage.curr_amt <= 0:
                    shieldDamage.expire()
                    if not shieldDamage.curr_amt == 0:
                        dmg = self.assignDamage(-1*shieldDamage.curr_amt, source, combat)
            else:
                shielded = shieldDamage.curr_amt
                amt -= shieldDamage.curr_amt
                if amt > 0: dmg = self.assignDamage(amt, source, combat)
        else: shielded = amt
        #self.send(DamagePreventedEvent(),amt=shielded)
        return dmg
    shieldDamage.curr_amt = amount
    return do_replace(target, "assignDamage", shieldDamage, msg=txt, condition=condition)

@permanent_method
def regenerate(target, txt="Regenerate", condition=None):
    def canDestroy(self):
        if self.canBeTapped(): self.tap()
        if isCreature(self):
            self.clearDamage()
            self.clearCombatState()
        # expire it
        canDestroy.expire()
        #self.send(RegenerationEvent())
        return False
    return until_end_of_turn(do_replace(target, "canDestroy", canDestroy, msg=txt, condition=condition))

def redirect_damage(from_target, to_target, amount, next=True, txt='', condition=None):
    if not txt:
        txt = 'Redirect %s%s damage from %s to %s'%("the next " if next else '', str(amount) if not amount == -1 else "all", from_target, to_target)
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
        # XXX Make sure the target is on the battlefield, otherwise the damage isn't redirected
        dmg += to_target.assignDamage(redirected, source, combat)
        #self.send(DamageRedirectedEvent(),amt=redirected)
        return dmg
    redirectDamage.curr_amt = amount
    return do_replace(from_target, "assignDamage", redirectDamage, msg=txt, condition=condition)

def fight(creature1, creature2):
    creature1.deal_damage(creature2, creature1.power)
    creature2.deal_damage(creature1, creature2.power)

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

# XXX This is kept around for cards that have abilities similar to the old
# triggered version of lifelink
def lifelink_old():
    def lifelink_effect(controller, source, amount):
        yield NoTarget()
        source.controller.life += amount
        yield

    return TriggeredAbility(DealsDamageTrigger(sender="source"),
        effects = lifelink_effect,
        keyword = "lifelink")

