from engine.symbols import Spirit
from engine.Match import isCard
from engine.GameEvent import BlockerDeclaredEvent, AttackerBlockedEvent
from TriggeredAbility import TriggeredAbility
from Trigger import Trigger, EnterFromTrigger, sender_match, source_match
from Target import Target, NoTarget
from EffectsUtilities import until_end_of_turn

__all__ = ["soulshift", "bushido"]

def soulshift(n):
    def effects(controller, source):
        target = yield Target(isCard.with_condition(lambda c: c.subtypes == Spirit and c.converted_mana_cost <= n), zone = "graveyard", player = "you")
        # Code for effect
        if controller.you_may("return target to your hand"):
            target.move_to("hand")
        yield
    return TriggeredAbility(EnterFromTrigger("graveyard", "battlefield", source_match, player="you"),
            effects=effects,
            txt="Soulshift %s"%n)

def bushido(value):
    if isinstance(value, int): txt="Bushido %d"%value
    else: txt = "Bushido X"
    def effects(controller, source):
        yield NoTarget()
        value = int(value)
        until_end_of_turn(source.augment_power_toughness(value, value))
        yield
    ability = TriggeredAbility([Trigger(BlockerDeclaredEvent(), sender_match), Trigger(AttackerBlockedEvent(), sender_match)], effects, txt=txt, keyword='bushido')
    ability.bushido_value = value
    return ability
