from engine.GameEvent import SpellPlayedEvent
from ActivatedAbility import CostAbility
from Limit import sorcery_limit
from Target import Target, NoTarget

__all__ = ["CastSpell", "CastPermanentSpell", "CastAuraSpell", "CastInstantSpell",
        "CastSorcerySpell"]

class CastSpell(CostAbility):
    cast = True
    zone = "hand"
    def do_announce(self):
        # Move the card to the stack zone - this is never called from the battlefield
        player = self.controller
        old_zone = self.source.zone
        self.source = self.source.move_to(player.stack)
        self.source._spell_controller = self.controller
        if super(CastSpell, self).do_announce():
            return True
        else:
            # XXX This is incorrect - what i really need to do is rewind
            # XXX Rewind
            self.source = self.source.move_to(old_zone)
            # XXX This is a hack on top of a hack: All it does is allow you to cancel casting
            # a spell from an ordered zone without having to wait for the next timestep for it to
            # re-appear in that zone. In other words, just as hacky as our regular "not-rewind",
            # only more so, because it needs to work on an OrderedZone.
            self.timestep()
            return False
    def get_cost(self):
        # ignore the cost returned by effects generator
        self.effects.next()
        self.cost = self.source.get_casting_cost()
    def played(self):
        # Don't change this order, otherwise abilities triggering on playing the spell
        # will be put on the stack before the played spell
        super(CastSpell, self).played()
        self.controller.send(SpellPlayedEvent(), spell=self.source)
    def countered(self):
        self.source.move_to("graveyard")
        super(CastSpell,self).countered()

class CastPermanentSpell(CastSpell):
    limit_type = sorcery_limit
    def __init__(self):
        super(CastPermanentSpell, self).__init__(self.effects, txt="Play spell")
    def effects(self, controller, source):
        yield source.cost
        yield NoTarget()
        yield
    def resolved(self):
        source = self.source
        new_card = source.move_to(self.controller.battlefield)
        if new_card == source: # didn't actually move to the battlefield
            source.move_to("graveyard")
        super(CastPermanentSpell, self).resolved()

class CastAuraSpell(CastPermanentSpell):
    def effects(self, controller, source):
        yield source.cost
        source.attach_on_enter = yield Target(source.target_type, zone=source.target_zone, player=source.target_player)
        yield

class CastNonPermanentSpell(CastSpell):
    def resolved(self):
        # Goes to graveyard after being resolved
        self.source.move_to("graveyard")
        super(CastNonPermanentSpell, self).resolved()

class CastInstantSpell(CastNonPermanentSpell): pass
class CastSorcerySpell(CastNonPermanentSpell): limit_type = sorcery_limit
