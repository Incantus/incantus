import copy
from game.GameEvent import AbilityAnnounced, AbilityCanceled, AbilityCountered, AbilityResolved, TimestepEvent

class Ability(object):
    def __init__(self, effects, txt=''):
        self.effect_generator = effects
        if not txt and effects.__doc__: txt = effects.__doc__
        self.txt = txt
        self.controller = None
    def announce(self, source, player):
        self.source = source
        self.controller = player
        self.preannounce()
        if self.do_announce():
            self.played()
            return True
        else:
            self.canceled()
            return False
    def preannounce(self):
        self.targets = []
        self.controller.send(AbilityAnnounced(), ability=self)
    def canceled(self): self.controller.send(AbilityCanceled(), ability=self)
    def do_announce(self): raise NotImplementedException()
    def played(self): self.controller.stack.push(self)
    def _get_targets_from_effects(self): return self.effects.next()
    def get_targets(self):
        targets = self._get_targets_from_effects()
        if not (type(targets) == tuple): targets = (targets,)
        if all((target.get(self.source) for target in targets)):
            self.targets = targets
            return True
        else: return False
    def check_targets(self): return any((target.check_target(self.source) for target in self.targets))
    def resolve(self):
        if self.check_targets():
            targets = [target.get_targeted() for target in self.targets]
            if len(targets) == 1: targets = targets[0]
            self.effects.send(targets)
            self.source.send(TimestepEvent())
            for _ in self.effects:
                self.source.send(TimestepEvent())
            self.resolved()
        else: self.countered()
        del self.effects
    def resolved(self):
        self.source.send(TimestepEvent())
        self.source.send(AbilityResolved())
    def can_be_countered(self): return True
    def countered(self): self.source.send(AbilityCountered())
    def copy(self): return copy.copy(self)
    def __str__(self):
        return self.txt
