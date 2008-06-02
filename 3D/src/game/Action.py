
from GameEvent import PlayLandEvent, PlayAbilityEvent, PlaySpellEvent

class Action(object):
    def __eq__(self, other):
        return self.__class__ == other.__class__
    def __str__(self):
        return str(self.__class__.__name__)

# should drawing a card be in here?

class PassPriority(Action):
    pass
class OKAction(Action):
    pass
class CancelAction(Action):
    pass

# For attackers to assign damage to multiple blockers
class DamageAssignment(Action):
    def __init__(self, assnment):
        self.assignment = assnment

class CardSelected(Action):
    def __init__(self, card, zone):
        self.selection = card
        self.zone = zone

class PlayerSelected(Action):
    def __init__(self, player):
        self.selection = player

class SingleSelected(Action):
    def __init__(self, selected):
        self.selection = selected

class MultipleSelected(Action):
    def __init__(self, selected):
        self.selection = selected

class ManaSelected(Action):
    def __init__(self, mana):
        self.mana = mana

class XSelected(Action):
    def __init__(self, amount):
        self.amount = amount

class PlayAbility(Action):
    def __init__(self, card):
        self.card = card
    def perform(self, player):
        card = self.card
        success = False
        # Replace the representation of a with the text from the card
        # XXX Must use the index of the ability, since we can't pickle abilities for network games
        abilities = [(ability, i) for i, ability in enumerate(card.current_role.abilities) if not ability.is_limited()]
        numabilities = len(abilities)
        if numabilities == 0: return False
        elif numabilities == 1: ability = abilities[0][0]
        else:
            index = player.getSelection(abilities, 1, required=False, prompt="%s: Select ability"%self.card)
            if index is False: return False
            ability = abilities[index][0]

        # Now make a copy of the ability to populate it
        ability = ability.copy()
        ability.controller = player

        if ability.needs_stack(): success = player.stack.announce(ability)
        else: success = player.stack.stackless(ability)
        if success:
            #print "%s plays (%s) of %s"%(player.name,ability,self.card)
            player.send(PlayAbilityEvent(), ability=ability)
        else:
            #print "%s: Failed playing %s - %s"%(player.name, self.card, ability)
            pass
        return success

class PlayLand(Action):
    def __init__(self, card):
        self.card = card
    def check_zone(self):
        # Can only play a land from your hand
        return self.card.zone == self.card.controller.hand
    def perform(self, player):
        self.card.controller = player
        if not self.check_zone(): return False
        if player.land_actions == 0: return False
        elif player.land_actions > 0: player.land_actions -= 1
        # This signals to everyone the move
        player.moveCard(self.card, self.card.zone, player.play)
        player.send(PlayLandEvent(), card=self.card)
        #print "%s plays %s"%(player.name,self.card)
        return True

class ActivateForMana(Action):
    def __init__(self, card):
        self.card = card
    def perform(self, player):
        card = self.card
        # Check if the card can be provide mana
        abilities = [(ability, i) for i, ability in enumerate(card.current_role.abilities) if ability.is_mana_ability() and not ability.is_limited()]

        numabilities = len(abilities)
        if numabilities == 0: return False
        elif numabilities == 1: ability = abilities[0][0]
        else:
            index = player.getSelection(abilities, 1, required=False, prompt="%s - Mana abilities"%self.card)
            if index is False: return False
            ability = abilities[index][0]

        ability = ability.copy()
        return player.stack.stackless(ability)
