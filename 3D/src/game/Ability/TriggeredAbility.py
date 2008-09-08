from Ability import Ability
from Trigger import robustApply

class TriggeredStackAbility(Ability):
    triggered = True
    def __init__(self, effects, trigger_keys, txt=''):
        super(TriggeredStackAbility, self).__init__(effects, txt)
        self.trigger_keys = trigger_keys
    def do_announce(self):
        self.effects = robustApply(self.effect_generator, **self.trigger_keys)
        return self.get_targets()

class TriggeredAbility(object):
    enabled = property(fget=lambda self: self._status_count > 0)
    def __init__(self, triggers, condition, effects, expiry=-1, zone="play", txt='Triggered Ability', keyword=''):
        if not (type(triggers) == list or type(triggers) == tuple): triggers=[triggers]
        self.triggers = triggers
        self.condition = condition
        self.effects = effects
        self.expiry = expiry
        self.zone = zone
        if keyword: self.txt = keyword.capitalize()
        else: self.txt = txt
        self.keyword = keyword
        self._status_count = 0
    def enable(self, source):
        self._status_count += 1
        if self._status_count == 1:
            self.source = source
            for trigger in self.triggers:
                trigger.setup_trigger(source,self.playAbility,self.condition,self.expiry)
    def disable(self):
        self._status_count -= 1
        if self._status_count == 0:
            for trigger in self.triggers:
                trigger.clear_trigger()
    def playAbility(self, **trigger_keys):
        player = self.source.controller
        trigger_keys["controller"] = player
        player.stack.add_triggered(TriggeredStackAbility(self.effects, trigger_keys, txt=self.txt), self.source)
    def copy(self):
        return TriggeredAbility([t.copy() for t in self.triggers], self.condition, self.effects, self.expiry, self.zone, self.txt)
    def __str__(self):
        return self.txt
