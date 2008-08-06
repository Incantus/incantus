from Target import Target
from game.Match import isLandType
from game.Cost import DiscardCost

def retrace(card):
    card.keywords.add("retrace")

    main_spell = card.play_spell
    cost = main_spell.cost + DiscardCost(cardtype=isLandType)

    retrace = main_spell.__class__(card, cost, target=main_spell.targets, effects=main_spell.effects, copy_targets=main_spell.copy_targets, limit=main_spell.limit, zone="graveyard")

    remove_ability = card.abilities.add(retrace)
    def remove():
        card.keywords.remove("retrace")
        remove_ability()
    return remove

