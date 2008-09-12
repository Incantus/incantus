from game.pydispatch import dispatcher
from game.GameEvent import CleanupEvent
from game.stacked_function import override, replace, logical_and, logical_or
from game.Match import isPlayer

def delay(source, delayed_trigger):
    delayed_trigger.enable(source)
    def expire(): delayed_trigger.disable()
    return expire

def combine(*restores):
    def expire():
        for restore in restores: restore()
    return expire

def until_end_of_turn(*restores):
    dispatcher.connect(combine(*restores), signal=CleanupEvent(), weak=False, expiry=1)

def do_override(func_name, func, combiner=logical_and):
    def effects(target):
        if isPlayer(target): obj = target
        else: obj = target.current_role
        yield override(obj, func_name, func, combiner)
    return effects

def do_replace(target, func_name, func, msg, condition):
    if isPlayer(target): obj = target
    else: obj = target.current_role
    return replace(obj, func_name, func, msg, condition=condition)
