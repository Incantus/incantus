import weakref
from MtGObject import MtGObject
from GameEvent import NameModifiedEvent, CostModifiedEvent, TextModifiedEvent, ColorModifiedEvent, TypesModifiedEvent, SubtypesModifiedEvent, SupertypesModifiedEvent, PowerToughnessModifiedEvent, LoyaltyModifiedEvent
from abilities import abilities, stacked_abilities
from characteristics import stacked_variable, stacked_characteristic, stacked_type
from CardRoles import Permanent, SpellRole, NoRole, LandOutPlayRole, OutPlayRole, TokenOutPlayRole, TokenPermanent
import CardDatabase

class GameObject(MtGObject):
    #__slots__ = ["key", "base_name", "base_cost", "base_text", "base_color", "base_types", "base_subtypes", "base_supertypes", "_owner", "out_play_role", "in_play_role", "stack_role"]
    def __init__(self, owner):
        self._owner = owner

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

        self.base_power = 0
        self.base_toughness = 0
        self.base_loyalty = 0

    owner = property(fget=lambda self: self._owner)
    def new_role(self, rolecls):
        role = rolecls(self.key)
        proxy_role = weakref.proxy(role)
        self._current_roles[self.key] = role
        # Set up base characteristics
        role.owner = self.owner
        role.name = stacked_variable(proxy_role, self.base_name, NameModifiedEvent())
        role.cost = stacked_variable(proxy_role, self.base_cost, CostModifiedEvent())
        role.text = stacked_variable(proxy_role, self.base_text, TextModifiedEvent())
        role.color = stacked_characteristic(proxy_role, self.base_color, ColorModifiedEvent())
        role.types = stacked_type(proxy_role, self.base_types, TypesModifiedEvent())
        role.subtypes = stacked_characteristic(proxy_role, self.base_subtypes, SubtypesModifiedEvent())
        role.supertypes = stacked_characteristic(proxy_role, self.base_supertypes, SupertypesModifiedEvent)
        role.abilities = stacked_abilities(weakref.ref(role), self.base_abilities)

        role.base_power = stacked_variable(proxy_role, self.base_power, PowerToughnessModifiedEvent())
        role.base_toughness = stacked_variable(proxy_role, self.base_toughness, PowerToughnessModifiedEvent())
        role.base_loyalty = stacked_variable(proxy_role, self.base_loyalty, LoyaltyModifiedEvent())
        return role

    def __repr__(self):
        return "%s at %s"%(str(self),str(id(self)))
    def __str__(self):
        return str(self.base_name)

    # Class attributes for mapping the cards
    _counter = 0
    _current_roles = {}
    _cardmap = {}
    def _add_to_map(self, key_name):
        self.key = (GameObject._counter, key_name)
        self._cardmap[self.key] = self
        GameObject._counter += 1

class Card(GameObject):
    def __init__(self, cardname, owner):
        super(Card, self).__init__(owner)

        CardDatabase.loadCardFromDB(self, cardname)
        if self.base_types == "Land":
            self.stack_role = NoRole
            self.out_play_role = LandOutPlayRole
        else:
            self.stack_role = SpellRole
            self.out_play_role = OutPlayRole

        if (self.base_types == "Instant" or self.base_types == "Sorcery"):
            self.in_play_role = NoRole
        else:
            self.in_play_role = Permanent

        self._add_to_map(self.base_name)

    @classmethod
    def create(cls, cardname, owner):
        card = cls(cardname, owner)
        newrole = card.new_role(card.out_play_role)
        return newrole

class Token(GameObject):
    def __init__(self, info, owner):
        super(Token, self).__init__(owner)
        if type(info) == dict: info = CardDatabase.convertToTxt(info)
        CardDatabase.execCode(self, info)
        self.out_play_role = self.stack_role = TokenOutPlayRole
        self.in_play_role = TokenPermanent
        self._add_to_map(self.base_name+" Token")

    @classmethod
    def create(cls, info, owner):
        token = cls(info, owner)
        newrole = token.new_role(token.out_play_role)
        newrole.is_LKI = False # so we can move it into play the first time
        return newrole

    def __str__(self):
        return "Token: %s"%self.base_name
