from engine import Mana
from engine.GameEvent import CounterAddedEvent, CounterRemovedEvent, InvalidTargetEvent
from engine.Match import isCard, isPermanent

class Cost(object):
    def is_mana_cost(self): return False
    def precompute(self, source, player): return True
    def compute(self, source, player): return True
    def pay(self, source, player): self.payment = None
    def __add__(self, other):
        if isinstance(other, str): return MultipleCosts([self,ManaCost(other)])
        elif isinstance(other, MultipleCosts): return MultipleCosts([self]+other.costs)
        elif isinstance(other, Cost): return MultipleCosts([self, other])
    def __radd__(self, other):
        if isinstance(other, str): return MultipleCosts([self,ManaCost(other)])
        elif isinstance(other, MultipleCosts): return MultipleCosts([self]+other.costs)
        elif isinstance(other, Cost): return MultipleCosts([self, other])
    def __eq__(self, other):
        return False
    def __str__(self):
        return ''

class NoCost(Cost):
    def precompute(self, source, player): return False
    def compute(self, source, player): return False
    def __eq__(self, other): return isinstance(other, NoCost)
    def __str__(self): return ''
    def converted_mana_cost(self): return 0

class MultipleCosts(Cost):
    def __init__(self, costs):
        super(MultipleCosts,self).__init__()
        for i, c in enumerate(costs):
            if isinstance(c, str): costs[i] = ManaCost(c)
        self.costs = costs
    X = property(fget=lambda self: self.final_costs[0].X if hasattr(self, "final_costs") and isinstance(self.final_costs[0], ManaCost) else 0)
    def consolidate(self, costs):
        # This combines all mana costs
        manacost = []
        othercost = []
        for c in costs:
            if c.is_mana_cost(): manacost.append(c)
            else: othercost.append(c)
        if manacost:
            cost = manacost[0]
            for mc in manacost[1:]: cost += mc
            return [cost]+othercost
        else: return othercost
    def precompute(self, source, player):
        for cost in self.costs:
            if not cost.precompute(source, player): return False
        self.final_costs = self.consolidate(self.costs)
        return True
    def compute(self, source, player):
        for cost in self.final_costs:
            if not cost.compute(source, player): return False
        return True
    def pay(self, source, player):
        self.payment = []
        for cost in self.final_costs:
            cost.pay(source, player)
            self.payment.append(cost.payment)
    def __iter__(self): return iter(self.final_costs)
    def __getitem__(self, i): return self.final_costs[i]
    def __iadd__(self, other):
        if isinstance(other, str): self.costs.append(ManaCost(other))
        elif isinstance(other, MultipleCosts): self.costs.extend(other.costs)
        elif isinstance(other, Cost): self.costs.append(other)
        return self
    def __add__(self, other):
        if isinstance(other, str): return MultipleCosts(self.costs+[ManaCost(other)])
        elif isinstance(other, MultipleCosts): return MultipleCosts(self.costs+other.costs)
        elif isinstance(other, Cost): return MultipleCosts(self.costs+[other])
    def __str__(self):
        return ','.join([str(c) for c in self.costs])

