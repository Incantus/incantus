
from GameObjects import MtGObject
from data_structures import keywords
from GameEvent import DealsDamageEvent, CardTapped, CardUntapped, PermanentDestroyedEvent, ReceivesDamageEvent, AttachedEvent, UnAttachedEvent, AttackerDeclaredEvent, AttackerBlockedEvent, BlockerDeclaredEvent, TokenLeavingPlay, TargetedByEvent, PowerToughnessChangedEvent, SubRoleAddedEvent, SubRoleRemovedEvent, NewTurnEvent

import new, inspect
def rebind_self(obj):
    # Bind all unbound functions
    for name, func in inspect.getmembers(obj, inspect.ismethoddescriptor):
        if hasattr(func, "stacked"):
            func.rebind(obj)
            #func.im_self != obj: setattr(obj, name, new.instancemethod(func.im_func, obj, func.im_class))

class NoRole(MtGObject):   # This is for lands
    # For token objects out of play
    def __init__(self, card):
        self.card = card
        self.facedown = False
    def faceDown(self):
        self.facedown = True
    def faceUp(self):
        self.facedown = False
    def copy(self):
        return NoRole(self.card)
    def match_role(self, matchrole):
        return False
    def __str__(self):
        return "NoRole"

class Spell(MtGObject):
    def __init__(self, card):
        self.card = card
        self.onstack = False
        self.abilities = []
        self.facedown = False
    # the damage stuff seems kind of hacky
    def canDealDamage(self):
        return True
    def dealDamage(self, target, amount, combat=False):
        if target.canBeDamagedBy(self.card) and amount > 0:
            target.assignDamage(amount, source=self.card, combat=combat)
    def canBeTargetedBy(self, targeter): return True
    def isTargetedBy(self, targeter):
        self.card.send(TargetedByEvent(), targeter=targeter)
    def faceDown(self):
        self.facedown = True
    def faceUp(self):
        self.facedown = False
    def copy(self):
        import copy
        newcopy = copy.copy(self)
        rebind_self(newcopy)
        newcopy.abilities = []
        return newcopy
    def match_role(self, matchrole):
        return matchrole == self.__class__
    def __str__(self):
        return "Spell"

class Permanent(MtGObject):
    def abilities():
        def fget(self):
            if not self._abilities:
                import operator
                self._abilities = reduce(operator.add, [role.abilities for role in self.subroles], [])
            return self._abilities
        return locals()
    abilities = property(**abilities())
    def __init__(self, card, subroles):
        self.card = card
        self._abilities = []
        if not (type(subroles) == list or type(subroles) == tuple): subroles = [subroles]
        self.subroles = subroles
        self.tapped = False
        self.flipped = False
        self.facedown = False
        self.attachments = []
        #self.targeted = False
        self.counters = []          # Any counters on permanent
        self.continuously_in_play = False
    def get_subrole(self, matchrole):
        for role in self.subroles:
            if isinstance(role, matchrole): return role
        return None
    def add_subrole(self, role):
        role.enteringPlay(self)
        self.subroles.append(role)
        self._abilities.extend(role.abilities)
        self.card.send(SubRoleAddedEvent(), subrole=role)
    def remove_subrole(self, role):
        if role in self.subroles: # XXX Is this correct - the role is only missing when card enters play, gains role for the turn, and then is blinked back
            role.leavingPlay()
            self.subroles.remove(role)
            for ability in role.abilities: self._abilities.remove(ability)
            self.card.send(SubRoleRemovedEvent(), subrole=role)
    def match_role(self, matchrole):
        success = False
        if matchrole == self.__class__: success = True
        else:
            for role in self.subroles:
                if isinstance(role, matchrole):
                    success = True
                    break
        return success
    def __getattr__(self, attr):
        for role in self.subroles:
            if hasattr(role, attr): return getattr(role, attr)
        return getattr(super(Permanent, self), attr)
    def canDealDamage(self):
        return True
    def dealDamage(self, target, amount, combat=False):
        if target.canBeDamagedBy(self.card) and amount > 0:
            target.assignDamage(amount, source=self.card, combat=combat)
        return amount
    def canBeTargetedBy(self, targeter):
        result = True
        for role in self.subroles: 
            if not role.canBeTargetedBy(targeter):
                result = False
                break
        return result
    def isTargetedBy(self, targeter):
        self.card.send(TargetedByEvent(), targeter=targeter)
    def faceDown(self):
        self.facedown = True
    def faceUp(self):
        self.facedown = False
    def canBeTapped(self): # Called by game action (such as an effect)
        return True
    def canTap(self): # Called as a result of user action
        for role in self.subroles:
            if not role.canTap(): return False
        else: return True
    def tap(self, trigger=True):
        # Don't tap if already tapped:
        if not self.tapped:
            self.tapped = True
            if trigger: self.card.send(CardTapped())
    def canUntap(self):
        return True
    def untap(self, trigger=True):
        if self.tapped:
            self.tapped = False
            if trigger: self.card.send(CardUntapped())
    def shouldDestroy(self):
        # This is called to check whether the permanent should be destroyed (by SBE)
        result = False
        for role in self.subroles: 
            if role.shouldDestroy():
                result = True
                break
        return result
    def canDestroy(self):
        # this can be replaced by regeneration for creatures - what about artifacts and enchantments?
        result = False
        for role in self.subroles:
            if role.canDestroy():
                result = True
                break
        return result
    def destroy(self, skip=False):
        if skip or self.canDestroy():
            controller = self.card.controller
            controller.moveCard(self.card, controller.play, self.card.owner.graveyard)
            self.card.send(PermanentDestroyedEvent())
    def summoningSickness(self):
        def remove_summoning_sickness(player):
            if self.card.controller == player:
                self.continuously_in_play = True
                self.unregister(remove_summoning_sickness, NewTurnEvent(), weak=False)
        self.register(remove_summoning_sickness, NewTurnEvent(), weak=False)
    def enteringPlay(self):
        # Setup any static and triggered abilities
        for role in self.subroles: role.enteringPlay(self)
        self.summoningSickness()
    def leavingPlay(self):
        self.continuously_in_play = False
        for role in self.subroles: role.leavingPlay()
        for attached in self.attachments: attached.attachedLeavingPlay()
    def copy(self):
        import copy
        # This doesn't create new lists for triggered abilities and static abilities
        newcopy = copy.copy(self)
        rebind_self(newcopy)
        newcopy.counters = []
        newcopy.attachments = []
        newcopy._abilities = []
        newcopy.subroles = [role.copy(newcopy) for role in self.subroles]
        return newcopy
    def __str__(self):
        return str(self.__class__.__name__)

