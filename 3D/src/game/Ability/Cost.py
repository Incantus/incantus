from game import Mana
from game.GameEvent import CounterAddedEvent, CounterRemovedEvent, InvalidTargetEvent
from game.Match import isCard, isPermanent

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
            if type(c) == str: costs[i] = ManaCost(c)
        self.costs = costs
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
    X = property(fget=lambda self: self._X)
    def is_mana_cost(self): return True
    def __iter__(self): return iter(self.cost)
    def precompute(self, source, player):
        mp = player.manapool
        self._X = 0
        if self.hasX(): self._X = player.getX()
        if self.isHybrid(): cost = player.make_selection(Mana.generate_hybrid_choices(self.cost), 1, prompt="Choose hybrid cost")
        else: cost = self.cost
        self.final_cost = Mana.convert_mana_string(cost)
        self.final_cost[-1] += self._X*self._num_X
        self.payment = "0"
        return self._X >= 0
    def compute(self, source, player):
        # XXX This is where I should check if the player has enough mana and the player should be
        # able to generate more mana
        mp = player.manapool
        cost = self.final_cost
        for i, val in enumerate(cost):
            if val < 0: cost[i] = 0
        while True:
            required = mp.enoughInPool(cost)
            if required == '0': return True
            if not player.getMoreMana(required): return False
    def pay(self, source, player):
        mp = player.manapool
        # Now I have enough mana - how do I distribute it?
        payment = mp.distribute(self.final_cost)
        if not payment:
            # Ask the player to distribute
            payment = Mana.convert_mana_string(player.getManaChoice(str(player.manapool), Mana.convert_to_mana_string(self.final_cost)))
        mp.spend(payment)
        self.payment = Mana.convert_to_mana_string(payment)
    def hasX(self):
        return self._num_X > 0
    def isHybrid(self):
        # XXX this is hacky
        return '(' in self.cost
    def converted_mana_cost(self):
        return Mana.converted_mana_cost(self.cost)
    #def __eq__(self, other):
    #     XXX compare_mana doesn't work with hybrid
    #    if isinstance(other, str): return Mana.compare_mana(self.cost, other)
    #    elif isinstance(other, ManaCost): return Mana.compare_mana(self.cost, other.cost)
    def __iadd__(self, other):
        if not hasattr(self, "final_cost"): raise Error()
        # XXX This is only called by consolidate
        for i, val in enumerate(other.final_cost):
            self.final_cost[i] += val
        return self
    def __add__(self, other):
        if isinstance(other, str): return ManaCost(Mana.combine_mana_strings(self.cost, other))
        elif isinstance(other, ManaCost): return ManaCost(Mana.combine_mana_strings(self.cost, other.cost))
        elif isinstance(other, MultipleCosts): return MultipleCosts([self, other.costs])
        elif isinstance(other, Cost): return MultipleCosts([self, other])
    def __str__(self):
        coststr = self.cost
        if self.hasX(): coststr += ",(X=%d)"%self.X
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
        else: return len(player.play.get(self.cardtype)) >= self.number
    def compute(self, source, player):
        self.targets = []
        # Tap myself
        if self.cardtype == None:
            if source.canTap(): self.targets.append(source)
            else: return False
        # otherwise see if there are enough targets for tapping
        else:
            prompt = "Select %d %s(s) for tapping"%(self.number-len(self.targets), self.cardtype)
            while True:
                target = player.getTarget(self.cardtype, zone="play", from_player="you", required=False, prompt=prompt)
                if target == False: return False
                if target in self.targets:
                    prompt = "Card already selected - select again"
                    player.send(InvalidTargetEvent(), target=target)
                elif target.tapped:
                    prompt = "Card already tapped - select again"
                    player.send(InvalidTargetEvent(), target=target)
                elif not target.canBeTapped():
                    prompt = "Card cannot be tapped - select again"
                    player.send(InvalidTargetEvent(), target=target)
                else:
                    self.targets.append(target)
                    prompt = "Select %d %s(s) for tapping"%(self.number-len(self.targets), self.cardtype)
                if len(self.targets) == self.number: break
        return True
    def pay(self, source, player):
        for target in self.targets: target.tap()
        self.payment = self.targets
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
        else: return len(player.play.get(self.cardtype)) >= self.number
    def compute(self, source, player):
        self.targets = []
        # Untap myself
        if self.cardtype == None:
            if source.canUntap(): self.targets.append(source)
            else: return False
        # otherwise see if there are enough targets for untapping
        else:
            prompt = "Select %d %s(s) for untapping"%(self.number-len(self.targets), self.cardtype)
            while True:
                target = player.getTarget(self.cardtype, zone="play", from_player="you", required=False, prompt=prompt)
                if target == False: return False
                if target in self.targets:
                    prompt = "Card already selected - select again"
                    player.send(InvalidTargetEvent(), target=target)
                elif not target.tapped:
                    prompt = "Card already untapped - select again"
                    player.send(InvalidTargetEvent(), target=target)
                elif not target.canUntap():
                    prompt = "Card cannot be untapped - select again"
                    player.send(InvalidTargetEvent(), target=target)
                else:
                    self.targets.append(target)
                    prompt = "Select %d %s(s) for untapping"%(self.number-len(self.targets), self.cardtype)
                if len(self.targets) == self.number: break
        return True
    def pay(self, source, player):
        for target in self.targets: target.untap()
        self.payment = self.targets
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
        else: return len(player.play.get(self.cardtype)) >= self.number
    def compute(self, source, player):
        self.targets = []
        if self.cardtype == None:
            # Sacrifice myself
            if str(source.zone) == "play": self.targets.append(source)
            else: return False
        else:
            prompt = "Select %d %s(s) for sacrifice"%(self.number-len(self.targets), self.cardtype)
            if self.msg: prompt = self.msg
            while True:
                target = player.getTarget(self.cardtype, zone="play", from_player="you", required=False, prompt=prompt)
                if target == False: return False
                if target in self.targets:
                    prompt = "Card already selected - select again"
                    player.send(InvalidTargetEvent(), target=target)
                else:
                    self.targets.append(target)
                    prompt = "Select %d %s(s) for sacrifice"%(self.number-len(self.targets), self.cardtype)
                    if self.msg: prompt = self.msg
                if len(self.targets) == self.number: break
        return True
    def pay(self, source, player):
        for target in self.targets:
            player.sacrifice(target)
        self.payment = self.targets
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
        self.targets = []
        if self.cardtype == None:
            if str(source.zone) == self.from_zone: self.targets.append(source)
            else: return False
        else:
            prompt = "Select %d %s(s) to %s"%(self.number-len(self.targets), self.cardtype, self.action_txt%'')
            while True:
                target = player.getTarget(self.cardtype, zone=self.from_zone, from_player="you", required=False, prompt=prompt)
                if target == False: return False
                if target in self.targets:
                    prompt = "%s already selected - select again"%target
                    player.send(InvalidTargetEvent(), target=target)
                else:
                    self.targets.append(target)
                    prompt = "Select %d %s(s) to %s"%(self.number-len(self.targets), self.cardtype, self.action_txt%'')
                if len(self.targets) == self.number: break
        return True
    def pay(self, source, player):
        self.payment = {}
        self.payment['after'] = []
        for target in self.targets:
            result = target.move_to(self.to_zone)
            if str(result.zone) == self.to_zone: self.payment['after'].append(result)
            else: self.payment['after'].append(None)
        self.payment['before'] = self.targets
    def __str__(self):
        if self.cardtype: txt = ' '+str(self.cardtype)
        else: txt = ''
        return (self.action_txt%txt).title()


