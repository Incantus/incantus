from Ability import Ability
from Limit import Unlimited
from Cost import ManaCost

class ActivatedAbility(Ability):
    zone = "play"
    limit_type = Unlimited   # This is because if instantiate when the class is created, all the signalling is cleared
    def __init__(self, card, cost="0", target=None, effects=[], copy_targets=True, limit=None, zone=None, txt=''):
        super(ActivatedAbility,self).__init__(card, target=target, effects=effects, copy_targets=copy_targets, txt=txt)
        if type(cost) == str or type(cost) == int: cost = ManaCost(cost)
        self.cost = cost
        if limit: self.limit = limit
        else: self.limit = self.limit_type()
        if zone: self.zone = zone
    def playable(self):
        return (str(self.card.zone) == self.zone and self.limit(self.card))
    def do_announce(self):
        # Do all the stuff in rule 409.1 like pick targets, pay costs, etc
        card, player, cost = self.card, self.controller, self.cost
        if (cost.precompute(card, player) and
           self.get_target() and
           cost.compute(card, player)):
               cost.pay(card, player)
               return True
        else:
            return False
    def __str__(self):
        if self.txt: return self.txt
        else: return "%s: %s"%(self.cost,super(ActivatedAbility,self).__str__())

class ManaAbility(ActivatedAbility):
    mana_ability = True
    def preannounce(self): pass
    def played(self): self.resolve()

#class MultipleAbilities(ActivatedAbility):
    # XXX This doesn't override all the functions it should
    # Is there a better way of doing this? Currently only used by Broken Ambitions
#    def __init__(self, card, cost="0", abilities=[]):
#        super(MultipleAbilities, self).__init__(card, cost)
#        self.abilities = abilities
#    def process_abilities(self, func_name):
#        success = True
#        for a in self.abilities:
#            func = getattr(a, func_name)
#            if not func():
#                success = False
#                break
#        print "func_name", func_name, success
#        return success
#    def precompute_cost(self): return self.process_abilities("precompute_cost")
#    def compute_cost(self): return self.process_abilities("compute_cost")
#    def pay_cost(self):
#        self.process_abilities("pay_cost")
#        return True
#    def get_target(self): return self.process_abilities("get_target")
#    def resolve(self): return self.process_abilities("resolve")
#    def __str__(self):
#        return ", ".join(map(str, self.abilities))

