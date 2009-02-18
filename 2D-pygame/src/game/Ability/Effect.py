from game.characteristics import characteristic
from game.GameObjects import MtGObject
from game.Match import isPlayer, isCreature, isCard, isPermanent, isLandType
from game.GameEvent import CardControllerChanged, TokenPlayed, ManaEvent, PlayerStatusChanged, SacrificeEvent, CleanupEvent, AddSubRoleEvent, RemoveSubRoleEvent, CounterAddedEvent, CounterRemovedEvent, SubtypeModifiedEvent, SubtypeRestoredEvent

class Effect(MtGObject):
    def __call__(self, card, target):
        return False
    def process_target(self, card, target):
        return True
    def __str__(self):
        return self.__class__.__name__
    def copy(self):
        import copy
        return copy.copy(self)

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
        target.getIntention(self.msg, msg=self.msg)
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

class RevealCard(Effect):
    def __init__(self, card, both=False):
        if callable(card): self.card = card
        else: self.card = lambda t: card
        self.both = both
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target for revealing card")
        showcard = self.card(target)
        target.revealCard(showcard)
        if self.both: target.opponent.revealCard(showcard)
        return True

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
    def __init__(self, effects=[]):
        self.effects = effects
    def process_target(self, card, target):
        success = True
        for effect in self.effects:
            if not effect.process_target(card, target): success = False
        return success
    def __call__(self, card, target):
        success = True
        for effect in self.effects:
            if not effect(card, target): success = False
        return success
    def __str__(self):
        return ", ".join(map(str,self.effects))

class DependentEffects(MultipleEffects):
    def __call__(self, card, target):
        for effect in self.effects:
            if not effect(card, target):
                success = False
                break
        else: success = True
        return success

class ModifySubType(Effect):
    def __init__(self, subtype, expire=True):
        self.subtype = subtype
        self.expire = expire
    def __call__(self, card, target):
        old_subtype = target.subtypes
        target.subtypes = self.subtype
        target.send(SubtypeModifiedEvent())
        def restore():
            target.subtypes = old_subtype
            target.send(SubtypeRestoredEvent())
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Modify creature type to %s"%self.subtype

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
            target.counter()
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
        card.controller = target
        target.play.add_card(card, trigger=False)
        # We didn't really leave play, but we are starting over with summoning sickness
        card.current_role.continuously_in_play = False
        card.summoningSickness()
        card.send(CardControllerChanged(), card=card)
    def __str__(self):
        return "Change controller"

class ChangeController(Effect):
    def __call__(self, card, target):
        # Switch the play locations
        old_controller = target.controller
        target.controller.play.remove_card(target, trigger=False)
        target.controller = card.controller
        card.controller.play.add_card(target, trigger=False)
        # We didn't really leave play, but we are starting over with summoning sickness
        target.current_role.continuously_in_play = False
        target.summoningSickness()
        card.send(CardControllerChanged(), card=target)
        return lambda : self.reverse(card, target, old_controller)
    def reverse(self, card, target, old_controller):
        target.controller.play.remove_card(target, trigger=False)
        target.controller = old_controller
        old_controller.play.add_card(target, trigger=False)
        # We didn't really leave play, but we are starting over with summoning sickness
        target.current_role.continuously_in_play = False
        target.summoningSickness()
        card.send(CardControllerChanged(), card=target)
    def __str__(self):
        return "Change controller"

class CreateToken(Effect):
    def __init__(self, token_info, number=1):
        self.token_name = token_info["name"]
        self.token_color = token_info["color"]
        self.token_type = token_info["type"]
        self.token_subtypes = token_info["subtypes"]
        self.token_role = token_info["role"]
        self.number = number
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target for adding token")
        from game.CardLibrary import CardLibrary
        from game.CardRoles import NoRole, Permanent
        for i in range(self.number):
            token = CardLibrary.createToken(self.token_name, target, self.token_color,  self.token_type, self.token_subtypes)
            # Create the role for it
            token.controller = target
            token.in_play_role = Permanent(token, self.token_role.copy())
            token.out_play_role = NoRole(token)
            # Now put it into play
            token.controller.play.add_card(token)
            card.send(TokenPlayed())
        return True
    def __str__(self):
        return "Add %s token"%(self.token_name)

class AddMana(Effect):
    def __init__(self, amt):
        self.amt = amt
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target for adding mana")
        target.manapool.addMana(self.amt)
        card.send(ManaEvent())
        return True
    def __str__(self):
        return "Add %s"%(self.amt)

