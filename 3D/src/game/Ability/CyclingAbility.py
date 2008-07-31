from ActivatedAbility import ActivatedAbility
import TriggeredAbility
from Effect import DrawCard, MoveCards
from game.Match import isCard, isLandType
from game.Cost import ManaCost, DiscardCost

class Cycling(ActivatedAbility):
    def __init__(self, card, cost="0", effects=None, triggered=None):
        self.cycle_cost = cost
        cost = ManaCost(cost) + DiscardCost()
        if not effects: effects = DrawCard(1)
        super(Cycling, self).__init__(card, cost=cost, effects=effects, zone="hand")
        self.triggered = triggered
    def played(self):
        super(Cycling, self).played()
        if self.triggered: TriggeredAbility.Play(self.card, self.triggered.copy())
    def __str__(self):
        return "%s: Cycling (Draw a card)"%self.cycle_cost

class Typecycling(Cycling):
    def __init__(self, card, cost="0", card_types=isCard, triggered=None):
        if (type(card_types) == list or type(card_types) == tuple): self.card_types = card_types
        else: self.card_types = [card_types]
        effects = MoveCards(from_zone="library", to_zone="hand", number=1, card_types=card_types, reveal=True)
        super(Typecycling, self).__init__(card, cost=cost, effects=effects, triggered=triggered)
    def __str__(self):
        return "%s: Typecycling (Search library for %s)"%(self.cycle_cost,' or '.join(map(str,self.card_types)))

class Landcycling(Typecycling):
    def __init__(self, card, cost="0", landtype=None, triggered=None):
        if not landtype: raise Exception
        self.landtype = landtype
        super(Landcycling, self).__init__(card, cost=cost, card_types=isLandType.with_condition(lambda l: l.subtypes == landtype), triggered=triggered)
    def __str__(self):
        return "%s: %scycling (Search library for a %s)"%(self.cycle_cost,self.landtype,self.landtype)

class Plainscycling(Landcycling):
    def __init__(self, card, cost="0", triggered=None):
        super(Plainscycling, self).__init__(card, cost=cost, landtype="Plains", triggered=triggered)

class Islandcycling(Landcycling):
    def __init__(self, card, cost="0", triggered=None):
        super(Islandcycling, self).__init__(card, cost=cost, landtype="Island", triggered=triggered)

class Swampcycling(Landcycling):
    def __init__(self, card, cost="0", triggered=None):
        super(Swampcycling, self).__init__(card, cost=cost, landtype="Swamp", triggered=triggered)

class Mountaincycling(Landcycling):
    def __init__(self, card, cost="0", triggered=None):
        super(Mountaincycling, self).__init__(card, cost=cost, landtype="Mountain", triggered=triggered)

class Forestcycling(Landcycling):
    def __init__(self, card, cost="0", triggered=None):
        super(Forestcycling, self).__init__(card, cost=cost, landtype="Forest", triggered=triggered)
