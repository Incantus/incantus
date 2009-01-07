import new, weakref
from characteristics import stacked_controller, PTModifiers, stacked_characteristic, additional_characteristics
from GameObjects import MtGObject
from GameEvent import DealsDamageEvent, DealsDamageToEvent, ReceivesDamageEvent, CardTapped, CardUntapped, PermanentDestroyedEvent, AttachedEvent, UnAttachedEvent, AttackerDeclaredEvent, AttackerBlockedEvent, BlockerDeclaredEvent, TokenLeavingPlay, TargetedByEvent, PowerToughnessModifiedEvent, NewTurnEvent, TimestepEvent, CounterAddedEvent, CounterRemovedEvent, AttackerClearedEvent, BlockerClearedEvent, CreatureInCombatEvent, CreatureCombatClearedEvent
from Planeswalker import Planeswalker
from Ability.Counters import *
from Ability.PermanentAbility import basic_mana_ability
from Ability.EffectsUtilities import combine
from Ability.Subtypes import all_basic_lands

class CardRole(MtGObject):
    def info():
        def fget(self):
            txt = [str(self.name)]
            color = str(self.color)
            if color: txt.append("\n%s"%color)
            txt.append("\n")
            supertypes = str(self.supertypes)
            if supertypes: txt.append(supertypes+" ")
            cardtypes = str(self.types)
            if cardtypes: txt.append(cardtypes)
            subtypes = str(self.subtypes)
            if subtypes: txt.append(" - %s"%subtypes)
            abilities = str(self.abilities)
            if abilities: txt.append('\n\n%s'%abilities)
            if self.counters:
                count = {}
                for counter in self.counters:
                    count[str(counter)] = count.get(str(counter), 0)+1
                txt.append('\n\nCounters: %s'%', '.join(["%s (%d)"%(counter, num) for counter, num in count.items()]))
            #type_info = self.type_info()
            #if type_info: txt.append('\n\n'+type_info)
            return ''.join(txt)
        return locals()

    info = property(**info())
    controller = property(fget=lambda self: self.owner)
    converted_mana_cost = property(fget=lambda self: self.cost.converted_mana_cost())

    def __init__(self, key):
        self.key = key
        self.zone = None
        self._counters = []
        self.attachments = []
        self.facedown = False
    def canBeTargetedBy(self, targeter): return True
    def canBeAttachedBy(self, targeter): return True
    def isTargetedBy(self, targeter):
        self.send(TargetedByEvent(), targeter=targeter)
    def modifyEntering(self): pass
    def enteringZone(self, zone):
        self.zone = zone
        self.modifyEntering()
        self.abilities.enteringZone()
        self.is_LKI = False
    def leavingZone(self):
        self.is_LKI = True
        self.abilities.leavingZone()
        self.zone = None
    # DSL functions
    def move_to(self, zone, position="top"):
        if not self.is_LKI:
            if type(zone) == str:
                zone = getattr(self.owner, zone)
            return zone.move_card(self, position)
        else: return self
    def deal_damage(self, to, amount, combat=False):
        if amount > 0:
            final_dmg = to.assignDamage(amount, source=self, combat=combat)
            if final_dmg > 0:
                self.send(DealsDamageToEvent(), to=to, amount=final_dmg, combat=combat)
        else: final_dmg = 0
        return final_dmg
    def add_counters(self, counter_type, number=1):
        if type(counter_type) == str: counter_type = Counter(counter_type)
        for counter in [counter_type.copy() for i in range(number)]:
            self._counters.append(counter)
            self.send(CounterAddedEvent(), counter=counter)
    def remove_counters(self, counter_type=None, number=1):
        if counter_type: counters = [counter for counter in self._counters if counter == counter_type]
        else: counters = self._counters[:]
        if not number == -1: counters = counters[:number]
        for counter in counters:
            self._counters.remove(counter)
            self.send(CounterRemovedEvent(), counter=counter)
        return len(counters) # Return the number of counters we actually removed
    def num_counters(self, counter_type=None):
        if counter_type: return len([c for c in self._counters if c == counter_type])
        else: return len(self._counters)
    counters = property(fget=lambda self: self._counters)
    def cda_power_toughness(self, power, toughness):
        expire = []
        if power: expire.append(self.base_power.cda(power))
        if toughness: expire.append(self.base_toughness.cda(toughness))
        return combine(*expire)
    power = property(fget=lambda self: int(self.base_power))
    toughness = property(fget=lambda self: int(self.base_toughness))
    loyalty = property(fget=lambda self: int(self.base_loyalty))
    def faceDown(self):
        self.facedown = True
    def faceUp(self):
        self.facedown = False
    def clone(self, other, exclude=set(), extra={}):
        # copyable values
        reverse = []
        copyable = set(["name", "cost", "text", "abilities", "color", "supertypes", "subtypes", "types", "base_power", "base_toughness", "base_loyalty"])
        for name in copyable-exclude:
            obj = getattr(self, name)
            extra_copyable = extra.get(name, None)
            reverse.append(obj.set_copy(getattr(other, name).copyable, extra_copyable))
        return combine(*reverse)
    def __str__(self): return str(self.name)
    def __repr__(self): return "%s %s at %d"%(self.name, self.__class__.__name__, id(self))
    def __del__(self):
        pass
        #print "Deleting %s role for %s"%(self.__class__.__name__, self.name)

