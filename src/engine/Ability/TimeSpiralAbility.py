from Cost import ManaCost
from StaticAbility import CardStaticAbility
from Trigger import Trigger, PhaseTrigger, source_match, sender_match
from TriggeredAbility import TriggeredAbility
from Target import NoTarget
from engine.GameEvent import UpkeepStepEvent, CounterRemovedEvent
from engine.CardRoles import NonBattlefieldRole
from ActivatedAbility import ActivatedAbility

__all__ = ['suspended', 'suspend', 'split_second']

# A card is "suspended" if it's in the exile zone, has suspend, and has a time counter on it.
def suspended(card):
    # XXX - Doesn't actually work since keywords aren't quite implemented right
    #return str(card.zone) == "exile" and "suspend" in card.abilities and card.num_counters("time") > 0
    return str(card.zone) == "exile" and card.num_counters("time") > 0

def suspend(number, cost):
    if isinstance(cost, str): cost = ManaCost(cost)
    # 702.59a. Suspend is a keyword that represents three abilities. The first is a static ability that functions while the card with suspend is in a player's hand. The second and third are triggered abilities that function in the exile zone. "Suspend N--[cost]" means "If you could begin to cast this card by putting it onto the stack from your hand, you may pay [cost] and exile it with N time counters on it. This action doesn't use the stack," and "At the beginning of your upkeep, if this card is suspended, remove a time counter from it," and "When the last time counter is removed from this card, if it's exiled, play it without paying its mana cost if able. If you can't, it remains exiled. If you cast a creature spell this way, it gains haste until you lose control of the spell or the permanent it becomes."
    def check_playability_and_exile(source, player):
        '''Suspend'''
        if player == source.controller and source.playable() and player.you_may_pay(source, cost):
            newsource = source.move_to("exile")
            if newsource and not newsource == source:
                newsource.add_counters("time", number=number)
            return True
        return False
    def static_effects(source):
        check_playability_and_exile.__doc__ = "Suspend %s for %s" % (source.name, cost)
        yield source.setup_special_action(check_playability_and_exile)
    static = CardStaticAbility(effects=static_effects, zone="hand", keyword="suspend")

    def first_trigger_effects(controller, source):
        target = yield NoTarget()
        if suspended(source):
            source.remove_counters("time")
        yield
    first_trigger = TriggeredAbility(PhaseTrigger(UpkeepStepEvent(), lambda source, player: player == source.controller and suspended(source)), effects=first_trigger_effects, txt="At the beginning of your upkeep, if this card is suspended, remove a time counter from it.", zone="exile")

    def second_trigger_effects(controller, source):
        target = yield NoTarget()
        if str(source.zone) == "exile":
            source.play_without_mana_cost(controller)
            # XXX - If you cast a creature spell this way, it gains haste until you lose control of the spell or permanent it becomes.
        yield
    second_trigger = TriggeredAbility(Trigger(CounterRemovedEvent(), lambda source, sender, counter: source == sender and counter.ctype == "time" and source.num_counters("time") == 0 and str(source.zone) == "exile"), effects=second_trigger_effects, txt="When the last time counter is removed from this card, if it's exiled, play it without paying its mana cost if able. If you can't, it remains exiled. If you cast a creature spell this way, it gains haste until you lose control of the spell or the permanent it becomes.", zone="exile")

    return static, first_trigger, second_trigger

def split_second():
    def effects(source):
        yield (override(NonBattlefieldRole, "_playable_other_restrictions", lambda self: True),
              override(ActivatedAbility, "playable", lambda self: hasattr(self, "mana_ability")))
    return CardStaticAbility(effects=effects, zone="stack", keyword="split second")
