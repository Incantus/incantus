from GameEvent import SacrificeEvent, CounterAddedEvent, CounterRemovedEvent
from LazyInt import LazyInt
import Mana

class Cost(object):
    def __init__(self):
        self.paid = False
    def compute(self, card, player):
        return True
    def pay(self, card, player):
        return False
    def reverse(self, card, player):
        # Since costs will not need to call reverse, since if they fail they won't have been paid anyway
        # If MultipleCost fails then it will need to back out previous payments
        pass
    def __add__(self, other):
        if isinstance(other, str): return MultipleCosts([self,ManaCost(other)])
        elif isinstance(other, MultipleCosts): return MultipleCosts([self]+other.costs)
        elif isinstance(other, Cost): return MultipleCosts([self, other])
    def __eq__(self, other):
        return False
    def __str__(self):
        return ''

class ManaCost(Cost):
    def cost():
        def fget(self):
            return str(self._mana_amt)
        return locals()
    cost = property(**cost())
    def __init__(self, cost):
        super(ManaCost,self).__init__()
        #if type(cost) == int: cost=str(cost)
        self._mana_amt = cost
        self.payment = "0"
        self._X = 0
        self.X = LazyInt(self._get_X, finalize=True)
    def _get_X(self): return self._X
    def compute(self, card, player):
        self.paid = False
        mp = player.manapool
        X = 0
        if mp.checkX(self.cost): X = player.getX()
        self._X = X
        self.final_cost = mp.convert_mana_string(self.cost)
        self.final_cost[-1] += X
        return X >= 0
    def pay(self, card, player):
        mp = player.manapool
        cost = self.final_cost
        for i, val in enumerate(cost):
            if val < 0: cost[i] = 0
        while not mp.checkMana(cost):
            if not player.getMoreMana(): return False
        # Now I have enough mana - how do I distribute it?
        payment = mp.distributeMana(cost)
        # Consolidate any X's in the mana string
        if not payment: payment = player.getManaChoice(required=mp.convert_to_mana_string(cost))
        if not payment: return False
        player.manapool.spend(payment)
        self.payment = payment
        self.paid = True
        return self.paid
    def reverse(self, card, player):
        if self.paid: player.manapool.addMana(self.payment)
    def hasX(self):
        return 'X' in self.cost
    def converted_cost(self):
        return Mana.converted_mana_cost(self.cost)
    def __eq__(self, other):
        if isinstance(other, str): return Mana.compareMana(self.cost, other)
        elif isinstance(other, ManaCost): return Mana.compareMana(self.cost, other.cost)
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
        return cmp(Mana.converted_mana_cost(self.cost), value)

class SacrificeCost(Cost):
    def __init__(self, cardtype=None, location="play"):
        super(SacrificeCost,self).__init__()
        self.cardtype = cardtype
        self.location = location
    def compute(self, card, player):
        self.paid = False
        # Sacrifice myself
        if self.cardtype == None: 
            self.target = card
            return True
        # get target for sacrifice
        location = getattr(player, self.location)
        if len(location.get(self.cardtype)) == 0: return False
        target = player.getTarget(self.cardtype, zone=location, required=False, prompt="Select %s for sacrifice"%self.cardtype)
        if not target: return False
        self.target = target
        return True
    def pay(self, card, player):
        #if not self.compute(card, player): return False
        location = getattr(player, self.location)
        # Make sure the sacrifice is still valid - this can not be replaced by regeneration
        if self.target.zone == location:
            # Make a copy of the current status in case the cost is canceled
            self.copy_cost = self.target.current_role.copy()
            player.moveCard(self.target, location, self.target.owner.graveyard)
            self.paid = True
            #player.send(Sacrifice())
        return self.paid
    def reverse(self, card, player):
        # XXX put the card back into play
        location = getattr(player, self.location)
        if self.paid: 
            player.moveCard(self.target, player.graveyard, location)
            self.target.current_role = self.copy_cost
    def __str__(self):
        return 'Sacrifice'

class CounterCost(Cost):
    def __init__(self, counter_type, number=1):
        self.counter_type = counter_type
        self.number = number
    def compute(self, card, player):
        self.paid = False
        self.counters = [counter for counter in card.counters if counter == self.counter_type]
        return len(self.counters) >= self.number
    def pay(self, card, player):
        for i in range(self.number):
            card.counters.remove(self.counters[i])
            card.send(CounterRemovedEvent(), counter=self.counters[i])
        self.paid = True
        return self.paid
    def reverse(self, card, player):
        if self.paid:
            for counter in self.counters[:self.number]:
                card.counters.append(counter)
                card.send(CounterAddedEvent(), counter=counter)
    def __str__(self):
        return "%d %s counter(s)"%(self.number, self.counter_type)

