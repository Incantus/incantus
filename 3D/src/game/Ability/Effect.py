import copy
from game.LazyInt import LazyInt
from game.characteristics import characteristic, stacked_characteristic, additional_characteristic
from game.GameObjects import MtGObject
from game.Match import isPlayer, isCreature, isCard, isPermanent, isLandType
from game.GameEvent import TokenPlayed, ManaEvent, SacrificeEvent, CleanupEvent, CounterAddedEvent, CounterRemovedEvent,  PowerToughnessChangedEvent, InvalidTargetEvent, SubroleModifiedEvent, ColorModifiedEvent, SubtypeModifiedEvent, LogEvent

class Effect(MtGObject):
    def __call__(self, card, target):
        return False
    def process_target(self, card, target):
        return True
    def __str__(self):
        return self.__class__.__name__
    #def copy(self):
    #    import copy
    #    return copy.copy(self)

class TriggerEffect(Effect):
    def __init__(self):
        self.trigger = False
    def __call__(self, card, target):
        self.trigger = True
    def setData(self, k):
        setattr(self, k[0], k[1])
        return True
    def reset(self):
        self.trigger = False

class WinGame(Effect):
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target (not a player)")
        print "%s, you won the game!!"%(target)
        return True
class LoseGame(Effect):
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target (not a player)")
        print "%s, you lost the game!!"%(target)
        return True

class PrintEffect(Effect):
    def __call__(self, card, target):
        print "%s, target %s"%(card, target)
        return True
class PauseEffect(Effect):
    def __init__(self, msg=''):
        self.msg = msg
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target (not a player)")
        target.getIntention(self.msg, msg=self.msg, notify=True)
        return True
    def __str__(self):
        return ''
class NullEffect(Effect):
    def __init__(self, func=None):
        if func == None: func = lambda c,t: None
        self.func = func
    def __call__(self, card, target):
        self.func(card, target)
    def __str__(self):
        return ''


# XXX Fix this for Gilt-leaf Palace
class RevealCard(Effect):
    def __init__(self, select=None, both=False):
        self.select = select
        self.both = both
    def __call__(self, card, target):
        if self.select and callable(self.select): showcard = self.select(target)
        else: showcard = card
        target.revealCard(showcard)
        if self.both: target.opponent.revealCard(showcard, prompt="%s reveals %s"%(target, showcard))
        target.send(LogEvent(), msg="%s reveals %s"%(target, showcard))
        return True

class DoOr(Effect):
    def __init__(self, effect, failed):
        self.effect = effect
        self.failed = failed
    def process_target(self, card, target):
        if not type(target) == list: target, failed_target = target, target
        else: target, failed_target = target
        return self.effect.process_target(card, target) and self.failed.process_target(card, failed_target)
    def __call__(self, card, target):
        if not type(target) == list: target, failed_target = target, target
        else: target, failed_target = target
        if not self.effect(card, target):
            return self.failed(card, failed_target)
        else: return True
    def __str__(self):
        return "Do %s, or %s"%(self.effect, self.failed)

class MayEffect(Effect):
    def __init__(self, effect, msg=''):
        self.effect = effect
        if not msg: msg = str(self.effect)
        self.msg = msg
    def process_target(self, card, target): return self.effect.process_target(card, target)
    def get_player(self, card): raise NotImplemented()
    def __call__(self, card, target):
        player = self.get_player(card)
        if player.getIntention(prompt="You may %s"%self.msg,msg="Would you like to %s?"%self.msg): return self.effect(card, target)
        else: return False
    def __str__(self):
        return "You may %s"%self.msg

class YouMay(MayEffect):
    def get_player(self, card): return card.controller
class OpponentMay(MayEffect):
    def get_player(self, card): return card.controller.opponent
class OwnerMay(MayEffect):
    def get_player(self, card): return card.owner

class ForEach(Effect):
    def __init__(self, effect=None):
        self.effect = effect
        if type(effect) == list: self.multiplex = True
        else: self.multiplex = False
    def __call__(self, card, target):
        success = True
        for i, t in enumerate(target):
            if self.multiplex:
                if not self.effect[i](card, t): success = False
            elif not self.effect(card, t): success = False
        return success
    def __str__(self):
        if self.multiplex: txt = ", ".join(map(str,self.effect))
        else: txt = str(self.effect)
        return "For each target, %s"%txt

class ForN(Effect):
    def __init__(self, number=1, effect=None):
        self.number = number
        self.effect = effect
    def __call__(self, card, target):
        success = True
        for i in range(self.number):
            if not self.effect(card, target): success = False
        return success
    def __str__(self):
        return "%s, %d time(s)"%(str(self.effect), self.number)

class MultipleEffects(Effect):
    def __init__(self, *effects):
        self.effects = effects
    def process_target(self, card, target):
        if not type(target) == list:
            target = [target]
            single = True
        else: single = False
        success = True
        for i, effect in enumerate(self.effects):
            if single: i = 0
            if not effect.process_target(card, target[i]): success = False
        return success
    def __call__(self, card, target):
        if not type(target) == list:
            target = [target]
            single = True
        else: single = False
        success = True
        for i, effect in enumerate(self.effects):
            if single: i = 0
            if not effect(card, target[i]): success = False
        return success
    def __str__(self):
        return ", ".join(map(str,self.effects))

