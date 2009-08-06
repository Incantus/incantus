from engine.GameEvent import SpellPlayedEvent
from ActivatedAbility import CostAbility
from Limit import sorcery

class CastSpell(CostAbility):
    zone = "hand"
    def do_announce(self):
        # Move the card to the stack zone - this is never called from play
        player = self.controller
        old_zone = self.source.zone
        self.source = self.source.move_to(player.stack)
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
        self.source.move_to("graveyard")
        super(CastSpell,self).countered()

class CastPermanentSpell(CastSpell):
    limit_type = sorcery
    def resolved(self):
        source = self.source
        new_card = source.move_to(self.controller.play)
        if new_card == source: # didn't actually move to play
            source.move_to("graveyard")
        super(CastPermanentSpell, self).resolved()

class CastNonPermanentSpell(CastSpell):
    def resolved(self):
        # Goes to graveyard after being resolved
        self.source.move_to("graveyard")
        super(CastNonPermanentSpell, self).resolved()

class CastInstantSpell(CastNonPermanentSpell): pass
class CastSorcerySpell(CastNonPermanentSpell): limit_type = sorcery
