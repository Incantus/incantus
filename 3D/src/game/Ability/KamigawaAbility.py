from game.GameEvent import BlockerDeclaredEvent, AttackerBlockedEvent
from game.LazyInt import LazyInt
from TriggeredAbility import TriggeredAbility, sender_match
from EffectsUtilities import until_end_of_turn
from Target import NoTarget
from Trigger import Trigger

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
