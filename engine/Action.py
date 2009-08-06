
from GameEvent import TimestepEvent, LandPlayedEvent, AbilityPlayedEvent, LogEvent

class Action(object):
    def __eq__(self, other):
        return self.__class__ == other.__class__
    def __repr__(self):
        return str(self.__class__.__name__)

class PassPriority(Action):
    pass
class OKAction(Action):
    pass
class CancelAction(Action):
    pass

# For attackers to assign damage to multiple blockers
class DistributionAssignment(Action):
    def __init__(self, assnment):
        self.assignment = assnment

class CardSelected(Action):
    def __init__(self, card):
        self.selection = card
    def __str__(self):
        return "%s - %s"%(repr(self), self.selection)

class MultipleCardsSelected(Action):
    def __init__(self, selected):
        self.selection = selected
    def __str__(self):
        return "%s - %s"%(repr(self), self.selection)

class PlayerSelected(Action):
    def __init__(self, player):
        self.selection = player
    def __str__(self):
        return "%s - %s"%(repr(self), self.selection)

class SingleSelected(Action):
    def __init__(self, selected):
        self.selection = selected
    def __str__(self):
        return "%s - %s"%(repr(self), self.selection)

class MultipleSelected(Action):
    def __init__(self, selected):
        self.selection = selected
    def __str__(self):
        return "%s - %s"%(repr(self), self.selection)

# Actions for selecting X and mana amounts
class ManaSelected(Action):
    def __init__(self, mana):
        self.mana = mana

class XSelected(Action):
    def __init__(self, amount):
        self.amount = amount
