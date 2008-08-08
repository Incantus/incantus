from GameObjects import MtGObject
from Zone import CardStack
from GameEvent import AbilityPlacedOnStack, AbilityRemovedFromStack

class Stack(MtGObject):
    def __init__(self, game):
        self.pending_triggered = []
        self.abilities = []
        self.game = game
        self.card_stack = CardStack()
    def add_triggered(self, ability):
        # XXX This is hacky, and is needed for triggered abilities where the target depends on the trigger
        # Since the trigger is a single object, it will have different arguments everytime it triggers
        # so the target will only reference the most recent one. I need to find a better way to bind things together
        for target in ability.targets:
            if hasattr(target, "triggered"): target.get(ability.card)
        self.pending_triggered.append(ability) 
    def process_triggered(self):
        # Check if there are any triggered abilities waiting
        if len(self.pending_triggered) > 0:
            # group all triggered abilities by player
            triggered_sets = dict([(player, []) for player in self.game.players])
            for ability in self.pending_triggered:
                triggered_sets[ability.controller].append(ability)
            # Now ask the player to order them if there are more than one
            for player in self.game.players:
                triggered = triggered_sets[player]
                if len(triggered) > 1:
                    triggered = player.getSelection(triggered, len(triggered), prompt="Drag to reorder triggered abilities(Top ability resolves first)")
                # Now reorder
                for ability in triggered: self.announce(ability)
            self.pending_triggered[:] = []
            return True
        else: return False
    def put_card(self, card):
        card.move_to(self.card_stack)
    def push(self, ability):
        self.abilities.append(ability)
        self.send(AbilityPlacedOnStack(), ability=ability)
    def resolve(self):
        ability = self.abilities.pop()
        ability.resolve()
        self.send(AbilityRemovedFromStack(), ability=ability)
    def counter(self, ability):
        self.abilities.remove(ability)
        ability.countered()
        self.send(AbilityRemovedFromStack(), ability=ability)
    def empty(self): return len(self.abilities) == 0
