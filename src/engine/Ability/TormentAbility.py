from Cost import ManaCost
from StaticAbility import CardStaticAbility
from TriggeredAbility import TriggeredAbility
from Trigger import EnterTrigger
from Target import NoTarget
from EffectsUtilities import override, replace

def madness(cost):
    if isinstance(cost, str): cost = ManaCost(cost)
    madnessed = [False]
    def madness_effects(source):
        def madness_exile(self, zone, position="top"):
            madnessed[0] = True
            return self.move_to("exile")
        def madness_discard(self, card):
            if self.you_may("exile %s with madness"%card.name):
                expire = replace(card, "move_to", madness_exile, msg="Madness - Exile %s instead of putting it into the graveyard"%card.name, condition=lambda self, zone, position="top": str(zone) == "graveyard")
                newcard = self.discard(card)
                expire()
                return newcard
            else:
                return self.discard(card)
        yield replace(source.controller, "discard", madness_discard, msg="Madness - If a player would discard this card, that player discards it, but may exile it instead of putting it into his or her graveyard.", condition=lambda self, card: card == source)
    def play_from_exile(source, controller):
        yield NoTarget()
        if controller.you_may("cast %s for %s rather than its mana cost"%(source.name, cost)):
            def modifyNewRole(self, new, zone):
                if str(zone) == "stack":
                    new.set_casting_cost(cost)
            override(source, "modifyNewRole", modifyNewRole)
            if not source._playable_other_restrictions():
                if not source.play(controller): source.move_to("graveyard")
        else:
            source.move_to("graveyard")
        yield
    return CardStaticAbility(effects=madness_effects, zone="hand"), TriggeredAbility(EnterTrigger("exile", lambda source, card: source == card and madnessed[0]), play_from_exile, zone="exile", txt="Madness %s"%cost, keyword="madness")

