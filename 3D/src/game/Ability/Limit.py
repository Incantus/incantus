from game.GameObjects import MtGObject
from game.GameEvent import TurnFinishedEvent, UpkeepStepEvent, MainPhaseEvent, EndMainPhaseEvent, NewTurnEvent

class Limit(MtGObject):
    def __call__(self, card): raise Exception()
    def played(self, card): pass
    def resolved(self, card): pass
    def __add__(self, other):
        if isinstance(other, Limit): return MultipleLimits(self, other)
        elif isinstance(other, MultipleLimits): return MultipleLimits(self, *other.limits)
        elif isinstance(other, Unlimited): return other

class Unlimited(Limit):
    def __call__(self, card):
        return True
    def __add__(self, other):
        return other

class MultipleLimits(Limit):
    def __init__(self, *limits):
        self.limits = limits
    def __call__(self, card):
        return all((limit(card) for limit in self.limits))
    def played(self, card):
        for l in self.limits: l.played(card)
    def resolved(self, card):
        for l in self.limits: l.resolved(card)
    def __add__(self, other):
        if isinstance(other, Limit): return MultipleLimits(other, self.limits)
        elif isinstance(other, MultipleLimits): return MultipleLimits(*(self.limits+other.limits))
        elif isinstance(other, Unlimited): return other

class ConditionalLimit(Limit):
    def __init__(self, condition):
        self.condition = condition
    def __call__(self, card):
        return self.condition(card)

class CountLimit(Limit):
    def __init__(self, count):
        self.original_count = count
        self.count = count
        # Setup the limit to reset every turn
        self.register(self.reset_count, event=TurnFinishedEvent())
    def played(self, card):
        self.count -= 1
    def reset_count(self):
        self.count = self.original_count
    def __call__(self, card):
        return self.count > 0

class TurnLimit(Limit):
    def __init__(self):
        self.register(self.state, event=NewTurnEvent())
        self.curr_player = None
    def state(self, sender, player):
        self.curr_player = player
    def __call__(self, card):
        return self.curr_player == card.controller

class UpkeepLimit(Limit):
    def __init__(self):
        self.register(self.state, event=UpkeepStepEvent())
        self.register(self.state, event=MainPhaseEvent())
        self.correct_phase = False
    def state(self, signal, sender):
        self.curr_player = sender.curr_player
        self.correct_phase = signal == UpkeepStepEvent()
    def __call__(self, card):
        return self.correct_phase and self.curr_player == card.controller

class SorceryLimit(Limit):
    def __init__(self):
        self.register(self.state, event=MainPhaseEvent())
        self.register(self.state, event=EndMainPhaseEvent())
        self.correct_phase = False
    def state(self, signal, sender):
        self.curr_player = sender.curr_player
        self.correct_phase = signal == MainPhaseEvent()
    def __call__(self, card):
        return self.correct_phase and self.curr_player == card.controller and card.controller.stack.empty()

class ThresholdLimit(Limit):
    def __call__(self, card):
        return len(card.controller.graveyard) >= 7

no_limit = Unlimited()
sorcery = SorceryLimit()