class TapCost(Cost):
    def __init__(self, cardtype=None, number=1):
        super(TapCost,self).__init__()
        #if cardtype: self.cardtype = cardtype.with_condition(lambda c: not c.tapped and c.canTap())
        #else: self.cardtype = None
        self.cardtype = cardtype
        self.number = number
    def compute(self, card, player):
        self.paid = False
        self.targets = []
        # Tap myself
        if self.cardtype == None: 
            self.targets.append(card)
            return not card.current_role.tapped and card.current_role.canTap()
        # otherwise see if there are enough targets for tapping
        location = player.play
        if not len(location.get(self.cardtype)) >= self.number: return False
        prompt = "Select %d %s(s) for tapping"%(self.number-len(self.targets), self.cardtype)
        while True:
            target = player.getTarget(self.cardtype, zone=location, required=False, prompt=prompt)
            if target == False: return False
            if target in self.targets:
                prompt = "Target already selected - select again"
                player.send(InvalidTargetEvent(), target=target)
            elif target.tapped:
                prompt = "Target already tapped - select again"
                player.send(InvalidTargetEvent(), target=target)
            else:
                prompt = "Select %d %s(s) for tapping"%(self.number-len(self.targets), self.cardtype)
                self.targets.append(target)
            if len(self.targets) == self.number: break
        return True
    def pay(self, card, player):
        # 104.4 Creatures that haven't been under a player's control continuously since the beginning of his or her most recent turn can't use any ability of theirs with the tap symbol in the cost.
        # canTap doesn't check for whether the card is already tapped - it's more for replacement effects that restrict tapping
        for target in self.targets:
            if not target.current_role.tapped: # and target.current_role.canTap():
                target.current_role.tap()
            else: 
                self.paid = False
                break
        else: self.paid = True
        return self.paid
    def reverse(self, card, player):
        if self.paid:
            for target in self.targets: target.untap()
    def __str__(self):
        if self.cardtype: who = " %s"%self.cardtype
        else: who = ""
        return 'T%s'%who

class ReturnToHandCost(Cost):
    def __init__(self, cardtypes=None, number=1):
        super(ReturnToHandCost,self).__init__()
        self.cardtypes = cardtypes
        self.number = number
    def compute(self, card, player):
        self.paid = False
        self.targets = []
        # otherwise see if there are enough targets for tapping
        location = player.play
        if not len(location.get(self.cardtypes)) >= self.number: return False
        prompt = "Select %d %s(s) to return to hand"%(self.number-len(self.targets), self.cardtypes)
        while True:
            target = player.getTarget(self.cardtypes, zone=location, required=False, prompt=prompt)
            if target == False: return False
            if target in self.targets:
                prompt = "%s already selected - select again"%self.cardtypes
                player.send(InvalidTargetEvent(), target=target)
            else:
                prompt = "Select %d %s(s) to return to hand"%(self.number-len(self.targets), self.cardtypes)
                self.targets.append(target)
            if len(self.targets) == self.number: break
        return True
    def pay(self, card, player):
        for target in self.targets:
            player.moveCard(target, target.zone, player.hand) 
        self.paid = True
        return self.paid
    def reverse(self, card, player):
        # return the cards to the play
        if self.paid:
            for target in self.targets: player.moveCard(target, target.zone, player.play)
    def __str__(self):
        if self.cardtypes: txt = str(self.cardtypes)
        else: txt = ''
        return "Return to hand %s"%txt

class MultipleCosts(Cost):
    def __init__(self, costs):
        super(MultipleCosts,self).__init__()
        self.costs = self.consolidate(costs)
    def consolidate(self, costs):
        # This combines all mana costs
        newcost = []
        manacost = []
        for c in costs:
            if type(c) == str: manacost.append(ManaCost(c))
            elif isinstance(c,ManaCost): manacost.append(c)
            else: newcost.append(c)
        if manacost: return [reduce(lambda x,y: x+y, manacost)]+newcost
        else: return costs
    def compute(self, card, player):
        self.paid = False
        for c in self.costs:
            if not c.compute(card, player): return False
        return True
    def __iadd__(self, other):
        if isinstance(other, str): self.costs.append(ManaCost(other))
        elif isinstance(other, MultipleCosts): self.costs.extend(other.costs)
        elif isinstance(other, Cost): self.costs.append(other)
        return self
    def __add__(self, other):
        if isinstance(other, str): return MultipleCosts(self.costs+[ManaCost(other)])
        elif isinstance(other, MultipleCosts): return MultipleCosts(self.costs+other.costs)
        elif isinstance(other, Cost): return MultipleCosts(self.costs+[other])
    def pay(self, card, player):
        # Sacrifice costs are always last, this way we don't actually move the card out of the graveyard
        # if other costs fail
        failed = False
        for c in self.costs:
            if not c.pay(card, player):
                failed = True
                # Reverse all the costs we've already paid
                self.reverse(card, player)
                break
        return not failed
    def reverse(self, card, player):
        # Don't check for self paid, because we need to ask each subcost if it was paid
        for c in self.costs: c.reverse(card, player)
    def __str__(self):
        return ','.join([str(c) for c in self.costs])