class DependentEffects(MultipleEffects):
    def __call__(self, card, target):
        if not type(target) == list:
            target = [target]
            single = True
        else: single = False
        for i, effect in enumerate(self.effects):
            if single: i = 0
            if not effect(card, target[i]):
                success = False
                break
        else: success = True
        return success

class ChoiceEffect(MultipleEffects):
    def __call__(self, card, target):
        choice = card.controller.getSelection(self.effects, 1, prompt="Select effect")
        return choice(card, target)
    def __str__(self):
        return " or ".join(map(str,self.effects))

class DistributeDamage(Effect):
    def __init__(self, amount):
        self.amount = amount
    def process_target(self, card, target):
        player = card.controller
        class Dummy: pass
        attacker = Dummy()
        attacker.power = self.amount
        attacker.name = card.name
        self.damage = player.getDamageAssignment([(attacker, target)])
        return True
    def __call__(self, card, target):
        if card.canDealDamage():
            for t, amt in self.damage.items():
                if amt > 0: card.dealDamage(t, amt)
            return True
        else: return False
    def __str__(self):
        return "Distribute damage"

class CounterAbility(Effect):
    def __call__(self, card, target):
        success = False
        if target.can_be_countered():
            target.countered()
            card.controller.stack.counter(target)
            success =  True
        return success
    def __str__(self):
        return "Counter"

class ChangeSelfController(Effect):
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target for changing controller")
        # Switch the play locations
        player = card.controller
        player.play.remove_card(card, trigger=False)
        target.play.add_card(card, trigger=False)
        card.controller = target
    def __str__(self):
        return "Change controller"

class ChangeController(Effect):
    def __init__(self, expire=True):
        self.expire = expire
    def __call__(self, card, target):
        if card.controller == target.controller:
            return lambda: None
        # Switch the play locations
        old_controller = target.controller
        old_controller.play.remove_card(target, trigger=False)
        card.controller.play.add_card(target, trigger=False)
        target.controller = card.controller
        restore = lambda: str(target.zone) == "play" and self.reverse(target, old_controller)
        if self.expire: card.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def reverse(self, target, old_controller):
        target.controller.play.remove_card(target, trigger=False)
        old_controller.play.add_card(target, trigger=False)
        target.controller = old_controller
    def __str__(self):
        return "Change controller"

class CreateToken(Effect):
    def get_number(self): return self.number
    def __init__(self, token_info, number=1):
        self.token_name = token_info.get("name", '')
        self.token_color = token_info.get("color", '')
        self.token_type = token_info.get("type", '')
        self.token_subtypes = token_info.get("subtypes", '')
        self.token_supertype = token_info.get("supertype", '')
        self.token_subrole = token_info.get("role")
        self.number = number
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target for adding token")
        from game.CardLibrary import CardLibrary
        from game.CardRoles import NoRole, Permanent
        for i in range(self.get_number()):
            token = CardLibrary.createToken(self.token_name, target, self.token_color,  self.token_type, self.token_subtypes, self.token_supertype)
            # Create the role for it
            token.controller = target
            token.in_play_role = Permanent(token, copy.deepcopy(self.token_subrole))
            token.current_role = token.out_play_role = NoRole(token)
            # Now put it into play
            token.controller.play.add_card(token)
            card.send(TokenPlayed())
        return True
    def __str__(self):
        if self.number > 1: a='s'
        else: a = ''
        return "Add %d %s token%s"%(self.number, self.token_name, a)

class AddMana(Effect):
    def amt():
        def fget(self):
            if callable(self._amt): return self._amt()
            else: return self._amt
        return locals()
    amt = property(**amt())
    def __init__(self, amt):
        self._amt = amt
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target for adding mana")
        target.manapool.add(self.amt)
        card.send(ManaEvent())
        return True
    def __str__(self):
        # XXX Maybe do some pretty printing of the amount if it's really big
        return "Add %s"%(self.amt)

class ManaChoice(Effect):
    def choices():
        def fget(self):
            if callable(self._choices): return self._choices()
            else: return self._choices
        return locals()
    choices = property(**choices())
    def __init__(self, choices):
        self._choices = choices
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target for adding mana")
        choices = [("Add %s to your mana pool"%c,c) for c in self.choices]
        choice = target.getSelection(choices, 1, idx=False, prompt="Select mana to add")
        target.manapool.add(choice)
        card.send(ManaEvent())
        return True
    def __str__(self):
        return "Add %s"%(" or ".join(self.choices))

class ChangeLife(Effect):
    def __init__(self, value=0):
        if type(value) == int or isinstance(value, LazyInt): self.func = lambda l: l+value
        else: self.func = value
    def __call__(self, card, target):
        old_life = target.life
        target.life = self.func(target.life)
        return True
    def __str__(self):
        return "Change life by %d"%int(self.func(0))

class TapTargetPermanent(Effect):
    def __call__(self, card, target):
        # Is there something that can prevent the tapping from occuring?
        if target.canBeTapped():
            target.tap()
            return True
        else: return False
    def __str__(self):
        return "Tap permanent"

