from Target import NoTarget
from Trigger import Trigger, EnterTrigger, sender_match, source_match
from engine.GameEvent import AttackerDeclaredEvent
from TriggeredAbility import TriggeredAbility
from engine.symbols import Black, Germ, Creature

def battle_cry():
    def effects(controller, source):
        yield NoTarget()
        for creature in controller.battlefield.get(isCreature):
            if creature == source: continue
            until_end_of_turn(creature.augment_power_toughness(1, 1))
        yield
    return TriggeredAbility(Trigger(AttackerDeclaredEvent(), sender_match), effects, zone="battlefield", keyword='battle cry')

def living_weapon():
    def effects(controller, source):
        yield NoTarget()
	for token in controller.play_tokens({'P/T': (0,0), 'color': Black, 'subtypes': Germ, 'types': Creature}):
            yield
            source.attach(token)
        yield
    return TriggeredAbility(EnterTrigger("battlefield", source_match), effects, zone="battlefield", keyword='living weapon')
