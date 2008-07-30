
from GameObjects import MtGObject
from data_structures import keywords
from GameEvent import DealsDamageEvent, CardTapped, CardUntapped, PermanentDestroyedEvent, ReceivesDamageEvent, AttachedEvent, UnAttachedEvent, AttackerDeclaredEvent, AttackerBlockedEvent, BlockerDeclaredEvent, TokenLeavingPlay, TargetedByEvent, PowerToughnessChangedEvent, SubRoleAddedEvent, SubRoleRemovedEvent, NewTurnEvent, TimestepEvent, CounterAddedEvent

import new, inspect, copy
def rebind_self(obj):
    # Bind all unbound functions
    for name, func in inspect.getmembers(obj, inspect.ismethoddescriptor):
        if hasattr(func, "stacked"):
            func.rebind(obj)

class GameRole(MtGObject):
    def __init__(self, card):
        self.card = card
    def __deepcopy__(self,memo,mutable=set([list,set,dict])):
        newcopy = copy.copy(self)
        for attr, value in self.__dict__.iteritems():
            if type(value) in mutable: setattr(newcopy,attr,copy.copy(value))
            else: setattr(newcopy,attr,value)
        rebind_self(newcopy)
        return newcopy
    def __str__(self):
        return self.__class__.__name__

class NoRole(GameRole):
    # For token objects out of play
    def enteringGraveyard(self): pass
    def leavingGraveyard(self): pass
    def match_role(self, matchrole):
        return False

class CardRole(GameRole):  # Cards out of play
    def __init__(self, card):
        super(CardRole, self).__init__(card)
        self.abilities = []
        self.graveyard_abilities = []
        self.removed_abilities = []
    def enteringGraveyard(self):
        # I should change the name of these entering and leaving functions - maybe enteringZone
        for ability in self.graveyard_abilities: ability.enteringPlay()
    def leavingGraveyard(self):
        for ability in self.graveyard_abilities: ability.leavingPlay()
    def canDealDamage(self):
        return True
    def dealDamage(self, target, amount, combat=False):
        if target.canBeDamagedBy(self.card) and amount > 0:
            target.assignDamage(amount, source=self.card, combat=combat)
    def canBeTargetedBy(self, targeter): return True
    def canBeAttachedBy(self, targeter): return True
    def isTargetedBy(self, targeter):
        self.card.send(TargetedByEvent(), targeter=targeter)
    def match_role(self, matchrole):
        return matchrole == self.__class__

class SpellRole(GameRole):  # Spells on the stack
    def __init__(self, card):
        super(SpellRole, self).__init__(card)
        self.facedown = False
        self.abilities = []
    # the damage stuff seems kind of hacky
    def canDealDamage(self):
        return True
    def dealDamage(self, target, amount, combat=False):
        if target.canBeDamagedBy(self.card) and amount > 0:
            target.assignDamage(amount, source=self.card, combat=combat)
    def canBeTargetedBy(self, targeter): return True
    def canBeAttachedBy(self, targeter): return True
    def isTargetedBy(self, targeter):
        self.card.send(TargetedByEvent(), targeter=targeter)
    def faceDown(self):
        self.facedown = True
    def faceUp(self):
        self.facedown = False
    def match_role(self, matchrole):
        return matchrole == self.__class__

class Permanent(GameRole):
    def abilities():
        def fget(self):
            if not self._abilities:
                import operator
                self._abilities = reduce(operator.add, [role.abilities for role in self.subroles], [])
            return self._abilities
        return locals()
    abilities = property(**abilities())
    def __init__(self, card, subroles):
        super(Permanent, self).__init__(card)
        self._abilities = []
        if not (type(subroles) == list or type(subroles) == tuple): subroles = [subroles]
        self.subroles = subroles
        self.tapped = False
        self.flipped = False
        self.facedown = False
        self.attachments = []
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
    def canBeAttachedBy(self, targeter):
        result = True
        for role in self.subroles: 
            if not role.canBeAttachedBy(targeter):
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
        else: return not self.tapped
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
    def __deepcopy__(self, memo):
        newcopy = super(Permanent, self).__deepcopy__(memo)
        newcopy.subroles = [copy.deepcopy(role, memo) for role in self.subroles]
        return newcopy