class ReturnToHandCost(ChangeZoneCost):
    def __init__(self, cardtype=None, number=1):
        super(ReturnToHandCost,self).__init__(from_zone="play", to_zone="hand", number=number, cardtype=cardtype)
        self.action_txt = "return%s to hand"

class RemoveFromPlayCost(ChangeZoneCost):
    def __init__(self, cardtype=None, number=1):
        super(RemoveFromPlayCost,self).__init__(from_zone="play", to_zone="removed", number=number, cardtype=cardtype)
        self.action_txt = "remove%s from play"

class RemoveFromHandCost(ChangeZoneCost):
    def __init__(self, cardtype=None, number=1):
        super(RemoveFromHandCost,self).__init__(from_zone="hand", to_zone="removed", number=number, cardtype=cardtype)
        self.action_txt = "remove%s from hand"

class RemoveFromGraveyardCost(ChangeZoneCost):
    def __init__(self, cardtype=None, number=1):
        super(RemoveFromGraveyardCost,self).__init__(from_zone="graveyard", to_zone="removed", number=number, cardtype=cardtype)
        self.action_txt = "remove%s from graveyard"

class RemoveCounterCost(Cost):
    def __init__(self, counter_type=None, cardtype=None, number=1):
        self.counter_type = counter_type
        self.number = number
        self.cardtype = cardtype
    def enough_counters(self, perm):
        return perm.num_counters(self.counter_type) >= self.number if self.counter_type else perm.num_counters() >= self.number
    def precompute(self, source, player):
        if self.cardtype == None: return True
        else: return any((True for perm in player.play.get(self.cardtype) if self.enough_counters(perm)))
    def compute(self, source, player):
        if self.cardtype == None:
            # Target myself
            if self.enough_counters(source): self.target = source
            else: return False
        else:
            prompt = "Select %s from which to remove %d %s counter(s)"%(self.cardtype, self.number, self.counter_type)
            if not self.counter_type: prompt = "Select %s from which to remove %d counter(s)"%(self.cardtype, self.number)
            while True:
                target = player.getTarget(self.cardtype, zone="play", from_player="you", required=False, prompt=prompt)
                if target == False: return False
                if not self.enough_counters(target):
                    prompt = "Card doesn't have enough %s counters - select again"%self.counter_type
                    player.send(InvalidTargetEvent(), target=target)
                else:
                    self.target = target
                    break
        if not self.counter_type:
            sellist = list(set([counter.ctype for counter in self.target.counters]))
            if len(sellist) == 1: self.counter_type = sellist[0]
            else: self.counter_type = player.make_selection(sellist, prompt='Choose a counter')
        return True
    def pay(self, source, player):
        self.payment = self.target.remove_counters(self.counter_type, self.number)
    def __str__(self):
        return "Remove %d %s counter(s)"%(self.number, self.counter_type)