class ManaChoice(Effect):
    def __init__(self, choices):
        self.choices = choices
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target for adding mana")
        choices = [("Add %s to your mana pool"%c,c) for c in self.choices]
        choice = target.getSelection(choices, 1, isCardlist=False, prompt="Select one mana to add")
        target.manapool.addMana(choice)
        card.send(ManaEvent())
        return True
    def __str__(self):
        return "Add %s"%(" or ".join(self.choices))

class ChangeLife(Effect):
    def __init__(self, value=0):
        if type(value) == int: self.func = lambda l: l+value
        else: self.func = value
    def __call__(self, card, target):
        target.life = self.func(target.life)
        target.send(PlayerStatusChanged())
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
    def __init__(self, amount):
        self.amount = amount
    def __call__(self, card, target):
        if card.canDealDamage():
            card.dealDamage(target, self.amount)
            return True
        else: return False
    def __str__(self):
        return "Deal %d damage"%int(self.amount)

class Destroy(Effect):
    def __call__(self, card, target):
        target.destroy()
        return True
    def __str__(self):
        return "Destroy"

class DestroyNoRegenerate(Effect):
    def __call__(self, card, target):
        # If we are not in play do nothing
        if not isPermanent(target): return False
        player = target.controller
        player.moveCard(target, player.play, target.owner.graveyard)
        return True
    def __str__(self):
        return "Destroy no regenerate"
class Sacrifice(DestroyNoRegenerate):
    def __call__(self, card, target):
        super(Sacrifice,self).__call__(card, target)
        #card.send(SacrificeEvent())
        return True
class SacrificeSelf(Effect):
    def __call__(self, card, target):
        # If we are not in play do nothing
        if not isPermanent(card): return False
        player = card.controller
        player.moveCard(card, player.play, card.owner.graveyard)
        #card.send(SacrificeEvent())
        return True
    def __str__(self):
        return "Sacrifice self"

class ForceSacrifice(Effect):
    def __init__(self, card_type=isCreature):
        self.card_type = card_type
    def __call__(self, card, target):
        if len(target.play.get(self.card_type)) > 0:
            sacrifice = target.getTarget(self.card_type, zone=target.play, required=True, prompt="Select a %s for sacrifice"%self.card_type)
            target.moveCard(sacrifice, target.play, sacrifice.owner.graveyard)
            return True
        else: return False
    def __str__(self):
        return "Sacrifice"

class PayExtraCost(Effect):
    def __init__(self, cost="0"):
        from game.Cost import ManaCost
        if type(cost) == str: cost = ManaCost(cost)
        self.cost = cost
    def __call__(self, card, target):
        if self.cost.compute(card, target):
            return self.cost.pay(card, target)
        else: return False
    def __str__(self):
        return "Pay extra %s"%self.cost

class Clone(Effect):
    def __call__(self, card, target):
        from copy import copy
        card.current_role = target.in_play_role.copy()
        # XXXcopy all abilities
        # not done
        characteristics = ["name", "cost", "color", "type", "subtypes", "supertype"]
        for c in characteristics: setattr(card, c, copy(getattr(target, c)))
        # XXX Need to restore original when leaving play
        return True
    def __str__(self):
        return "Clone"

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

class ReplacementEffect(Effect):
    def __init__(self, func, name, txt='', expire=True):
        self.func = func
        self.name = name
        self.txt = txt
        self.expire = expire
    def __call__(self, card, target):
        import new
        from game.stacked_function import stacked_function, replacement
        name = self.name
        obj = target
        cls = target.__class__

        is_derived = False
        # The function is defined in the superclass (which we don't override)
        if not name in cls.__dict__:
            is_derived = True
            # Bind the call to the superclass function
            orig_func = new.instancemethod(lambda self, *args, **named: getattr(super(cls, self), name).__call__(*args,**named), obj, cls)
        else:
            orig_func = getattr(obj, name)
        if not hasattr(orig_func, "stacked"):
            stacked_func = stacked_function(orig_func, combiner=replacement, reverse=False)
            setattr(target, name, stacked_func)
        else: stacked_func = orig_func
        # Add the replacement effect along with the card name (in case of multiple effects)
        new_func = [new.instancemethod(self.func, obj, cls), card.name, False]
        stacked_func.add_func(new_func)
        def restore(stacked_func=stacked_func, self=self):
            stacked_func.remove_func(new_func)
            if not stacked_func.stacking():
                setattr(target, name, stacked_func.funcs[0])
                del stacked_func
        if self.expire: card.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Override local %s"%self.name

