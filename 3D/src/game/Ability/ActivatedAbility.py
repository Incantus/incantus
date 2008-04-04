from Ability import Ability, Stackless
from Target import Target
from game.Match import isCard, isCreature
import game.Cost

class ActivatedAbility(Ability):
    def __init__(self, card, cost="0", target=None, effects=[], limit=None, copy_targets=True, zone="play"):
        super(ActivatedAbility,self).__init__(card, target=target, effects=effects, limit=limit, copy_targets=copy_targets)
        if type(cost) == str or type(cost) == int: cost = game.Cost.ManaCost(cost)
        self.cost = cost
        self.zone = zone
    def is_limited(self):
        return not self.card.zone == getattr(self.card.controller, self.zone) or super(ActivatedAbility,self).is_limited()
    def compute_cost(self):
        return self.cost.compute(self.card, self.card.controller)
    def pay_cost(self):
        return self.cost.pay(self.card, self.card.controller)
    def __str__(self):
        if self.txt: return self.txt
        else: return "%s: %s"%(self.cost,super(ActivatedAbility,self).__str__())

class MultipleAbilities(ActivatedAbility):
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
    def compute_cost(self): return self.process_abilities("compute_cost")
    def pay_cost(self): return self.process_abilities("pay_cost")
    def get_target(self): return self.process_abilities("get_target")
    def resolve(self): return self.process_abilities("resolve")
    def __str__(self):
        return ", ".join(map(str, self.abilities))

class ManaAbility(ActivatedAbility):
    def __init__(self, card, cost="0", target=Target(targeting="controller"), effects=[]):
        super(ManaAbility,self).__init__(card, cost=cost, target=target, effects=effects)
    def is_mana_ability(self):
        return True
    def needs_stack(self):
        return False

class EquipAbility(ActivatedAbility):
    def __init__(self, card, cost="0"):
        import Limit, Effect
        super(EquipAbility,self).__init__(card, cost=cost, target=Target(target_types=isCreature), effects=Effect.AttachToPermanent(), limit=Limit.SorceryLimit(card))

class ChoiceAbility(ActivatedAbility):
    def __init__(self, card, cost="0", msg='', choice_target=Target(targeting="controller"), target=Target(targeting="controller"), effects=[], during_resolution=False):
        super(ChoiceAbility, self).__init__(card, cost=cost, target=target,effects=effects)
        self.choice_target = choice_target
        if not msg: msg = "...%s"%', '.join(map(str,self.effects))
        self.msg = msg
        self.during_resolution = during_resolution
    def get_target(self):
        target_aquired = self.choice_target.get(self.card)
        if not self.during_resolution: 
            choice = self.choice_target.target.getIntention(prompt=self.msg,msg=self.msg)
            if not choice: return False
        return super(ChoiceAbility,self).get_target()
    def resolve(self):
        if self.during_resolution:
            choice = self.choice_target.target.getIntention(prompt=self.msg,msg=self.msg)
            if not choice: return False
        return super(ChoiceAbility,self).resolve()
    def __str__(self):
        return "You may ...%s"%', '.join(map(str,self.effects))

class DoOrAbility(ActivatedAbility):
    def __init__(self, card, cost="0", target=Target(targeting="controller"), failure_target=Target(targeting="controller"), effects=[], failed=[], copy_targets=False):
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

class StacklessDoOrAbility(Stackless, DoOrAbility): pass
