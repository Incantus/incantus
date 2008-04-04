
from GameEvent import PlayActionEvent, PlayLandEvent, PlayAbilityEvent, PlaySpellEvent

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

class PlayAction(Action):
    def __init__(self, card):
        self.card = card
    def perform(self, player):
        payed_cost = False
        # Do all the stuff in rule 409.1
        numabilities = len(self.card.current_role.abilities)
        if numabilities == 0: return False

        success = True
        if numabilities > 1:
            # Replace the representation of a with the text from the card
            abilities = [(str(a), i) for i, a in enumerate(self.card.current_role.abilities) if not a.is_limited()]
            # XXX Must use the index of the ability, since we can't pickle abilities for network games
            if not abilities: return False
            index = player.getSelection(abilities, 1, required=False,prompt="%s: Select ability"%self.card)
            if index is False: return False
            ability = self.card.current_role.abilities[index]
        else:
            ability = self.card.current_role.abilities[0]
            if ability.is_limited(): return False

        # Now make a copy of the ability to populate it
        ability = ability.copy()

        # Do all the stuff in rule 409.1 like pick targets, pay
        # costs, etc
        success =  ability.compute_cost()
        if success and ability.needs_target(): success = ability.get_target()
        if success: success = ability.pay_cost()

        if success:
            #print "%s plays (%s) of %s"%(player.name,ability,self.card)
            if ability.needs_stack():
                # Add it to the stack
                self.card.current_role.onstack = True
                player.stack.push(ability)
                player.send(PlayActionEvent(), card=self.card, ability=ability)
            else:
                ability.played()
                ability.do_resolve()
                player.send(PlayActionEvent(), card=self.card, ability=ability)
                del ability
        # if not successful, invalidate casting
        else:
            #print "%s: Failed playing %s - %s"%(player.name, self.card, ability)
            # Abort everything
            #XXX self.card.current_role.onstack = False
            #return costs - this is already done
            #ability.reverse_payment()
            del ability
        return success

class PlayLand(PlayAction):
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

class PlayAbility(PlayAction):
    # The function of this is identical to PlaySpell - the only reason I need it
    # is to differentiate the times when only Instants/Abilities can be played
    # XXX There might be a better way to structure this - probably when coding Flash (502.57)
    def perform(self, player):
        success = super(PlayAbility,self).perform(player)
        if success: player.send(PlayAbilityEvent(), card=self.card)
        return success

class PlayInstant(PlayAction):
    # The function of this is identical to PlaySpell - the only reason I need it
    # is to differentiate the times when only Instants/Abilities can be played
    # XXX There might be a better way to structure this - probably when coding Flash (502.57)
    def perform(self, player):
        success = super(PlayInstant,self).perform(player)
        if success: player.send(PlaySpellEvent(), card=self.card)
        return success

class PlaySpell(PlayAction):
    # The function of this is identical to PlaySpell - the only reason I need it
    # is to differentiate the times when only Instants/Abilities can be played
    # XXX There might be a better way to structure this
    def perform(self, player):
        success = super(PlaySpell,self).perform(player)
        if success: player.send(PlaySpellEvent(), card=self.card)
        return success

class ActivateForMana(Action):
    def __init__(self, card):
        self.card = card
    def perform(self, player):
        import Ability
        # Check if the card can be provide mana
        mana_abilities = []
        for ability in self.card.current_role.abilities:
            if ability.is_mana_ability(): # and ability.cost == "0": 
                mana_abilities.append(ability)

        if mana_abilities:
            if len(mana_abilities) > 1:
                # XXX Must use the index of the ability, since we can't pickle abilities for network games
                abilities = [(str(a), i) for i, a in enumerate(mana_abilities)]
                index = player.getSelection(abilities, 1, required=False, prompt="%s - Mana abilities"%self.card)
                if index is False: return False
                ability = mana_abilities[index]
                # Ask which mana ability to use
            else: ability = mana_abilities[0]
            if not ability: return False

            ability = ability.copy()
            # Does it have to be free mana? How about mana that requires a sacrifice
            success =  ability.compute_cost()
            if success and ability.needs_target(): success = ability.get_target()
            if success: success = ability.pay_cost()

            if success:
                #print "%s activates (%s) of %s"%(player.name,ability,self.card)
                ability.played()
                ability.do_resolve()
            del ability
            return success
        else: return False