class UntapTargetPermanent(Effect):
    def __call__(self, card, target):
        # Is there something that can prevent the tapping from occuring?
        if target.tapped:
            target.untap()
            return True
        else: return False
    def __str__(self):
        return "Untap permanent"

class DealDamage(Effect):
    def __init__(self, amount, source=None):
        self.amount = amount
        self.source = source
    def __call__(self, card, target):
        if self.source: source = self.source.target
        else: source = card
        if source.canDealDamage():
            source.dealDamage(target, self.amount)
            return True
        else: return False
    def __str__(self):
        return "Deal %d damage"%int(self.amount)

class Destroy(Effect):
    def __call__(self, card, target):
        # If we are not in play do nothing
        if not isPermanent(target): return False
        target.destroy()
        return True
    def __str__(self):
        return "Destroy"
class DestroyNoRegenerate(Effect):
    def __call__(self, card, target):
        # If we are not in play do nothing
        if not isPermanent(target): return False
        target.destroy(skip=True)
        return True
    def __str__(self):
        return "Destroy no regenerate"

class Sacrifice(Effect):
    def __call__(self, card, target):
        if not isPermanent(target): return False
        target.move_to(target.owner.graveyard)
        #card.send(SacrificeEvent())
        return True
    def __str__(self):
        return "Sacrifice"
class SacrificeSelf(Effect):
    def __call__(self, card, target):
        # If we are not in play do nothing
        if not isPermanent(card): return False
        card.move_to(card.owner.graveyard)
        #card.send(SacrificeEvent())
        return True
    def __str__(self):
        return "Sacrifice self"

class ForceSacrifice(Effect):
    def __init__(self, card_type=isCreature, number=1, required=True):
        self.card_type = card_type
        self.number = number
        self.required = required
    def __call__(self, card, target):
        num_available = len(target.play.get(self.card_type))
        for i in range(self.number):
            if num_available == 0: return False
            sacrifice = target.getTarget(self.card_type, zone=target.play, required=self.required, prompt="Select a %s for sacrifice"%self.card_type)
            if not sacrifice: return False
            else:
                sacrifice.move_to(sacrifice.owner.graveyard)
                num_available -= 1
        return True
    def __str__(self):
        return "Sacrifice %s"%self.card_type

class PayExtraCost(Effect):
    def __init__(self, cost="0", selector=None):
        from game.Cost import ManaCost
        if type(cost) == str: cost = ManaCost(cost)
        self.cost = cost
        self.selector = selector
    def __call__(self, card, target):
        if self.selector == "you": player = card.controller
        elif self.selector == "opponent": player = card.controller.opponent
        elif self.selector == "owner": player = card.owner
        else:
            if not isPlayer(target): player = target.controller
            else: player = target
        intent = player.getIntention("", "Pay %s for %s?"%(self.cost, card))
        if intent and self.cost.precompute(card, player) and self.cost.compute(card, player):
            self.cost.pay(card, player)
            return True
        else: return False
    def __str__(self):
        return "Pay extra %s"%self.cost

# XXX Clone is broken right now
class Clone(Effect):
    def __call__(self, card, target):
        card.current_role = copy.deepcopy(target.in_play_role)
        for ability in card.current_role.abilities: ability.card = card
        for ability in card.current_role.triggered_abilities: ability.card = card
        for ability in card.current_role.static_abilities: ability.card = card
        # XXXcopy all abilities
        # not done
        characteristics = ["name", "cost", "color", "type", "subtypes", "supertype"]
        for c in characteristics: setattr(card, c, copy(getattr(target, c)))
        # XXX Need to restore original when leaving play
        return True
    def __str__(self):
        return "Clone"

# XXX CopySpell is broken right now
class CopySpell(Effect):
    def process_target(self, card, target):
        # XXX This doesn't work with spells that don't work when you copy their targets
        from Ability import Ability
        self.new_spell = None
        success = True
        player = card.controller
        if player.getIntention(prompt="Choose new targets?", msg="...choose new targets?"):
            new_targets = [t.copy() for t in target.targets]
            new_spell = Ability(card, target=new_targets, effects=target.effects)
            if new_spell.needs_target(): success = new_spell.get_target()
            if not success: return False
        else:
            new_spell = Ability(card, target=target.targets, effects=target.effects)
        self.new_spell = new_spell
        return success
    def __call__(self, card, target):
        self.new_spell.resolve()
        self.new_spell = None
        return True
    def __str__(self):
        return "Copy spell"


# XXX Difference between ReplacementEffect and OverrideGlobal
# combiner method
# ReplacementEffect curently only targets objects while
# OverrideGlobal only targets classes

import new
from game.stacked_function import stacked_function, replacement
class ReplacementEffect(Effect):
    def __init__(self, func, name, txt='', expire=True, condition=None):
        self.func = func
        self.name = name
        self.txt = txt
        self.expire = expire
        self.condition = condition
    def __call__(self, card, target):
        from CreatureAbility import override_replace
        restore = override_replace(target, self.name, self.func, txt=self.txt, condition=self.condition)
        if self.expire: card.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Override local %s with replacement effect"%self.name
