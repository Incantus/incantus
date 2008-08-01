from game.GameEvent import PlaySpellEvent
from ActivatedAbility import *
from Limit import SorceryLimit

# XXX Fix the controller of the spell
class CastSpell(object):
    def __init__(self, card, cost="0", target=None, effects=[], copy_targets=True, limit=None):
        super(CastSpell, self).__init__(card, cost=cost, target=target, effects=effects, copy_targets=copy_targets, limit=limit, zone="hand")
    def played(self):
        super(CastSpell, self).played()
        self.controller.send(PlaySpellEvent(), card=self.card)
    def countered(self):
        super(CastSpell,self).countered()
        player = self.controller
        player.discard(self.card)

class CastPermanentSpell(CastSpell, ActivatedAbility):
    def __init__(self, card, cost="0", target=None, effects=[], limit=None, copy_targets=True):
        if limit: limit += SorceryLimit(card)
        else: limit = SorceryLimit(card)
        super(CastPermanentSpell, self).__init__(card, cost=cost, target=target, effects=effects, copy_targets=copy_targets, limit=limit)
    def preresolve(self):
        # The card is put into play before any effects resolve
        self.card.move_to(self.controller.play)
        self.card.controller = self.controller
        return super(CastPermanentSpell, self).preresolve()
    def __str__(self):
        return "%s: Put into play"%self.cost

class CastNonPermanentSpell(CastSpell, ActivatedAbility):
    def resolved(self):
        # The discard comes after the card does its thing
        # XXX Fix this when making the stack a zone
        self.card.move_to(self.card.owner.graveyard)
        super(CastNonPermanentSpell, self).resolved()
    def __str__(self):
        return "%s: %s"%(self.cost, ', '.join(map(str,self.effects)))

class CastInstantSpell(CastNonPermanentSpell): pass
class CastSorcerySpell(CastNonPermanentSpell):
    def __init__(self, card, cost="0", target=None, effects=[], limit=None, copy_targets=True):
        if limit: limit = MultipleLimits([SorceryLimit(card), limit])
        else: limit = SorceryLimit(card)
        super(CastSorcerySpell, self).__init__(card, cost=cost, target=target, effects=effects, copy_targets=copy_targets, limit=limit)

class CastBuybackSpell(CastSpell, ActivatedAbility):
    def __str__(self):
        return "Buyback "+super(CastBuybackSpell, self).__str__()

# XXX This should really be a replacement effect, replacing going to your graveyard
# This only matters if you play a spell that you don't own
def buyback(out_play_role, buyback="0"):
    main_spell = out_play_role.abilities[0]
    cost = main_spell.cost + buyback

    out_play_role.abilities.append(CastBuybackSpell(out_play_role.card, cost, main_spell.targets, main_spell.effects, main_spell.copy_targets, main_spell.limit))
