import copy
from symbols import *

class Match(object):
    def __init__(self, condition=None):
        if condition: self.condition = condition
        else: self.condition = lambda obj: True
    def with_condition(self, condition):
        # Creates a duplicate match with nested conditions
        newmatch = copy.copy(self)
        old_condition = newmatch.condition
        newmatch.condition = lambda obj: old_condition(obj) and condition(obj)
        return newmatch
    def match(self, obj):
        return self.condition(obj)
    def __call__(self, obj):
        return self.match(obj)

class PlayerMatch(Match):
    def match(self, player):
        import Player
        return isinstance(player, Player.Player) and super(PlayerMatch,self).match(player)
    def __str__(self):
        return "Player"
class OpponentMatch(Match):
    def __init__(self, controller, condition=None):
        super(OpponentMatch,self).__init__(condition)
        self.controller = controller
    def match(self, player):
        import Player
        return isinstance(player, Player.Player) and player in self.controller.opponents and super(OpponentMatch,self).match(player)
    def __str__(self):
        return "Opponent"

isPlayer = PlayerMatch()


class CardRoleMatch(Match):
    def match(self, card=None):
        import CardRoles
        return isinstance(card, CardRoles.CardRole) and super(CardRoleMatch,self).match(card)
    def __str__(self):
        return "Card"
    def zone(self, zone):
        pass
    def color(self, color):
        pass
    def types(self, types):
        pass
    def subtypes(self, subtypes):
        pass
    def supertypes(self, supertypes):
        pass

isCard = CardRoleMatch()

class ZoneMatch(Match):
    def __init__(self, zone, txt=''):
        super(ZoneMatch, self).__init__()
        self.zone = zone
        if not txt: txt = "Card in %s"%zone
        self.txt = txt
    def match(self, obj):
        return isCard(obj) and str(obj.zone) == self.zone and super(ZoneMatch,self).match(obj)
    def __str__(self): return self.txt

#isSpell = ZoneMatch("stack", "spell")
isPermanent = ZoneMatch("battlefield", "permanent")
isLegendaryPermanent = isPermanent.with_condition(lambda c: c.supertypes == Legendary)
isPermanentCard = isCard.with_condition(lambda c: c.types.intersects(set([Artifact, Enchantment, Creature, Land, Planeswalker])))

isToken = isPermanent.with_condition(lambda c: c._token)
isNonToken = isPermanent.with_condition(lambda c: not c._token)

# Type specific matching
class TypeMatch(Match):
    # Can match against power, toughness, anything
    # condition should be a boolean function
    def __init__(self, cardtype, on_battlefield=False):
        super(TypeMatch,self).__init__()
        self.cardtype = cardtype
        self.on_battlefield = on_battlefield
    def match(self, obj):
        if self.on_battlefield:
            return isPermanent(obj) and obj.types == self.cardtype and super(TypeMatch,self).match(obj)
        else:
            return isCard(obj) and obj.types == self.cardtype and super(TypeMatch,self).match(obj)
    def __str__(self):
        name = str(self.cardtype)
        if not self.on_battlefield: name += " card"
        return name

isCreature = TypeMatch(Creature, on_battlefield=True)
isLand = TypeMatch(Land, on_battlefield=True)
isBasicLand = isLand.with_condition(lambda l: l.supertypes == Basic)
isNonBasicLand = isLand.with_condition(lambda l: not l.supertypes == Basic)
isNonLand = isPermanent.with_condition(lambda p: not p.types == Land)
isArtifact = TypeMatch(Artifact, on_battlefield=True)
isArtifactCreature = isArtifact.with_condition(lambda a: a.types == Creature)
isNonCreatureArtifact = isArtifact.with_condition(lambda a: not a.types == Creature)
isEnchantment = TypeMatch(Enchantment, on_battlefield=True)
isEquipment = isArtifact.with_condition(lambda a: a.subtypes == Equipment)
isFortification = isArtifact.with_condition(lambda a: a.subtypes == Fortification)
isAura = isEnchantment.with_condition(lambda e: e.subtypes == Aura)
isAttachment = isPermanent.with_condition(lambda p: p.subtypes.intersects(set([Aura, Equipment, Fortification])))
isPlaneswalker = TypeMatch(Planeswalker, on_battlefield=True)

isSorceryCard = TypeMatch(Sorcery)
isInstantCard = TypeMatch(Instant)
isCreatureCard = TypeMatch(Creature)
isLandCard = TypeMatch(Land)
isBasicLandCard = isLandCard.with_condition(lambda l: l.supertypes == Basic)
isNonBasicLandCard = isLandCard.with_condition(lambda l: not l.supertypes == Basic)
isNonLandCard = isCard.with_condition(lambda p: not p.types == Land)
isArtifactCard = TypeMatch(Artifact)
isEnchantmentCard = TypeMatch(Enchantment)
isEquipmentCard = isArtifactCard.with_condition(lambda a: a.subtypes == Equipment)
isAuraCard = isEnchantmentCard.with_condition(lambda e: e.subtypes == Aura)

class PlayerOrCreatureMatch(Match):
    def match(self, obj):
        return (isPlayer(obj) or isCreature(obj)) and super(PlayerOrCreatureMatch,self).match(obj)
    def __str__(self):
        return "Player or Creature"
isCreatureOrPlayer = isPlayerOrCreature = PlayerOrCreatureMatch()

# For targeting and matching objects on the stack
class AbilityMatch(Match):
    # This is for targetting abilities on the stack
    def __init__(self, ability_type, txt='', condition=None):
        super(AbilityMatch, self).__init__(condition)
        self.ability_type = ability_type
        self.txt = txt
    def match(self, ability):
        return isinstance(ability, self.ability_type) and super(AbilityMatch,self).match(ability)
    def __str__(self):
        if self.txt: return self.txt
        else: return str(self.ability_type.__name__)

#from Ability.StackAbility import StackAbility
from Ability.CastingAbility import CastSpell, CastSorcerySpell, CastInstantSpell
#from Ability.ActivatedAbility import ActivatedAbility
#from Ability.TriggeredAbility import TriggeredStackAbility
#isStackAbility = AbilityMatch(StackAbility, "Ability")
#isActivatedAbility = AbilityMatch(ActivatedAbility, "Activated Ability")
#isTriggeredAbility = AbilityMatch(TriggeredStackAbility, "Triggered Ability")
isSpell = AbilityMatch(CastSpell, "Spell")
isInstantSpell = AbilityMatch(CastInstantSpell, "Instant")
isSorcerySpell = AbilityMatch(CastSorcerySpell, "Sorcery")
