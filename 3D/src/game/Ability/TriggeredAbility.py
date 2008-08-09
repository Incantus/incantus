from game.GameObjects import MtGObject

class TriggeredAbility(MtGObject):
    def __init__(self, card, trigger, condition, ability, expiry=-1, zone="play", txt=''):
        self.card = card
        self.trigger = trigger
        self.condition = condition
        self.ability = ability
        self.expiry = expiry
        self.zone = zone
        self.txt = txt
    def enteringZone(self):
        self.trigger.setup_trigger(self,self.playAbility,self.condition,self.expiry)
    def leavingZone(self):
        self.trigger.clear_trigger(wait=False)
    def playAbility(self, trigger=None): # We don't care about the trigger
        self.ability.copy().announce(self.card.controller)
    def copy(self, card=None):
        if not card: card = self.card
        return TriggeredAbility(card, self.trigger.copy(), self.condition, self.ability.copy(card), self.expiry, self.zone, self.txt)
    def __str__(self):
        return self.txt