# For token objects out of play
class NoRole(CardRole):
    is_LKI = True

# Cards on the stack
class SpellRole(CardRole): pass

class Permanent(CardRole):
    controller = property(fget=lambda self: self._controller.current)
    continuously_in_play = property(fget=lambda self: self._continuously_in_play)
    def initialize_controller(self, controller):
        self._controller = stacked_controller(self, controller)
    def set_controller(self, new_controller):
        return self._controller.set(new_controller)
    def __init__(self, card):
        super(Permanent, self).__init__(card)
        self._controller = None
        self.tapped = False
        self.flipped = False
        self.facedown = False
        self._continuously_in_play = False
    def faceDown(self):
        self.facedown = True
    def faceUp(self):
        self.facedown = False
    def canBeTapped(self): # Called by game action (such as an effect)
        return not self.tapped
    def canTap(self): # Called as a result of user action
        return not self.tapped
    def tap(self):
        # Don't tap if already tapped:
        if self.canBeTapped():
            self.tapped = True
            self.send(CardTapped())
            return True
        else: return False
    def canUntap(self):
        return self.tapped
    canUntapDuringUntapStep = canUntap
    def untap(self):
        if self.tapped:
            self.tapped = False
            self.send(CardUntapped())
            return True
        else: return False
    def shouldDestroy(self):
        # This is called to check whether the permanent should be destroyed (by SBE)
        return True
    def canDestroy(self):
        # this can be replaced by regeneration for creatures - what about artifacts and enchantments?
        return True
    def destroy(self, regenerate=True):
        if not regenerate or self.canDestroy():
            self.move_to("graveyard")
            self.send(PermanentDestroyedEvent())
    def continuouslyInPlay(self):
        return self.continuously_in_play
    def summoningSickness(self):
        def remove_summoning_sickness(player):
            if self.controller == player:
                self.unregister(remove_summoning_sickness, NewTurnEvent(), weak=False)
                self._continuously_in_play = True
        self._continuously_in_play = False
        self.register(remove_summoning_sickness, NewTurnEvent(), weak=False)

    def modifyEntering(self):
        # Add the necessary superclasses, depending on our type/subtypes
        self.__class__ = new.classobj("_Permanent", (self.__class__,), {})
        self.add_basecls()
        super(Permanent, self).modifyEntering()
    def add_basecls(self):
        cls = self.__class__
        orig_bases = cls.__bases__
        if self.types == "Creature" and not Creature in orig_bases:
            cls.__bases__ = (Creature,)+orig_bases
            self.activateCreature()
        if self.types == "Land" and not Land in orig_bases:
            cls.__bases__ = (Land,)+orig_bases
            self.activateLand()
        if self.types == "Planeswalker" and not Planeswalker in orig_bases:
            cls.__bases__ = (Planeswalker,)+orig_bases
            self.activatePlaneswalker()
        if (self.subtypes.intersects(set(["Aura", "Equipment", "Fortification"]))) and not Attachment in orig_bases:
            cls.__bases__ = (Attachment,)+orig_bases
            self.activateAttachment()

class TokenPermanent(Permanent):
    _token = True
    def move_to(self, zone, position="top"):
        newrole = super(TokenPermanent, self).move_to(zone, position)
        if not str(zone) == "play": newrole.send(TokenLeavingPlay())
        return newrole

