import copy
from pydispatch import dispatcher
from GameEvent import TokenLeavingPlay, ColorModifiedEvent, SubtypeModifiedEvent, SupertypeModifiedEvent
from abilities import abilities, stacked_abilities
from characteristics import stacked_characteristic

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
    def register(self, callback, event, sender=dispatcher.Any, weak=True, expiry=-1):
        # register to receive events
        # if expiry == -1, then it is continuous, otherwise number is the number of times
        # that the callback is processed
        # XXX Major python problem - each callback must be a separate function (or wrapped in a lambda)
        # which makes it hard to disconnect it
        dispatcher.connect(callback, signal=event, sender=sender,weak=weak,expiry=expiry)
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
    #__slots__ = ["name", "base_name", "base_cost", "base_text", "base_color", "base_type", "base_subtypes", "base_supertypes", "_owner", "zone", "out_play_role", "in_play_role", "stack_role", "_current_role", "key"]
    def __init__(self, owner):
        # characteristics

        self.out_play_role = None
        self.in_play_role = None
        self.stack_role = None

        self.name = self.base_name = None
        self.base_cost = None
        self.base_text = None
        self.base_color = None
        self.base_type = None
        self.base_subtypes = None
        self.base_supertype = None
        self.base_abilities = abilities()
        self.play_spell = None

        self._owner = owner
        self.zone = None

        self._current_role = None
    owner = property(fget=lambda self: self._owner)
    def current_role():
        doc = '''The current role for this card. Either a Spell (when in hand, library, graveyard or out of game), Spell, (stack) or Permanent (in play)'''
        def fget(self):
            return self._current_role
        def fset(self, role):
            role = copy.deepcopy(role)

            # Set up base characteristics
            role.name = self.base_name
            role.owner = self.owner
            role.cost = self.base_cost
            role.text = self.base_text
            role.color = stacked_characteristic(self, self.base_color, ColorModifiedEvent())
            role.type = self.base_type
            role.subtypes = stacked_characteristic(self, self.base_subtypes, SubtypeModifiedEvent())
            role.supertype = stacked_characteristic(self, self.base_supertype, SupertypeModifiedEvent)
            role.abilities = stacked_abilities(self, self.base_abilities)
            self._current_role = role
        return locals()
    current_role = property(**current_role())
    def move_to(self, to_zone, position=-1):
        to_zone.move_card(self, position)
    # I should probably get rid of the getattr call, and make everybody refer to current_role directly
    # But that makes the code so much uglier
    # XXX This is just temporary
    controller = property(fget=lambda self: self._current_role.controller, fset=lambda self, c: setattr(self._current_role, "controller", c))
    def __getattr__(self, attr):
        if hasattr(self.current_role, attr):
            return getattr(self._current_role,attr)
        else: raise Exception, "no attribute named %s"%attr
    def __repr__(self):
        return "%s at %s"%(str(self),str(id(self)))

class Card(GameObject):
    def __init__(self, owner):
        super(Card, self).__init__(owner)
        # characteristics
        self.expansion = None
        self.hidden = False
    def __str__(self):
        return self.name

class Token(GameObject):
    def move_to(self, to_zone, position=-1):
        super(Token, self).move_to(to_zone, position)
        if not str(to_zone) == "play": self.send(TokenLeavingPlay())
    def __str__(self):
        return "Token: %s"%self.name
