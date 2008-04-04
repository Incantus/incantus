from game.GameObjects import MtGObject
from game.GameEvent import AbilityCountered, AbilityResolved
from Target import Target
from Limit import Unlimited

class Ability(MtGObject):
    def __init__(self, card, target=None, effects=[], limit=None, copy_targets=True, txt=''):
        self.card = card
        if not (type(effects) == list or type(effects) == tuple):
            self.effects = [effects]
        else: self.effects = effects
        if target == None: target = [Target(targeting="controller")]
        elif not (type(target) == list or type(target) == tuple):
            target = [target]
        self.targets = target
        self.txt = txt
        if not limit: limit=Unlimited(card)
        self.limit = limit
        self.copy_targets = copy_targets
    def is_limited(self):
        return self.limit()
    def is_mana_ability(self):
        return False
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
    def do_resolve(self):
        self.preresolve()
        if self.resolve(): self.resolved()
        else: self.countered()
        self.cleanup()
    def resolve(self):
        success = True
        if self.needs_target() and not self.check_target(): return False
        for i, effect in enumerate(self.effects):
            if len(self.targets) == 1: i = 0
            if effect(self.card, self.targets[i].target) == False: success=False
        return success
    def preresolve(self): pass
    def played(self): pass
    def resolved(self): self.card.send(AbilityResolved())
    def can_be_countered(self): return True
    def countered(self): self.card.send(AbilityCountered())
    def cleanup(self): self.card.out_play_role.onstack = False
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

class StacklessAbility(Stackless, Ability): pass

class PostponeTargeting(object):
    def get_target(self):
        return True
    def resolve(self):
        if not super(PostponeTargeting, self).get_target(): return False
        return super(PostponeTargeting, self).resolve()

class PostponedAbility(PostponeTargeting, Ability): pass
