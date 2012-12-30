from StaticAbility import CardStaticAbility
from Cost import SpecialCost, ManaCost
from EffectsUtilities import do_override
from InvasionAbility import kicked

__all__ = ['multikicker']

class MultiKickerCost(SpecialCost):
    def __init__(self, cost):
        if isinstance(cost, str): cost = ManaCost(cost)
        self._cost = cost
        self.cost = cost
    def precompute(self, source, player):
        self.kicked = player.getX(prompt="Number of times to pay %s"%self._cost)
        #source.kicked.times = 0
        if self.kicked > 0: self.cost = reduce(lambda x, y: x + y, [self._cost for i in range(1, self.kicked)], self._cost)
        elif self.kicked < 0: self.kicked = 0 # CancelAction becomes -1
        if self.kicked and super(MultiKickerCost, self).precompute(source, player):
            source.kicked.add(str(self._cost))
            source.kicked.times += self.kicked
        else:
            self.cost = ManaCost('0')
        return True
    def compute(self, source, player):
        if self.kicked:
            self.kicked = super(MultiKickerCost, self).compute(source, player)
        return True
    def pay(self, source, player):
        if self.kicked: super(MultiKickerCost, self).pay(source, player)
    def payment(self):
        if self.kicked: return self.cost.payment
        else: return "0"
    payment = property(fget=payment)

def multikicker(cost):
    def effects(card):
        card.kicked = kicked()
        #yield (do_override(card, "_get_additional_costs", lambda self: MultiKickerCost(cost)),
        #      do_override(card, "modifyNewRole", lambda self, new, zone: setattr(new, "kicked", self.kicked)))
        def modifyNewRole(self, new, zone):
            if str(zone) == "battlefield":
                setattr(new, "kicked", self.kicked)
        yield (do_override(card, "_get_additional_costs", lambda self: MultiKickerCost(cost)),
              do_override(card, "modifyNewRole", modifyNewRole))
    return CardStaticAbility(effects, zone="stack", txt='multikicker %s'%cost, keyword="kicker")
