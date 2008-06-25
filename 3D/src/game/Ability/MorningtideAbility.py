from game.GameEvent import UpkeepStepEvent, ReceivesCombatDamageEvent
from game.Cost import ManaCost, DiscardCost, SpecialCost
from game.Match import isCreature, SelfMatch, isPlayer
from Ability import Stackless
from CastingAbility import CastPermanentSpell
from ActivatedAbility import ActivatedAbility
from TriggeredAbility import TriggeredAbility
from Target import Target
from Trigger import Trigger, EnterTrigger, PlayerTrigger
from Effect import AddPowerToughnessCounter
from MemoryVariable import MemoryVariable

class Reinforce(ActivatedAbility):
    def __init__(self, card, cost, number=1):
        from Target import Target
        from Effect import AddPowerToughnessCounter
        self.reinforce_cost = cost
        self.number = number
        if type(cost) == str: cost = ManaCost(cost)
        super(Reinforce, self).__init__(card, cost=cost+DiscardCost(), target=Target(target_types=isCreature), effects=AddPowerToughnessCounter(number=number), zone="hand")
    def __str__(self):
        return "%s: Reinforce %d"%(self.reinforce_cost, self.number)

def reinforce(out_play_role, cost, number=1):
    out_play_role.abilities.append(Reinforce(out_play_role.card, cost, number))

class KinshipAbility(Stackless, ActivatedAbility):
    def __init__(self, card, cost="0", target=Target(targeting="you"), effects=[]):
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

class ProwlVariable(MemoryVariable):
    def __init__(self, card):
        self.card = card
        self.can_prowl = False
        self.register(self.dealt_damage, event=ReceivesCombatDamageEvent())
        super(ProwlVariable, self).__init__()
    def dealt_damage(self, sender, source, amount):
        if isPlayer(sender) and not sender == self.card.controller and source.subtypes.intersects(self.card.subtypes):
            self.can_prowl = True
    def value(self): return self.can_prowl
    def reset(self): self.can_prowl = False

class ProwlCost(SpecialCost):
    def __init__(self, orig_cost, prowl_cost, can_prowl):
        if type(orig_cost) == str: orig_cost = ManaCost(orig_cost)
        if type(prowl_cost) == str: prowl_cost = ManaCost(prowl_cost)
        self.orig_cost = orig_cost
        self.prowl_cost = prowl_cost
        self.can_prowl = can_prowl
        self.reset()
    def reset(self):
        self.prowled = False
        self.cost = self.orig_cost
    def precompute(self, card, player):
        if self.can_prowl.value():
            self.prowled = player.getIntention("pay prowl cost?", "Play for prowl cost?")
            if self.prowled: self.cost = self.prowl_cost
        return super(ProwlCost, self).precompute(card, player)

def prowl(subrole, card, cost, ability=None):
    # You may play this for its prowl cost if you dealt combat damage to a player this turn with a [card subtypes]
    prowl_cost = ProwlCost(orig_cost=card.cost, prowl_cost=cost, can_prowl=ProwlVariable(card))
    card.out_play_role.abilities[0].cost = prowl_cost
    if ability:
        prowl = TriggeredAbility(card, trigger = EnterTrigger("play"),
                match_condition=SelfMatch(card, lambda card: prowl_cost.prowled),
                ability=ability)
        subrole.triggered_abilities.append(prowl)
