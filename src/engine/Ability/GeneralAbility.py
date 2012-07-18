from engine.CardRoles import CreatureType
from engine.Planeswalker import PlaneswalkerType
from engine.Player import Player
from EffectsUtilities import combine, do_replace
from Utils import flatten

preventAll = lambda self, amt, source, combat=False: 0

def prevent_all_damage():
    msg = "~ - prevent all damage"
    return combine(do_replace(CreatureType, "assignDamage", preventAll, msg=msg),
            do_replace(Player, "assignDamage", preventAll, msg=msg),
            do_replace(PlaneswalkerType, "assignDamage", preventAll, msg=msg))

def prevent_all_combat_damage():
    def condition(self, amt, source, combat=False): return combat
    msg = "~ - prevent all combat damage"
    return combine(do_replace(CreatureType, "assignDamage", preventAll, msg=msg, condition=condition),
            do_replace(Player, "assignDamage", preventAll, msg=msg, condition=condition),
            do_replace(PlaneswalkerType, "assignDamage", preventAll, msg=msg, condition=condition))

def prevent_all_noncombat_damage():
    def condition(self, amt, source, combat=False): return not combat
    msg = "~ - prevent all noncombat damage"
    return combine(do_replace(CreatureType, "assignDamage", preventAll, msg=msg, condition=condition),
            do_replace(Player, "assignDamage", preventAll, msg=msg, condition=condition),
            do_replace(PlaneswalkerType, "assignDamage", preventAll, msg=msg, condition=condition))

def modal_effects(*modes, **kw):
    choose = kw['choose']
    def effects(controller, source):
        selected = controller.make_selection([(mode.__doc__,mode) for mode in modes], choose, prompt='Select %d mode(s):'%choose)
        if choose > 1: chosen = tuple((mode(controller, source) for mode in selected))
        else: chosen = (selected(controller, source), )
        # get the costs
        # We need to have a "payment = yield NoCost" in the mode to pass
        # back the cost in case the mode needs to reference is (see Profane Command)
        empty_costs = tuple((mode.next() for mode in chosen))
        payment = yield source.cost

        # get the targets - demultiplex them
        targets, unflatten = flatten(mode.send(payment) for mode in chosen)
        targets = yield targets
        if not isinstance(targets, tuple): targets = (targets,)
        for t, mode in zip(unflatten(targets), chosen):
            yield mode.send(t)
            for res in mode: yield res

    return effects
