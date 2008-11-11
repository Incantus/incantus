from game.Match import isCreature, isPermanent
from game.GameEvent import ClashEvent
from TriggeredAbility import TriggeredAbility
from StaticAbility import CardStaticAbility, CiPAbility
from PermanentAbility import enter_play_tapped, CiP
from Target import NoTarget
from Trigger import EnterTrigger, LeaveTrigger, DealDamageToTrigger
from Subtypes import all_creatures
from EffectsUtilities import keyword_action

# This should be called from within an effects function
@keyword_action
def clash(controller, opponent=None):
    winner = None
    if not opponent: opponent = controller.choose_opponent()
    cards = (controller.library.top(), opponent.library.top())
    controller_cmc, opponent_cmc = [card.cost.converted_mana_cost() for card in cards]
    if controller_cmc > opponent_cmc:
        winner = controller
        msg = "%s wins the clash!"%winner
    elif opponent_cmc > controller_cmc:
        winner = opponent
        msg = "%s wins the clash!"%winner
    else:
        msg = "No one wins the clash"

    controller.revealCard(cards, msgs=[controller.name, opponent.name], title=msg, prompt=msg)

    for player, card in zip((controller, opponent), cards):
        player.send(ClashEvent(), winner=winner)
        msg = "Move %s to the bottom of your library?"%card
        if player.getIntention(msg, msg):
            card.move_to(card.owner.library, position="bottom")
    return winner == controller

def champion(types=None, subtypes=None):
    if types:
        if type(types) == tuple: types = set(types)
        else: types = set((types,))
    if subtypes:
        if type(subtypes) == tuple: subtypes = set(subtypes)
        else: subtypes = set((subtypes,))

    if types and subtypes:
        cardtype = isPermanent.with_condition(lambda p: p.types.intersects(types) and p.subtypes.intersects(subtypes))
    elif types:
        cardtype = isPermanent.with_condition(lambda p: p.types.intersects(types))
    elif subtypes:
        cardtype = isPermanent.with_condition(lambda p: p.subtypes.intersects(subtypes))
    def champion1(controller, source):
        source.championed = None
        yield NoTarget()
        # Code for effect
        cards = controller.choose_from_zone(cardtype=cardtype.with_condition(lambda p: not p == source), required=False, action="champion")
        if cards:
            card = cards[0]
            source.championed = card.move_to(card.owner.removed)
        else:
            controller.sacrifice(source)
        yield
    champion_send = TriggeredAbility(EnterTrigger("play"),
            condition = lambda source, card: source == card,
            effects = champion1,
            txt = "Champion %s"%cardtype)

    def champion2(controller, source):
        target = yield NoTarget()
        # Code for effect
        removed = source.championed
        if removed: removed.move_to(removed.owner.play)
        yield
    champion_return = TriggeredAbility(LeaveTrigger("play"),
            condition = lambda source, card: source == card,
            effects = champion2)
    return champion_send, champion_return

def hideaway(cost="0"):
    def effects(source):
        yield CiP(source, enter_play_tapped, txt="%s comes into play tapped"%source)
    cip = CiPAbility(effects, txt="~ comes into play tapped")

    def hideaway_effect(controller, source):
        source.hidden = None
        yield NoTarget()
        topcards = controller.library.top(4)
        card = controller.getCardSelection(topcards, number=1, required=True, prompt="Choose 1 card to hideaway")[0]
        source.hidden = card
        card.move_to(controller.removed)
        card.faceDown()
        topcards.remove(card)
        for card in topcards: card.move_to(controller.library, position="bottom")
        yield
    hideaway = TriggeredAbility(EnterTrigger("play"),
            condition = lambda source, card: source == card,
            effects = hideaway_effect)
    return cip, hideaway

def deathtouch():
    def condition(source, to):
        return isCreature(to)
    def effects(controller, source, to):
        yield NoTarget()
        to.destroy()
        yield

    return TriggeredAbility(DealDamageToTrigger(sender="source"),
        condition = condition,
        effects = effects,
        keyword = "deathtouch")

def changeling():
    def effects(card):
        yield card.subtypes.add_all(all_creatures, "Every creature type")
    return CardStaticAbility(effects=effects, zone="all", keyword="changeling")

#def evoke(card, cost):
#    evoke_cost = EvokeCost(orig_cost=card.cost, evoke_cost=cost)
#    card.play_spell.cost = evoke_cost
#    evoke = TriggeredAbility(card, trigger = EnterTrigger("play"),
#            match_condition=SelfMatch(card, lambda x: evoke_cost.evoked),
#            ability=Ability(card, target=Target(targeting="self"),
#                effects=[SacrificeSelf(), NullEffect(lambda c, t: evoke_cost.reset())]))
#    card.abilities.add(evoke)

