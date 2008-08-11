from game.GameEvent import AbilityAnnounced, AbilityCanceled, AbilityCountered, AbilityResolved, TimestepEvent

class Ability(object):
    def __init__(self, card, effects, txt=''):
        self.card = card
        self.effect_generator = effects
        self.txt = txt
        self.controller = None
    def announce(self, player):
        self.controller = player
        self.preannounce()
        if self.do_announce():
            self.played()
            return True
        else:
            self.canceled()
            return False
    def preannounce(self): self.controller.send(AbilityAnnounced(), ability=self)
    def canceled(self): self.controller.send(AbilityCanceled(), ability=self)
    def do_announce(self): raise NotImplementedException()
    def played(self): self.controller.stack.push(self)
    def _get_targets_from_effects(self): return self.effects.next()
    def get_targets(self):
        targets = self._get_targets_from_effects()
        if not (type(targets) == tuple): targets = (targets,)
        if all((target.get(self.card) for target in targets)):
            self.targets = targets
            return True
        else: return False
    def check_targets(self): return all((target.check_target(self.card) for target in self.targets))
    def resolve(self):
        if self.check_targets():
            targets = [target.target for target in self.targets]
            if len(targets) == 1: targets = targets[0]
            self.effects.send(targets)
            self.card.send(TimestepEvent())
            for _ in self.effects:
                self.card.send(TimestepEvent())
            self.resolved()
        else: self.countered()
        del self.effects
    def resolved(self): self.card.send(AbilityResolved())
    def can_be_countered(self): return True
    def countered(self): self.card.send(AbilityCountered())
    def copy(self, card=None):
        import copy
        newcopy = copy.copy(self)
        if not card: newcopy.card = self.card
        else: newcopy.card = card
        return newcopy
    def __str__(self):
        return self.txt
