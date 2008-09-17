from game.GameEvent import SpellPlayedEvent, TimestepEvent
from ActivatedAbility import CostAbility
from Limit import sorcery

class CastSpell(CostAbility):
    zone = "hand"
    def do_announce(self):
        # Move the card to the stack zone - this is never called from play
        player = self.controller
        old_zone = self.source.zone
        self.source = player.stack.put_card(self.source)
        if super(CastSpell, self).do_announce():
            return True
        else:
            # XXX This is incorrect - what i really need to do is rewind
            # XXX Rewind
            self.source = self.source.move_to(old_zone)
            return False
    def played(self):
        # Don't change this order, otherwise abilities triggering on playing the spell
        # will be put on the stack before the played spell
        super(CastSpell, self).played()
        self.controller.send(SpellPlayedEvent(), spell=self.source)
    def countered(self):
        self.source.move_to(self.source.owner.graveyard)
        super(CastSpell,self).countered()

class CastPermanentSpell(CastSpell):
    limit_type = sorcery
    def resolved(self):
        self.source.move_to(self.controller.play)
        self.source.send(TimestepEvent())
        super(CastPermanentSpell, self).resolved()

class EnchantAbility(CastSpell):
    limit_type = sorcery
    def __init__(self, effects, target_type, txt=''):
        self.target_type = target_type
        super(EnchantAbility, self).__init__(effects, txt=txt, keyword='enchant')
    def resolved(self):
        source = self.source.move_to(self.controller.play)
        source.send(TimestepEvent())
        source.set_target_type(self.target_type)
        source.attach(self.targets[0].target)
        super(EnchantAbility, self).resolved()

class CastNonPermanentSpell(CastSpell):
    def resolved(self):
        # The discard comes after the card does its thing
        self.source.move_to(self.source.owner.graveyard)
        super(CastNonPermanentSpell, self).resolved()

class CastInstantSpell(CastNonPermanentSpell): pass
class CastSorcerySpell(CastNonPermanentSpell): limit_type = sorcery

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