class stacked_land_subtype(stacked_characteristic):
    def __init__(self, orig_stacked):
        self._orig = orig_stacked
        self._stacking = orig_stacked._stacking
        self.card = orig_stacked.card
        self.change_event = orig_stacked.change_event
    def revert(self):
        self.card.subtypes = self._orig
    def set(self, *subtypes):
        if len(all_basic_lands.intersection(subtypes)) > 0:
            card = self.card
            expire1 = super(stacked_land_subtype, self).set(*subtypes)
            card._remove_all_basic_abilities()
            expire2 = card.abilities.remove_all()
            card._add_basic_abilities()
            return combine(expire1, expire2, card._remove_basic_abilities, card._add_basic_abilities)
        else:
            return self._insert_into_stacking(characteristic(*subtypes))
    def add(self, *subtypes):
        if len(all_basic_lands.intersection(subtypes)) > 0:
            expire = super(stacked_land_subtype, self).add(*subtypes)
            self.card._add_basic_abilities()
            return combine(expire, self.card._remove_basic_abilities)
        else:
            return self._insert_into_stacking(additional_characteristics(*subtypes))

class Land(object):
    _track_basic = dict([(subtype, {}) for subtype in all_basic_lands])
    def activateLand(self):
        self.subtypes = stacked_land_subtype(self.subtypes)
        self._add_basic_abilities()
    def leavingZone(self):
        self.subtypes.revert()
        super(Land,self).leavingZone()
    def _add_basic_abilities(self):
        for subtype in all_basic_lands:
            if self.subtypes == subtype and not self in self._track_basic[subtype]:
                self._track_basic[subtype][self] = self.abilities.add(basic_mana_ability(subtype))
    def _remove_basic_abilities(self):
        for subtype in all_basic_lands:
            if not self.subtypes == subtype:
                # Don't have basic subtype anymore, remove ability if it was added
                expire = self._track_basic[subtype].pop(self, None)
                if expire: expire()
    def _remove_all_basic_abilities(self):
        for subtype in all_basic_lands:
            expire = self._track_basic[subtype].pop(self, None)
            if expire: expire()

