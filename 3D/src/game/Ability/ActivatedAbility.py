from Ability import Ability
from Target import Target
from Limit import Unlimited
import game.Cost

class ActivatedAbility(Ability):
    def __init__(self, card, cost="0", target=None, effects=[], copy_targets=True, limit=None, zone="play", txt=''):
        super(ActivatedAbility,self).__init__(card, target=target, effects=effects, copy_targets=copy_targets, txt=txt)
        if type(cost) == str or type(cost) == int: cost = game.Cost.ManaCost(cost)
        self.cost = cost
        if limit == None: limit = Unlimited(card)
        self.limit = limit
        self.zone = zone
    def is_limited(self):
        return not (str(self.card.zone) == self.zone and self.limit())
    def is_mana_ability(self):
        return False
    def precompute_cost(self):
        return self.cost.precompute(self.card, self.card.controller)
    def compute_cost(self):
        return self.cost.compute(self.card, self.card.controller)
    def pay_cost(self):
        self.cost.pay(self.card, self.card.controller)
        return True
    def __str__(self):
        if self.txt: return self.txt
        else: return "%s: %s"%(self.cost,super(ActivatedAbility,self).__str__())

class MultipleAbilities(ActivatedAbility):
    # XXX This doesn't override all the functions it should
    # Is there a better way of doing this? Currently only used by Broken Ambitions
    def __init__(self, card, cost="0", abilities=[]):
        super(MultipleAbilities, self).__init__(card, cost)
        self.abilities = abilities
    def process_abilities(self, func_name):
        success = True
        for a in self.abilities:
            func = getattr(a, func_name)
            if not func():
                success = False
                break
        print "func_name", func_name, success
        return success
    def precompute_cost(self): return self.process_abilities("precompute_cost")
    def compute_cost(self): return self.process_abilities("compute_cost")
    def pay_cost(self):
        self.process_abilities("pay_cost")
        return True
    def get_target(self): return self.process_abilities("get_target")
    def resolve(self): return self.process_abilities("resolve")
    def __str__(self):
        return ", ".join(map(str, self.abilities))

class ManaAbility(ActivatedAbility):
    def __init__(self, card, cost="0", target=Target(targeting="you"), effects=[], txt=''):
        super(ManaAbility,self).__init__(card, cost=cost, target=target, effects=effects, txt=txt)
    def is_mana_ability(self):
        return True
    def needs_stack(self):
        return False
