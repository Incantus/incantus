import copy, itertools
from GameObjects import MtGObject
from GameEvent import DealsDamageEvent, DealsDamageToEvent, ReceivesDamageEvent, CardTapped, CardUntapped, PermanentDestroyedEvent, PermanentSacrificedEvent, AttachedEvent, UnAttachedEvent, AttackerDeclaredEvent, AttackerBlockedEvent, BlockerDeclaredEvent, TokenLeavingPlay, TargetedByEvent, PowerToughnessChangedEvent, SubRoleAddedEvent, SubRoleRemovedEvent, NewTurnEvent, TimestepEvent, CounterAddedEvent, CounterRemovedEvent, AttackerClearedEvent, BlockerClearedEvent, CreatureInCombatEvent, CreatureCombatClearedEvent, ControllerChanged
from Ability.Counters import Counter, PowerToughnessCounter

class GameRole(MtGObject):
    def info():
        def fget(self): 
            txt = [str(self.name)]
            color = str(self.color)
            if color: txt.append("\n%s"%color)
            txt.append("\n") 
            supertype = str(self.supertype)
            if supertype: txt.append(supertype+" ")
            txt.append(str(self.type))
            subtypes = str(self.subtypes)
            if subtypes: txt.append(" - %s"%subtypes)
            abilities = str(self.abilities)
            if abilities: txt.append('\n\n%s'%abilities)
            if self.counters: txt.append('\n\nCounters: %s'%', '.join(map(str,self.counters)))
            subrole_info = self.subrole_info()
            if subrole_info: txt.append('\n\n'+subrole_info)
            return ''.join(txt)
        return locals()
    info = property(**info())
    controller = property(fget=lambda self: self.card.owner)
    zone = property(fget=lambda self: self.card.zone)
    def __init__(self, card):
        self.card = card
        self._counters = []
    # the damage stuff seems kind of hacky
    def send(self, *args, **named):
        self.card.send(*args, **named)
    def dealDamage(self, target, amount, combat=False):
        final_dmg = 0
        if target.canBeDamagedBy(self.card) and amount > 0:
            final_dmg = target.assignDamage(amount, source=self.card, combat=combat)
            if final_dmg > 0: self.send(DealsDamageToEvent(), to=target, amount=final_dmg, combat=combat)
        #self.send(DealsDamageEvent(), amount=final_dmg, combat=combat)
        return final_dmg
    def canBeTargetedBy(self, targeter): return True
    def canBeAttachedBy(self, targeter): return True
    def isTargetedBy(self, targeter):
        self.send(TargetedByEvent(), targeter=targeter)
    def enteringZone(self, zone): self.abilities.enteringZone(zone)
    def leavingZone(self, zone): self.abilities.leavingZone(zone)
    def match_role(self, matchrole):
        return matchrole == self.__class__
    def move_to(self, zone, position="top"):
        self.card.move_to(zone, position)
    def add_counters(self, counter_type, number=1):
        if type(counter_type) == str: counter_type = Counter(counter_type)
        for counter in [counter_type.copy() for i in range(number)]:
            self._counters.append(counter)
            self.send(CounterAddedEvent(), counter=counter)
    def remove_counters(self, counter_type, number=1):
        num = 0
        for counter in itertools.islice((c for c in self._counters if c == counter_type), number):
            num += 1
            self._counters.remove(counter)
            self.send(CounterRemovedEvent(), counter=counter)
        return num  # Return the number of counters we actually removed
    def num_counters(self, counter=None):
        if counter: return len([c for c in self._counters if c == counter])
        else: return len(self._counters)
    counters = property(fget=lambda self: self._counters)
    def __deepcopy__(self,memo,mutable=set([list,set,dict])):
        newcopy = copy.copy(self)
        for attr, value in self.__dict__.iteritems():
            if type(value) in mutable: setattr(newcopy,attr,copy.copy(value))
            #elif callable(value): setattr(newcopy,attr, value)
            #else: setattr(newcopy,attr,copy.deepcopy(value,memo))
            else: setattr(newcopy,attr, value)
        return newcopy
    def __str__(self):
        return self.__class__.__name__

