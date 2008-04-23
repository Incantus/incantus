import CardRoles

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
    #def match(self, **kargs):
    #    return self.condition(**kargs)
    #def __call__(self, **kargs):
    #    return self.match(**kargs)

class ObjMatch(Match):
    def __init__(self, condition=None):
        if condition: self.condition = condition
        else: self.condition = lambda x: True
    def match(self, obj):
        return self.condition(obj)
    def __call__(self, obj):
        return self.match(obj)

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

class RoleMatch(ObjMatch):
    # Can match against power, toughness, anything
    # condition should be a boolean function
    def __init__(self, cardrole, condition=None, use_in_play=False):
        super(RoleMatch,self).__init__(condition)
        self.cardrole = cardrole
        self.use_in_play = use_in_play
    def match(self, obj=None, use_in_play=False):
        role = obj.current_role
        if (use_in_play or self.use_in_play): role=obj.in_play_role
        return role.match_role(self.cardrole) and super(RoleMatch,self).match(obj)
        #return isinstance(role, self.cardrole) and super(RoleMatch,self).match(obj)
    def __str__(self):
        matchname = self.cardrole.__name__
        if self.use_in_play: matchname += " card"
        return matchname

class PlayerMatch(ObjMatch):
    def match(self, player=None):
        import Player # To avoid circular imports
        return isinstance(player, Player.Player) and self.condition(player)
    def __str__(self):
        return "Player"

class OpponentMatch(ObjMatch):
    def __init__(self, card, condition=None):
        super(OpponentMatch,self).__init__(condition)
        self.card = card
    def match(self, player=None):
        import Player # To avoid circular imports
        return isinstance(player, Player.Player) and not self.card.controller == player and self.condition(player)
    def __str__(self):
        return "Opponent"


class GameObjectMatch(ObjMatch):
    def match(self, obj=None):
        import GameObjects
        return isinstance(obj, GameObjects.GameObject) and self.condition(obj)
    def __str__(self):
        return "GameObject"

class CardMatch(ObjMatch):
    def match(self, card=None):
        import GameObjects
        return isinstance(card, GameObjects.Card) and self.condition(card)
    def __str__(self):
        return "Card"

class SelfMatch(ObjMatch):
    # Matches against the same card
    def __init__(self, card, condition=None):
        super(SelfMatch,self).__init__(condition)
        self.card = card
    def match(self, card=None):
        return card == self.card and super(SelfMatch,self).match(card)
    def __str__(self):
        return str(self.card)

isPlayer = PlayerMatch()

isSpell = RoleMatch(CardRoles.Spell)
isPermanent = RoleMatch(CardRoles.Permanent)
isLegendaryPermanent = isPermanent.with_condition(lambda c: c.supertype == "Legendary")
isCreature = RoleMatch(CardRoles.Creature)
isLand = RoleMatch(CardRoles.Land)
isBasicLand = isLand.with_condition(lambda l: l.supertype == "Basic")
isNonBasicLand = isLand.with_condition(lambda l: not l.supertype == "Basic")
isArtifact = RoleMatch(CardRoles.Artifact)
isToken = RoleMatch(CardRoles.TokenCreature)
isEnchantment = RoleMatch(CardRoles.Enchantment)
isEquipment = RoleMatch(CardRoles.Equipment)
isAura = RoleMatch(CardRoles.Aura)
isAttachment = RoleMatch(CardRoles.Attachment)

class ArtifactCreatureMatch(ObjMatch):
    def match(self, obj):
        return (isArtifact(obj) and isCreature(obj)) and super(ArtifactCreatureMatch,self).match(obj)
    def __str__(self):
        return "Artifact Creature"
isArtifactCreature = ArtifactCreatureMatch()

class PlayerOrCreatureMatch(ObjMatch):
    def match(self, obj):
        return (isPlayer(obj) or isCreature(obj)) and super(PlayerOrCreatureMatch,self).match(obj)
    def __str__(self):
        return "Player or Creature"
isPlayerOrCreature = PlayerOrCreatureMatch()
isCreatureOrPlayer = isPlayerOrCreature

isPermanentType = RoleMatch(CardRoles.Permanent, use_in_play=True)
isCreatureType = RoleMatch(CardRoles.Creature, use_in_play=True)
isLandType = RoleMatch(CardRoles.Land, use_in_play=True)
isArtifactType = RoleMatch(CardRoles.Artifact, use_in_play=True)
isEnchantmentType = RoleMatch(CardRoles.Enchantment, use_in_play=True)
isEquipmentType = RoleMatch(CardRoles.Equipment, use_in_play=True)
isAuraType = RoleMatch(CardRoles.Aura, use_in_play=True)

class nonLandType(CardMatch):
    def match(self, card=None):
        return not isLandType(card) and super(nonLandType,self).match(card)
    def __str__(self):
        return "non Land"

isNonLandType = nonLandType()

isCard = CardMatch()
isGameObject = GameObjectMatch()

from Ability import Ability
from Ability.CastingAbility import CastSpell, CastNonPermanentSpell
from Ability.ActivatedAbility import ActivatedAbility
isAbility = AbilityMatch(Ability, "Ability")
isSpellAbility = AbilityMatch(CastSpell, "Spell")
isNonPermanentSpellAbility = AbilityMatch(CastNonPermanentSpell, "Instant or Sorcery")
isActivatedAbility = AbilityMatch(ActivatedAbility, "Activated Ability")
