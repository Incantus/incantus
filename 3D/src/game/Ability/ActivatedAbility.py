from Ability import Ability, Stackless
from Target import Target
from Limit import Unlimited
import game.Cost

class ActivatedAbility(Ability):
    def __init__(self, card, cost="0", target=None, effects=[], copy_targets=True, limit=None, zone="play"):
        super(ActivatedAbility,self).__init__(card, target=target, effects=effects, copy_targets=copy_targets)
        if type(cost) == str or type(cost) == int: cost = game.Cost.ManaCost(cost)
        self.cost = cost
        if limit == None: limit = Unlimited(card)
        self.limit = limit
        self.zone = zone
    def is_limited(self):
        return not (self.card.zone == getattr(self.card.controller, self.zone) and self.limit())
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
    def __init__(self, card, cost="0", target=Target(targeting="you"), effects=[]):
        super(ManaAbility,self).__init__(card, cost=cost, target=target, effects=effects)
    def is_mana_ability(self):
        return True
    def needs_stack(self):
        return False

class MayAbility(ActivatedAbility):
    def __init__(self, card, cost="0", msg='', choice_target=Target(targeting="you"), target=Target(targeting="you"), effects=[], limit=None, zone="play"):
        super(MayAbility, self).__init__(card, cost=cost, target=target,effects=effects,limit=limit,zone=zone)
        self.choice_target = choice_target
        if not msg: msg = "...%s"%', '.join(map(str,self.effects))
        self.msg = msg
    def get_target(self):
        if not self.choice_target.get(self.card): return False
        else: return super(MayAbility,self).get_target()
    def preresolve(self):
        return self.choice_target.target.getIntention(prompt=self.msg,msg=self.msg)
    def __str__(self):
        return "You may... %s"%', '.join(map(str,self.effects))

class DoOrAbility(ActivatedAbility):
    def __init__(self, card, cost="0", target=Target(targeting="you"), failure_target=Target(targeting="you"), effects=[], failed=[], copy_targets=False):
        super(DoOrAbility, self).__init__(card, cost=cost, target=target,effects=effects,copy_targets=copy_targets)
        if not (type(failed) == list or type(failed) == tuple): failed = [failed]
        self.failed = failed
        if not (type(failure_target) == list or type(failure_target) == tuple): failure_target=[failure_target]
        self.failure_targets = failure_target
        self.target_failure = False
    def get_target(self):
        self.target_failure = False
        target_aquired = super(DoOrAbility,self).get_target()
        if not target_aquired: self.target_failure = True
        for target in self.failure_targets:
            if not target.get(self.card): return False
        target_aquired = True
        for i, effect in enumerate(self.failed):
            if len(self.failure_targets) == 1: i = 0
            if not effect.process_target(self.card, self.failure_targets[i].target): target_aquired = False
        return target_aquired
    def resolve(self):
        success = False
        if not self.target_failure: success = super(DoOrAbility,self).resolve()
        if not success:
            # Make sure the target for failure is still valid
            success = True
            for target in self.failure_targets:
                if not target.check_target(self.card): success = False
            if success:
                for i, effect in enumerate(self.failed):
                    if len(self.failure_targets) == 1: i = 0
                    if effect(self.card, self.failure_targets[i].target) == False: success=False
        return success
    def __str__(self):
        if not self.target_failure: return ', '.join(map(str,self.effects))
        else: return ', '.join(map(str,self.failed))
        #return "%s or %s"%(', '.join(map(str,self.effects)), ', '.join(map(str,self.failed)))

class StacklessActivatedAbility(Stackless, ActivatedAbility): pass
class StacklessDoOrAbility(Stackless, DoOrAbility): pass
