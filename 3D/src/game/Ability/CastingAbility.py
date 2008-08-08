from game.GameEvent import SpellPlayedEvent
from ActivatedAbility import ActivatedAbility
from Limit import SorceryLimit, MultipleLimits

class CastSpell(ActivatedAbility):
    zone = "hand"
    #def __init__(self, card, cost="0", target=None, effects=[], copy_targets=True, limit=None, zone="hand", txt=''):
    #    super(CastSpell, self).__init__(card, cost=cost, target=target, effects=effects, copy_targets=copy_targets, limit=limit, zone=zone, txt=txt)
    def do_announce(self):
        # Move the card to the stack zone - this is never called from play
        player = self.controller
        #self.card.move_to(player.stack)
        if super(CastSpell, self).do_announce():
            player.send(SpellPlayedEvent(), card=self.card)
            return True
        else: return False
    def countered(self):
        self.card.move_to(self.card.owner.graveyard)
        super(CastSpell,self).countered()

class CastPermanentSpell(CastSpell):
    def __init__(self, card, cost="0", target=None, effects=[], limit=None, copy_targets=True, zone="hand", txt=''):
        if limit: limit += SorceryLimit(card)
        else: limit = SorceryLimit(card)
        super(CastPermanentSpell, self).__init__(card, cost=cost, target=target, effects=effects, copy_targets=copy_targets, limit=limit, zone=zone, txt=txt)
    def resolved(self):
        self.card.move_to(self.controller.play)
        super(CastPermanentSpell, self).resolved()
    def __str__(self):
        return "%s: Put into play"%self.cost

class CastNonPermanentSpell(CastSpell):
    def resolved(self):
        # The discard comes after the card does its thing
        self.card.move_to(self.card.owner.graveyard)
        super(CastNonPermanentSpell, self).resolved()

class CastInstantSpell(CastNonPermanentSpell): pass
class CastSorcerySpell(CastNonPermanentSpell):
    def __init__(self, card, cost="0", target=None, effects=[], limit=None, copy_targets=True, zone="hand", txt=''):
        if limit and not isinstance(limit, SorceryLimit): limit = MultipleLimits(card, [SorceryLimit(card), limit])
        else: limit = SorceryLimit(card)
        super(CastSorcerySpell, self).__init__(card, cost=cost, target=target, effects=effects, copy_targets=copy_targets, limit=limit, zone=zone, txt='')

#class CastBuybackSpell(CastSpell):
#    def __str__(self):
#        return "Buyback "+super(CastBuybackSpell, self).__str__()
#
## XXX This should really be a replacement effect, replacing going to your graveyard
## This only matters if you play a spell that you don't own
#def buyback(card, buyback="0"):
#    main_spell = card.play_spell
#    cost = main_spell.cost + buyback
#
#    card.abilities.add(CastBuybackSpell(out_play_role.card, cost, main_spell.targets, main_spell.effects, main_spell.copy_targets, main_spell.limit))
