from game.GameObjects import MtGObject
from game.GameEvent import EndTurnEvent, UpkeepStepEvent, MainPhaseEvent, EndMainPhaseEvent, NewTurnEvent

class Limit(MtGObject):
    def __init__(self, card):
        self.card = card
    def __call__(self):
        return False

class Unlimited(Limit):
    def __call__(self):
        return True

class MultipleLimits(Limit):
    def __init__(self, card, limits):
        super(MultipleLimits,self).__init__(card)
        self.limits = limits
    def __iter__(self):
        return iter(self.limits)
    def __call__(self):
        # XXX This is broken
        for l in self.limits:
            if not l():
                limited = False
                break
        else: limited = True
        return limited

class ConditionalLimit(Limit):
    def __init__(self, card, condition):
        super(ConditionalLimit, self).__init__(card)
        self.condition = condition
    def __call__(self):
        return self.condition(self.card)

class CountLimit(Limit):
    def __init__(self, card, count):
        super(CountLimit, self).__init__(card)
        self.original_count = count
        self.count = count
        # Setup the limit to reset every turn
        self.register(self.reset, event=EndTurnEvent())
    def reset(self):
        self.count = self.original_count
    def __call__(self):
        self.count -= 1
        return self.count >= 0

class TurnLimit(Limit):
    def __init__(self, card):
        super(TurnLimit, self).__init__(card)
        self.register(self.state, event=NewTurnEvent())
        self.your_turn = False
    def state(self, sender, player):
        self.your_turn = player == self.card.controller
    def __call__(self):
        return self.your_turn

class UpkeepLimit(Limit):
    def __init__(self, card):
        super(UpkeepLimit, self).__init__(card)
        self.register(self.state, event=UpkeepStepEvent())
        self.register(self.state, event=MainPhaseEvent())
        self.upkeep = False
    def state(self, signal, sender):
        if sender.curr_player == self.card.controller and signal == UpkeepStepEvent():
            self.upkeep = True
        else:
            self.upkeep = False
    def __call__(self):
        return self.upkeep

class SorceryLimit(Limit):
    def __init__(self, card):
        super(SorceryLimit, self).__init__(card)
        self.register(self.state, event=MainPhaseEvent())
        self.register(self.state, event=EndMainPhaseEvent())
        self.main_phase = False
    def state(self, signal, sender):
        if sender.curr_player == self.card.controller and signal == MainPhaseEvent():
            self.main_phase = True
        else: self.main_phase= False
    def __call__(self):
        return (self.main_phase and self.card.controller.stack.empty())

class ThresholdLimit(Limit):
    def __init__(self, card):
        super(ThresholdLimit, self).__init__(card)
    def __call__(self):
        return len(self.card.controller.graveyard) >= 7