class ManaCost(Cost):
    def cost():
        def fget(self):
            return str(self._mana_amt)
        return locals()
    cost = property(**cost())
    def __init__(self, cost):
        super(ManaCost,self).__init__()
        self._mana_amt = cost
        self._num_X = sum([1 for symbol in cost if symbol == "X"])
        self._X = 0
        self._final_cost = Mana.convert_mana_string("0")
    X = property(fget=lambda self: self._X)
    def is_mana_cost(self): return True
    def __iter__(self): return iter(self.cost)
    def precompute(self, source, player):
        mp = player.manapool
        self._X = 0
        if self.hasX(): self._X = player.getX()
        if self.isHybrid(): cost = player.make_selection([('Pay {%s}'%c,c) for c in Mana.generate_hybrid_choices(self.cost)], 1, prompt="Choose hybrid cost")
        else: cost = self.cost
        self._final_cost = Mana.convert_mana_string(cost)
        self._final_cost[-1] += self._X*self._num_X
        self.payment = "0"
        return self._X >= 0
    def compute(self, source, player):
        # XXX This is where I should check if the player has enough mana and the player should be
        # able to generate more mana
        mp = player.manapool
        cost = self._final_cost
        for i, val in enumerate(cost):
            if val < 0: cost[i] = 0
        while True:
            required = mp.enoughInPool(cost)
            if required == '0': return True
            if not player.getMoreMana(required): return False
    def pay(self, source, player):
        mp = player.manapool
        # Now I have enough mana - how do I distribute it?
        payment = mp.distribute(self._final_cost)
        if not payment:
            # Ask the player to distribute
            payment = Mana.convert_mana_string(player.getManaChoice(str(player.manapool), Mana.convert_to_mana_string(self._final_cost)))
        mp.spend(payment)
        self.payment = Mana.convert_to_mana_string(payment)
    def hasX(self):
        return self._num_X > 0
    def isHybrid(self):
        # XXX this is hacky
        return ('(' in self.cost or '{' in self.cost)
    def converted_mana_cost(self):
        return Mana.converted_mana_cost(self.cost)
    def colors(self): return Mana.convert_to_color(self.cost)
    #def __eq__(self, other):
    #     XXX compare_mana doesn't work with hybrid
    #    if isinstance(other, str): return Mana.compare_mana(self.cost, other)
    #    elif isinstance(other, ManaCost): return Mana.compare_mana(self.cost, other.cost)
    def __iadd__(self, other):
        if not hasattr(self, "_final_cost"): raise Error()
        # XXX This is only called by consolidate
        for i, val in enumerate(other._final_cost):
            self._final_cost[i] += val
        return self
    def __add__(self, other):
        if isinstance(other, str): return ManaCost(Mana.combine_mana_strings(self.cost, other))
        elif isinstance(other, ManaCost): return ManaCost(Mana.combine_mana_strings(self.cost, other.cost))
        elif isinstance(other, MultipleCosts): return MultipleCosts([self]+other.costs)
        elif isinstance(other, Cost): return MultipleCosts([self, other])
    def __str__(self):
        coststr = self.cost
        #if self.hasX(): coststr += ",(X=%d)"%self.X
        return coststr
    def __cmp__(self, value):
        return cmp(self.converted_mana_cost(), value)

class TapCost(Cost):
    def __init__(self, cardtype=None, number=1):
        super(TapCost,self).__init__()
        self.cardtype = cardtype
        self.number = number
    def precompute(self, source, player):
        if self.cardtype == None: return source.canTap()
        else: return len(player.battlefield.get(self.cardtype)) >= self.number
    def compute(self, source, player):
        self._cards = []
        # Tap myself
        if self.cardtype == None:
            if source.canTap(): self._cards.append(source)
            else: return False
        # otherwise see if there are enough cards for tapping
        else:
            prompt = "Select %d %s(s) for tapping"%(self.number-len(self._cards), self.cardtype)
            while True:
                card = player.getTarget(self.cardtype, zone="battlefield", from_player="you", required=False, prompt=prompt)
                if card == False: return False
                if card in self._cards:
                    prompt = "Card already selected - select again"
                    player.send(InvalidTargetEvent(), target=card)
                elif card.tapped:
                    prompt = "Card already tapped - select again"
                    player.send(InvalidTargetEvent(), target=card)
                elif not card.canBeTapped():
                    prompt = "Card cannot be tapped - select again"
                    player.send(InvalidTargetEvent(), target=card)
                else:
                    self._cards.append(card)
                    prompt = "Select %d %s(s) for tapping"%(self.number-len(self._cards), self.cardtype)
                if len(self._cards) == self.number: break
        return True
    def pay(self, source, player):
        for card in self._cards: card.tap()
        self.payment = self._cards
    def __str__(self):
        if self.cardtype: who = " %s"%self.cardtype
        else: who = ""
        return 'T%s'%who

class UntapCost(Cost):
    def __init__(self, cardtype=None, number=1):
        super(UntapCost,self).__init__()
        self.cardtype = cardtype
        self.number = number
    def precompute(self, source, player):
        if self.cardtype == None: return source.canUntap()
        else: return len(player.battlefield.get(self.cardtype)) >= self.number
    def compute(self, source, player):
        self._cards = []
        # Untap myself
        if self.cardtype == None:
            if source.canUntap(): self._cards.append(source)
            else: return False
        # otherwise see if there are enough cards for untapping
        else:
            prompt = "Select %d %s(s) for untapping"%(self.number-len(self._cards), self.cardtype)
            while True:
                card = player.getTarget(self.cardtype, zone="battlefield", from_player="you", required=False, prompt=prompt)
                if card == False: return False
                if card in self._cards:
                    prompt = "Card already selected - select again"
                    player.send(InvalidTargetEvent(), target=card)
                elif not card.tapped:
                    prompt = "Card already untapped - select again"
                    player.send(InvalidTargetEvent(), target=card)
                elif not card.canUntap():
                    prompt = "Card cannot be untapped - select again"
                    player.send(InvalidTargetEvent(), target=card)
                else:
                    self._cards.append(card)
                    prompt = "Select %d %s(s) for untapping"%(self.number-len(self._cards), self.cardtype)
                if len(self._cards) == self.number: break
        return True
    def pay(self, source, player):
        for card in self._cards: card.untap()
        self.payment = self._cards
    def __str__(self):
        if self.cardtype: who = " %s"%self.cardtype
        else: who = ""
        return 'Q%s'%who