class Creature(object):
    def power():
        def fget(self):
            if self.cached_PT_dirty: self._calculate_power_toughness()
            return self.curr_power
        def fset(self, power):
            self.base_power.cda(power)
        return locals()
    power = property(**power())
    def toughness():
        def fget(self):
            if self.cached_PT_dirty: self._calculate_power_toughness()
            return self.curr_toughness
        def fset(self, toughness):
            self.base_toughness.cda(toughness)
        return locals()
    toughness = property(**toughness())
    def _calculate_power_toughness(self):
        # Calculate layering rules
        power, toughness = int(self.base_power), int(self.base_toughness) # layer 6a
        power, toughness = self.PT_other_modifiers.calculate(power, toughness) # layer 6b
        power += sum([c.power for c in self.counters if hasattr(c,"power")]) # layer 6c
        toughness += sum([c.toughness for c in self.counters if hasattr(c,"toughness")]) # layer 6c
        power, toughness = self.PT_static_modifiers.calculate(power, toughness) # layer 6d
        power, toughness = self.PT_switch_modifiers.calculate(power, toughness) # layer 6e
        #self.cached_PT_dirty = False
        self.curr_power, self.curr_toughness = power, toughness
    def _new_timestep(self, sender):
        self.cached_PT_dirty=True
    def activateCreature(self):
        self.curr_power = self.curr_toughness = 0
        self.cached_PT_dirty = False

        # Only accessed internally
        self.__damage = 0

        proxy = weakref.proxy(self)
        self.PT_other_modifiers = PTModifiers(proxy) # layer 6b - other modifiers
        self.PT_static_modifiers = PTModifiers(proxy) # layer 6d - static modifiers
        self.PT_switch_modifiers = PTModifiers(proxy) # layer 6e - P/T switching modifiers
        self.in_combat = False
        self.attacking = False
        self.blocking = False
        self.blocked = False
        self.cached_PT_dirty = True

        self.register(self._new_timestep, TimestepEvent())
    def leavingZone(self):
        self.unregister(self._new_timestep, TimestepEvent())
        super(Creature,self).leavingZone()
    def combatDamage(self):
        return self.power
    def clearDamage(self):
        self.__damage = 0
    def currentDamage(self):
        return self.__damage
    def lethalDamage(self):
        return self.toughness - self.__damage
    def assignDamage(self, amt, source, combat=False):
        # Damage is always greater than 0
        if not self.is_LKI:
            if "wither" in source.abilities: self.add_counters(PowerToughnessCounter(-1, -1), amt)
            else: self.__damage += amt
        return amt
    def trample(self, damage_assn):
        from Match import isCreature
        total_damage = self.combatDamage()
        total_applied = 0
        not_enough = False
        for b in damage_assn.keys():
            # Skip players and blockers who no longer exist
            if not isCreature(b): continue
            # if total assigned damage is lethal
            if damage_assn[b] < b.lethalDamage():
                not_enough = True
                break
            total_applied += damage_assn[b]
        if not_enough: return 0
        else: return total_damage - total_applied
    def canTap(self):
        return self.continuouslyInPlay() and super(Creature, self).canTap()
    def canUntap(self):
        return self.continuouslyInPlay() and super(Creature, self).canUntap()
    def checkAttack(self, attackers, not_attacking):
        return True
    def canAttack(self):
        return (not self.tapped) and (not self.in_combat) and self.continuouslyInPlay()
    def checkBlock(self, combat_assignment, not_blocking):
        return True
    def canBeBlocked(self):
        return True
    def canBeBlockedBy(self, blocker):
        return True
    def canBlock(self):
        return not (self.tapped or self.in_combat)
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
    def setOpponent(self, opponent):
        self.opponent = opponent
    def setAttacking(self):
        self.setCombat(True)
        self.tap()
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
        player = self.controller
        cost = MultipleCosts(self.block_cost)
        if cost.precompute(self, player) and cost.compute(self, player):
            cost.pay(self, player)
    def computeAttackCost(self):
        self.attack_cost = ["0"]
        return True
    def payAttackCost(self):
        from Ability.Cost import MultipleCosts
        player = self.controller
        cost = MultipleCosts(self.attack_cost)
        if cost.precompute(self, player) and cost.compute(self, player):
            cost.pay(self, player)
    def shouldDestroy(self):
        return self.__damage >= self.toughness and super(Creature, self).shouldDestroy()

    def set_power_toughness(self, power, toughness):
        PT = PowerToughnessSetter(power, toughness)
        return self.PT_other_modifiers.add(PT)
    def set_power(self, power):
        PT = PowerSetter(power, None)
        return self.PT_other_modifiers.add(PT)
    def set_toughness(self, toughness):
        PT = ToughnessSetter(None, toughness)
        return self.PT_other_modifiers.add(PT)
    def augment_power_toughness(self, power, toughness):
        PT = PowerToughnessModifier(power, toughness)
        return self.PT_other_modifiers.add(PT)
    def augment_power_toughness_static(self, power, toughness):
        PT = PowerToughnessModifier(power, toughness)
        return self.PT_static_modifiers.add(PT)
    def switch_power_toughness(self):
        PT = PowerToughnessSwitcher()
        return self.PT_switch_modifiers.add(PT)

    def type_info(self):
        txt = ["%d/%d"%(self.base_power, self.base_toughness)]
        txt.append(str(self.PT_other_modifiers))
        txt.append(', '.join([str(c) for c in self.counters if hasattr(c,"power")]))
        txt.append(str(self.PT_static_modifiers))
        txt.append(str(self.PT_switch_modifiers))
        return 'P/T:\n'+'\n'.join(["6%s: %s"%(layer, mod) for layer, mod in zip("ABCDE", txt) if mod])

class Attachment(object):
    attached_abilities = property(fget=lambda self: self.abilities.attached())
    attached_to = property(fget=lambda self: self._attached_to)
    def activateAttachment(self):
        from Match import isLand, isCreature
        self._attached_to = None
        self.target_zone = "play"
        self.target_player = None
        if self.subtypes == "Equipment":
            self.target_type = isCreature
        elif self.subtypes == "Fortification":
            self.target_type = isLand
    def leavingZone(self):
        self.unattach()
        super(Attachment,self).leavingZone()
    def attach(self, target):
        if self._attached_to != None: self.unattach()
        self._attached_to = target
        self._attached_to.attachments.append(self)
        for ability in self.attached_abilities: ability.enable(self)
        self.send(AttachedEvent(), attached=self._attached_to)
        return self.unattach
    def unattach(self):
        if self._attached_to:
            for ability in self.attached_abilities: ability.disable()
            self._attached_to.attachments.remove(self)
            self.send(UnAttachedEvent(), unattached=self._attached_to)
        self._attached_to = None
    def isValidAttachment(self, attachment=None):
        return self.canBeAttachedTo(self.attached_to)
    def canBeAttachedTo(self, attachment):
        if self.target_player:
            check_player = (self.target_player == "you" and attachment.controller == self.controller) or (self.target_player == "opponent" and attachment.controller in self.controller.opponents)
        else: check_player = True
        return (attachment and str(attachment.zone) == self.target_zone and check_player and self.target_type(attachment) and attachment.canBeAttachedBy(self))
