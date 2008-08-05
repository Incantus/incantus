from Target import Target
from game.Match import isLandType
from game.Cost import DiscardCost

def retrace(out_play_role):
    card = out_play_role.card
    #card.keywords.add("retrace")

    main_spell = out_play_role.abilities[0]
    cost = main_spell.cost + DiscardCost(cardtype=isLandType)

    retrace = main_spell.__class__(out_play_role.card, cost, target=main_spell.targets, effects=main_spell.effects, copy_targets=main_spell.copy_targets, limit=main_spell.limit, zone="graveyard")

    out_play_role.abilities.append(retrace)

    def remove():
    #    card.keywords.remove("persist")
        out_play_role.abilities.remove(retrace)
    return remove