class ConditionalCost(Cost):
    def __init__(self, orig_cost, new_cost, func):
        if type(orig_cost) == str: orig_cost = ManaCost(orig_cost)
        if type(new_cost) == str: new_cost = ManaCost(new_cost)
        self.orig_cost = orig_cost
        self.new_cost = new_cost
        self.cost = self.orig_cost
        self.func = func
    def compute(self, card, player):
        if self.func(card, player):
            self.cost = self.new_cost
        return self.cost.compute(card, player)
    def pay(self, card, player):
        return self.cost.pay(card, player)
    def reverse(self, card, player):
        self.cost.reverse(card, player)
    def __str__(self):
        return str(self.cost)

class LifeCost(Cost):
    def __init__(self, amt):
        self.amt = amt
    def compute(self, card, player):
        return player.life - self.amt > 0
    def pay(self, card, player):
        player.life -= self.amt
        return True
    def reverse(self, card, player):
        player.life += self.amt
    def __str__(self):
        return "Pay %d life"%self.amt


class DiscardCost(Cost):
    def __init__(self, cardtype=None, number=1):
        self.number = number
        self.cardtype = cardtype
    def compute(self, card, player):
        self.paid = False
        self.discards = []
        if self.cardtype == None:
            # Discard this card
            self.discards = [card]
        else:
            if self.number > 1: a='s'
            else: a = ''
            if len(player.hand.get(self.cardtype)) < self.number: return False
            num = 0
            prompt = "Select %s card%s to discard: %d left of %d"%(self.cardtype, a, self.number-num,self.number)
            while num < self.number:
                card = player.getTarget(self.cardtype, zone=player.hand,required=False,prompt=prompt)
                if not card: return False
                if not card in self.discards:
                    self.discards.append(card)
                    num += 1
                    prompt = "Select %s card%s to discard: %d left of %d"%(self.cardtype, a, self.number-num,self.number)
                else:
                    prompt = "Card already selected. Select %s card%s to discard: %d left of %d"%(self.cardtype, a, self.number-num,self.number)
        return True
    def pay(self, card, player):
        for c in self.discards:
            player.discard(c)
        self.paid = True
        return self.paid
    def reverse(self, card, player):
        # return the cards to the players hand
        if self.paid:
            for c in self.discards: player.moveCard(c, player.graveyard, player.hand)
    def __str__(self):
        if self.cardtype: txt = str(self.cardtype)
        else: txt = ''
        if self.number > 1: a = 's'
        else: a = ''
        return "Discard %d %s%s"%(self.number, txt, a)

class ConvokeCost(Cost):
    def __init__(self, convoke):
        if type(convoke) == str: convoke = ManaCost(convoke)
        self.cost = convoke
    def compute(self, card, player):
        return self.cost.compute(card, player)
    def pay(self, card, player):
        return self.cost.pay(card, player)
    def reverse(self, card, player):
        self.cost.reverse(card, player)
    def __str__(self):
        return "Convoke %s"%str(self.cost)

# XXX This is unnecessary
class BuybackCost(Cost):
    def __init__(self, buyback):
        if type(buyback) == str: buyback = ManaCost(buyback)
        self.cost = buyback
    def compute(self, card, player):
        return self.cost.compute(card, player)
    def pay(self, card, player):
        return self.cost.pay(card, player)
    def reverse(self, card, player):
        self.cost.reverse(card, player)
    def __str__(self):
        return "Buyback %s"%str(self.cost)

class EvokeCost(Cost):
    def __init__(self, orig_cost, evoke_cost):
        if type(orig_cost) == str: orig_cost = ManaCost(orig_cost)
        if type(evoke_cost) == str: evoke_cost = ManaCost(evoke_cost)
        self.orig_cost = orig_cost
        self.evoke_cost = evoke_cost
        self.cost = self.orig_cost
    def compute(self, card, player):
        self.evoked = False
        self.evoked = player.getIntention("Pay evoke cost?", "...pay evoke cost?")
        if self.evoked: self.cost = self.evoke_cost
        return self.cost.compute(card, player)
    def pay(self, card, player):
        return self.cost.pay(card, player)
    def reverse(self, card, player):
        self.cost.reverse(card, player)
    def __str__(self):
        return str(self.cost)

class ProwlCost(Cost):
    def __init__(self, orig_cost, prowl_cost):
        if type(orig_cost) == str: orig_cost = ManaCost(orig_cost)
        if type(prowl_cost) == str: prowl_cost = ManaCost(prowl_cost)
        self.orig_cost = orig_cost
        self.prowl_cost = prowl_cost
        self.cost = self.orig_cost
        self.can_prowl = False
    def compute(self, card, player):
        if self.can_prowl:
            self.prowled = player.getIntention("Pay prowl cost?", "...pay prowl cost?")
            if self.prowled: self.cost = self.prowl_cost
        return self.cost.compute(card, player)
    def pay(self, card, player):
        return self.cost.pay(card, player)
    def reverse(self, card, player):
        self.cost.reverse(card, player)
    def __str__(self):
        return str(self.cost)