class OverrideGlobal(Effect):
    def __init__(self, func, name, global_class, combiner, reverse=True, expire=True, new_func_gen = new.instancemethod):
        self.func = func
        self.name = name
        self.global_class = global_class
        self.combiner = combiner
        self.reverse = reverse
        self.expire = expire
        self.new_func_gen = new_func_gen
    def __call__(self, card, target):
        name = self.name
        obj = None
        cls = self.global_class
        target = self.global_class

        is_derived = False
        # The function is defined in the superclass (which we don't override)
        if not name in cls.__dict__:
            is_derived = True
            # Bind the call to the superclass function
            orig_func = new.instancemethod(lambda self, *args, **named: getattr(super(cls, self), name).__call__(*args,**named), obj, cls)
        else:
            orig_func = getattr(target, name)
        if not hasattr(orig_func, "stacked"):
            stacked_func = stacked_function(orig_func, combiner=self.combiner, reverse=self.reverse)
            setattr(target, name, stacked_func)
        else: stacked_func = orig_func
        # Build the new function
        new_func = self.new_func_gen(self.func, obj, cls)
        stacked_func.add_func(new_func)
        def restore(stacked_func=stacked_func):
            stacked_func.remove_func(new_func)
            if not stacked_func.stacking():
                setattr(target, name, stacked_func.funcs[0])
                del stacked_func
        if self.expire: card.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Override %s"%self.name
class OverrideGlobalReplacement(OverrideGlobal):
    def __init__(self, func, name, global_class, condition=None, txt='', expire=True):
        if not condition: condition = lambda *args, **kw: True
        if not txt: txt = func.__doc__
        new_func_gen = lambda func, obj, cls: [False, new.instancemethod(func,obj,cls), txt, condition]
        super(OverrideGlobalReplacement,self).__init__(func, name, global_class, combiner=replacement, reverse=False, expire=expire, new_func_gen=new_func_gen)
    def __str__(self):
        return "Override global %s with replacement effect"%self.name

class AttachToPermanent(Effect):
    def __call__(self, card, target):
        return card.attach(target)
    def __str__(self):
        return "Attach"

class ChangeAttachment(Effect):
    def __init__(self, must_be_different=False):
        self.must_be_different = must_be_different
    def process_target(self, card, target):
        self.attach_to = None
        player = card.controller
        target_types = target.target_types
        new_target = player.getTarget(target_types, required=False, prompt="Select %s to attach %s to"%(target_types, card))
        if new_target and new_target.canBeTargetedBy(card) and not (self.must_be_different and new_target == target.attached_to):
            new_target.isTargetedBy(card)
            self.attach_to = new_target
            return True
        else: 
            player.send(InvalidTargetEvent(), target=target)
            return False
    def __call__(self, card, target):
        old_attachment = target.attached_to
        target.attach(self.attach_to)
        return lambda: target.attach(old_attachment)
    def __str__(self):
        return "Reattach"

class ModifyCharacteristic(Effect):
    def __init__(self, characteristic, expire=True):
        self.characteristic = characteristic
        self.expire = expire
    def __call__(self, card, target):
        characteristic = getattr(target, self.attribute)
        if not hasattr(characteristic, "stacked"):
            stacked_char = stacked_characteristic(characteristic)
            setattr(target, self.attribute, stacked_char)
        else: stacked_char = characteristic
        stacked_char.add(self.characteristic)
        card.send(self.change_event, card=target)
        def restore(stacked_char=stacked_char):
            stacked_char.remove(self.characteristic)
            if not stacked_char.stacking():
                setattr(target, self.attribute, stacked_char.pop())
                del stacked_char
            card.send(self.change_event, card=target)
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "%s %s"%(self.attribute, str(self.characteristic))

class ModifyColor(ModifyCharacteristic):
    def __init__(self, color, expire=True):
        super(ModifyColor, self).__init__(color, expire)
        self.attribute = "color"
        self.change_event = ColorModifiedEvent()
class ModifySubtype(ModifyCharacteristic):
    def __init__(self, subtype, expire=True):
        super(ModifySubtype, self).__init__(subtype, expire)
        self.attribute = "subtypes"
        self.change_event = SubtypeModifiedEvent()

# XXX Broken right now
class RemoveSubRoles(Effect):
    def __init__(self, expire=True):
        self.expire = expire
    def __call__(self, card, target):
        old_roles = list(target.subroles)
        for role in old_roles:
            target.remove_subrole(role)
        old_char = {}
        card_characteristics = ["type", "subtypes", "supertype"]
        old_chars = dict([(char, getattr(target, char)) for char in card_characteristics])
        for char in card_characteristics: setattr(target, char, characteristic([]))
        def restore():
            card.send(SubroleModifiedEvent(), card=target)
            for role in old_roles: target.add_subrole(role)
            for char, val in old_chars.items(): setattr(target, char, val)
        card.send(SubroleModifiedEvent(), card=target)
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Remove roles"

