import new
from stacked_function import *
from characteristics import stacked_controller, stacked_PT, stacked_land_subtype
from symbols import Land, Creature, Planeswalker, Instant, Sorcery, Aura, Equipment, Fortification
from MtGObject import MtGObject
from GameEvent import DealsDamageToEvent, CardTapped, CardUntapped, PermanentDestroyedEvent, AttachedEvent, UnAttachedEvent, AttackerDeclaredEvent, AttackerBlockedEvent, BlockerDeclaredEvent, NonCardLeavingZone, TargetedByEvent, PowerToughnessModifiedEvent, NewTurnEvent, TimestepEvent, CounterAddedEvent, CounterRemovedEvent, AttackerClearedEvent, BlockerClearedEvent, CreatureInCombatEvent, CreatureCombatClearedEvent, LandPlayedEvent
from Planeswalker import PlaneswalkerType
from Ability.Counters import Counter, PowerToughnessCounter, PowerToughnessModifier, PowerToughnessSetter, PowerToughnessSwitcher, PowerSetter, ToughnessSetter
from Ability.CastingAbility import CastPermanentSpell, CastAuraSpell
from Ability.LandAbility import basic_mana_ability
from Ability.EffectsUtilities import combine
from symbols.subtypes import all_basic_lands
from Ability.Cost import Cost, MultipleCosts
from Ability.Limit import sorcery_limit, no_limit
from Ability.CiPAbility import CiP, enter_tapped, attach_on_enter
from Ability.Cost import ManaCost

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
            type_info = self.type_info()
            if type_info: txt.append('\n\n'+type_info)
            return ''.join(txt)
        return locals()

    info = property(**info())
    def type_info(self): return ""

    controller = property(fget=lambda self: self.owner)
    converted_mana_cost = property(fget=lambda self: self.cost.converted_mana_cost())

    def __init__(self, key):
        # Insert dummy class for mixins - this should probably be a metaclass thing
        cls = self.__class__
        self.__class__ = new.classobj("_%s"%cls.__name__, (cls,), {})
        self.key = key
        self.zone = None
        self._counters = []
        self.attachments = []

    @overridable(logical_and)
    def canBeTargetedBy(self, targeter): return True
    @overridable(logical_and)
    def canBeAttachedBy(self, targeter): return True
    def isTargetedBy(self, targeter):
        self.send(TargetedByEvent(), targeter=targeter)

    @overridable(do_all)
    def modifyEntering(self):
        # Add the necessary superclasses, depending on our type/subtypes
        self.activate()
    @overridable(do_all)
    def modifyNewRole(self, new_role, zone): pass
    def activate(self):
        cls = self.__class__
        orig_bases = cls.__bases__
        if self.types == Land and not LandType in orig_bases:
            cls.__bases__ = (LandType,)+orig_bases
            self.activateLand()
    def enteringZone(self, zone):
        self.zone = zone
        self.modifyEntering()
        self.abilities.enteringZone()
        self.is_LKI = False
    def leavingZone(self):
        self.is_LKI = True
        self.abilities.leavingZone()
        #self.zone = None
    # DSL functions
    def move_to(self, zone, position="top"):
        if not self.is_LKI:
            if isinstance(zone, str):
                zone = getattr(self.owner, zone)
            return zone.move_card(self, position)
        else: return self
    def deal_damage(self, to, amount, combat=False):
        if amount > 0: final_dmg = to.assignDamage(amount, source=self, combat=combat)
        else: final_dmg = 0
        if "lifelink" in self.abilities: self.controller.life += final_dmg
        return final_dmg
    def add_counters(self, counter_type, number=1):
        if isinstance(counter_type, str): counter_type = Counter(counter_type)
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
        if power is not None: expire.append(self.base_power.cda(power))
        if toughness is not None: expire.append(self.base_toughness.cda(toughness))
        return combine(*expire)
    power = property(fget=lambda self: int(self.base_power))
    toughness = property(fget=lambda self: int(self.base_toughness))
    loyalty = property(fget=lambda self: int(self.base_loyalty))
    def clone(self, other, exclude=set(), extra={}):
        # Allow "lazy" exclusion: typing exclude="color" or exclude="name" or even exclude=("color", "name") will still result in the needed set.
        if not isinstance(exclude, set):
            if not isinstance(exclude, (list, tuple)):
                exclude = (exclude,)
            exclude = set(exclude)
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
    def __getattr__(self, attr):
        # Any attribute not defined should be false
        return False
    def __del__(self):
        #print "Deleting %s role for %3d)%s in zone %s"%(self.__class__.__name__, self.key[0],self.name, self.zone)
        pass
    @overridable(do_sum)
    def get_special_actions(self):
        return []
    def setup_special_action(self, action):
        return override(self, "get_special_actions", lambda self: [action])