class SacrificeCost(Cost):
    def __init__(self, cardtype=None, number=1, msg=''):
        super(SacrificeCost,self).__init__()
        self.cardtype = cardtype
        self.number = number
        self.msg = msg
    def precompute(self, source, player):
        if self.cardtype == None: return True
        else: return len(player.battlefield.get(self.cardtype)) >= self.number
    def compute(self, source, player):
        self._cards = []
        if self.cardtype == None:
            # Sacrifice myself
            if str(source.zone) == "battlefield": self._cards.append(source)
            else: return False
        else:
            prompt = "Select %d %s(s) for sacrifice"%(self.number-len(self._cards), self.cardtype)
            if self.msg: prompt = self.msg
            while True:
                card = player.getTarget(self.cardtype, zone="battlefield", from_player="you", required=False, prompt=prompt)
                if card == False: return False
                if card in self._cards:
                    prompt = "Card already selected - select again"
                    player.send(InvalidTargetEvent(), target=card)
                else:
                    self._cards.append(card)
                    prompt = "Select %d %s(s) for sacrifice"%(self.number-len(self._cards), self.cardtype)
                    if self.msg: prompt = self.msg
                if len(self._cards) == self.number: break
        return True
    def pay(self, source, player):
        for card in self._cards:
            player.sacrifice(card)
        self.payment = self._cards
    def __str__(self):
        return 'Sacrifice'

class ChangeZoneCost(Cost):
    def __init__(self, from_zone, to_zone, cardtype=None, number=1):
        super(ChangeZoneCost,self).__init__()
        self.cardtype = cardtype
        self.number = number
        self.from_zone = from_zone
        self.to_zone = to_zone
    def precompute(self, source, player):
        from_zone = getattr(player, self.from_zone)
        if self.cardtype == None: return True
        else: return len(from_zone.get(self.cardtype)) >= self.number
    def compute(self, source, player):
        self._cards = []
        if self.cardtype == None:
            if str(source.zone) == self.from_zone: self._cards.append(source)
            else: return False
        else:
            prompt = "Select %d %s(s) to %s"%(self.number-len(self._cards), self.cardtype, self.action_txt%'')
            while True:
                card = player.getTarget(self.cardtype, zone=self.from_zone, from_player="you", required=False, prompt=prompt)
                if card == False: return False
                if card in self._cards:
                    prompt = "%s already selected - select again"%card
                    player.send(InvalidTargetEvent(), target=card)
                else:
                    self._cards.append(card)
                    prompt = "Select %d %s(s) to %s"%(self.number-len(self._cards), self.cardtype, self.action_txt%'')
                if len(self._cards) == self.number: break
        return True
    def pay(self, source, player):
        self.payment = {}
        self.payment['after'] = []
        for card in self._cards:
            result = card.move_to(self.to_zone)
            if str(result.zone) == self.to_zone: self.payment['after'].append(result)
            else: self.payment['after'].append(None)
        self.payment['before'] = self._cards
    def __str__(self):
        if self.cardtype: txt = ' '+str(self.cardtype)
        else: txt = ''
        return (self.action_txt%txt).title()

class ExileFromLibraryCost(ChangeZoneCost):
    def __init__(self, number=1, position='top'):
        super(ExileFromLibraryCost, self).__init__(from_zone="library", to_zone="exile", cardtype=isCard, number=number)
        self.position = position
    def compute(self, source, player):
        if self.position == "top":
            self._cards = self.library.top(self.number)
        elif self.position == "bottom":
            self._cards = self.library.bottom(self.number)
        return True

class GraveyardFromLibraryCost(ChangeZoneCost):
    def __init__(self, number=1, position='top'):
        super(GraveyardFromLibraryCost, self).__init__(from_zone="library", to_zone="graveyard", cardtype=isCard, number=number)
    def compute(self, source, player):
        if self.position == "top":
            self._cards = self.library.top(self.number)
        elif self.position == "bottom":
            self._cards = self.library.bottom(self.number)
        return True

class ReturnToHandCost(ChangeZoneCost):
    def __init__(self, cardtype=None, number=1):
        super(ReturnToHandCost,self).__init__(from_zone="battlefield", to_zone="hand", cardtype=cardtype, number=number)
        self.action_txt = "return%s to hand"

