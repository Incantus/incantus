from game.GameObjects import MtGObject
from game.GameEvent import *

class MemoryVariable(MtGObject):
    def __init__(self, card):
        self.card = card
        self.register(self.reset, event=EndTurnEvent())
    def value(self): pass
    def reset(self): pass
    def __int__(self):
        return int(self.value())
    def __long__(self):
        return long(self.value())
    def __str__(self):
        return str(self.value())


class PlayerDamageVariable(MemoryVariable):
    def __init__(self, card):
        super(PlayerDamageVariable, self).__init__(card)
        self.players = {}
        self.register(self.damaged, event=PlayerDamageEvent())
    def reset(self):
        for player in self.players.keys():
            self.players[player] = 0
    def damaged(self, sender, source, amount):
        if not sender in self.players: self.players[sender] = 0
        self.players[sender] += amount