# Idea for spells - just have the OutBattlefieldRole mirror a cast spell in terms of when it
# can be played and its cost
# Cards on the stack
class SpellRole(CardRole):
    controller = property(lambda self: self._spell_controller)
    def activate(self):
        if self.subtypes == Aura: self.abilities.add(attach_on_enter())
        super(SpellRole, self).activate()
    def get_casting_cost(self):
        # Handle alternative costs - default is casting cost

        # "Special" costs are set during spell resolution,
        # as in "play that card without paying its mana cost".
        cost = self._get_special_cost()
        if not cost:
            alternative = self._get_alternative_costs()
            if len(alternative) > 1:
                # get player to choose
                cost = self.controller.make_selection(alternative, prompt="choose alternative cost")
            else: cost = alternative[0]

        # Additional costs
        additional = self._get_additional_costs()
        if additional: cost = cost+additional
        return cost
    def set_casting_cost(self, cost):
        return override(self, "_get_special_cost", lambda self: cost)
    @overridable(do_sum)
    def _get_additional_costs(self):
        return Cost()
    @overridable(do_sum)
    def _get_alternative_costs(self):
        return [self.cost.current]
    @overridable(most_recent)
    def _get_special_cost(self):
        return None

class CopySpellRole(SpellRole):
    def move_to(self, zone, position="top"):
        newrole = super(CopySpellRole, self).move_to(zone, position)
        newrole.is_LKI = True
        newrole.send(NonCardLeavingZone())
        return newrole


class NonBattlefieldRole(CardRole):
    @overridable(logical_or)
    def _playable_timing(self):
        return self._timing(self)
    @overridable(logical_or)
    def _playable_zone(self):
        return str(self.zone) == "hand"
    @overridable(logical_or)
    def _playable_other_restrictions(self):
        return False
    def playable(self):
        return (self._playable_timing() and self._playable_zone() and
                not self._playable_other_restrictions())
        #return self._play_spell.playable()
    # These are helper functions
    def play_without_mana_cost(self, player):
        def modifyNewRole(self, new, zone):
            if str(zone) == "stack":
                new.set_casting_cost(ManaCost("0"))
        override(self, "modifyNewRole", modifyNewRole)
        if not self._playable_other_restrictions():
            self.play(player)
            return True
        else: return False
    def move_to_battlefield_tapped(self, txt):
        CiP(self, enter_tapped, txt=txt)
        self.move_to("battlefield")

class OtherNonBattlefieldRole(NonBattlefieldRole):
    def activate(self):
        if self.types == Instant: self._timing = no_limit
        else: self._timing = sorcery_limit

        if self.subtypes == Aura:
            self.abilities.add(CastAuraSpell(), attach_on_enter())
        else: self.abilities.add(CastPermanentSpell())
        self._play_spell = self.abilities.cast()
        super(OtherNonBattlefieldRole, self).activate()
    def play(self, player):
        # XXX This is an ugly ugly hack
        play_ability = self._play_spell.copy()
        play_ability.controller = player
        play_ability.source = self
        return play_ability.announce()

class LandNonBattlefieldRole(NonBattlefieldRole):
    def activate(self):
        self._timing = sorcery_limit
        super(LandNonBattlefieldRole, self).activate()
    @overridable(logical_or)
    def _playable_other_restrictions(self):
        return (self.owner.land_actions < 1 or 
               super(LandNonBattlefieldRole,self)._playable_other_restrictions())
    def play(self, player):
        player.land_actions -= 1
        card = self.move_to(player.battlefield)
        player.send(TimestepEvent())
        # do we send the original or new land?
        player.send(LandPlayedEvent(), card=card)
        return True