class AddCounterCost(Cost):
    def __init__(self, counter_type, cardtype=None, number=1):
        self.counter_type = counter_type
        self.number = number
        self.cardtype = cardtype
    def precompute(self, source, player):
        if self.cardtype == None: return True
        else: return len(player.play.get(self.cardtype)) >= self.number
    def compute(self, source, player):
        if self.cardtype == None:
            # Target myself
            if str(source.zone) == "play": self.target = source
            else: return False
        else:
            prompt = "Select %s on which to place %d %s counter(s)"%(self.cardtype, self.number, self.counter_type)
            while True:
                target = player.getTarget(self.cardtype, zone="play", from_player="you", required=False, prompt=prompt)
                if target == False: return False
                else:
                    self.target = target
                    break
        return True
    def pay(self, source, player):
        self.target.add_counters(self.counter_type, self.number)
        self.payment = self.number
    def __str__(self):
        return "Add %d %s counter(s)"%(self.number, self.counter_type)

class ConditionalCost(Cost):
    def __init__(self, orig_cost, new_cost, func):
        if type(orig_cost) == str: orig_cost = ManaCost(orig_cost)
        if type(new_cost) == str: new_cost = ManaCost(new_cost)
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
        if self.number > 1: a='s'
        else: a = ''
        num = 0
        prompt = "Select %s card%s to reveal: %d left of %d"%(self.cardtype, a, self.number-num,self.number)
        while num < self.number:
            target = player.getTarget(self.cardtype, zone="hand", from_player="you", required=False,prompt=prompt)
            if not target: return False
            if not target in self.reveals:
                self.reveals.append(target)
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
    def __init__(self, cardtype=None, number=1):
        self.number = number
        self.cardtype = cardtype
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
        else:
            if self.number > 1: a='s'
            else: a = ''
            num = 0
            prompt = "Select %s card%s to discard: %d left of %d"%(self.cardtype, a, self.number-num,self.number)
            while num < self.number:
                target = player.getTarget(self.cardtype, zone="hand", from_player="you",required=False,prompt=prompt)
                if not target: return False
                if not target in self.discards:
                    self.discards.append(target)
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

class EvokeCost(SpecialCost):
    def __init__(self, orig_cost, evoke_cost):
        if type(orig_cost) == str: orig_cost = ManaCost(orig_cost)
        if type(evoke_cost) == str: evoke_cost = ManaCost(evoke_cost)
        self.orig_cost = orig_cost
        self.evoke_cost = evoke_cost
        self.reset()
    def reset(self):
        self.evoked = False
        self.cost = self.orig_cost
    def precompute(self, source, player):
        self.evoked = player.getIntention("Pay evoke cost?", "...pay evoke cost?")
        if self.evoked: self.cost = self.evoke_cost
        return super(EvokeCost, self).precompute(source, player)