class SubRole(object):
    def __init__(self):
        self.abilities = []
        self.triggered_abilities = []
        self.static_abilities = []
        self.keywords = keywords()
    def subrole_info(self): return ''
    def send(self, *args, **named):
        self.perm.card.send(*args, **named)
    def register(self, *args, **named):
        self.perm.card.register(*args, **named)
    def unregister(self, *args, **named):
        self.perm.card.unregister(*args, **named)
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
    def canBeAttachedBy(self, targeter): return True
    def canTap(self): return True
    def __deepcopy__(self,memo,mutable=set([list,set,dict])):
        # This only copies one level deep
        # So the subrole(s) are always the pristine one specified in the card definition
        newcopy = copy.copy(self)
        for attr, value in self.__dict__.iteritems():
            if type(value) in mutable:
                setattr(newcopy,attr,copy.copy(value))
            else:
                setattr(newcopy,attr,copy.deepcopy(value, memo))
        rebind_self(newcopy)
        return newcopy
    def __str__(self):
        return self.__class__.__name__

class Land(SubRole):
    def __init__(self, color):
        super(Land,self).__init__()
        self.color = color

class PTModifiers(object):
    def __init__(self):
        self._modifiers = []
    def add(self, PT):
        #self.role.send(PowerToughnessChangedEvent())
        self._modifiers.append(PT)
    def remove(self, PT):
        for i, modifier in enumerate(self._modifiers):
            if PT is modifier: break
        else: raise ValueError
        #self.role.send(PowerToughnessChangedEvent())
        self._modifiers.pop(i)
    def calculate(self, power, toughness):
        return reduce(lambda PT, modifier: modifier.calculate(PT[0], PT[1]), self._modifiers, (power, toughness))
    def __str__(self):
        return ', '.join([str(modifier) for modifier in self._modifiers])

