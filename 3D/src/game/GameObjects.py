import weakref
from pydispatch import dispatcher
from GameEvent import TokenLeavingPlay, ColorModifiedEvent, TypesModifiedEvent, SubtypesModifiedEvent, SupertypesModifiedEvent
from abilities import abilities, stacked_abilities
from characteristics import stacked_variable, stacked_characteristic, stacked_type
import CardDatabase

class MtGObject(object):
    #Universal dispatcher
    # this class is for all objects that can send and receive signals
    #_lock = False
    #_holding = False
    def send(self, event, *args, **named):
        #send event to dispatcher
        dispatcher.send(event, self, *args, **named)
        #if not MtGObject._lock: dispatcher.send(event, self, *args, **named)
        #else: MtGObject._holding.append(lambda: dispatcher.send(event, self, *args, **named))
    def register(self, callback, event, sender=dispatcher.Any, weak=True, expiry=-1, priority=dispatcher.LOWEST_PRIORITY):
        # register to receive events
        # if expiry == -1, then it is continuous, otherwise number is the number of times
        # that the callback is processed
        # XXX Major python problem - each callback must be a separate function (or wrapped in a lambda)
        # which makes it hard to disconnect it
        dispatcher.connect(callback, signal=event, sender=sender,weak=weak,expiry=expiry,priority=priority)
    def unregister(self, callback, event, sender=dispatcher.Any, weak=True):
        dispatcher.disconnect(callback, signal=event, sender=sender, weak=weak)
    #@staticmethod
    #def lock():
    #    MtGObject._lock = True
    #    MtGObject._holding = []
    #@staticmethod
    #def release():
    #    MtGObject._lock = False
    #    # Call the sends that were held
    #    for func in MtGObject._holding: func()

class GameObject(MtGObject):
    #__slots__ = ["name", "base_name", "base_cost", "base_text", "base_color", "base_types", "base_subtypes", "base_supertypes", "_owner", "zone", "out_play_role", "in_play_role", "stack_role", "_current_role", "key"]
    def __init__(self, owner):
        self._owner = owner
        self.zone = None

        self._current_role = None
        self._last_known_info = None
        self.in_play_role = None
        self.stack_role = None
        self.out_play_role = None

        # characteristics
        self.base_name = None
        self.base_cost = None
        self.base_text = None
        self.base_color = None
        self.base_types = None
        self.base_subtypes = None
        self.base_supertypes = None
        self.base_abilities = abilities()
        self.play_spell = None

        self.base_power = 0 #None  It should really be None for CDAs
        self.base_toughness = 0 #None
        self.base_loyalty = None

    owner = property(fget=lambda self: self._owner)
    def current_role():
        doc = '''The current role for this card. Either a Card (when in hand, library, graveyard or removed from game), Spell, (stack) or Permanent (in play)'''
        def fget(self): return self._current_role
        def fset(self, newrole):
            self._last_known_info = self._current_role
            self._cardmap[self.key] = self._current_role = self.build_role(newrole(self))
        return locals()
    current_role = property(**current_role())
    def build_role(self, role):
        proxy_role = weakref.proxy(role)
        # Set up base characteristics
        role.owner = self.owner
        role.name = stacked_variable(self.base_name)
        role.cost = self.base_cost
        role.text = stacked_variable(self.base_text)
        role.color = stacked_characteristic(proxy_role, self.base_color, ColorModifiedEvent())
        role.types = stacked_type(proxy_role, self.base_types, TypesModifiedEvent())
        role.subtypes = stacked_characteristic(proxy_role, self.base_subtypes, SubtypesModifiedEvent())
        role.supertypes = stacked_characteristic(proxy_role, self.base_supertypes, SupertypesModifiedEvent)
        role.abilities = stacked_abilities(weakref.ref(role), self.base_abilities)

        role.play_spell = self.play_spell

        role.base_power = stacked_variable(self.base_power)
        role.base_toughness = stacked_variable(self.base_toughness)
        role.base_loyalty = stacked_variable(self.base_loyalty)
        return role

    def move_to(self, zone, position="top"):
        return zone.move_card(self, position)
    def __repr__(self):
        return "%s at %s"%(str(self),str(id(self)))
    def __str__(self):
        return str(self.base_name)

    # Class attributes for mapping the cards
    _counter = 0
    _cardmap = {}
    def _add_to_map(self):
        self.key = (GameObject._counter, self.base_name)
        #self._cardmap[self.key] = self
        GameObject._counter += 1

class Card(GameObject):
    def __init__(self, cardname, owner):
        super(Card, self).__init__(owner)
        # characteristics
        self.expansion = None
        self.hidden = False

        from CardRoles import Permanent, SpellRole, CardRole, NoRole
        CardDatabase.loadCardFromDB(self, cardname)
        self.stack_role = SpellRole
        self.out_play_role = CardRole
        if (self.base_types == "Instant" or self.base_types == "Sorcery"):
            self.in_play_role = NoRole
        else:
            self.in_play_role = Permanent

        if (self.base_subtypes == "Aura"):
            from game.Ability.PermanentAbility import CiP, attach_on_enter
            CiP(self, attach_on_enter, txt="Attach to target")

        self._add_to_map()

class Token(GameObject):
    def __init__(self, info, owner):
        super(Token, self).__init__(owner)
        from CardRoles import NoRole, Permanent
        if type(info) == dict: info = CardDatabase.convertToTxt(info)
        CardDatabase.execCode(self, info)
        self.out_play_role = self.stack_role = NoRole
        self.in_play_role = Permanent
        self.base_name = "%s Token"%self.base_name
        self._add_to_map()
    def move_to(self, zone, position="top"):
        if not str(zone) == "play": self.send(TokenLeavingPlay())
        return super(Token, self).move_to(zone, position)
    def __str__(self):
        return "Token: %s"%self.base_name
