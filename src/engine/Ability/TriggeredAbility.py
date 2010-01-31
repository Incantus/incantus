from engine.Util import isiterable
from StackAbility import StackAbility
from EffectsUtilities import robustApply, permanent_method
from Utils import flatten

__all__ = ["source_match", "sender_match", "attached_match", "controller_match",
           "TriggeredAbility", "SpecialTriggeredAbility",
           "modal_triggered_effects"]

source_match = lambda source, card: source == card
sender_match = lambda source, sender: source == sender
attached_match = lambda source, card: source.attached_to == card
controller_match = lambda source, player: source.controller == player

class TriggeredStackAbility(StackAbility):
    triggered = True
    def __init__(self, effects, trigger_keys, source, controller, txt=''):
        super(TriggeredStackAbility, self).__init__(effects, txt)
        self.trigger_keys = trigger_keys
        self.source = source
        self.controller = controller
    def do_announce(self):
        self.effects = robustApply(self.effect_generator, **self.trigger_keys)
        return self.get_targets()
    def targets_from_effects(self):
        return self.effects.next()

class TriggeredAbility(object):
    enabled = property(fget=lambda self: self._status_count > 0)
    def __init__(self, triggers, effects, zone="battlefield", expiry=-1, txt='', keyword=''):
        if not isiterable(triggers): triggers=(triggers,)
        self.triggers = triggers
        self.effect_generator = effects
        self.expiry = expiry
        self.zone = zone
        if keyword and not txt: self.txt = keyword.capitalize()
        else: self.txt = txt
        self.keyword = keyword
        self._status_count = 0
    def toggle(self, val):
        if val:
            self._status_count += 1
            if self._status_count == 1:
                for trigger in self.triggers:
                    trigger.setup_trigger(self.source,self.playAbility,self.expiry)
        else:
            self._status_count -= 1
            if self._status_count == 0:
                for trigger in self.triggers:
                    trigger.clear_trigger()
    def enable(self, source):
        self.source = source
        self.toggle(True)
    def disable(self):
        self.toggle(False)
    def playAbility(self, **trigger_keys):
        player = self.source.controller
        trigger_keys["controller"] = player
        ability = TriggeredStackAbility(self.effect_generator, trigger_keys, self.source, player, txt=self.txt)
        player.stack.add_triggered(ability)
    def copy(self):
        return TriggeredAbility([t.copy() for t in self.triggers], self.effect_generator, self.zone, self.expiry, self.txt)
    def __str__(self):
        return self.txt
    def __repr__(self): return "%s<%s %o: %s>"%('*' if self.enabled else '', self.__class__.__name__, id(self), self.txt)

class SpecialTriggeredAbility(TriggeredAbility):
    def __init__(self, triggers, effects, special_funcs, zone="battlefield", expiry=-1, txt='', keyword=''):
        super(SpecialTriggeredAbility, self).__init__(triggers, effects, zone, expiry, txt, keyword)
        self.buildup, self.teardown = special_funcs
    def toggle(self, val):
        if val: self.buildup(self.source)
        else: self.teardown(self.source)
        super(SpecialTriggeredAbility, self).toggle(val)
    def copy(self):
        newcopy = super(SpecialTriggeredAbility, self).copy()
        newcopy.buildup, newcopy.teardown = self.buildup, self.teardown
        return newcopy

def modal_triggered_effects(*modes, **kw):
    choose = kw['choose']
    def modal_effects(**keys):
        controller = keys['controller']
        source = keys['source']
        selected = controller.make_selection([(mode.__doc__,mode) for mode in modes], choose, prompt='Select %d mode(s):'%choose)
        if choose > 1: chosen = tuple((robustApply(mode, **keys) for mode in selected))
        else: chosen = (robustApply(selected, **keys), )
        # get the targets
        targets, unflatten = flatten(mode.next() for mode in chosen)
        targets = yield targets
        if not isinstance(targets, tuple): targets = (targets,)
        for t, mode in zip(unflatten(targets), chosen):
            yield mode.send(t)
            for res in mode: yield res

    return modal_effects

@permanent_method
def delayed(source, ability):
    triggers, effects = ability()
    if not isiterable(triggers): triggers=(triggers,)
    def playAbility(**trigger_keys):
        delayed = TriggeredStackAbility(effects, trigger_keys, source)
        source.controller.stack.add_triggered(delayed)
        for t in triggers: t.clear_trigger()

    for t in triggers: t.setup_trigger(source, playAbility, 1)
