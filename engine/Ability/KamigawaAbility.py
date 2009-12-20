from engine.symbols import Spirit
from engine.Match import isCard
from engine.GameEvent import BlockerDeclaredEvent, AttackerBlockedEvent
from TriggeredAbility import TriggeredAbility, sender_match, source_match
from Trigger import Trigger, EnterFromTrigger
from Target import Target, NoTarget
from EffectsUtilities import until_end_of_turn

def soulshift(n):
    def effects(controller, source):
        target = yield Target(isCard.with_condition(lambda c: c.subtypes == Spirit and c.converted_mana_cost <= n), zone = "graveyard", player = "you")
        # Code for effect
        if controller.you_may("return target to your hand"):
            target.move_to("hand")
        yield
    return TriggeredAbility(EnterFromTrigger("graveyard", "play", player="you"),
            condition=source_match,
            effects=effects,
            txt="Soulshift %s"%n)

def bushido(value):
    if type(value) == int: txt="Bushido %d"%value
    else: txt = "Bushido X"
    def effects(controller, source):
        yield NoTarget()
        value = int(value)
        until_end_of_turn(source.augment_power_toughness(value, value))
        yield
    ability = TriggeredAbility([Trigger(BlockerDeclaredEvent()), Trigger(AttackerBlockedEvent())], sender_match, effects, zone="play", txt=txt, keyword='bushido')
    ability.bushido_value = value
    return ability
