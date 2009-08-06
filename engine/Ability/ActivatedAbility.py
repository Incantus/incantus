from Ability import Ability
from Limit import no_limit
from Cost import ManaCost

class CostAbility(Ability):
    zone = "play"
    limit_type = no_limit   # This is because if instantiate when the class is created, all the signalling is cleared
    def __init__(self, effects, limit=None, zone=None, txt='', keyword=''):
        super(CostAbility,self).__init__(effects, txt=txt)
        if limit: self.limit = limit
        else: self.limit = self.limit_type
        if zone: self.zone = zone
        if keyword and not txt: self.txt = keyword.capitalize()
        self.keyword = keyword
    def playable(self, source):
        return (self.zone == "all" or str(source.zone) == self.zone) and self.limit(source)
    def do_announce(self):
        # Do all the stuff in rule 409.1 like pick targets, pay costs, etc
        source, player = self.source, self.controller
        self.effects = self.effect_generator(player, source)  # Start up generator
        self.cost = self.effects.next()
        if type(self.cost) == str: self.cost = ManaCost(self.cost)
        if (self.cost.precompute(source, player) and
           self.get_targets() and
           self.cost.compute(source, player)):
               self.cost.pay(source, player)
               return True
        else:
            return False
    def played(self):
        self.limit.played(self.source)
        super(CostAbility, self).played()
    def resolved(self):
        self.limit.resolved(self.source)
        super(CostAbility, self).resolved()
    def _get_targets_from_effects(self):
        return self.effects.send(self.cost)
    def __str__(self):
        return self.txt

class ActivatedAbility(CostAbility):
    activated = True
    enabled = property(fget=lambda self: self._status_count > 0)
    def __init__(self, effects, limit=None, zone=None, txt='', keyword=''):
        super(ActivatedAbility,self).__init__(effects, limit, zone, txt, keyword)
        self._status_count = 0
    def enable(self, source):
        self.source = source
        self.toggle(True)
    def disable(self): self.toggle(False)
    def toggle(self, val):
        if val: self._status_count += 1
        else: self._status_count -= 1
    def play(self, player):
        # Make copy and announce it
        copy = self.copy()
        copy.controller = player
        return copy.announce()
    def playable(self, source): return self.enabled and super(ActivatedAbility, self).playable(source)
    def __repr__(self): return "%s<%s %o: %s>"%('*' if self.enabled else '', self.__class__.__name__, id(self), self.txt)

class ManaAbility(ActivatedAbility):
    mana_ability = True
    def preannounce(self): pass
    def canceled(self): pass
    def played(self):
        self.limit.played(self.source)
        self.resolve()
    def resolved(self):
        self.limit.resolved(self.source)
        super(ManaAbility, self).resolved()