class OverrideGlobal(Effect):
    def __init__(self, func, name, global_class, combiner, reverse=True, expire=True):
        self.func = func
        self.name = name
        self.global_class = global_class
        self.combiner = combiner
        self.reverse = reverse
        self.expire = expire
    def __call__(self, card, target):
        import new
        from game.stacked_function import stacked_function
        name = self.name
        obj = None
        cls = self.global_class
        target = self.global_class

        is_derived = False
        # The function is defined in the superclass (which we don't override)
        if not name in target.__dict__:
            is_derived = True
            # Bind the call to the superclass function
            orig_func = new.instancemethod(lambda self, *args, **named: getattr(super(cls, self), name).__call__(*args,**named), obj, cls)
        else:
            orig_func = getattr(target, name)
        if not hasattr(orig_func, "stacked"):
            stacked_func = stacked_function(orig_func, combiner=self.combiner, reverse=self.reverse)
            setattr(target, name, stacked_func)
        else: stacked_func = orig_func
        new_func = new.instancemethod(self.func, obj, cls)
        stacked_func.add_func(new_func)
        def restore(stacked_func=stacked_func, self=self):
            stacked_func.remove_func(new_func)
            if not stacked_func.stacking():
                setattr(target, name, stacked_func.funcs[0])
                del stacked_func
        if self.expire: card.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Override %s"%self.name

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
        else: return False
    def __call__(self, card, target):
        old_attachment = target.attached_to
        target.attach(self.attach_to)
        return lambda: target.attach(old_attachment)
    def __str__(self):
        return "Reattach"

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
            for role in old_roles: target.add_subrole(role)
            for char, val in old_chars.items(): setattr(target, char, val)
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Remove roles"

class AddSubRole(Effect):
    def __init__(self, subrole, subrole_info, expire=True):
        self.subrole = subrole
        self.subrole_info = subrole_info
        self.expire = expire
    def __call__(self, card, target):
        target.add_subrole(self.subrole)
        for chr,val in self.subrole_info.items():
            characteristic = getattr(target, chr)
            if hasattr(val, "is_characteristic"):
                old_characteristic = characteristic
                setattr(target, chr, val)
            else:
                characteristic.add(val)
        def restore():
            card.send(RemoveSubRoleEvent(), card=target)
            target.remove_subrole(self.subrole)
            for chr, val in self.subrole_info.items():
                characteristic = getattr(target, chr)
                if hasattr(val, "is_characteristic"):
                    setattr(target, chr, old_characteristic)
                else:
                    characteristic.remove(val)
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        # XXX Should the card send these messages, or the target?
        card.send(AddSubRoleEvent(), card=target)
        return restore
    def __str__(self):
        return "Add %s"%self.subrole

class GiveKeyword(Effect):
    def __init__(self, keyword_func, expire=True, keyword=''):
        self.keyword_func = keyword_func
        self.expire = expire
        self.keyword_name = keyword
    def __call__(self, card, target):
        from game.CardRoles import Creature
        # XXX This looks ugly, but is necessary to bind the correct subrole
        restore = self.keyword_func(target.current_role.get_subrole(Creature))
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Give %s"%self.keyword_name

class DoUntil(Effect):
    def __init__(self, effect, event, match_condition):
        self.effect = effect
        self.event = event
        self.match_condition = match_condition
        self.triggers = []
    def __call__(self, card, target):
        import Trigger
        restore = self.effect(card, target)
        trigger = Trigger.Trigger(self.event)
        def do_until():
            restore()
            trigger.clear_trigger()
            self.triggers.remove(trigger)
        trigger.setup_trigger(None, do_until, self.match_condition)
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
        new_ability.card = target.card
        target.abilities.append(new_ability)
        restore = lambda: target.abilities.remove(new_ability)
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Give %s"%self.ability

class RemoveCounter(Effect):
    def __init__(self, counter_type, number=1):
        self.counter_type = counter_type
        self.number = number
    def process_target(self, card, target):
        self.counters = [counter for counter in target.counters if counter == self.counter_type]
        return len(self.counters) >= self.number
    def __call__(self, card, target):
        for counter in self.counters[:self.number]:
            target.counters.remove(counter)
            target.send(CounterRemovedEvent(), counter=counter)
        return True
    def __str__(self):
        return "Remove %s counter"%self.counter_type


