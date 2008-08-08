from game.GameObjects import MtGObject
from game.GameEvent import AbilityAnnounced, AbilityPlayedEvent, AbilityCanceled, AbilityCountered, AbilityResolved, TimestepEvent
from Target import Target

class Ability(MtGObject):
    def __init__(self, card, target=None, effects=[], copy_targets=True, txt=''):
        self.card = card
        if not (type(effects) == list or type(effects) == tuple): effects = [effects]
        self.effects = effects
        if target == None: target = [Target(targeting="you")]
        elif not (type(target) == list or type(target) == tuple): target = [target]
        self.targets = target
        self.copy_targets = copy_targets
        self.txt = txt
        self.controller = None
    def announce(self, player):
        self.controller = player
        self.preannounce()
        if self.do_announce():
            self.played()
            player.send(AbilityPlayedEvent(), ability=self)
        else:
            player.send(AbilityCanceled(), ability=self)
    def preannounce(self): self.controller.send(AbilityAnnounced(), ability=self)
    def do_announce(self): return self.get_target()
    def played(self): self.controller.stack.push(self)
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
    def get_target(self):
        for target in self.targets:
            if not target.get(self.card):
                return False
        target_aquired = True
        # Some effects need to process the target before it goes on the stack
        for target, effect in self.multiplex():
            if not effect.process_target(self.card, target): target_aquired = False
        return target_aquired
    def resolve(self):
        if all((target.check_target(self.card) for target in self.targets)):
            for target, effect in self.multiplex():
                effect(self.card, target)
                self.send(TimestepEvent())
            self.resolved()
        else: self.countered()
    def resolved(self): self.card.send(AbilityResolved())
    def can_be_countered(self): return True
    def countered(self): self.card.send(AbilityCountered())
    def copy(self, card=None):
        import copy
        newcopy = copy.copy(self)
        if not card: newcopy.card = self.card
        else: newcopy.card = card
        if self.copy_targets: newcopy.targets = [t.copy() for t in self.targets]
        return newcopy
    def __str__(self):
        if self.txt: return self.txt
        else: return ', '.join(map(str,self.effects))
