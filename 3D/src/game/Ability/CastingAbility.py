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
    def countered(self):
        super(CastSpell,self).countered()
        player = self.setup_card_controller()
        player.discard(self.card)
    #def __str__(self):
    #    return "%s: Cast Spell"%self.cost

class PermanentSpell(CastSpell):
    def __init__(self, card, cost="0", target=None, effects=[], limit=None, copy_targets=True):
        super(CastSpell, self).__init__(card, cost=cost,target=target,effects=effects, limit=limit, copy_targets=copy_targets, zone="hand")
    # Auras break if I put it into play afterward
    def preresolve(self):
        # The card is put into play before any effects resolve
        controller = self.card.controller #self.setup_card_controller()
        controller.moveCard(self.card, self.card.zone, controller.play)
        return super(PermanentSpell, self).preresolve()
    def __str__(self):
        return "%s: Put into play"%self.cost

class NonPermanentSpell(CastSpell):  # This class is a composite of abilities for Instants and Sorceries
    def resolved(self):
        # The discard comes after the card does its thing 
        # See oracle for Planar Void to get an idea
        controller = self.setup_card_controller()
        # Don't put in graveyard if it's no longer there
        if self.card.zone == controller.hand:
            controller.moveCard(self.card, controller.hand, controller.graveyard)
        super(NonPermanentSpell, self).resolved()
    def __str__(self):
        return "%s: %s"%(self.cost, ', '.join(map(str,self.effects)))

class CastPermanentSpell(PermanentSpell, ActivatedAbility): pass
class CastNonPermanentSpell(NonPermanentSpell, ActivatedAbility): pass
class CastDoOrNonPermanentSpell(NonPermanentSpell, DoOrAbility): pass

class BuybackSpell(CastSpell):
    def resolved(self):
        controller = self.setup_card_controller()
        super(BuybackSpell, self).resolved()

class CastBuybackSpell(BuybackSpell, ActivatedAbility):
    def __str__(self):
        return "Buyback "+super(CastBuybackSpell, self).__str__()

# XXX This should really be a replacement effect, replacing going to your graveyard
# This only matters if you play a spell that you don't own
def buyback(out_play_role, buyback="0"):
    main_spell = out_play_role.abilities[0]
    cost = main_spell.cost + buyback

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
        return "%s: Cycling (Draw a card)"%self.cycle_cost
