from random import shuffle
from engine.symbols import Land
from engine.GameEvent import DeclareAttackersEvent, InvalidTargetEvent, EndTurnStepEvent, SpellPlayedEvent
from engine.Match import isCreature
from ActivatedAbility import ActivatedAbility
from TriggeredAbility import TriggeredAbility
from CiPAbility import CiP, CiPAbility
from CreatureAbility import haste
from EffectsUtilities import until_end_of_turn, do_replace, no_condition
from Target import NoTarget
from Trigger import Trigger, PhaseTrigger, SpellPlayedTrigger
from Counters import PowerToughnessCounter
from Limit import sorcery_limit

__all__ = ["exalted", "devour", "unearth", "cascade"]

def exalted():
    def condition(source, sender, attackers):
        return sender.active_player == source.controller and len(attackers) == 1
    def effects(controller, source, attackers):
        yield NoTarget()
        until_end_of_turn(attackers[0].augment_power_toughness(1, 1))
        yield
    return TriggeredAbility(Trigger(DeclareAttackersEvent(), condition), effects, zone="battlefield", keyword='exalted')

def devour(value):
    txt = "Devour %d"%value
    def enterBattlefieldWith(source):
        cards = set()
        if source.controller.you_may("Sacrifice creatures to %s"%source.name):
            i = 0
            num_creatures = len(source.controller.battlefield.get(isCreature))
            while i < num_creatures:
                creature = source.controller.getTarget(isCreature, zone="battlefield", from_player="you", required=False, prompt="Select any number of creatures to sacrifice: (%d selected so far)"%i)
                if creature == False: break
                elif not creature in cards:
                    cards.add(creature)
                    i += 1
                else: source.controller.send(InvalidTargetEvent(), target=creature)
            for card in cards: source.controller.sacrifice(card)
            source.devoured = cards
            if cards: source.add_counters(PowerToughnessCounter(1, 1), len(cards)*value)
    def effects(source):
        yield CiP(source, enterBattlefieldWith, txt=txt)
    return CiPAbility(effects, txt=txt, keyword="devour")

def unearth(cost):
    def effects(controller, source):
        yield cost
        yield NoTarget()
        source = source.move_to(controller.battlefield)
        yield
        source.abilities.add(haste())

        # Exile at end of turn
        @source.delayed
        def ability():
            def condition(source):
                return str(source.zone) == "battlefield"
            def effects(controller, source):
                '''Exile this from the game at end of turn'''
                yield NoTarget()
                source.move_to("exile")
                yield
            return PhaseTrigger(EndTurnStepEvent(), condition), effects

        # Exile if it leaves play
        leave_battlefield_condition = lambda self, zone, position="top": str(self.zone) == "battlefield"
        def move_to(self, zone, position="top"):
            return self.move_to("exile")
        until_end_of_turn(do_replace(source, "move_to", move_to,
            condition=leave_battlefield_condition,
            msg="%s - exile from game"%source.name))
        yield
    return ActivatedAbility(effects, limit=sorcery_limit, zone="graveyard", txt="Unearth %s"%str(cost), keyword="unearth")

def cascade():
    def condition(source, spell):
        return source == spell
    def cascade_effects(source, controller, spell):
        target = yield NoTarget()
        cmc = source.converted_mana_cost
        exiled = []
        for card in controller.library:
            exile = card.move_to("exile")
            exiled.append(exile)
            if not exile.types == Land and exile.converted_mana_cost < cmc:
                break
        yield
        if exiled:
            controller.reveal_cards(exiled)
            exile = exiled[-1]
            if controller.you_may("cast %s without paying its mana cost?"%exile):
                exiled.remove(exile)
                exile.play_without_mana_cost(controller)
            # move exiled cards back to bottom of library in random order
            if exiled: shuffle(exiled)
            for card in exiled:
                card.move_to("library", position='bottom')
                yield
        yield
    return TriggeredAbility(SpellPlayedTrigger(condition),
            effects = cascade_effects,
            zone = "stack",
            keyword = "cascade")
