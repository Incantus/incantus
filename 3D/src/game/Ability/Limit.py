from game.GameObjects import MtGObject
from game.GameEvent import TurnFinishedEvent, UpkeepStepEvent, MainPhaseEvent, EndMainPhaseEvent, NewTurnEvent

class Limit(MtGObject):
    def __call__(self, card): raise Exception()
    def __add__(self, other):
        if isinstance(other, Limit): return MultipleLimits(self, other)
        elif isinstance(other, MultipleLimits): return MultipleLimits(self, *other.limits)

class Unlimited(Limit):
    def __call__(self, card):
        return True

class MultipleLimits(Limit):
    def __init__(self, *limits):
        counts = []
        other = []
        for l in limits:
            if isinstance(l, CountLimit): counts.append(l)
            else: other.append(l)
        self.limits = other+counts
    def __call__(self, card):
        return all((limit(card) for limit in self.limits))
    def __add__(self, other):
        if isinstance(other, Limit): return MultipleLimits(other, self.limits)
        elif isinstance(other, MultipleLimits): return MultipleLimits(*(self.limits+other.limits))

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
        self.register(self.reset, event=TurnFinishedEvent())
    def reset(self):
        self.count = self.original_count
    def __call__(self, card):
        self.count -= 1
        return self.count >= 0

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

class PlaneswalkerLimit(SorceryLimit):
    def __init__(self):
        self.original_count = self.count = 1
        # Setup the limit to reset every turn
        self.register(self.reset, event=TurnFinishedEvent())
        super(PlaneswalkerLimit, self).__init__()
    def reset(self):
        self.count = self.original_count
    def __call__(self, card):
        self.count -= 1
        return self.count >= 0 and super(PlaneswalkerLimit, self).__call__(card)

