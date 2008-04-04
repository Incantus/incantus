from game.GameObjects import MtGObject
from game.GameEvent import EndTurnEvent, UpkeepStepEvent, DrawStepEvent, MainPhaseEvent, EndMainPhaseEvent

class Limit(MtGObject):
    def __init__(self, card):
        self.card = card
    def __call__(self):
        return True

class Unlimited(Limit):
    def __call__(self):
        return False

NoLimit = Unlimited

class MultipleLimits(Limit):
    def __init__(self, card, limits):
        super(MultipleLimits,self).__init__(card)
        self.limits = limits
    def __call_(self):
        for l in self.limits:
            if l():
                limited = True
                break
        else: limited = False
        return limited

class ZoneLimit(Limit):
    def __init__(self, card, zone):
        super(ZoneLimit,self).__init__(card)
        self.zone = zone
    def __call__(self):
        return not self.card.zone == getattr(self.card.controller, self.zone)

class ConditionalLimit(Limit):
    def __init__(self, card, condition):
        super(ConditionalLimit, self).__init__(card)
        self.condition = condition
    def __call__(self):
        return not self.condition(self.card)

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
        return self.count < 0

class UpkeepLimit(Limit):
    def __init__(self, card):
        super(UpkeepLimit, self).__init__(card)
        self.register(self.state, event=UpkeepStepEvent())
        self.register(self.state, event=DrawStepEvent())
        self.upkeep = False
    def state(self, signal, sender):
        if sender.curr_player == self.card.controller and signal == UpkeepStepEvent():
            self.upkeep = True
        else: self.upkeep = False
    def __call__(self):
        return not self.upkeep

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
        return not (self.main_phase and self.card.controller.stack.empty())

