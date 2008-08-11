from Ability import Ability
from Trigger import robustApply

class TriggeredStackAbility(Ability):
    triggered = True
    def __init__(self, card, effects, trigger_keys, txt=''):
        super(TriggeredStackAbility, self).__init__(card, effects, txt)
        self.trigger_keys = trigger_keys
    def do_announce(self):
        self.effects = robustApply(self.effect_generator, **self.trigger_keys)
        return self.get_targets()

class TriggeredAbility(object):
    def __init__(self, card, triggers, condition, effects, expiry=-1, zone="play", txt=''):
        self.card = card
        self.triggers = triggers
        self.condition = condition
        self.effects = effects
        self.expiry = expiry
        self.zone = zone
        self.txt = txt
    def enteringZone(self):
        for trigger in self.triggers:
            trigger.setup_trigger(self.card,self.playAbility,self.condition,self.expiry)
    def leavingZone(self):
        for trigger in self.triggers:
            trigger.clear_trigger()
    def playAbility(self, **trigger_keys):
        player = self.card.controller
        player.stack.add_triggered(TriggeredStackAbility(self.card, self.effects, trigger_keys, txt=self.txt), player)
    def copy(self, card=None):
        if not card: card = self.card
        return TriggeredAbility(card, [t.copy() for t in self.triggers], self.condition, self.effects, self.expiry, self.zone, self.txt)
    def __str__(self):
        return self.txt
