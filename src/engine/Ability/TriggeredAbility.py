from engine.Util import isiterable
from Ability import Ability
from EffectsUtilities import robustApply
from Utils import flatten, unflatten

source_match = lambda source, card: source == card
sender_match = lambda source, sender: source == sender
attached_match = lambda source, card: source.attached_to == card

class TriggeredStackAbility(Ability):
    triggered = True
    def __init__(self, effects, trigger_keys, source, controller, txt=''):
        super(TriggeredStackAbility, self).__init__(effects, txt)
        self.trigger_keys = trigger_keys
        self.source = source
        self.controller = controller
    def do_announce(self):
        self.effects = robustApply(self.effect_generator, **self.trigger_keys)
        return self.get_targets()

class TriggeredAbility(object):
    enabled = property(fget=lambda self: self._status_count > 0)
    def __init__(self, triggers, condition, effects, expiry=-1, zone="battlefield", txt='', keyword=''):
        if not isiterable(triggers): triggers=(triggers,)
        self.triggers = triggers
        self.condition = condition
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
                    trigger.setup_trigger(self.source,self.playAbility,self.condition,self.expiry)
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
        return TriggeredAbility([t.copy() for t in self.triggers], self.condition, self.effect_generator, self.expiry, self.zone, self.txt)
    def __str__(self):
        return self.txt
    def __repr__(self): return "%s<%s %o: %s>"%('*' if self.enabled else '', self.__class__.__name__, id(self), self.txt)

class SpecialTriggeredAbility(TriggeredAbility):
    def __init__(self, triggers, condition, effects, special_funcs, expiry=-1, zone="battlefield", txt='', keyword=''):
        super(SpecialTriggeredAbility, self).__init__(triggers, condition, effects, expiry, zone, txt, keyword)
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
        targets = tuple((mode.next() for mode in chosen))
        demux = [len(target) if isinstance(target, tuple) else 1 for target in targets]
        targets = yield tuple(flatten(targets))
        for t, mode in zip(tuple(unflatten(targets, demux)), chosen):
            yield mode.send(t)
            for res in mode: yield res

    return modal_effects
