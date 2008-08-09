from Cost import DiscardCost
from Target import Target
from game.Match import isLandType

def retrace(card):
    main_spell = card.play_spell
    cost = main_spell.cost + DiscardCost(cardtype=isLandType)

    return main_spell.__class__(card, cost, target=main_spell.targets, effects=main_spell.effects, copy_targets=main_spell.copy_targets, limit=main_spell.limit, zone="graveyard", txt="retrace")