class Role(object):
    def __init__(self):
        self.abilities = []
        self.triggered_abilities = []
        self.static_abilities = []
    def send(self, *args, **named):
        self.perm.card.send(*args, **named)
    def enteringPlay(self, perm):
        self.perm = perm
        self.card = perm.card
        for ta in self.triggered_abilities: ta.enteringPlay()
        for sa in self.static_abilities: sa.enteringPlay()
    def leavingPlay(self):
        for ta in self.triggered_abilities: ta.leavingPlay()
        for sa in self.static_abilities: sa.leavingPlay()
    def canDestroy(self): return True
    def shouldDestroy(self): return False
    def canBeTargetedBy(self, targeter): return True
    def canTap(self): return True
    def __deepcopy__(self, memo,mutable=set([list,set,dict])):
        # This only copies one level deep
        # So the in_play_role is always the pristine one specified in the card definition
        import copy
        role = self.__class__.__new__(self.__class__)
        for attr, value in self.__dict__.iteritems():
            if type(value) in mutable:
                setattr(role,attr,copy.copy(value))
            else: setattr(role,attr,value)
        return role
    def copy(self, perm=None):
        import copy
        newcopy = copy.deepcopy(self)
        newcopy.perm = perm
        rebind_self(newcopy)
        return newcopy
    def __str__(self):
        return self.__class__.__name__

class Land(Role):
    def __init__(self, color):
        super(Land,self).__init__()
        self.color = color

class PTModifiers(list):
    def __init__(self, role):
        super(PTModifiers,self).__init__()
        self.role = role
    def append(self, object):
        self.role.send(PowerToughnessChangedEvent())
        return super(PTModifiers,self).append(object)
    def remove(self, object):
        self.role.send(PowerToughnessChangedEvent())
        return super(PTModifiers,self).remove(object)