class AddSubRole(Effect):
    def __init__(self, subrole, subrole_info, expire=True):
        if not (type(subrole) == list or type(subrole) == tuple): subrole = [subrole]
        self.subroles = subrole
        self.subrole_info = subrole_info
        self.expire = expire
    def __call__(self, card, target):
        added_roles = []
        for subrole in self.subroles:
            new_subrole = copy.deepcopy(subrole)
            target.add_subrole(new_subrole)
            added_roles.append(new_subrole)
        stacked = []
        for char_str, val in self.subrole_info.items():
            val = additional_characteristic(val)
            chr = getattr(target, char_str)
            if not hasattr(chr, "stacked"):
                stacked_char = stacked_characteristic(chr)
                setattr(target, char_str, stacked_char)
            else: stacked_char = chr
            stacked_char.add(val)
            stacked.append((char_str, stacked_char, val))
        # XXX Should the card send these messages, or the target?
        card.send(SubroleModifiedEvent(), card=target)
        def restore(stacked=stacked):
            for subrole in added_roles:
                target.remove_subrole(subrole)
            for char_str, stacked_char, val in stacked:
                stacked_char.remove(val)
                if not stacked_char.stacking():
                    setattr(target, char_str, stacked_char.pop())
                    del stacked_char
            card.send(SubroleModifiedEvent(), card=target)
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Add %s"%' '.join(map(str,self.subroles))

class GiveKeyword(Effect):
    def __init__(self, keyword_func, expire=True, keyword='', perm=False):
        self.keyword_func = keyword_func
        self.expire = expire
        self.keyword_name = keyword
        self.perm = perm
    def __call__(self, card, target):
        from game.CardRoles import Creature
        # XXX This looks ugly, but is necessary to bind the correct subrole
        if isPlayer(target): restore = self.keyword_func(target)
        else: 
            if self.perm: restore = self.keyword_func(target.current_role)
            else: restore = self.keyword_func(target.current_role.get_subrole(Creature))
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Give %s"%self.keyword_name

class ConditionalEffect(Effect):
    def __init__(self, effect, condition):
        self.effect = effect
        self.condition = condition
    def process_target(self, card, target): return self.effect.process_target(card, target)
    def __call__(self, card, target):
        if self.condition(card, target):
            restore = self.effect(card, target)
            return restore
        else: return False
    def __str__(self):
        return "Conditionally do %s"%(self.effect)

class DoUntil(Effect):
    def __init__(self, effect, event, match_condition,expiry=-1):
        self.effect = effect
        self.event = event
        self.match_condition = match_condition
        self.triggers = []
        self.expiry=expiry
    def process_target(self, card, target): return self.effect.process_target(card, target)
    def __call__(self, card, target):
        import Trigger
        restore = self.effect(card, target)
        trigger = Trigger.Trigger(self.event)
        def do_until():
            restore()
            trigger.clear_trigger()
            self.triggers.remove(trigger)
        trigger.setup_trigger(None, do_until, self.match_condition,expiry)
        self.triggers.append(trigger)
        return restore
    def __str__(self):
        return "Do %s until %s"%(self.effect, self.event)

class AddActivatedAbility(Effect):
    def __init__(self, ability, expire=True):
        self.ability = ability
        self.expire = expire
    def __call__(self, card, target):
        new_ability = self.ability.copy()
        new_ability.card = target
        target.abilities.append(new_ability)
        restore = lambda a=target.abilities: a.remove(new_ability)
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Give %s"%self.ability
class AddTriggeredAbility(Effect):
    def __init__(self, ability, expire=True):
        self.ability = ability
        self.expire = expire
    def __call__(self, card, target):
        triggered_ability = self.ability.copy()
        triggered_ability.card = target.card
        triggered_ability.ability.card = target.card
        target.triggered_abilities.append(triggered_ability)
        triggered_ability.enteringPlay()
        def restore(ta=target.triggered_abilities):
            triggered_ability.leavingPlay()
            ta.remove(triggered_ability)
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Give %s"%self.ability

class RemoveCounter(Effect):
    def __init__(self, counter, number=1):
        self.counter = counter
        self.number = number
    def process_target(self, card, target):
        self.counters = [counter for counter in target.counters if counter == self.counter]
        return len(self.counters) >= self.number
    def __call__(self, card, target):
        for counter in self.counters[:self.number]:
            target.counters.remove(counter)
            target.send(CounterRemovedEvent(), counter=counter)
        return True
    def __str__(self):
        if self.number > 1: a='s'
        else: a = ''
        return "Remove %d %s counter%s"%(self.number, self.counter, a)

class AddCounter(Effect):
    # Can't use properties, because the functions are bound when the property is created
    def get_number(self): return self.number

    def __init__(self, counter, number=1, expire=False):
        self.counter = counter
        self.expire = expire
        self.number = number
    def __call__(self, card, target):
        counters = []
        for i in range(self.get_number()):
            counter = self.counter.copy()
            counters.append(counter)
            target.counters.append(counter)
            target.send(CounterAddedEvent(), counter=counter)
        def remove_counter():
            for c in counters:
                target.counters.remove(c)
                target.send(CounterRemovedEvent(), counter=c)
        if self.expire: target.register(remove_counter, CleanupEvent(), weak=False, expiry=1)
        return remove_counter
    def __str__(self):
        if self.number > 1: a='s'
        else: a = ''
        return "Add %d %s counter%s"%(self.number, self.counter, a)

