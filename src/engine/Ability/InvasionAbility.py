from StaticAbility import CardStaticAbility
from Cost import SpecialCost, ManaCost
from EffectsUtilities import do_override

__all__ = ["kicker"]

class KickerCost(SpecialCost):
    def __init__(self, cost):
        if isinstance(cost, str): cost = ManaCost(cost)
        self.cost = cost
    def precompute(self, source, player):
        self.kicked = False
        if player.you_may("pay the kicker cost of %s"%self.cost):
            if super(KickerCost, self).precompute(source, player):
                source.kicked.add(str(self.cost))
                source.kicked.times += 1
                self.kicked = True
        return True
    def compute(self, source, player):
        if self.kicked:
            self.kicked = super(KickerCost, self).compute(source, player)
        return True
    def pay(self, source, player):
        if self.kicked: super(KickerCost, self).pay(source, player)
    def payment(self):
        if self.kicked: return self.cost.payment
        else: return "0"
    payment = property(fget=payment)

class kicked(set):
    def __init__(self, *args, **kw):
        self.times = 0
        super(kicked, self).__init__(*args, **kw)
    def __eq__(self, other): return other in self

def kicker(cost):
    def effects(card):
        card.kicked = kicked()
        #yield (do_override(card, "_get_additional_costs", lambda self: KickerCost(cost)),
        #      do_override(card, "modifyNewRole", lambda self, new, zone: setattr(new, "kicked", self.kicked)))
        def modifyNewRole(self, new, zone):
            if str(zone) == "battlefield":
                setattr(new, "kicked", self.kicked)
        yield (do_override(card, "_get_additional_costs", lambda self: KickerCost(cost)),
              do_override(card, "modifyNewRole", modifyNewRole))
    return CardStaticAbility(effects, zone="stack", keyword="kicker")

