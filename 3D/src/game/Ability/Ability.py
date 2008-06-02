from game.GameObjects import MtGObject
from game.GameEvent import PlayAbilityEvent, AbilityCountered, AbilityResolved, TimestepEvent
from Target import Target

class Ability(MtGObject):
    def __init__(self, card, target=None, effects=[], copy_targets=True, txt=''):
        self.card = card
        self.controller = None
        if not (type(effects) == list or type(effects) == tuple):
            self.effects = [effects]
        else: self.effects = effects
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
        for i, effect in enumerate(self.effects):
            if len(self.targets) == 1: i = 0
            if not effect.process_target(self.card, self.targets[i].target): target_aquired = False
        return not target_aquired == False
    def preresolve(self): return True
    def do_resolve(self):
        if self.resolve(): self.resolved()
        else: self.countered()
        self.cleanup()
    def resolve(self):
        success = True
        if self.needs_target() and not self.check_target(): return False
        if not self.preresolve(): return False
        self.send(TimestepEvent())    # This is for any cards that are moved into play
        for i, effect in enumerate(self.effects):
            if len(self.targets) == 1: i = 0
            if effect(self.card, self.targets[i].target) == False: success=False
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
