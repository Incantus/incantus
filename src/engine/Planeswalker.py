from stacked_function import replace
from abilities import stacked_abilities
from Ability.Counters import Counter
from Ability.Limit import SorceryLimit, CountLimit
from GameEvent import DealsDamageToEvent

planeswalker_sorcery = SorceryLimit()

class planeswalker_abilities(stacked_abilities):
    def __init__(self, source, abilities):
        super(planeswalker_abilities, self).__init__(source, abilities._stacking[0])
        self.walker_limit = planeswalker_sorcery+CountLimit(1)
        self.change_limit(*abilities._stacking[0]._abilities)
    def add(self, *abilities):
        self.change_limit(*abilities)
        super(planeswalker_abilities, self).add(*abilities)
    def change_limit(self, *abilities):
        for a in abilities:
            if hasattr(a, "activated"): a.limit += self.walker_limit

def redirect_to(planeswalker):
    from Player import Player
    def condition(self, amt, source, combat):
        controller = planeswalker.controller
        return self == controller and not (combat or source.controller == controller)
    def redirectDamage(self, amt, source, combat=False):
        redirect = source.controller.getIntention("", "Redirect %d damage to %s?"%(amt, planeswalker))
        if redirect: dmg = planeswalker.assignDamage(amt, source, combat)
        else: dmg = self.assignDamage(amt, source, combat)
        return dmg
    return replace(Player, "assignDamage", redirectDamage, condition=condition, msg="Redirect damage to %s"%planeswalker)

class PlaneswalkerType(object):
    def activatePlaneswalker(self):
        # These are immutable and come from the card
        self.add_counters("loyalty", self.loyalty)
        self.redirect_expire = redirect_to(self)
        self.abilities = planeswalker_abilities(self, self.abilities)
    def leavingZone(self):
        super(PlaneswalkerType, self).leavingZone()
        self.redirect_expire()
    def assignDamage(self, amt, source, combat=False):
        # amt is greater than 0
        self.remove_counters("loyalty", amt)
        source.send(DealsDamageToEvent(), to=self, amount=amt, combat=combat)
        return amt
    def shouldDestroy(self):
        return self.num_counters("loyalty") <= 0
