from game.pydispatch import dispatcher
from game.pydispatch.robustapply import function
from game.GameEvent import CleanupEvent
from game.stacked_function import override, replace, logical_and, logical_or, do_all
from game.Match import isPlayer

def do_when(func, event, condition=lambda *args: True):
    def wrap_(**kw):
        if robustApply(condition, **kw):
            func()
            dispatcher.disconnect(wrap_, signal=event, weak=False)
    dispatcher.connect(wrap_, signal=event, weak=False)

def delay(source, delayed_trigger):
    delayed_trigger.enable(source)
    def expire(): delayed_trigger.disable()
    return expire

def combine(*restores):
    if len(restores) == 1: expire = restores[0]
    else:
        def expire():
            for restore in restores: restore()
    return expire

def until_end_of_turn(*restores):
    dispatcher.connect(combine(*restores), signal=CleanupEvent(), weak=False, expiry=1)

def keyword_action(func):
    from game.Player import Player
    setattr(Player, func.__name__, func)

def permanent_method(func):
    from game.CardRoles import Permanent
    setattr(Permanent, func.__name__, func)

#def do_override(target, func_name, func, combiner=logical_and):
#    if isPlayer(target): obj = target
#    else: obj = target.current_role
#    return override(obj, func_name, func, combiner)

#def do_replace(target, func_name, func, msg, condition):
#    if isPlayer(target): obj = target
#    else: obj = target.current_role
#    return replace(obj, func_name, func, msg, condition=condition)

do_override = override
do_replace = replace

def robustApply(receiver, **named):
    """Call receiver with arguments and an appropriate subset of named
    """
    receiver, codeObject, startIndex = function(receiver)
    acceptable = codeObject.co_varnames[startIndex:codeObject.co_argcount]
    if not (codeObject.co_flags & 8):
        # fc does not have a **kwds type parameter, therefore
        # remove unacceptable arguments.
        for arg in named.keys():
            if arg not in acceptable:
                del named[arg]
    return receiver(**named)
