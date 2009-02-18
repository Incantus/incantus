from game.GameEvent import UpkeepStepEvent
from game.Cost import ManaCost, DiscardCost
from game.Match import isCreature
from Ability import Stackless
from ActivatedAbility import ActivatedAbility
from TriggeredAbility import TriggeredAbility
from Target import Target
from Trigger import PlayerTrigger
from Effect import AddPowerToughnessCounter

class Reinforce(ActivatedAbility):
    def __init__(self, card, cost="0", number=1):
        from Target import Target
        from Effect import AddPowerToughnessCounter
        self.reinforce_cost = cost
        cost = ManaCost(cost) + DiscardCost()
        self.number = number
        super(Reinforce, self).__init__(card, cost=cost, target=Target(target_types=isCreature), effects=AddPowerToughnessCounter(1,1,number=number,expire=False), zone="hand")
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
        topcard = controller.library[-1]
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