class AddPowerToughnessCounter(AddCounter):
    from Counters import PowerToughnessCounter
    def __init__(self, power=1, toughness=1, number=1, expire=False):
        super(AddPowerToughnessCounter,self).__init__(self.PowerToughnessCounter(power,toughness), number, expire)
    def __call__(self, card, target):
        counters = []
        for i in range(self.get_number()):
            counter = self.counter.copy()
            counters.append(counter)
            target.counters.append(counter)
            target.send(CounterAddedEvent(), counter=counter)
            target.send(PowerToughnessChangedEvent())
        def remove_counter():
            for c in counters:
                target.counters.remove(c)
                target.send(CounterRemovedEvent(), counter=c)
                target.send(PowerToughnessChangedEvent())
        if self.expire: target.register(remove_counter, CleanupEvent(), weak=False, expiry=1)
        return remove_counter

class ModifyPowerToughness(Effect):
    from Counters import PowerToughnessModifier, PowerToughnessSetter, PowerSetter, ToughnessSetter
    def __init__(self, power, toughness, expire=True):
        self.power = power
        self.toughness = toughness
        self.expire = expire
    def get_PT(self):
        if callable(self.power): power = self.power()
        else: power = self.power
        if callable(self.toughness): toughness = self.toughness()
        else: toughness = self.toughness
        return power, toughness
    def __call__(self, card, target):
        power, toughness = self.get_PT()
        PT = self.PT_class(power, toughness)
        modifiers = self.get_modifier_list(target)
        modifiers.add(PT)
        target.send(PowerToughnessChangedEvent())
        def remove():
            modifiers.remove(PT)
            target.send(PowerToughnessChangedEvent())
        if self.expire: target.register(remove, CleanupEvent(), weak=False, expiry=1)
        return remove

class AugmentPowerToughness(ModifyPowerToughness):
    def __init__(self, power, toughness, expire=True):
        super(AugmentPowerToughness, self).__init__(power, toughness, expire)
        self.PT_class = self.PowerToughnessModifier
    def get_modifier_list(self, target):
        if self.expire: modifiers = target.PT_other_modifiers
        else: modifiers = target.PT_static_modifiers
        return modifiers
    def __str__(self):
        power, toughness = self.get_PT()
        return "Add %+d/%+d"%(power, toughness)

class SetPowerToughness(ModifyPowerToughness):
    def __init__(self, power, toughness, expire=True):
        super(SetPowerToughness, self).__init__(power, toughness, expire)
        self.PT_class = self.PowerToughnessSetter
    def get_modifier_list(self, target):
        return target.PT_other_modifiers
    def __str__(self):
        power, toughness = self.get_PT()
        return "Set %d/%d"%(power, toughness)
class SetPower(SetPowerToughness):
    def __init__(self, power, expire=True):
        super(SetPower, self).__init__(power, None, expire)
        self.PT_class = self.PowerSetter
    def __str__(self):
        power, toughness = self.get_PT()
        return "Set %d/-"%(power)
class SetToughness(SetPowerToughness):
    def __init__(self, toughness, expire=True):
        super(SetToughness, self).__init__(None, toughness, expire)
        self.PT_class = self.ToughnessSetter
    def __str__(self):
        power, toughness = self.get_PT()
        return "Set -/%d"%(toughness)


class SwitchPowerToughness(Effect):
    from Counters import PowerToughnessSwitcher
    def __init__(self, expire=True):
        self.expire = expire
    def __call__(self, card, target):
        PT = self.PowerToughnessSwitcher()
        modifiers = target.PT_switch_modifiers
        modifiers.add(PT)
        target.send(PowerToughnessChangedEvent())
        def remove():
            modifiers.remove(PT)
            target.send(PowerToughnessChangedEvent())
        if self.expire: target.register(remove, CleanupEvent(), weak=False, expiry=1)
        return remove
    def __str__(self):
        return "Switch P/T"

# Change Zone is used when targeting specific cards to move between zones
# unlike MoveCards, which selects the cards once the ability resolves
class ChangeZone(Effect):
    def __init__(self, from_zone, to_zone, to_position="top", to_owner=True, func=lambda card: None, expire=False):
        if from_zone == to_zone: raise Exception("Cannot ChangeZone from a zone to the same zone")
        self.from_zone = from_zone
        self.to_zone = to_zone
        self.to_position = to_position
        self.to_owner = to_owner
        self.func = func
        self.expire = expire
    def __call__(self, card, target):
        if self.from_zone == "play": from_zone = target.controller.play
        else: from_zone = getattr(target.owner, self.from_zone)
        if self.to_owner: to_zone = getattr(target.owner, self.to_zone)
        else:
            to_zone = getattr(card.controller, self.to_zone)
            target.controller = card.controller
        if self.to_position == "top": position = -1
        else: position = 0
        target.move_to(to_zone, position=position)
        self.func(target)
        def restore():
            # XXX What do we do if the target is not in the zone we left him?
            if target.zone == to_zone: 
                target.move_to(from_zone)
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Move from %s to %s"%(self.from_zone, self.to_zone)

