from engine.Util import isiterable
from engine.Match import isLandCard
from StaticAbility import CardStaticAbility
from Cost import DiscardCost
from EffectsUtilities import override

__all__ = ["retrace", "chroma"]

def retrace():
    '''Retrace appears on some instants and sorceries. It represents a static ability that functions while the card is in a player's graveyard. 'Retrace' means "You may play this card from your graveyard by discarding a land card as an additional cost to play it." '''
    def retrace_effects(card):
        def modifyNewRole(self, new, zone):
            if str(zone) == "stack":
                override(new, "_get_additional_costs", lambda self: DiscardCost(cardtype=isLandCard))
        def play_from_graveyard(self):
            if self.controller.you_may("Play %s using retrace"%self):
                override(self, "modifyNewRole", modifyNewRole)
                return True
            else: return False
        yield override(card, "_playable_zone", play_from_graveyard)
    return CardStaticAbility(effects=retrace_effects, zone="graveyard", keyword="retrace")

def chroma(selection, mana_color):
    if not isiterable(selection): selection = (selection,)
    return sum([sum([1 for symbol in obj.cost if symbol == mana_color]) for obj in selection if obj.cost.is_mana_cost()])