class TokenNonBattlefieldRole(CardRole):
    is_LKI = True
    def move_to_battlefield_tapped(self, txt):
        CiP(self, enter_tapped, txt=txt)
        self.move_to("battlefield")

class EmblemRole(CardRole):
    def move_to(self, zone, position="top"):
        if not str(zone) == "command":
            # How would this ever happen?
            print "Hey, you! Don't try to put an emblem anywhere but the command zone!"
            return False
    def __str__(self):
        return self.text

# This handles cards that can't exist in certain zones (like lands on the stack,
# non-permanents on the battlefield
class NoRole(CardRole):
    def enteringZone(self, zone):
        raise Exception()

class Permanent(CardRole):
    controller = property(fget=lambda self: self._controller.current)
    continuously_on_battlefield = property(fget=lambda self: self._continuously_on_battlefield)
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
        self._continuously_on_battlefield = False
    def facedown(self):
        self.facedown = True
    def faceup(self):
        self.facedown = False
    def canBeTapped(self): # Called by game action (such as an effect)
        return not self.tapped
    @overridable(logical_and)
    def canTap(self): # Called as a result of user action
        return not self.tapped
    def tap(self):
        # Don't tap if already tapped:
        if self.canBeTapped():
            self.tapped = True
            self.send(CardTapped())
            return True
        else: return False
    @overridable(logical_and)
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
    @overridable(logical_and)
    def destroy(self, regenerate=True):
        if not regenerate or self.canDestroy():
            destroyed = self.move_to("graveyard")
            self.send(PermanentDestroyedEvent())
            return destroyed
        else: return self
    @overridable(logical_or)
    def continuouslyOnBattlefield(self):
        return self.continuously_on_battlefield
    def summoningSickness(self):
        def remove_summoning_sickness(player):
            if self.controller == player:
                self.unregister(remove_summoning_sickness, NewTurnEvent(), weak=False)
                self._continuously_on_battlefield = True
        self._continuously_on_battlefield = False
        self.register(remove_summoning_sickness, NewTurnEvent(), weak=False)

    def activate(self):
        cls = self.__class__
        orig_bases = cls.__bases__
        if self.types == Creature and not CreatureType in orig_bases:
            cls.__bases__ = (CreatureType,)+orig_bases
            self.activateCreature()
        if self.types == Planeswalker and not PlaneswalkerType in orig_bases:
            cls.__bases__ = (PlaneswalkerType,)+orig_bases
            self.activatePlaneswalker()
        if (self.subtypes.intersects(set([Aura, Equipment, Fortification]))) and not AttachmentType in orig_bases:
            cls.__bases__ = (AttachmentType,)+orig_bases
            self.activateAttachment()
        super(Permanent, self).activate()

class TokenPermanent(Permanent):
    _token = True
    def move_to(self, zone, position="top"):
        newrole = super(TokenPermanent, self).move_to(zone, position)
        newrole.is_LKI = True
        newrole.send(NonCardLeavingZone())
        return newrole

class LandType(object):
    _track_basic = dict([(subtype, {}) for subtype in all_basic_lands])
    def activateLand(self):
        self.subtypes = stacked_land_subtype(self.subtypes)
        self._add_basic_abilities()
    def leavingZone(self):
        self.subtypes.revert()
        super(LandType,self).leavingZone()
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