class ChangeZoneFromPlay(ChangeZone):
    def __init__(self, to_zone, to_position="top", func=lambda card: None):
        super(ChangeZoneFromPlay,self).__init__(from_zone="play", to_zone=to_zone, to_position=to_position, func = func)

class ChangeZoneToPlay(ChangeZone):
    def __init__(self, from_zone, to_owner=False, func=lambda card: None):
        super(ChangeZoneToPlay,self).__init__(from_zone=from_zone, to_zone="play", to_owner=to_owner, func = func)

class PlayCard(Effect):
    def __init__(self, cost=None):
        from game.Cost import ManaCost
        if type(cost) == str: cost = ManaCost(cost)
        self.cost = cost
    def __call__(self, card, target):
        from game.Action import PlayAbility, PlayLand
        from game.GameEvent import PlayAbilityEvent, LogEvent
        if isPermanent(target): raise Exception("Can't play a permanent") # XXX Do i need this?
        if not isLandType(target):
            player = card.controller
            # XXX Generally the first ability of the spell is casting it - might not always be the case
            ability = target.abilities[0].copy()
            ability.controller = player

            # Different cost to play
            if self.cost and hasattr(ability, "cost"): ability.cost = self.cost
            success = player.stack.announce(ability)
            if success:
                player.send(PlayAbilityEvent(), ability=ability)
                player.send(LogEvent(), msg="%s plays (%s) of %s"%(player,ability,target))
            else:
                player.send(LogEvent(), msg="%s: Failed playing %s - %s"%(player,target,ability))
        else:
            action = PlayLand(target)
            success = action.perform(card.controller)
        return success
    def __str__(self):
        return "Play card"

class ShuffleIntoLibrary(Effect):
    # This class can't use the ChangeZone functionality, because that targets a card, and the card's
    # final location (the graveyard) is different from starting location (probably hand) so that the
    # targeting of "self" will fail (because the zone is different)
    def __call__(self, card, target):
        player = card.owner
        player.library.disable_ordering()
        card.move_to(player.library)
        player.library.enable_ordering()
        player.shuffleLibrary()
        return True
    def __str__(self):
        return "Shuffle into library"

class ShuffleLibrary(Effect):
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target (not a player)")
        target.shuffleLibrary()
        return True
    def __str__(self):
        return "Shuffle library"

