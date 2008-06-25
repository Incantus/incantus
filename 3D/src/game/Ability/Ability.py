from game.GameObjects import MtGObject
from game.GameEvent import PlayAbilityEvent, AbilityCountered, AbilityResolved, TimestepEvent
from Target import Target

class Ability(MtGObject):
    def __init__(self, card, target=None, effects=[], copy_targets=True, txt=''):
        self.card = card
        self.controller = None
        if not (type(effects) == list or type(effects) == tuple): effects = [effects]
        self.effects = effects
        if target == None: target = [Target(targeting="you")]
        elif not (type(target) == list or type(target) == tuple): target = [target]
        self.targets = target
        self.copy_targets = copy_targets
        self.txt = txt
    def played(self):
        # XXX This is done in Action.py
        #self.controller.send(PlayAbilityEvent(), ability=self)
        pass
    def needs_stack(self):
        return True
    def needs_target(self):
        return not self.targets == None
    def multiplex(self):
        num_targets, num_effects = len(self.targets), len(self.effects)
        if num_effects == 0: return #For cast spell effects
        if num_targets == 1 and num_effects > 1:
            target = self.targets[0]
            for effect in self.effects:
                yield target.target, effect
        elif num_targets == num_effects:
            for target, effect in zip(self.targets, self.effects):
                yield target.target, effect
        elif num_effects == 1:
            yield [target.target for target in self.targets], self.effects[0]
        else: raise Exception("Mismatched number of targets and effects in %s of %s"%(self, self.card))
    def check_target(self):
        success = True
        for target in self.targets:
            if not target.check_target(self.card): success = False
        return success
    def get_target(self):
        for target in self.targets:
            if not target.get(self.card): return False
        # Some effects need to process the target before it goes on the stack
        target_aquired = True
        for target, effect in self.multiplex():
            if not effect.process_target(self.card, target): target_aquired = False
        return target_aquired
    def preresolve(self): return True
    def do_resolve(self):
        if self.resolve(): self.resolved()
        else: self.countered()
        self.cleanup()
    def resolve(self):
        success = True
        if self.needs_target() and not self.check_target(): return False
        if not self.preresolve(): return False
        self.send(TimestepEvent())    # This is for any cards that are moved into play in preresolve
        for target, effect in self.multiplex():
            if effect(self.card, target) == False: success=False
            self.send(TimestepEvent())
        return success
    def resolved(self): self.card.send(AbilityResolved())
    def can_be_countered(self): return True
    def countered(self): self.card.send(AbilityCountered())
    def cleanup(self): pass
    def copy(self):
        import copy
        newcopy = copy.copy(self)
        # XXX If copy the effects then things like TriggerEffect won't work
        #newcopy.effects = [e.copy() for e in self.effects]
        if self.copy_targets: newcopy.targets = [t.copy() for t in self.targets]
        return newcopy
    def __str__(self):
        if self.txt: return self.txt
        else: return ', '.join(map(str,self.effects))

# The following are mixin classes

class Stackless(object):
    def needs_stack(self): return False

class PostponeTargeting(object):
    def get_target(self):
        return True
    def resolve(self):
        if not super(PostponeTargeting, self).get_target(): return False
        return super(PostponeTargeting, self).resolve()

class StacklessAbility(Stackless, Ability): pass
class PostponedAbility(PostponeTargeting, Ability): pass