class CreatureType(object):
    def power():
        def fget(self):
            if self._cached_PT_dirty: self._calculate_power_toughness()
            return self.curr_power
        def fset(self, power):
            self.base_power.cda(power)
        return locals()
    power = property(**power())
    def toughness():
        def fget(self):
            if self._cached_PT_dirty: self._calculate_power_toughness()
            return self.curr_toughness
        def fset(self, toughness):
            self.base_toughness.cda(toughness)
        return locals()
    toughness = property(**toughness())
    def _calculate_power_toughness(self):
        # Calculate layering rules
        power, toughness = int(self.base_power), int(self.base_toughness) # layer 7a
        power, toughness = self.PT_set_modifiers.calculate(power, toughness) # layer 7b
        power, toughness = self.PT_augment_modifiers.calculate(power, toughness) # layer 7c
        power += sum([c.power for c in self.counters if hasattr(c,"power")]) # layer 7d
        toughness += sum([c.toughness for c in self.counters if hasattr(c,"toughness")]) # layer 7d
        power, toughness = self.PT_switch_modifiers.calculate(power, toughness) # layer 7e
        #self._cached_PT_dirty = False
        self.curr_power, self.curr_toughness = power, toughness
    def _new_timestep(self, sender):
        self._cached_PT_dirty=True
    def activateCreature(self):
        self.curr_power = self.curr_toughness = 0
        self._cached_PT_dirty = False

        # Only accessed internally
        self.__damage = 0
        self.deathtouched = False

        self.PT_set_modifiers = stacked_PT(self) # layer 7b - setting PT modifiers
        self.PT_augment_modifiers = stacked_PT(self) # layer 7c - augment PT modifiers
        self.PT_switch_modifiers = stacked_PT(self) # layer 7e - P/T switching modifiers
        self.in_combat = False
        self.did_strike = False
        self.attacking = False
        self.blocking = False
        self.blocked = False
        self.blockers = set()
        self._cached_PT_dirty = True

        self.register(self._new_timestep, TimestepEvent())
    def leavingZone(self):
        self.unregister(self._new_timestep, TimestepEvent())
        super(CreatureType,self).leavingZone()
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
            if "wither" in source.abilities or "infect" in source.abilities: self.add_counters(PowerToughnessCounter(-1, -1), amt)
            else: self.__damage += amt
            if "deathtouch" in source.abilities: self.deathtouched = True
        source.send(DealsDamageToEvent(), to=self, amount=amt, combat=combat)
        return amt
    def trample(self, damage_assn):
        total = self.combatDamage()
        for blocker, damage in damage_assn.items():
            total -= damage
            # if total assigned damage is not lethal,
            # can't trample any to defending player
            if damage < blocker.lethalDamage():
                return 0
        else: return total
    def canTap(self):
        return self.continuouslyOnBattlefield() and super(CreatureType, self).canTap()
    def canUntap(self):
        return self.continuouslyOnBattlefield() and super(CreatureType, self).canUntap()
    @overridable(logical_and)
    def checkAttack(self, attackers, not_attacking):
        return True
    @overridable(logical_and)
    def canAttack(self):
        return (not self.tapped) and (not self.in_combat) and self.continuouslyOnBattlefield()
    @overridable(logical_and)
    def canAttackSpecific(self, other):
        return True
    @overridable(logical_and)
    def checkBlock(self, combat_assignment, not_blocking):
        return True
    @overridable(logical_and)
    def canBeBlocked(self):
        return True
    @overridable(logical_and)
    def canBeBlockedBy(self, blocker):
        return True
    @overridable(logical_and)
    def canBlock(self):
        return not (self.tapped or self.in_combat)
    @overridable(logical_and)
    def canBlockAttacker(self, attacker):
        return True
    def didStrike(self):
        self.did_strike = True
    def canStrike(self, is_first_strike):
        if is_first_strike:
            return ("first strike" in self.abilities or "double strike" in self.abilities)
        else:
            return (not self.did_strike or "double strike" in self.abilities)
    def clearCombatState(self):
        self.setCombat(False)    # XXX Should be a property that sends a signal when set
        self.did_strike = False
        if self.attacking:
            self.attacking = False
            self.send(AttackerClearedEvent())
            self.blocked = False
            self.blockers.clear()
        elif self.blocking:
            self.blocking = False
            self.send(BlockerClearedEvent())
    def setOpponent(self, opponent):
        self.opponent = opponent
    @overridable(logical_and)
    def setAttacking(self):
        self.setCombat(True)
        self.tap()
        self.attacking = True
        self.send(AttackerDeclaredEvent())
    def setBlocked(self, blockers):
        self.blocked = True
        self.blockers.update(blockers)
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
        self.block_cost = cost = MultipleCosts(["0"])
        player = self.controller
        return cost.precompute(self, player) and cost.compute(self, player)
    def payBlockCost(self):
        self.block_cost.pay(self, self.controller)
    def computeAttackCost(self):
        self.attack_cost = cost = MultipleCosts(["0"])
        player = self.controller
        return cost.precompute(self, player) and cost.compute(self, player)
    def payAttackCost(self):
        self.attack_cost.pay(self, self.controller)
    @overridable(logical_and)
    def shouldDestroy(self):
        return self.__damage >= self.toughness and super(CreatureType, self).shouldDestroy()

    def set_power_toughness(self, power, toughness):
        PT = PowerToughnessSetter(power, toughness)
        return self.PT_set_modifiers.add(PT)
    def set_power(self, power):
        PT = PowerSetter(power, None)
        return self.PT_set_modifiers.add(PT)
    def set_toughness(self, toughness):
        PT = ToughnessSetter(None, toughness)
        return self.PT_set_modifiers.add(PT)
    def augment_power_toughness(self, power, toughness):
        PT = PowerToughnessModifier(power, toughness)
        return self.PT_augment_modifiers.add(PT)
    def switch_power_toughness(self):
        PT = PowerToughnessSwitcher()
        return self.PT_switch_modifiers.add(PT)

    def type_info(self):
        txt = ["%d/%d"%(self.base_power, self.base_toughness)]
        txt.append(str(self.PT_set_modifiers))
        txt.append(str(self.PT_augment_modifiers))
        txt.append(', '.join([str(c) for c in self.counters if hasattr(c,"power")]))
        txt.append(str(self.PT_switch_modifiers))
        return 'P/T: (%d/%d)\n'%(self.power, self.toughness)+'\n'.join(["7%s: %s"%(layer, mod) for layer, mod in zip("abcde", txt) if mod])

