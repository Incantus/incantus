from game.Match import isCard
from game.GameEvent import BlockerDeclaredEvent, AttackerBlockedEvent
from game.LazyInt import LazyInt
from TriggeredAbility import TriggeredAbility, sender_match
from Trigger import Trigger, EnterFromTrigger
from Target import NoTarget
from EffectsUtilities import until_end_of_turn

def soulshift(n):
    def effects(source):
        target = yield Target(isCard.with_condition(lambda c: c.subtypes == "Spirit" and c.cost
.converted_mana_cost() <= 3), zone = "graveyard", player = "you")
        # Code for effect
        if controller.you_may("return target to your hand"):
            target.move_to("hand")
        yield
    return TriggeredAbility(EnterFromTrigger("graveyard", "play", player="you"),
            condition=condition,
            effects=effects,
            txt="Soulshift %s"%n)

def bushido(value):
    if callable(value): value = LazyInt(value)
    txt="Bushido %d"%value
    if isinstance(value, LazyInt): txt="Bushido X"
    def effects(controller, source):
        yield NoTarget()
        temp = value if not isinstance(value, LazyInt) else value.value()
        until_end_of_turn(source.augment_power_toughness(temp, temp))
        yield
    ability = TriggeredAbility([Trigger(BlockerDeclaredEvent()), Trigger(AttackerBlockedEvent())], sender_match, effects, zone="play", txt=txt, keyword='bushido')
    ability.bushido_value = value
    return ability