class Creature(SubRole):
    def power():
        def fget(self):
            if self.cached_PT_dirty: self._calculate_power_toughness()
            return self.curr_power
        return locals()
    power = property(**power())
    def toughness():
        def fget(self):
            if self.cached_PT_dirty: self._calculate_power_toughness()
            return self.curr_toughness
        return locals()
    toughness = property(**toughness())
    def _calculate_power_toughness(self):
        # Calculate layering rules
        power, toughness = self.base_power, self.base_toughness # layer 6a
        power, toughness = self.PT_other_modifiers.calculate(power, toughness) # layer 6b
        power += sum([c.power for c in self.perm.counters if hasattr(c,"power")]) # layer 6c
        toughness += sum([c.toughness for c in self.perm.counters if hasattr(c,"toughness")]) # layer 6c
        power, toughness = self.PT_static_modifiers.calculate(power, toughness) # layer 6d
        power, toughness = self.PT_switch_modifiers.calculate(power, toughness) # layer 6e
        self.cached_PT_dirty = False
        self.curr_power, self.curr_toughness = power, toughness
    def __init__(self, power, toughness):
        super(Creature,self).__init__()
        # These are immutable and come from the card
        self.base_power = self.curr_power = power
        self.base_toughness = self.curr_toughness = toughness
        self.cached_PT_dirty = False

        # Only accessed internally
        self.__damage = 0

        self.PT_other_modifiers = PTModifiers() # layer 6b - other modifiers
        self.PT_static_modifiers = PTModifiers() # layer 6d - static modifiers
        self.PT_switch_modifiers = PTModifiers() # layer 6e - P/T switching modifiers
        self.in_combat = False
        self.attacking = False
        self.blocking = False
        self.blocked = False
    def subrole_info(self):
        txt = ["%d/%d"%(self.base_power, self.base_toughness)]
        txt.append(str(self.PT_other_modifiers))
        txt.append(', '.join([str(c) for c in self.perm.counters if hasattr(c,"power")]))
        txt.append(str(self.PT_static_modifiers))
        txt.append(str(self.PT_switch_modifiers))
        return 'P/T:\n'+'\n'.join(["6%s: %s"%(layer, mod) for layer, mod in zip("ABCDE", txt) if mod])
    def _PT_changed(self, sender): self.cached_PT_dirty=True
    def enteringPlay(self, perm):
        super(Creature,self).enteringPlay(perm)
        self.register(self._PT_changed, TimestepEvent())
        #self.register(self._PT_changed, PowerToughnessChangedEvent(), sender=self.card)
    def leavingPlay(self):
        super(Creature,self).leavingPlay()
        self.unregister(self._PT_changed, TimestepEvent())
        #self.unregister(PowerToughnessChangedEvent(), sender=self.card)
    def canBeDamagedBy(self, damager):
        return True
    def combatDamage(self):
        return self.power
    def clearDamage(self):
        self.__damage = 0
    def currentDamage(self):
        return self.__damage
    def assignDamage(self, amt, source, combat=False):
        from Ability.Counters import PowerToughnessCounter
        if amt > 0:
            if not "wither" in source.keywords: self.__damage += amt
            else:
                for counter in [PowerToughnessCounter(-1, -1) for i in range(amt)]:
                    self.card.counters.append(counter)
                    self.send(CounterAddedEvent(), counter=counter) 
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
    def continuouslyInPlay(self):
        return self.perm.continuously_in_play
    def checkAttack(self, attackers, not_attacking):
        return True
    def canAttack(self):
        return (not self.perm.tapped) and (not self.in_combat) and self.continuouslyInPlay()
    def checkBlock(self, combat_assignment, not_blocking):
        return True
    def canBeBlocked(self):
        return True
    def canBeBlockedBy(self, blocker):
        return True
    def canBlock(self):
        return not (self.perm.tapped or self.in_combat)
    def canBlockAttacker(self, attacker):
        return True
    def setBlocking(self, attacker):
        self.setCombat(True)
        self.blocking = True
        self.send(BlockerDeclaredEvent(), attacker=attacker)
    def setAttacking(self):
        self.setCombat(True)
        self.perm.tap()
        self.attacking = True
        self.send(AttackerDeclaredEvent())
    def setBlocked(self, blockers):
        if blockers:
            self.blocked = True
            self.send(AttackerBlockedEvent(), blockers=blockers)
    def setCombat(self, in_combat):
        self.in_combat = in_combat
    def computeBlockCost(self):
        self.block_cost = ["0"]
        return True
    def payBlockCost(self):
        player = self.card.controller
        from Cost import MultipleCosts
        cost = MultipleCosts(self.block_cost)
        if cost.precompute(self.card, player) and cost.compute(self.card, player):
            cost.pay(self.card, player)
    def computeAttackCost(self):
        self.attack_cost = ["0"]
        return True
    def payAttackCost(self):
        player = self.card.controller
        from Cost import MultipleCosts
        cost = MultipleCosts(self.attack_cost)
        if cost.precompute(self.card, player) and cost.compute(self.card, player):
            cost.pay(self.card, player)

    # These two override the functions in the Permanent
    def canTap(self): return self.continuouslyInPlay()
    def shouldDestroy(self):
        return self.__damage >= self.toughness

class TokenCreature(Creature):
    def leavingPlay(self):
        self.send(TokenLeavingPlay())
        super(TokenCreature,self).leavingPlay()

class Artifact(SubRole): pass
class Enchantment(SubRole): pass

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
    def isValidAttachment(self): return False

class Equipment(Attachment, Artifact):
    def __init__(self):
        from Match import isCreature
        super(Equipment,self).__init__()
        self.attached_to = None
        self.target_types = isCreature
    def isValidAttachment(self):
        attachment = self.attached_to
        return (str(attachment.zone) == "play" and self.target_types.match(attachment) and attachment.canBeAttachedBy(self.card))

class Aura(Attachment, Enchantment):
    def __init__(self, target_types=None):
        super(Aura,self).__init__()
        self.attached_to = None
        self.target_types = target_types
    def isValidAttachment(self):
        attachment = self.attached_to
        return (attachment and str(attachment.zone) == "play" and self.target_types.match(attachment) and attachment.canBeAttachedBy(self.card))