class ExileFromBattlefieldCost(ChangeZoneCost):
    def __init__(self, cardtype=None, number=1):
        super(ExileFromBattlefieldCost,self).__init__(from_zone="battlefield", to_zone="exile", cardtype=cardtype, number=number)
        self.action_txt = "exile%s from the battlefield"

class ExileFromHandCost(ChangeZoneCost):
    def __init__(self, cardtype=None, number=1):
        super(ExileFromHandCost,self).__init__(from_zone="hand", to_zone="exile", cardtype=cardtype, number=number)
        self.action_txt = "exile%s from hand"

class ExileFromGraveyardCost(ChangeZoneCost):
    def __init__(self, cardtype=None, number=1):
        super(ExileFromGraveyardCost,self).__init__(from_zone="graveyard", to_zone="exile", cardtype=cardtype, number=number)
        self.action_txt = "exile%s from graveyard"

class RemoveCounterCost(Cost):
    def __init__(self, counter_type=None, cardtype=None, number=1):
        self.counter_type = counter_type
        self.number = number
        self.cardtype = cardtype
    def enough_counters(self, perm):
        return perm.num_counters(self.counter_type) >= self.number if self.counter_type else perm.num_counters() >= self.number
    def precompute(self, source, player):
        if self.cardtype == None: return True
        else: return any((True for perm in player.battlefield.get(self.cardtype) if self.enough_counters(perm)))
    def compute(self, source, player):
        if self.cardtype == None:
            # Target myself
            if self.enough_counters(source): self._card = source
            else: return False
        else:
            prompt = "Select %s from which to remove %d %s counter(s)"%(self.cardtype, self.number, self.counter_type)
            if not self.counter_type: prompt = "Select %s from which to remove %d counter(s)"%(self.cardtype, self.number)
            while True:
                card = player.getTarget(self.cardtype, zone="battlefield", from_player="you", required=False, prompt=prompt)
                if card == False: return False
                if not self.enough_counters(card):
                    prompt = "Card doesn't have enough %s counters - select again"%self.counter_type
                    player.send(InvalidTargetEvent(), target=card)
                else:
                    self._card = card
                    break
        if not self.counter_type:
            sellist = list(set([counter.ctype for counter in self._card.counters]))
            if len(sellist) == 1: self.counter_type = sellist[0]
            else: self.counter_type = player.make_selection(sellist, prompt='Choose a counter')
        return True
    def pay(self, source, player):
        self.payment = self._card.remove_counters(self.counter_type, self.number)
    def __str__(self):
        return "Remove %d %s counter(s)"%(self.number, self.counter_type)

class AddCounterCost(Cost):
    def __init__(self, counter_type, cardtype=None, number=1):
        self.counter_type = counter_type
        self.number = number
        self.cardtype = cardtype
    def precompute(self, source, player):
        if self.cardtype == None: return True
        else: return len(player.battlefield.get(self.cardtype)) >= self.number
    def compute(self, source, player):
        if self.cardtype == None:
            # Target myself
            if str(source.zone) == "battlefield": self._card = source
            else: return False
        else:
            prompt = "Select %s on which to place %d %s counter(s)"%(self.cardtype, self.number, self.counter_type)
            while True:
                card = player.getTarget(self.cardtype, zone="battlefield", from_player="you", required=False, prompt=prompt)
                if card == False: return False
                else:
                    self._card = card
                    break
        return True
    def pay(self, source, player):
        self._card.add_counters(self.counter_type, self.number)
        self.payment = self.number
    def __str__(self):
        return "Add %d %s counter(s)"%(self.number, self.counter_type)

class ConditionalCost(Cost):
    def __init__(self, orig_cost, new_cost, func):
        if isinstance(orig_cost, str): orig_cost = ManaCost(orig_cost)
        if isinstance(new_cost, str): new_cost = ManaCost(new_cost)
        self.orig_cost = orig_cost
        self.new_cost = new_cost
        self.cost = self.orig_cost
        self.func = func
    def precompute(self, source, player):
        if self.func(source, player): self.cost = self.new_cost
        return self.cost.precompute(source, player)
    def compute(self, source, player):
        return self.cost.compute(source, player)
    def pay(self, source, player):
        self.cost.pay(source, player)
    def __str__(self):
        return str(self.cost)
    payment = property(fget=lambda self: self.cost.payment)

class LifeCost(Cost):
    def __init__(self, amt):
        self.amt = amt
    def precompute(self, source, player):
        return player.life - self.amt > 0
    def pay(self, source, player):
        player.life -= self.amt
        self.payment = self.amt
    def __str__(self):
        return "Pay %d life"%self.amt

