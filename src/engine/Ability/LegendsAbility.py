from engine.GameEvent import AttackerBlockedEvent
from TriggeredAbility import TriggeredAbility
from Trigger import Trigger, sender_match
from Target import NoTarget

def rampage(number):
    def effects(controller, source, blockers):
        yield NoTarget()
        value = (len(blockers) - 1) * number
        until_end_of_turn(source.augment_power_toughness(number, number))
        yield
    return TriggeredAbility(Trigger(AttackerBlockedEvent(), sender_match), effects, txt='Rampage %i'%number, keyword="rampage")