class Creature(Role):
    def power():
        def fget(self):
            # Calculate layering rules
            base = self.base_power
            if len(self.PT_setters): base = self.PT_setters[-1].power # layer 6a
            layer6b = sum([t.power for t in self.PT_other_modifiers])
            layer6c = sum([t.power for t in self.perm.counters if hasattr(t,"power")])
            layer6d = sum([t.power for t in self.PT_static_modifiers])
            return base+layer6b+layer6c+layer6d
        return locals()
    power = property(**power())
    def toughness():
        def fget(self):
            base = self.base_toughness
            if len(self.PT_setters): base = self.PT_setters[-1].toughness # layer 6a
            layer6b = sum([t.toughness for t in self.PT_other_modifiers])
            layer6c = sum([t.toughness for t in self.perm.counters if hasattr(t,"toughness")])
            layer6d = sum([t.toughness for t in self.PT_static_modifiers])
            return base+layer6b+layer6c+layer6d
        return locals()
    toughness = property(**toughness())
    def __init__(self, power, toughness):
        super(Creature,self).__init__()
        # These are immutable and come from the card
        self.base_power = power
        self.base_toughness = toughness

        # Only accessed internally
        self.__damage = 0

        self.PT_setters = [] # layer 6a - characteristic defining
        self.PT_other_modifiers = [] # layer 6b - other modifiers
        self.PT_static_modifiers = [] # layer 6c - static modifiers
        self.in_combat = False
        self.attacking = False
        self.blocking = False
        self.blocked = False
        self.keywords = keywords()
    def copy(self, perm=None):
        import copy
        newcopy = copy.deepcopy(self)
        newcopy.perm = perm
        newcopy.keywords = self.keywords.copy()
        rebind_self(newcopy)
        return newcopy
    def canBeDamagedBy(self, damager):
        return True
    def combatDamage(self):
        return self.power
    def clearDamage(self):
        self.__damage = 0
    def currentDamage(self):
        return self.__damage
    def assignDamage(self, amt, source, combat=False):
        if amt > 0:
            self.__damage += amt
            source.send(DealsDamageEvent(), to=self.card, amount=amt)
            self.send(ReceivesDamageEvent(), source=source, amount=amt)
    def removeDamage(self, amt):
        self.__damage -= amt
    def trample(self, damage_assn):
        from Match import isCreature
        total_damage = self.combatDamage()
        total_applied = 0
        not_enough = False
        for b in damage_assn.keys():
            # Skip players and blockers who no longer exist
            if not isCreature(b): continue
            # if total assigned damage is lethal
            # lethal_damage will never be less than 1
            lethal_damage = b.toughness-b.currentDamage()
            assert lethal_damage >= 1, "Error in damage calculation"
            if damage_assn[b] < lethal_damage:
                not_enough = True
                break
            total_applied += damage_assn[b]
        if not_enough: return 0
        else: return total_damage - total_applied
    def clearCombatState(self):
        self.in_combat = False    # XXX Should be a property that sends a signal when set
        self.attacking = False
        self.blocking = False
        self.blocked = False
    def mustAttack(self):
        return False
    def mustBeBlocked(self):
        return False
    def continuouslyInPlay(self):
        return self.perm.continuously_in_play
    def canAttack(self):
        return (not self.perm.tapped) and (not self.in_combat) and self.continuouslyInPlay()
    def computeBlockCost(self):
        self.block_cost = []
    def payBlockCost(self):
        player = self.card.controller
        from Cost import MultipleCosts
        cost = MultipleCosts(self.block_cost)
        return cost.compute(self.card, player) and cost.pay(self.card, player)
    def computeAttackCost(self):
        self.attack_cost = ["0"]
        return True
    def payAttackCost(self):
        player = self.card.controller
        from Cost import MultipleCosts
        cost = MultipleCosts(self.attack_cost)
        return cost.compute(self.card, player) and cost.pay(self.card, player)
    def canBeBlocked(self):
        return True
    def canBeBlockedBy(self, blocker):
        return True
    def canBlock(self):
        return not self.in_combat
    def canBlockAttacker(self, attacker):
        return True
    def setBlocking(self, attacker):
        self.setCombat(True)
        self.blocking = True
        self.send(BlockerDeclaredEvent(), attacker=attacker)
        return True
    def setAttacking(self):
        self.setCombat(True)
        self.perm.tap()
        self.attacking = True
        self.send(AttackerDeclaredEvent())
        return True
    def setBlocked(self, blockers):
        self.blocked = True
        self.send(AttackerBlockedEvent(), blockers=blockers)
        return True
    def setCombat(self, in_combat):
        self.in_combat = in_combat
        return True
    
    # These two override the functions in the Permanent
    def canTap(self): return self.continuouslyInPlay()
    def shouldDestroy(self):
        return self.__damage >= self.toughness

class TokenCreature(Creature):
    def leavingPlay(self):
        self.send(TokenLeavingPlay())
        super(TokenCreature,self).leavingPlay()

class Artifact(Role): pass
class Enchantment(Role): pass

class Attachment(object):
    def attach(self, target):
        if self.attached_to != None: self.unattach()
        self.attached_to = target
        self.attached_to.attachments.append(self.perm.card)
        for a in self.perm.attached_abilities: a.enteringPlay()
        self.send(AttachedEvent(), attached=self.attached_to)
        return True
    def unattach(self):
        if self.attached_to:
            for a in self.perm.attached_abilities: a.leavingPlay()
            self.attached_to.attachments.remove(self.perm.card)
            self.send(UnAttachedEvent(), unattached=self.attached_to)
        self.attached_to = None
    def attachedLeavingPlay(self):
        for a in self.perm.attached_abilities: a.leavingPlay()
        self.send(UnAttachedEvent(), unattached=self.attached_to)
        self.attached_to = None
    def leavingPlay(self):
        self.unattach()
        super(Attachment,self).leavingPlay()
        return True

class Equipment(Attachment, Artifact):
    def __init__(self):
        super(Equipment,self).__init__()
        self.attached_to = None
        self.target_types = None

class Aura(Attachment, Enchantment):
    def __init__(self, target_types=None):
        super(Aura,self).__init__()
        self.attached_to = None
        self.target_types = target_types
