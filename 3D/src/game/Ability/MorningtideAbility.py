from game.GameEvent import UpkeepStepEvent, EndTurnEvent
from game.Cost import ManaCost, DiscardCost, ProwlCost
from game.Match import isCreature, SelfMatch
from Ability import Stackless, StacklessAbility
from CastingAbility import CastPermanentSpell
from ActivatedAbility import ActivatedAbility
from TriggeredAbility import TriggeredAbility
from Target import Target
from Trigger import Trigger, EnterTrigger, PlayerTrigger, ReceiveCombatDamageTrigger
from Effect import AddPowerToughnessCounter, NullEffect

class Reinforce(ActivatedAbility):
    def __init__(self, card, cost="0", number=1):
        from Target import Target
        from Effect import AddPowerToughnessCounter
        self.reinforce_cost = cost
        cost = ManaCost(cost) + DiscardCost()
        self.number = number
        super(Reinforce, self).__init__(card, cost=cost, target=Target(target_types=isCreature), effects=AddPowerToughnessCounter(number=number), zone="hand")
    def __str__(self):
        return "%s: Reinforce %d"%(self.reinforce_cost, self.number)

def reinforce(out_play_role, cost="0", number=1):
    out_play_role.abilities.append(Reinforce(out_play_role.card, cost, number))

class StacklessActivatedAbility(Stackless, ActivatedAbility): pass
class KinshipAbility(StacklessActivatedAbility):
    def __init__(self, card, cost="0", target=Target(targeting="controller"), effects=[]):
        super(KinshipAbility, self).__init__(card, cost=cost, target=target, effects=effects)
    def resolve(self):
        success = False
        controller = self.card.controller
        topcard = controller.library.top()
        msg = "Top card of library"
        controller.revealCard(topcard, title=msg, prompt=msg)
        if self.card.subtypes.intersects(topcard.subtypes):
            reveal = controller.getIntention("Reveal card to %s?"%controller.opponent, "reveal card to %s?"%controller.opponent)
            if reveal:
                controller.opponent.revealCard(topcard, title=msg, prompt=msg)
                success = super(KinshipAbility,self).resolve()
        return success
    def __str__(self):
        return "Kinship: %s"%super(KinshipAbility,self).__str__()

def kinship(subrole, card, kinship_ability):
    kinship = TriggeredAbility(card, trigger = PlayerTrigger(event=UpkeepStepEvent()),
            match_condition = lambda player, card=card: player == card.controller,
            ability=kinship_ability)

    subrole.triggered_abilities.append(kinship)
    def remove_kinship():
        kinship.leavingPlay()
        subrole.triggered_abilities.remove(kinship)
    return remove_kinship

def prowl(subrole, card, cost="0", ability=None):
    # You may play this for its prowl cost if you dealt combat damage to a player this turn with a [card subtypes]
    prowl_cost = ProwlCost(orig_cost=card.cost, prowl_cost=cost)
    if len(card.out_play_role.abilities) == 0:
        card.out_play_role.abilities = [CastPermanentSpell(card, prowl_cost)]
    else:
        card.out_play_role.abilities[0].cost = prowl_cost
    if ability:
        prowl = TriggeredAbility(card, trigger = EnterTrigger("play"),
                match_condition=SelfMatch(card, lambda card: prowl_cost.prowled),
                ability=ability)
        subrole.triggered_abilities.append(prowl)
    def can_prowl(card, target, prowl_cost=prowl_cost):
        prowl_cost.can_prowl = True
        card.register(lambda p=prowl_cost: setattr(p, "can_prowl", False), event=EndTurnEvent(), weak=False, expiry=1)
    detect_prowl = TriggeredAbility(card, trigger = ReceiveCombatDamageTrigger(),
            match_condition = lambda sender,source,amount: sender != source.controller and source.subtypes.intersects(card.subtypes),
            ability=StacklessAbility(card, effects=NullEffect(can_prowl)),
            always_on=True)
    subrole.triggered_abilities.append(detect_prowl)
