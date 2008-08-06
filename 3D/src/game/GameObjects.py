import copy
from pydispatch import dispatcher
from GameEvent import HasPriorityEvent, ControllerChanged, TokenLeavingPlay
from data_structures import keywords
from abilities import abilities

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
    #__slots__ = ["name", "cost", "text", "color", "type", "subtypes", "supertypes", "owner", "controller", "zone", "out_play_role", "in_play_role", "_current_role"]
    def __init__(self, owner):
        # characteristics
        self.name = None
        self.cost = None
        self.text = None
        # The next four are characteristics that can be affected by other spells
        self.color = None
        self.type = None
        self.subtypes = None
        self.supertype = None

        self.out_play_role = None
        self.in_play_role = None
        self.stack_role = None

        self.base_name = None
        self.base_cost = None
        self.base_text = None
        self.base_color = None
        self.base_type = None
        self.base_subtypes = None
        self.base_supertype = None
        self.base_keywords = self.keywords = keywords()
        self.base_abilities = self.abilities = abilities([])
        self.play_spell = None

        self._owner = owner
        self._controller = None  # XXX I think this is incorrect
        self.zone = None

        self._current_role = None
        self._last_known_info = None
    def controller():
        doc = "The controller of this card - only valid when in play or on the stack"
        def fget(self):
            if not self._controller: return self._owner
            else: return self._controller
        def fset(self, controller):
            if controller == None: self._controller = controller
            elif not controller == self._controller:
                self._controller, old_controller = controller, self._controller
                self.summoningSickness()
                if old_controller: self.send(ControllerChanged(), original=old_controller)
        return dict(doc=doc, fset=fset, fget=fget)
    controller = property(**controller())
    owner = property(fget=lambda self: self._owner)
    def save_lki(self):
        # How long should we keep LKI?
        self._last_known_info = self._current_role
        #def reset_lki(): 
        #    del self._last_known_info
        #    self._last_known_info = None #self.in_play_role
        #self.register(reset_lki, event=HasPriorityEvent(), weak=False, expiry=1)
    def current_role():
        doc = '''The current role for this card. Either a Spell (when in hand, library, graveyard or out of game), Spell, (stack) or Permanent (in play)'''
        def fget(self):
            return self._current_role
        def fset(self, role):
            self._current_role = copy.deepcopy(role)

            # Set up base characteristics
            self.name = self.base_name
            self.cost = self.base_cost
            self.text = self.base_text
            self.color = self.base_color
            self.type = self.base_type
            self.subtypes = self.base_subtypes
            self.supertypes = self.base_supertype
            self.abilities = self.base_abilities
            self.keywords = copy.deepcopy(self.base_keywords)
        return locals()
    current_role = property(**current_role())
    def info():
        def fget(self):
            txt = [str(self.name)]
            color = str(self.color)
            if color: txt.append("\n%s"%color)
            txt.append("\n")
            supertype = str(self.supertype)
            if supertype: txt.append(supertype+" ")
            txt.append(str(self.type))
            subtypes = str(self.subtypes)
            if subtypes: txt.append(" - %s"%subtypes)
            #txt.append("\n\n"+'\n'.join(self.text))
            #keywords = str(self.keywords)
            #if keywords: txt.append('\n\n%s'%keywords)
            abilities = str(self.abilities)
            if abilities: txt.append('\n\n%s'%abilities)
            counters = ', '.join([str(c) for c in self.counters])
            if counters: txt.append('\nCounters: %s'%counters)
            subrole_info = self.subrole_info()
            if subrole_info: txt.append('\n\n'+subrole_info)
            return ''.join(txt)
        return locals()
    info = property(**info())
    def move_to(self, to_zone, position=-1):
        to_zone.move_card(self, position)
    def enteringZone(self, zone):
        self.current_role.enteringZone(zone)
        self.abilities.enteringZone(zone)
    def leavingZone(self, zone):
        self.current_role.leavingZone(zone)
        self.abilities.leavingZone(zone)
    # I should probably get rid of the getattr call, and make everybody refer to current_role directly
    # But that makes the code so much uglier
    def __getattr__(self, attr):
        if hasattr(self.current_role, attr):
            return getattr(self.current_role,attr)
        else:
            # We are probably out of play - check the last known info
            return getattr(self._last_known_info, attr)
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
