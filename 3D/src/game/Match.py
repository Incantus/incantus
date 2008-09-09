
class Match(object):
    def __init__(self, condition=None):
        if condition: self.condition = condition
        else: self.condition = lambda: True
    def with_condition(self, condition):
        # Creates a duplicate match with a condition
        import copy
        newmatch = copy.copy(self)
        newmatch.condition = condition
        return newmatch

class ObjMatch(Match):
    def __init__(self, condition=None):
        if condition: self.condition = condition
        else: self.condition = lambda x: True
    def match(self, obj):
        return self.condition(obj)
    def __call__(self, obj):
        return self.match(obj)

class PlayerMatch(ObjMatch):
    def match(self, player=None):
        import Player
        return isinstance(player, Player.Player) and self.condition(player)
    def __str__(self):
        return "Player"
class OpponentMatch(ObjMatch):
    def __init__(self, card, condition=None):
        super(OpponentMatch,self).__init__(condition)
        self.card = card
    def match(self, player=None):
        return isinstance(player, Player.Player) and not self.card.controller == player and self.condition(player)
    def __str__(self):
        return "Opponent"

isPlayer = PlayerMatch()


# Matching any type of game object (cards or tokens)

class GameObjectMatch(ObjMatch):
    def match(self, obj=None):
        import GameObjects
        return isinstance(obj, GameObjects.GameObject) and self.condition(obj)
    def __str__(self):
        return "GameObject"

class TokenMatch(ObjMatch):
    def match(self, obj=None):
        import GameObjects
        return isinstance(obj, GameObjects.Token) and self.condition(obj)
    def __str__(self):
        return "GameObject"

class CardMatch(ObjMatch):
    def match(self, card=None):
        import GameObjects
        return isinstance(card, GameObjects.Card) and self.condition(card)
    def __str__(self):
        return "Card"

isGameObject = GameObjectMatch()
isCard = CardMatch()
isToken = TokenMatch()

class ZoneMatch(ObjMatch):
    def __init__(self, zone, condition=None, txt=''):
        super(ZoneMatch, self).__init__(condition)
        self.zone = zone
        if not txt: txt = "Card in %s"%zone
        self.txt = txt
    def match(self, obj):
        return isGameObject(obj) and str(obj.zone) == self.zone
    def __str__(self): return self.txt

isSpell = ZoneMatch("stack", "spell")
isPermanent = ZoneMatch("play", "permanent")
isLegendaryPermanent = isPermanent.with_condition(lambda c: c.supertype == "Legendary")
isPermanentCard = isCard.with_condition(lambda c: c.type == "Artifact" or c.type == "Enchantment" or c.type == "Creature" or c.type == "Land" or c.type == "Planeswalker")

# Type specific matching
class TypeMatch(ObjMatch):
    # Can match against power, toughness, anything
    # condition should be a boolean function
    def __init__(self, cardtype, in_play=False):
        super(TypeMatch,self).__init__()
        self.cardtype = cardtype
        self.in_play = in_play
    def match(self, obj):
        if self.in_play:
            return isPermanent(obj) and obj.type == self.cardtype and super(TypeMatch,self).match(obj)
        else:
            return isGameObject(obj) and obj.type == self.cardtype and super(TypeMatch,self).match(obj)
    def __str__(self):
        name = str(self.cardtype)
        if not self.in_play: name += " card"
        return name

isCreature = TypeMatch("Creature", in_play=True)
isLand = TypeMatch("Land", in_play=True)
isBasicLand = isLand.with_condition(lambda l: l.supertype == "Basic")
isNonBasicLand = isLand.with_condition(lambda l: not l.supertype == "Basic")
isNonLand = isPermanent.with_condition(lambda p: not p.type == "Land")
isArtifact = TypeMatch("Artifact", in_play=True)
isEnchantment = TypeMatch("Enchantment", in_play=True)
isEquipment = isArtifact.with_condition(lambda a: a.subtypes == "Equipment")
isAura = isEnchantment.with_condition(lambda e: e.subtypes == "Aura")
isPlaneswalker = TypeMatch("Planeswalker", in_play=True)

isSorceryCard = TypeMatch("Sorcery")
isInstantCard = TypeMatch("Instant")
isCreatureCard = TypeMatch("Creature")
isLandCard = TypeMatch("Land")
isArtifactCard = TypeMatch("Artifact")
isEnchantmentCard = TypeMatch("Enchantment")
isEquipmentCard = isArtifactCard.with_condition(lambda a: a.subtypes == "Equipment")
isAuraCard = isEnchantmentCard.with_condition(lambda e: e.subtypes == "Aura")

class PlayerOrCreatureMatch(ObjMatch):
    def match(self, obj):
        return (isPlayer(obj) or isCreature(obj)) and super(PlayerOrCreatureMatch,self).match(obj)
    def __str__(self):
        return "Player or Creature"
isCreatureOrPlayer = isPlayerOrCreature = PlayerOrCreatureMatch()

# For targeting and matching objects on the stack
class AbilityMatch(ObjMatch):
    # This is for targetting abilities on the stack
    def __init__(self, ability_type, txt='', condition=None):
        super(AbilityMatch, self).__init__(condition)
        self.ability_type = ability_type
        self.txt = txt
    def match(self, ability):
        return isinstance(ability, self.ability_type) and self.condition(ability)
    def __str__(self):
        if self.txt: return self.txt
        else: return str(self.ability_type.__name__)

from Ability.Ability import Ability
from Ability.CastingAbility import CastSpell, CastSorcerySpell, CastInstantSpell
from Ability.ActivatedAbility import ActivatedAbility
isAbility = AbilityMatch(Ability, "Ability")
isSpellAbility = AbilityMatch(CastSpell, "Spell")
isInstantSpell = AbilityMatch(CastInstantSpell, "Instant")
isSorcerySpell = AbilityMatch(CastSorcerySpell, "Sorcery")
isActivatedAbility = AbilityMatch(ActivatedAbility, "Activated Ability")
