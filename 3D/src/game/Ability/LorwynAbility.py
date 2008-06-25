from Ability import Ability, Stackless, PostponeTargeting
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
            msg = "Noone wins the clash!"
        card.send(ClashEvent(), winners=winners)

        controller.revealCard(clashing_cards, msgs=[controller.name, opponent.name], title=msg, prompt=msg)
        opponent.revealCard(clashing_cards[::-1], msgs=[opponent.name, controller.name], title=msg, prompt=msg)

        for player, card in zip([controller, opponent], clashing_cards):
            move_to_bottom = player.getIntention("Move %s to the bottom of your library?"%card, "move %s to the bottom of your library?"%card)
            if move_to_bottom:
                #print "%s moved %s to bottom of library"%(player, card)
                player.library.move_card(card, player.library, position=0)

        if success: success = super(ClashAbility,self).resolve()
        return success
    def __str__(self):
        return "Clash with opponent"

def clash(subrole, card, clash_ability):
    clash = TriggeredAbility(card, trigger = EnterTrigger("play"),
            match_condition=SelfMatch(card),
            ability=clash_ability)

    subrole.triggered_abilities.append(clash)
    def remove_clash():
        clash.leavingPlay()
        subrole.triggered_abilities.remove(clash)
    return remove_clash


# XXX This should really set up a delayed trigger
# Also, the postponed ability is needed because there is no way to save which card was selected
# XXX Champion is broken
class PostponedAbility(PostponeTargeting, Ability): pass
def champion(subrole, card, role=isPermanent, subtypes=None):
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
    championed = Target(target_types=role.with_condition(lambda p: not p == card and p.controller == card.controller and p.subtypes.intersects(subtypes)), msg=msg)
    champion = TriggeredAbility(card, trigger = EnterTrigger("play"),
            match_condition=SelfMatch(card),
            ability = PostponedAbility(card,
                target=championed,
                effects=DoOr(ChangeZone(from_zone="play", to_zone="removed"), failed=SacrificeSelf()),
                copy_targets=False))
    champion_return = TriggeredAbility(card, trigger = LeavingTrigger("play"),
            match_condition=SelfMatch(card, lambda x: championed.target and championed.target.zone != None),
            ability=Ability(card, target=SpecialTarget(targeting= lambda: championed.target),
                effects=ChangeZone(from_zone="removed", to_zone="play")))
    subrole.triggered_abilities.extend([champion,champion_return])
    def remove_champion():
        champion.leavingPlay()
        champion_return.leavingPlay()
        subrole.triggered_abilities.remove(champion)
        subrole.triggered_abilities.remove(champion_return)
    return remove_champion

def evoke(subrole, card, cost):
    evoke_cost = EvokeCost(orig_cost=card.cost, evoke_cost=cost)
    if len(card.out_play_role.abilities) == 0:
        card.out_play_role.abilities = [CastPermanentSpell(card, evoke_cost)]
    else:
        card.out_play_role.abilities[0].cost = evoke_cost
    evoke = TriggeredAbility(card, trigger = EnterTrigger("play"),
            match_condition=SelfMatch(card, lambda x: evoke_cost.evoked),
            ability=Ability(card, target=Target(targeting="self"),
                effects=[SacrificeSelf(), NullEffect(lambda c, t: evoke_cost.reset())]))
    subrole.triggered_abilities.append(evoke)

def hideaway(subrole, card, cost="0", limit=None):
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

    subrole.triggered_abilities.append(hideaway)
    subrole.abilities.append(return_hidden)

    def remove_hideaway():
        hideaway.leavingPlay()
        subrole.triggered_abilities.remove(hideaway)
        subrole.abilities.remove(return_hidden)
    return remove_hideaway


# XXX Deathtouch is broken for multiple blockers - since the same trigger object is shared
def deathtouch(subrole, card=None):
    subrole.keywords.add("deathtouch")
    if not card:
        card = subrole.card
        in_play = False
    else: in_play=True
    trigger = DealDamageTrigger(sender=card)
    deathtouch = TriggeredAbility(card, trigger = trigger,
            match_condition = lambda sender, to: isCreature(to),
            ability = Ability(card, target=TriggeredTarget(trigger, 'to'),
                effects=Destroy())) 
    subrole.triggered_abilities.append(deathtouch)
    if in_play: deathtouch.enteringPlay()
    def remove_deathtouch():
        subrole.keywords.remove("deathtouch")
        deathtouch.leavingPlay()
        subrole.triggered_abilities.remove(deathtouch)
    return remove_deathtouch

#####################################################################

# These keyword abilities change a characteristic of the card itself

def changeling(subrole, card):
    # This looks weird, but covers Instants and sorceries that have changeling
    # XXX Maybe they should have keywords too?
    if hasattr(subrole, "keywords"): subrole.keywords.add("changeling")
    old_subtypes = card.subtypes
    card.subtypes = all_characteristics()
    def remove_changeling():
        card.subtypes = old_subtypes
        subrole.keywords.remove("changeling")
    return remove_changeling
