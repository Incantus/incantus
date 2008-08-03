
from GameEvent import PlayLandEvent, PlayAbilityEvent, LogEvent

class Action(object):
    def __eq__(self, other):
        return self.__class__ == other.__class__
    def __repr__(self):
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
    def __init__(self, card):
        self.selection = card

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
        abilities = [ability for ability in card.current_role.abilities if not ability.is_limited()]
        numabilities = len(abilities)
        if numabilities == 0: return False
        elif numabilities == 1: ability = abilities[0]
        else:
            ability = player.getSelection(abilities, 1, required=False, prompt="%s: Select ability"%self.card)
            if ability == False: return False

        # Now make a copy of the ability to populate it
        ability = ability.copy()
        ability.controller = player

        if ability.needs_stack(): success = player.stack.announce(ability)
        else: success = player.stack.stackless(ability)
        if success:
            player.send(PlayAbilityEvent(), ability=ability)
            player.send(LogEvent(), msg="%s plays (%s) of %s"%(player.name,ability,self.card))
        return success
    def __repr__(self):
        return "%s %s"%(self.__class__.__name__, self.card)

class PlayLand(Action):
    def __init__(self, card):
        self.card = card
    def check_zone(self):
        # Can only play a land from your hand
        return str(self.card.zone) == "hand"
    def perform(self, player):
        if not self.check_zone(): return False
        if player.land_actions == 0: return False
        elif player.land_actions > 0: player.land_actions -= 1
        card = self.card
        card.move_to(player.play)
        player.send(PlayLandEvent(), card=card)
        player.send(LogEvent(), msg="%s plays %s"%(player.name,card))
        return True
    def __repr__(self):
        return "%s %s"%(self.__class__.__name__, self.card)

class ActivateForMana(Action):
    def __init__(self, card):
        self.card = card
    def perform(self, player):
        card = self.card
        # Check if the card can be provide mana
        abilities = [ability for ability in card.current_role.abilities if ability.is_mana_ability() and not ability.is_limited()]

        numabilities = len(abilities)
        if numabilities == 0: return False
        elif numabilities == 1: ability = abilities[0]
        else:
            ability = player.getSelection(abilities, 1, required=False, prompt="%s - Mana abilities"%self.card)
            if ability is False: return False

        ability = ability.copy()
        return player.stack.stackless(ability)
