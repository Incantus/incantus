from GameObjects import MtGObject
from Zone import CardStack
from GameEvent import AbilityPlacedOnStack, AbilityRemovedFromStack

class Stack(MtGObject):
    def __init__(self, game):
        self.abilities = []
        self.game = game
        self.card_stack = CardStack()
        self.pending_triggered =[]
    def add_triggered(self, ability, source):
        self.pending_triggered.append(ability)
        # XXX This is a bit ugly
        ability.source = source
    def process_triggered(self):
        # Check if there are any triggered abilities waiting
        if len(self.pending_triggered) > 0:
            # group all triggered abilities by player
            triggered_sets = dict([(player, []) for player in self.game.players])
            for ability in self.pending_triggered:
                player = ability.source.controller
                triggered_sets[player].append(ability)
            # Now ask the player to order them if there are more than one
            for player in self.game.players:
                triggered = triggered_sets[player]
                if len(triggered) > 1:
                    triggered = player.getSelection(triggered, -1, prompt="Drag to reorder triggered abilities(Top ability resolves first)")
                # Now reorder
                for ability in triggered: ability.announce(ability.source, player)
            self.pending_triggered[:] = []
            return True
        else: return False
    def put_card(self, card):
        return card.move_to(self.card_stack)
    def push(self, ability):
        self.abilities.append(ability)
        self.send(AbilityPlacedOnStack(), ability=ability)
    def resolve(self):
        ability = self.abilities.pop()
        ability.resolve()
        self.send(AbilityRemovedFromStack(), ability=ability)
    def counter(self, ability):
        self.abilities.remove(ability)
        self.send(AbilityRemovedFromStack(), ability=ability)
    def empty(self): return len(self.abilities) == 0
    def __contains__(self, ability): return ability in self.abilities
    def index(self, ability): return self.abilities.index(ability)
    def __getitem__(self, i): return self.abilities[i]