class NoRole(GameRole):
    # For token objects out of play
    def match_role(self, matchrole):
        return False

class CardRole(GameRole):  # Cards out of play
    def __init__(self, card):
        super(CardRole, self).__init__(card)

class SpellRole(GameRole):  # Spells on the stack
    def __init__(self, card):
        super(SpellRole, self).__init__(card)
        self.facedown = False
    def faceDown(self):
        self.facedown = True
    def faceUp(self):
        self.facedown = False

class Permanent(GameRole):
    def controller():
        doc = "The controller of this card - only valid when in play or on the stack"
        def fget(self): return self._controller
        def fset(self, controller):
            if controller == None: self._controller = controller
            elif not controller == self._controller:
                self._controller, old_controller = controller, self._controller
                self.summoningSickness()
                if old_controller: self.send(ControllerChanged(), original=old_controller)
        return dict(doc=doc, fset=fset, fget=fget)
    controller = property(**controller())
    continuously_in_play = property(fget=lambda self: self._continuously_in_play)
    def __init__(self, card, subroles):
        super(Permanent, self).__init__(card)
        self._controller = None
        if not (type(subroles) == list or type(subroles) == tuple): subroles = [subroles]
        self.subroles = subroles
        self.tapped = False
        self.flipped = False
        self.facedown = False
        self.attachments = []
        self._continuously_in_play = False
    def get_subrole(self, matchrole):
        for role in self.subroles:
            if isinstance(role, matchrole): return role
        return None
    def add_subrole(self, role):
        role.enteringPlay(self)
        self.subroles.append(role)
        self.send(SubRoleAddedEvent(), subrole=role)
    def remove_subrole(self, role):
        # XXX Is this correct - the role is only missing when card enters play, gains role for the turn,
        # and then is blinked back
        if role in self.subroles:
            role.leavingPlay()
            self.subroles.remove(role)
            self.send(SubRoleRemovedEvent(), subrole=role)
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
    def faceDown(self):
        self.facedown = True
    def faceUp(self):
        self.facedown = False
    def canBeTapped(self): # Called by game action (such as an effect)
        return not self.tapped
    def canTap(self): # Called as a result of user action
        for role in self.subroles:
            if not role.canTap(): return False
        else: return not self.tapped
    def tap(self):
        # Don't tap if already tapped:
        if self.canBeTapped():
            self.tapped = True
            self.send(CardTapped())
            return True
        else: return False
    def canUntap(self):
        return self.tapped
    def untap(self):
        if self.tapped:
            self.tapped = False
            self.send(CardUntapped())
            return True
        else: return False
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
    def destroy(self, regenerate=True):
        if not regenerate or self.canDestroy():
            self.move_to(self.owner.graveyard)
            self.send(PermanentDestroyedEvent())
    def sacrifice(self):
        self.move_to(self.owner.graveyard)
        self.send(PermanentSacrificedEvent())
    def summoningSickness(self):
        def remove_summoning_sickness(player):
            if self.controller == player:
                self.unregister(remove_summoning_sickness, NewTurnEvent(), weak=False)
                self._continuously_in_play = True
        self._continuously_in_play = False
        self.register(remove_summoning_sickness, NewTurnEvent(), weak=False)
    def enteringZone(self, zone):
        for role in self.subroles: role.enteringPlay(self)
        super(Permanent, self).enteringZone(zone)
    def leavingZone(self, zone):
        for role in self.subroles: role.leavingPlay()
        for attached in self.attachments: attached.attachedLeavingPlay()
        super(Permanent, self).leavingZone(zone)
    def __deepcopy__(self, memo):
        newcopy = super(Permanent, self).__deepcopy__(memo)
        newcopy.subroles = [copy.deepcopy(role, memo) for role in self.subroles]
        return newcopy

class SubRole(object):
    def subrole_info(self): return ''
    def send(self, *args, **named):
        self.perm.send(*args, **named)
    def register(self, *args, **named):
        self.perm.card.register(*args, **named)
    def unregister(self, *args, **named):
        self.perm.card.unregister(*args, **named)
    def enteringPlay(self, perm):
        self.perm = perm
        self.card = perm.card
    def leavingPlay(self): pass
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
            if type(value) in mutable: setattr(newcopy,attr,copy.copy(value))
            elif callable(value): setattr(newcopy,attr, value)
            else: setattr(newcopy,attr,copy.deepcopy(value, memo))
        return newcopy
    def __str__(self):
        return self.__class__.__name__