class AddCounter(Effect):
    def __init__(self, counter, number=1, expire=True):
        self.counter = counter
        self.expire = expire
        self.number = number
    def __call__(self, card, target):
        counters = []
        for i in range(self.number):
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
        return "Add %s counter"%self.counter

class AddPowerToughnessCounter(AddCounter):
    from Counters import PowerToughnessCounter
    def __init__(self, power, toughness, number=1, expire=True):
        super(AddPowerToughnessCounter,self).__init__(self.PowerToughnessCounter(power,toughness), number, expire)

class AugmentPowerToughness(Effect):
    from Counters import PowerToughnessCounter
    def __init__(self, power, toughness, expire=True):
        self.power = power
        self.toughness = toughness
        self.expire = expire
    def __call__(self, card, target):
        PT = self.PowerToughnessCounter(self.power, self.toughness)
        target.PT_modifiers.append(PT)
        remove_counter = lambda: target.PT_modifiers.remove(PT)
        if self.expire: target.register(remove_counter, CleanupEvent(), weak=False, expiry=1)
        return remove_counter
    def __str__(self):
        return "Add %+d/%+d"%(int(self.power), int(self.toughness))

class ChangeZone(Effect):
    def __init__(self, from_zone, to_zone, to_position="top", func=lambda card: None, expire=False):
        self.from_zone = from_zone
        self.to_zone = to_zone
        self.to_position = to_position
        self.func = func
        self.expire = expire
    def __call__(self, card, target):
        if self.from_zone == "play": from_zone = target.controller.play
        else: from_zone = getattr(target.owner, self.from_zone)
        to_zone = getattr(target.owner, self.to_zone)
        if self.to_position == "top": position = -1
        else: position = 0
        self.func(target)
        to_zone.move_card(target, from_zone, position=position)
        target.targeted = False
        def restore():
            # XXX What do we do if the target is not in the zone we left him?
            if target.zone == to_zone: 
                from_zone.move_card(target, to_zone)
        if self.expire: target.register(restore, CleanupEvent(), weak=False, expiry=1)
        return restore
    def __str__(self):
        return "Move from %s to %s"%(self.from_zone, self.to_zone)

class ChangeZoneFromPlay(ChangeZone):
    def __init__(self, to_zone, to_position="top", func=lambda card: None):
        super(ChangeZoneFromPlay,self).__init__(from_zone="play", to_zone=to_zone, to_position=to_position, func = func)

class PlayCard(Effect):
    def __init__(self, cost=None):
        from game.Cost import ManaCost
        if type(cost) == str: cost = ManaCost(cost)
        self.cost = cost
    def __call__(self, card, target):
        from game.Action import PlayInstant
        if isPermanent(target): return False
        if not isLandType(target): action = PlayInstant(target)
        else: action = target.play_action(target)
        
        # Different cost to play
        casting_ability = target.abilities[0]
        if self.cost and hasattr(casting_ability, "cost"):
            # XXX Generally the first ability of the spell is casting it - might not always be the case
            original_cost = casting_ability.cost
            casting_ability.cost = self.cost
        result = action.perform(card.controller)
        if self.cost and hasattr(casting_ability, "cost"): casting_ability.cost = original_cost
        return result
    def __str__(self):
        return "Play card"

class ReturnToLibrary(Effect):
    # This class can't use the ChangeZone functionality, because that targets a card, and the card's
    # final location (the graveyard) is different from starting location (probably hand) so that the
    # targeting of "self" will fail (because the zone is different)
    def __call__(self, card, target):
        player = card.owner
        player.moveCard(card, player.graveyard, player.library)
        player.library.shuffle()
        return True
    def __str__(self):
        return "Return to library"

class ShuffleLibrary(Effect):
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target (not a player)")
        target.library.shuffle()
        return True
    def __str__(self):
        return "Shuffle library"

