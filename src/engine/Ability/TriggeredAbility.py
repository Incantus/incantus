from engine.Util import isiterable
from engine.CardRoles import card_method
from Ability import Ability
from StackAbility import StackAbility
from EffectsUtilities import robustApply
from Utils import flatten

__all__ = ["TriggeredAbility", "SpecialTriggeredAbility",
           "modal_triggered_effects"]

class TriggeredStackAbility(StackAbility):
    triggered = True
    def __init__(self, effects, trigger_keys, source, controller=None, txt=''):
        super(TriggeredStackAbility, self).__init__(effects, txt)
        self.trigger_keys = trigger_keys
        self.source = source
        # Sometimes the controller of triggered ability effect isn't the same as the
        # controller of the source
        if not controller: self.controller = source.controller
        else: self.controller = controller
        trigger_keys["controller"] = self.controller
    def do_announce(self):
        self.effects = robustApply(self.effect_generator, **self.trigger_keys)
        return self.get_targets()
    def targets_from_effects(self):
        return self.effects.next()

class TriggeredAbility(Ability):
    def __init__(self, triggers, effects, zone="battlefield", txt='', keyword=''):
        if not isiterable(triggers): triggers=(triggers,)
        self.triggers = triggers
        self.effect_generator = effects
        self.zone = zone
        self.keyword = keyword
        if keyword and not txt: txt = keyword.capitalize()
        super(TriggeredAbility, self).__init__(txt)
    def _enable(self):
        for trigger in self.triggers:
            trigger.setup_trigger(self.source,self.playAbility)
    def _disable(self):
        for trigger in self.triggers:
            trigger.clear_trigger()
    def playAbility(self, **trigger_keys):
        #ability = TriggeredStackAbility(self.effect_generator, trigger_keys, self.source, txt=self.txt)
        if self.effect_generator.__doc__: txt = self.effect_generator.__doc__
        else: txt = self.txt
        ability = TriggeredStackAbility(self.effect_generator, trigger_keys, self.source, txt=txt)
        self.source.controller.stack.add_triggered(ability)
    def copy(self):
        return TriggeredAbility([t.copy() for t in self.triggers], self.effect_generator, self.zone, self.txt)

class SpecialTriggeredAbility(TriggeredAbility):
    def __init__(self, triggers, effects, special_funcs, zone="battlefield", txt='', keyword=''):
        super(SpecialTriggeredAbility, self).__init__(triggers, effects, zone, txt, keyword)
        self.buildup, self.teardown = special_funcs
    def _enable(self):
        self.buildup(self.source)
        super(SpecialTriggeredAbility, self)._enable()
    def _disable(self):
        self.teardown(self.source)
        super(SpecialTriggeredAbility, self)._disable()
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

@card_method
def delay(source, ability):
    '''Ability should be defined for stack abilities. Setup a one time delayed triggered ability'''
    triggers, effects = ability()
    if not isiterable(triggers): triggers=(triggers,)
    controller = source.controller # in case controller changes before it triggers
    def playAbility(**trigger_keys):
        delayed = TriggeredStackAbility(effects, trigger_keys, source, controller)
        controller.stack.add_triggered(delayed)
        for t in triggers: t.clear_trigger()
    for t in triggers: t.setup_trigger(source, playAbility, weak=False)

@card_method
def trigger(source, ability):
    '''Ability should be defined for stack abilities. Setup a recurring delayed triggered ability'''
    triggers, effects = ability()
    if not isiterable(triggers): triggers=(triggers,)
    controller = source.controller # in case controller changes before it triggers
    def playAbility(**trigger_keys):
        delayed = TriggeredStackAbility(effects, trigger_keys, source, controller)
        controller.stack.add_triggered(delayed)
    for t in triggers: t.setup_trigger(source, playAbility, weak=False)
    def expire():
        for t in triggers: t.clear_trigger()
    return expire