class Land(SubRole): pass

# PowerToughnessChanged isn't needed, because the power/toughness is invalidated every timestep (and the gui calculates it)
class PTModifiers(object):
    def __init__(self):
        self._modifiers = []
    def add(self, PT):
        self._modifiers.append(PT)
        #self.subrole.send(PowerToughnessChangedEvent())
        def remove():
            self._modifiers.remove(PT)
            #self.subrole.send(PowerToughnessChangedEvent())
        return remove
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
        return '' #'P/T:\n'+'\n'.join(["6%s: %s"%(layer, mod) for layer, mod in zip("ABCDE", txt) if mod])
    def _PT_changed(self, sender): self.cached_PT_dirty=True
    def enteringPlay(self, perm):
        super(Creature,self).enteringPlay(perm)
        self.cached_PT_dirty = True
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
        if amt > 0:
            if "wither" in source.abilities: self.perm.add_counters(PowerToughnessCounter(-1, -1), amt)
            else: self.__damage += amt
            self.send(ReceivesDamageEvent(), source=source, amount=amt, combat=combat)
        return amt
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
    def clearCombatState(self):
        self.setCombat(False)    # XXX Should be a property that sends a signal when set
        if self.attacking:
            self.attacking = False
            self.send(AttackerClearedEvent())
            self.blocked = False
        elif self.blocking:
            self.blocking = False
            self.send(BlockerClearedEvent())
    def setAttacking(self):
        self.setCombat(True)
        self.perm.tap()
        self.attacking = True
        self.send(AttackerDeclaredEvent())
    def setBlocked(self, blockers):
        if blockers:
            self.blocked = True
            self.send(AttackerBlockedEvent(), blockers=blockers)
    def setBlocking(self, attacker):
        self.setCombat(True)
        self.blocking = True
        self.send(BlockerDeclaredEvent(), attacker=attacker)
    def setCombat(self, in_combat):
        self.in_combat = in_combat
        if in_combat: self.send(CreatureInCombatEvent())
        else: self.send(CreatureCombatClearedEvent())
    def computeBlockCost(self):
        self.block_cost = ["0"]
        return True
    def payBlockCost(self):
        from Ability.Cost import MultipleCosts
        player = self.card.controller
        cost = MultipleCosts(self.block_cost)
        if cost.precompute(self.card, player) and cost.compute(self.card, player):
            cost.pay(self.card, player)
    def computeAttackCost(self):
        self.attack_cost = ["0"]
        return True
    def payAttackCost(self):
        from Ability.Cost import MultipleCosts
        player = self.card.controller
        cost = MultipleCosts(self.attack_cost)
        if cost.precompute(self.card, player) and cost.compute(self.card, player):
            cost.pay(self.card, player)

    # These two override the functions in the Permanent
    def canTap(self): return self.continuouslyInPlay()
    def shouldDestroy(self):
        return self.__damage >= self.toughness

class Artifact(SubRole): pass
class Enchantment(SubRole): pass

class Attachment(object):
    attached_abilities = property(fget=lambda self: self.perm.abilities.attached())
    def attach(self, target):
        if self.attached_to != None: self.unattach()
        self.attached_to = target
        self.attached_to.attachments.append(self.perm.card)
        for ability in self.attached_abilities: ability.enteringZone(target)
        self.send(AttachedEvent(), attached=self.attached_to)
        return True
    def unattach(self):
        if self.attached_to:
            for ability in self.attached_abilities: ability.leavingZone()
            self.attached_to.attachments.remove(self.perm.card)
            self.send(UnAttachedEvent(), unattached=self.attached_to)
        self.attached_to = None
    def attachedLeavingPlay(self):
        for ability in self.attached_abilities: ability.leavingZone()
        self.send(UnAttachedEvent(), unattached=self.attached_to)
        self.attached_to = None
    def leavingPlay(self):
        self.unattach()
        super(Attachment,self).leavingPlay()
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