# This deals with starting zones other than in play
class MoveTargetCards(Effect):
    def __init__(self, from_zone, to_zone, from_position="", to_position="top", number=1, card_types=None, subset=None, func=lambda card: None, reveal=False, peek=False, required=False):
        self.from_zone = from_zone
        self.to_zone = to_zone
        self.number = number
        self.subset = subset
        self.from_position = from_position
        self.to_position = to_position
        if card_types == None: card_types = isCard
        if (type(card_types) == list or type(card_types) == tuple): self.card_types = card_types
        else: self.card_types = [card_types]
        self.func = func
        self.reveal = reveal
        self.peek = peek
        self.required = required
    def process_target(self, card, target):
        from_zone = getattr(target, self.from_zone)
        if len(from_zone) == 0: return False
        if not self.from_position: # We can select anywhere so ask the player
            # Prefilter the list to only show valid card types
            selection = reduce(lambda x, y: x+y, [from_zone.get(ttype) for ttype in self.card_types])
            if len(selection) == 0: return False
            if self.number == -1 or len(selection) < self.number: self.number = len(selection)
            # Now we get the selection - if the from location is library or hand the target player makes the choice
            if self.from_zone in ["library", "hand"] and not self.peek: selector = target
            else: selector = card.controller
            self.cardlist = selector.getSelection(selection[:self.subset], self.number, required=self.required, prompt="Select %s to move from %s to %s"%(' or '.join(map(str,self.card_types)), self.from_zone, self.to_zone))
            if not self.cardlist: return False
            if self.number == 1: self.cardlist = [self.cardlist]
        elif self.from_position == "top": self.cardlist = from_zone.cards[:-(self.number+1):-1]
        elif self.from_position == "bottom": self.cardlist = from_zone.cards[:self.number]
        else: raise Exception("Incorrect from position specified for MoveTargetCards (%s)"%card)

        # If we are moving to the play zone make sure that the card is a Permanent
        # XXX Does the card need to be checked to see if it can be targetted? I'm not sure since it's not in play
        if self.to_zone=="play" and sum([isPermanent.match(c, use_in_play=True) for c in self.cardlist]) == 0: return False
        #return sum([self.match_condition(c) and c.canBeTargetedBy(card) for c in cards]) != 0
        target.targeted = True
        return True
    def __call__(self, card, target):
        from_zone = getattr(target, self.from_zone)
        if self.to_position == "top": position = -1
        else: position = 0
        for c in self.cardlist[::-1]:
            if not c.zone == from_zone: continue
            # Make sure we get the owner's zone
            if not self.to_zone == "play": to_zone = getattr(c.owner, self.to_zone)
            else:
                to_zone = card.controller.play
                c.controller = card.controller
            to_zone.move_card(c, from_zone, position=position)
            self.func(c)
        # XXX if there is a library access in here, then we might need to shuffle it
        #if self.from_zone == "library" and not self.from_position: from_zone.shuffle()
        target.targeted = False
        if self.reveal == True: target.opponent.revealCard(self.cardlist, prompt="%s reveals card(s) "%target)
        return True
    def __str__(self):
        return "Move %d %s(s) from %s to %s"%(self.number,' or '.join(map(str,self.card_types)),self.from_zone,self.to_zone)

# These could be implemented as MoveTargetCards, but it's better to use the Player functions
# (so that appropriate signals will be send)
class DrawCard(Effect):
    def __init__(self, number=1):
        self.number = number
    def __call__(self, card, target):
        if not isPlayer(target): raise Exception("Invalid target (not a player)")
        for i in range(self.number): target.draw()
        return True
    def __str__(self):
        return "Draw %d card(s)"%(self.number)
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
        if len(selection) < self.number: return False
        if self.random:
            import random
            result = [selection[i] for i in random.sample(range(len(selection)), self.number)]
            if self.number == 1: result = result[0]
        else:
            result = target.getSelection(selection, self.number, required=self.required, prompt="Discard cards")
        if not result: return False
        if self.number > 1:
            for card in result: target.discard(card)
        else: target.discard(result)
        return True
    def __str__(self):
        return "Discard %d card(s)"%(self.number)
#class DrawCard(MoveTargetCards):
#    def __init__(self, number=1):
#        super(DrawCard,self).__init__(from_zone="library", to_zone="hand", from_position="top", number=number)
#    def __str__(self):
#        return "Draw %d card(s)"%(self.number)
#class DiscardCard(MoveTargetCards):
#    def __init__(self, number=1, card_types=isCard):
#        super(DiscardCard,self).__init__(from_zone="hand", to_zone="graveyard", number=number, card_types=card_types)
#    def __str__(self):
#        return "Discard %d card(s)"%(self.number)
