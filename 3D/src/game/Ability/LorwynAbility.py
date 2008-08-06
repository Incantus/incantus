from Ability import Ability, Stackless
from ActivatedAbility import ActivatedAbility
from CastingAbility import CastPermanentSpell
from Effect import *
from Target import Target, SpecialTarget, TriggeredTarget
from TriggeredAbility import TriggeredAbility
from Trigger import EnterTrigger, LeavingTrigger, DealDamageTrigger
from Limit import Unlimited
from game.Match import SelfMatch, isLandType, isCreature
from game.Cost import EvokeCost, ManaCost, TapCost, MultipleCosts
from game.characteristics import all_characteristics
from game.GameEvent import ClashEvent

class ClashAbility(Stackless, ActivatedAbility):
    def __init__(self, card, cost="0", target=Target(targeting="you"),effects=[]):
        super(ClashAbility, self).__init__(card, cost=cost, target=target, effects=effects)
    def resolve(self):
        success = False
        controller = self.card.controller
        opponent = controller.opponent
        clashing_cards = [controller.library.top(), opponent.library.top()]
        converted_costs = []
        for c in clashing_cards: converted_costs.append(c.cost.converted_cost())
        winners = []
        if converted_costs[0] > converted_costs[1]:
            success = True
            msg = "%s wins the clash!"%controller
            winners.append(controller)
        elif converted_costs[1] > converted_costs[0]:
            success = False
            msg = "%s wins the clash!"%opponent
            winners.append(opponent)
        else:
            success = False
            msg = "No one wins the clash!"
        card.send(ClashEvent(), winners=winners)

        controller.revealCard(clashing_cards, msgs=[controller.name, opponent.name], title=msg, prompt=msg)
        opponent.revealCard(clashing_cards[::-1], msgs=[opponent.name, controller.name], title=msg, prompt=msg)

        for player, card in zip([controller, opponent], clashing_cards):
            move_to_bottom = player.getIntention("Move %s to the bottom of your library?"%card, "move %s to the bottom of your library?"%card)
            if move_to_bottom:
                #print "%s moved %s to bottom of library"%(player, card)
                card.move_to(player.library, position=0)

        if success: success = super(ClashAbility,self).resolve()
        return success
    def __str__(self):
        return "Clash with opponent"

def clash(card, clash_ability):
    clash = TriggeredAbility(card, trigger = EnterTrigger("play"),
            match_condition=SelfMatch(card),
            ability=clash_ability)

    return card.abilities.add(clash)

# XXX This should really set up a delayed trigger
# XXX Champion is broken because it won't let you escape the selection
def champion(card, role=isPermanent, subtypes=None):
    if subtypes == None:
        subtypes = card.subtypes
        msg = "Champion %s"%str(subtypes)
    elif type(subtypes) == str:
        subtypes = characteristic(subtypes)
        msg = "Champion %s"%subtypes
    else:
        subtypes = all_characteristics()
        msg = "Champion %s"%role
    msg += " or sacrifice (Esc)"
    card.championed = None
    # XXX The function should set up the delayed trigger
    champion = TriggeredAbility(card, trigger = EnterTrigger("play"),
            match_condition=SelfMatch(card),
            ability = Ability(card,
                effects=DoOr(MoveCards(from_zone="play", to_zone="removed", card_types=role.with_condition(lambda p: not p == card and p.controller == card.controller and p.subtypes.intersects(subtypes)), func=lambda c: setattr(card, "championed", c), required=False, prompt=msg), failed=SacrificeSelf())))

    champion_return = TriggeredAbility(card, trigger = LeavingTrigger("play"),
            match_condition=SelfMatch(card, lambda c: c.championed and c.championed.zone != None),
            ability=Ability(card, target=SpecialTarget(targeting= lambda: card.championed and setattr(card, "championed", None)),
                effects=ChangeZone(from_zone="removed", to_zone="play")))
    return card.abilities.add([champion,champion_return])

def evoke(card, cost):
    evoke_cost = EvokeCost(orig_cost=card.cost, evoke_cost=cost)
    card.play_spell.cost = evoke_cost
    evoke = TriggeredAbility(card, trigger = EnterTrigger("play"),
            match_condition=SelfMatch(card, lambda x: evoke_cost.evoked),
            ability=Ability(card, target=Target(targeting="self"),
                effects=[SacrificeSelf(), NullEffect(lambda c, t: evoke_cost.reset())]))
    card.abilities.add(evoke)

def hideaway(card, cost="0", limit=None):
    if limit==None: limit=Unlimited(card)
    card.in_play_role.tapped = True
    hidden = MoveCards(from_zone="library", to_zone="removed", return_position="bottom", number=1, subset=4, required=True, func = lambda c: None) #XXX c.faceDown())
    hideaway = TriggeredAbility(card, trigger = EnterTrigger("play"),
            match_condition=SelfMatch(card),
            ability=Ability(card, target=Target(targeting="you"), effects=hidden))

    return_hidden = Ability(card, cost,
            target=SpecialTarget(targeting=lambda: hidden.cardlist[0]),
            effects=YouMay(PlayCard(cost="0")),
            limit=limit)

    return card.abilities.add([hideaway, return_hidden])


# XXX Deathtouch is broken for multiple blockers - since the same trigger object is shared
def deathtouch(card):
    card.keywords.add("deathtouch")
    trigger = DealDamageTrigger(sender=card)
    deathtouch = TriggeredAbility(card, trigger = trigger,
            match_condition = lambda sender, to: isCreature(to),
            ability = Ability(card, target=TriggeredTarget(trigger, 'to'),
                effects=Destroy())) 
    remove = card.abilities.add(deathtouch)
    def remove_deathtouch():
        card.keywords.remove("deathtouch")
        remove()
    return remove_deathtouch

#####################################################################

# These keyword abilities change a characteristic of the card itself

def changeling(card):
    card.keywords.add("changeling")
    remove = ModifySubtype(subtype=all_characteristics(), expire=False)(card, card)
    def remove_changeling():
        card.keywords.remove("changeling")
        remove()
    return remove_changeling