class AttachmentType(object):
    attached_abilities = property(fget=lambda self: self.abilities.attached())
    attached_to = property(fget=lambda self: self._attached_to)
    def activateAttachment(self):
        from Match import isLand, isCreature
        self._attached_to = None
        self.target_zone = "battlefield"
        self.target_player = None
        if self.subtypes == Equipment:
            self.target_type = isCreature
        elif self.subtypes == Fortification:
            self.target_type = isLand
    def leavingZone(self):
        self.unattach(True)
        super(AttachmentType,self).leavingZone()
    def attach(self, target, during=False):
        if (during or self.canBeAttachedTo(target)) and not self._attached_to == target: # Rule 701.3b: "...If an effect tries to attach an Aura, Equipment, or Fortification to the object it's already attached to, the effect does nothing."
            if self._attached_to != None: self.unattach()
            self._attached_to = target
            self._attached_to.attachments.append(self)
            for ability in self.attached_abilities: ability.enable(self)
            self.send(AttachedEvent(), attached=self._attached_to)
        return self.unattach # XXX - Should this really return anything?
    def unattach(self, is_LKI=False):
        if self._attached_to:
            for ability in self.attached_abilities: ability.disable()
            self._attached_to.attachments.remove(self)
            self.send(UnAttachedEvent(), unattached=self._attached_to)
            if not is_LKI: self._attached_to = None
    def isValidAttachment(self, attachment=None):
        if attachment == None: attachment = self.attached_to
        return self.canBeAttachedTo(attachment)
    def canBeAttachedTo(self, attachment):
        if self.target_player:
            check_player = (self.target_player == "you" and attachment.controller == self.controller) or (self.target_player == "opponent" and attachment.controller in self.controller.opponents)
        else: check_player = True
        return (attachment and not attachment.is_LKI and str(attachment.zone) == self.target_zone and check_player and self.target_type(attachment) and attachment.canBeAttachedBy(self))


def card_method(func):
    setattr(CardRole, func.__name__, func)

def permanent_method(func):
    setattr(Permanent, func.__name__, func)
