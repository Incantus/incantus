from ActivatedAbility import *
from Limit import MultipleLimits, ZoneLimit

class CastSpell(object):
    def __init__(self, card, cost="0", target=None, effects=[], limit=None, copy_targets=True):
        #limit = MultipleLimits([limit, ZoneLimit("hand")])
        super(CastSpell, self).__init__(card, cost=cost,target=target,effects=effects, limit=limit, copy_targets=copy_targets, zone="hand")
    def setup_card_controller(self):
        # Subclasses decide what to do with the card
        player = self.card.owner
        self.card.controller = player
        return player
    def counter(self):
        super(CastSpell,self).counter()
        player = self.setup_card_controller()
        player.discard(self.card)
    def __str__(self):
        return "%s: Cast Spell"%self.cost

class PermanentSpell(CastSpell):
    def cleanup(self):
        controller = self.setup_card_controller()
        controller.moveCard(self.card, self.card.zone, controller.play)
        super(PermanentSpell, self).cleanup()

class NonPermanentSpell(CastSpell):  # This class is a composite of abilities for Instants and Sorceries
    def cleanup(self):
        # The discard comes after the card does its thing 
        # See oracle for Planar Void to get an idea
        controller = self.setup_card_controller()
        controller.discard(self.card)
        super(NonPermanentSpell, self).cleanup()
    def __str__(self):
        return "%s: %s"%(self.cost, ', '.join(map(str,self.effects)))

class CastPermanentSpell(PermanentSpell, ActivatedAbility): pass
class CastNonPermanentSpell(NonPermanentSpell, ActivatedAbility): pass
class CastDoOrNonPermanentSpell(NonPermanentSpell, DoOrAbility): pass

class BuybackSpell(CastSpell):
    def cleanup(self):
        controller = self.setup_card_controller()
        super(BuybackSpell, self).cleanup()

import game.Cost
def buyback(out_play_role, buyback="0"):
    main_spell = out_play_role.abilities[0]
    cost = main_spell.cost + game.Cost.BuybackCost(buyback)
    class CastBuybackSpell(BuybackSpell, ActivatedAbility): pass

    out_play_role.abilities.append(CastBuybackSpell(out_play_role.card, cost, main_spell.targets, main_spell.effects, main_spell.limit, main_spell.copy_targets))

class Cycling(ActivatedAbility):
    def __init__(self, card, cost="0", triggered=None):
        from Effect import DrawCard
        self.cycle_cost = cost
        cost = game.Cost.ManaCost(cost) + game.Cost.DiscardCost()
        super(Cycling, self).__init__(card, cost=cost, effects=DrawCard(1), zone="hand")
        self.triggered = triggered
    def played(self):
        import TriggeredAbility
        if self.triggered: TriggeredAbility.Play(self.card, self.triggered.copy())
    def __str__(self):
        return "%s: Cycling"%self.cycle_cost
