from engine.Player import keyword_action
from engine.Match import isCreature, isPermanent
from engine.GameEvent import ClashEvent
from engine.symbols.subtypes import all_creatures
from TriggeredAbility import TriggeredAbility
from CiPAbility import enters_battlefield_with
from StaticAbility import CardStaticAbility
from Target import NoTarget
from Trigger import EnterTrigger, LeaveTrigger, DealsDamageToTrigger, source_match
from Cost import ManaCost, SpecialCost
from EffectsUtilities import do_override

__all__ = ["champion", "hideaway", "changeling", "evoke"]

# This should be called from within an effects function
@keyword_action
def clash(controller, opponent=None):
    winner = None
    if not opponent: opponent = controller.choose_opponent()
    card0, card1 = (controller.library.top(), opponent.library.top())
    if card0: controller_cmc = card0.converted_mana_cost
    else: controller_cmc = -1
    if card1: opponent_cmc = card1.converted_mana_cost
    else: opponent_cmc = -1
    if controller_cmc > opponent_cmc:
        winner = controller
        msg = "%s wins the clash!"%winner
    elif opponent_cmc > controller_cmc:
        winner = opponent
        msg = "%s wins the clash!"%winner
    else:
        msg = "No one wins the clash"

    # XXX This is buggered
    controller.reveal_cards([card0, card1], msg)

    for player, card in zip((controller, opponent), (card0, card1)):
        player.send(ClashEvent(), winner=winner)
        if card:
            msg = "Move %s to the bottom of your library?"%card
            if player.getIntention(msg): card.move_to("library", position="bottom")
    return winner == controller

def champion(types=None, subtypes=None):
    if types:
        if isinstance(types, (list, tuple)): types = set(types)
        else: types = set((types,))
    if subtypes:
        if isinstance(subtypes, (list, tuple)): subtypes = set(subtypes)
        else: subtypes = set((subtypes,))

    if types and subtypes:
        cardtype = isPermanent.with_condition(lambda p: p.types.intersects(types) and p.subtypes.intersects(subtypes))
    elif types:
        cardtype = isPermanent.with_condition(lambda p: p.types.intersects(types))
    elif subtypes:
        cardtype = isPermanent.with_condition(lambda p: p.subtypes.intersects(subtypes))
    def champion1(controller, source):
        yield NoTarget()
        # Code for effect
        cards = controller.choose_from_zone(cardtype=cardtype.with_condition(lambda p: not p == source), required=False, action="champion")
        if cards:
            card = cards[0]
            source.championed = card.move_to("exile")
        else:
            controller.sacrifice(source)
        yield
    champion_send = TriggeredAbility(EnterTrigger("battlefield", source_match),
            effects = champion1,
            txt = "Champion a %s"%cardtype)

    def champion2(controller, source):
        target = yield NoTarget()
        # Code for effect
        exiled = source.championed if hasattr(source, "championed") else None
        if exiled: exiled.move_to("battlefield")
        yield
    champion_return = TriggeredAbility(LeaveTrigger("battlefield", source_match),
            effects = champion2)
    return champion_send, champion_return

def hideaway():
    def enter_tapped(self):
        '''Enters the battlefield tapped'''
        self.tapped = True
        self.hidden = None

    def hideaway_effect(controller, source):
        source.hidden = None
        yield NoTarget()
        topcards = controller.library.top(4)
        if topcards:
            card = controller.choose_from(topcards, number=1, prompt="Choose 1 card to hideaway")
            newcard = card.move_to("exile")
            if not newcard == card:
                newcard.faceDown()
                source.hidden = newcard
            topcards.remove(card)
            for card in topcards: card.move_to("library", position="bottom")
        yield
    hideaway = TriggeredAbility(EnterTrigger("battlefield", source_match),
                     effects = hideaway_effect, keyword="hideaway")
    return enters_battlefield_with(enter_tapped), hideaway


def changeling():
    def effects(card):
        yield card.subtypes.add_all(all_creatures, "Every creature type")
    return CardStaticAbility(effects=effects, zone="all", keyword="changeling")


class EvokeCost(SpecialCost):
    def __init__(self, cost):
        if isinstance(cost, str): cost = ManaCost(cost)
        self.cost = cost
    def pay(self, source, player):
        source.evoked = True
        super(EvokeCost, self).pay(source, player)
    def __str__(self): return super(EvokeCost, self).__str__()+" (Evoke)"
def evoke(cost):
    def effects(source):
        source.evoked = False
        yield (do_override(source, "_get_alternative_costs", lambda self: [EvokeCost(cost)]),
              do_override(source, "modifyNewRole", lambda self, new, zone: setattr(new, "evoked",self.evoked)))
    def evoke_effects(controller, source):
        '''When this permanent comes into play, if its evoke cost was paid, its controller sacrifices it.'''
        yield NoTarget()
        if source.evoked: source.controller.sacrifice(source)
        yield
    return (CardStaticAbility(effects, keyword="evoke", zone="stack"),
            TriggeredAbility(EnterTrigger("battlefield", lambda source, card: source == card and source.evoked), effects=evoke_effects))

def deathtouch_old():
    def condition(source, to):
        return isCreature(to)
    def effects(controller, source, to):
        yield NoTarget()
        to.destroy()
        yield

    return TriggeredAbility(DealsDamageToTrigger(condition, sender="source"),
        effects = effects,
        keyword = "deathtouch")

