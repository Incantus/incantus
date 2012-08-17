from Limit import sorcery_limit
from ActivatedAbility import ActivatedAbility
from Target import NoTarget
from Cost import DiscardCost
from engine.Match import isCard

__all__ = ["transmute"]

def transmute(cost):
    '''502.48a Transmute [cost] means [Cost], Discard this card: Search your library for a card with the same converted mana cost as the discarded card, reveal that card, and put it into your hand. Then shuffle your library. Play this ability only any time you could play a sorcery.
       502.48b Although the transmute ability is playable only if the card is in a player?s hand, it continues to exist while the object is on the battlefield and in all other zones. Therefore objects with transmute will be affected by effects that depend on objects having one or more activated abilities.'''
    def effects(controller, source):
        yield cost + DiscardCost()
        target = yield NoTarget()
        CMC = source.converted_mana_cost
        for card in controller.choose_from_zone(number=1, cardtype=isCard.with_condition(lambda c: c.converted_mana_cost == CMC), zone="library", action="card with converted mana cost %s to put into your hand"%CMC, required=False):
            controller.reveal_cards((card,))
            yield
            card.move_to("hand")
        yield
    return ActivatedAbility(effects, limit=sorcery_limit, zone="hand", txt="Transmute %s"%str(cost), keyword="transmute")