class MoveCards(Effect):
    def __init__(self, from_zone, to_zone, from_position="", to_position="top", number=1, card_types=None, subset=None, return_position = "top", func=lambda card: None, reveal=False, peek=False, required=False, prompt=''):
        self.from_zone = from_zone
        self.to_zone = to_zone
        self.number = number
        self.subset = subset
        self.selection = []
        self.from_position = from_position
        self.to_position = to_position
        self.return_position = return_position
        if not ((self.from_position in ["", "top", "bottom"] or type(self.from_position) == int) or (self.to_position in ["top", "bottom"] or type(self.to_position) == int) or (self.return_position in ["top", "bottom"])):
            raise Exception("Incorrect from position specified for MoveCards (%s)"%card)
        if card_types == None:
            card_types = isCard
            required = True
        if (type(card_types) == list or type(card_types) == tuple): self.card_types = card_types
        else: self.card_types = [card_types]
        self.func = func
        self.reveal = reveal
        self.peek = peek
        self.required = required
        self.prompt = prompt
    def select_cards_in_visible(self, card, player):
        from_zone = getattr(player, self.from_zone)
        if not self.prompt: base_prompt = str(self)
        else: base_prompt = self.prompt
        prompt = base_prompt
        selection = set()
        for ttype in self.card_types: selection.update(from_zone.get(ttype))
        num_available = len(selection)
        if num_available == 0 and self.required: return False
        elif num_available < self.number: self.number = num_available
        cardlist = []
        while True:
            target = player.getTarget(self.card_types, zone=from_zone, required=self.required, prompt=prompt)
            if target == False: return False
            if target in cardlist:
                prompt = "%s already selected - select again"%selcard
                player.send(InvalidTargetEvent(), target=target)
            else:
                cardlist.append(target)
                prompt = base_prompt
            if len(cardlist) == self.number: break
        self.cardlist = cardlist
        return True
    def select_cards(self, card, target):
        from_zone = getattr(target, self.from_zone)
        if len(from_zone) == 0: return False
        if self.from_position == '':
            # We can select anywhere so ask the player
            # Prefilter the list to only show valid card types
            selection = from_zone.get()[:self.subset]
            if self.number == -1 or len(selection) < self.number: self.number = len(selection)
            # Now we get the selection - if the from location is library or hand the target player makes the choice
            if self.from_zone in ["library", "hand"] and not self.peek: self.selector = target
            else: self.selector = card.controller
            if not self.prompt: prompt = str(self)
            else: prompt = self.prompt
            cardlist = self.selector.getCardSelection(selection, self.number, from_zone=self.from_zone, from_player = target, required=self.required, card_types = self.card_types, prompt=prompt)
            if not cardlist: cardlist = []
            self.selection = [card for card in selection if not card in cardlist]
        elif self.from_position == "top": 
            if self.number == -1: self.number = len(from_zone)
            cardlist = from_zone.top(self.number)
        elif self.from_position == "bottom": 
            if self.number == -1: self.number = len(from_zone)
            cardlist = from_zone.bottom(self.number)
        else: cardlist = from_zone.top(self.from_position)[0]
        if not type(cardlist) == list: self.cardlist = [cardlist]
        else: self.cardlist = cardlist

        # If we are moving to the play zone make sure that the card is a Permanent
        # XXX Does the card need to be checked to see if it can be targetted? I'm not sure since it's not in play
        if self.to_zone=="play" and sum([isPermanent.match(c, use_in_play=True) for c in self.cardlist]) == 0: return False
        #return sum([self.match_condition(c) and c.canBeTargetedBy(card) for c in cards]) != 0
        return True
    def __call__(self, card, target):
        if self.from_zone in ["play", "hand"]: success = self.select_cards_in_visible(card, target)
        else: success = self.select_cards(card, target)
        if not success: return False
        from_zone = getattr(target, self.from_zone)
        if self.to_position == "top":
            position = -1
            cards = iter(self.cardlist[::-1])
        elif self.to_position == "bottom":
            position = 0
            cards = iter(self.cardlist)
        else:
            position = -1*self.to_position # From the top
            cards = iter(self.cardlist[::-1])

        for card in cards:
            if not card.zone == from_zone: continue
            # Make sure we get the owner's zone
            if not self.to_zone == "play": to_zone = getattr(card.owner, self.to_zone)
            else:
                to_zone = card.controller.play
                card.controller = card.controller
            if hasattr(to_zone, "ordered") and self.peek: to_zone.disable_ordering()
            card.move_to(to_zone, position=position)
            if hasattr(to_zone, "ordered") and self.peek: to_zone.enable_ordering()
            self.func(card)
        if len(self.selection) and self.subset:
            if self.return_position == "top": position = -1
            else: position = 0
            for card in self.selection:
                card.move_to(from_zone, position=position)

        # XXX if there is a library access in here, then we might need to shuffle it
        if self.from_zone == "library" and not (self.from_position or self.subset): from_zone.shuffle()
        if self.reveal == True and self.cardlist:
            self.selector.opponent.revealCard(self.cardlist, prompt="%s reveals card(s) "%self.selector)
            self.selector.send(LogEvent(), msg="%s reveals %s"%(self.selector, ', '.join(map(str, self.cardlist))))
        return True
    def __str__(self):
        if self.number == -1: num = "all"
        else: num = int(self.number)
        if self.number > 1: a='s'
        else: a = ''
        if self.from_position and not self.from_zone in ["hand", "play"]: fpos = "%s of "%self.from_position
        else: fpos = ''
        if self.to_position and not self.to_zone in ["hand", "play"]: tpos = "%s of "%self.to_position
        else: tpos = ''
        return "Move %s %s%s from %s%s to %s%s"%(num,' or '.join(map(str,self.card_types)),a,fpos,self.from_zone,tpos,self.to_zone)

# These could be implemented as MoveCards, but it's better to use the Player functions
# (so that appropriate signals will be send)
class DrawCard(Effect):
    def __init__(self, number=1):
        self.number = number
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target (not a player)")
        for i in range(self.number): target.draw()
        return True
    def __str__(self):
        if self.number > 1: a='s'
        else: a = ''
        return "Draw %d card%s"%(self.number, a)
class DiscardCard(Effect):
    def __init__(self, number=1, card_types=isCard, required=True, random=False):
        self.number = number
        self.card_types = card_types
        self.required = required
        self.random = random
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target (not a player)")
        # Prefilter the list to only show valid card types
        selection = target.hand.get(self.card_types)
        if len(selection) <= self.number and self.required: num_discard = -1 #len(selection)
        else: num_discard = self.number
        if num_discard == -1: #Discard all
            result = selection
        elif self.random:
            import random
            result = [selection[i] for i in random.sample(range(len(selection)), num_discard)]
        else:
            if num_discard > 1: a='s'
            else: a = ''
            num_selected = 0
            prompt = "Select %s card%s to discard: %d left of %d"%(self.card_types, a, num_discard-num_selected,num_discard)
            result = []
            while num_selected < num_discard:
                card = target.getTarget(self.card_types, zone=target.hand,required=self.required,prompt=prompt)
                if not card and not self.required: return False
                if not card in result:
                    result.append(card)
                    num_selected += 1
                    prompt = "Select %s card%s to discard: %d left of %d"%(self.card_types, a, num_discard-num_selected,num_discard)
                else: prompt = "Card already selected. Select %s card%s to discard: %d left of %d"%(self.card_types, a, num_discard-num_selected,num_discard)
        for card in result: target.discard(card)
        return True
    def __str__(self):
        num = str(self.number)
        if self.number > 1: a='s'
        elif self.number == -1:
            a = 's'
            num = "all"
        else: a = ''
        return "Discard %s card%s"%(num, a)