class RevealCost(Cost):
    def __init__(self, cardtype=isCard, number=1):
        self.number = number
        self.cardtype = cardtype
    def precompute(self, source, player):
        return len(player.hand.get(self.cardtype)) >= self.number
    def compute(self, source, player):
        self.reveals = []
        if self.number == -1:
            # Reveal entire hand
            self.reveals.extend([c for c in player.hand])
        else:
            if self.number > 1: a='s'
            else: a = ''
            num = 0
            prompt = "Select %s card%s to reveal: %d left of %d"%(self.cardtype, a, self.number-num,self.number)
            while num < self.number:
                card = player.getTarget(self.cardtype, zone="hand", from_player="you", required=False,prompt=prompt)
                if not card: return False
                if not card in self.reveals:
                    self.reveals.append(card)
                    num += 1
                    prompt = "Select %s card%s to reveal: %d left of %d"%(self.cardtype, a, self.number-num,self.number)
                else:
                    prompt = "Card already selected. Select %s card%s to reveal: %d left of %d"%(self.cardtype, a, self.number-num,self.number)
        return True
    def pay(self, source, player):
        player.reveal_cards(self.reveals)
        self.payment = self.reveals
    def __str__(self):
        txt = "%d %s"%(self.number, str(self.cardtype))
        if self.number > 1: txt += 's'
        return "Reveal %s"%txt

class DiscardCost(Cost):
    def __init__(self, cardtype=None, number=1, random=False):
        self.number = number
        self.cardtype = cardtype
        self.random = random
    def precompute(self, source, player):
        if self.cardtype: return len(player.hand.get(self.cardtype)) >= self.number
        else: return True
    def compute(self, source, player):
        self.discards = []
        if self.number == -1:
            # Discard entire hand
            self.discards.extend([c for c in player.hand])
        elif not self.cardtype:
            # Discard this card
            if str(source.zone) == "hand": self.discards = [source]
            else: return False
        elif self.random:
            import random
            self.discards.extend(list(random.sample(self.hand, self.number)))
        else:
            if self.number > 1: a='s'
            else: a = ''
            num = 0
            prompt = "Select %s card%s to discard: %d left of %d"%(self.cardtype, a, self.number-num,self.number)
            while num < self.number:
                card = player.getTarget(self.cardtype, zone="hand", from_player="you",required=False,prompt=prompt)
                if not card: return False
                if not card in self.discards:
                    self.discards.append(card)
                    num += 1
                    prompt = "Select %s card%s to discard: %d left of %d"%(self.cardtype, a, self.number-num,self.number)
                else:
                    prompt = "Card already selected. Select %s card%s to discard: %d left of %d"%(self.cardtype, a, self.number-num,self.number)
        return True
    def pay(self, source, player):
        for c in self.discards:
            player.discard(c)
        self.payment = self.discards
    def __str__(self):
        if self.cardtype:
            txt = "%d %s"%(self.number, str(self.cardtype))
            if self.number > 1: txt += 's'
        else: txt = 'this card'
        return "Discard %s"%txt

class LoyaltyCost(Cost):
    def __init__(self, number=0):
        self.number = number
    def precompute(self, source, player):
        if self.number < 0: return source.num_counters("loyalty") >= -self.number
        else: return True
    def pay(self, source, player):
        if self.number < 0: source.remove_counters("loyalty", -self.number)
        else: source.add_counters("loyalty", self.number)
        self.payment = self.number
    def __str__(self):
        return "%d loyalty"%(self.number)

class SpecialCost(Cost):
    def is_mana_cost(self): return self.cost.is_mana_cost()
    def precompute(self, source, player):
        return self.cost.precompute(source, player)
    def compute(self, source, player):
        return self.cost.compute(source, player)
    def pay(self, source, player):
        self.cost.pay(source, player)
    def __getattr__(self, attr):
        return getattr(self.cost, attr)
    def __str__(self):
        return str(self.cost)
    payment = property(fget=lambda self: self.cost.payment)

class ChoiceCost(SpecialCost):
    def __init__(self, *costs):
        super(ChoiceCost,self).__init__()
        self.choice_costs = costs
        self.reset()
    def reset(self): self.cost = None
    def precompute(self, source, player):
        self.cost = player.make_selection(self.choice_costs, 1, prompt="Select additional cost")
        return super(ChoiceCost, self).precompute(source, player)
    def __str__(self):
        return "Choose between %s"%' or '.join([str(c) for c in self.choice_costs])
