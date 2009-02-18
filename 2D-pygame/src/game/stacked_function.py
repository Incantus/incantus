#import operator, itertools

# this is probably where the static layering rules come into play
def logical_or(funcs, *args, **kw):
    return reduce(lambda x, y: x or y(*args, **kw), funcs, False)
    #return reduce(operator.or_, (f(*args, **kw) for f in funcs))
def logical_and(funcs, *args, **kw):
    # This looks weird, but it is the shortcutting version
    return reduce(lambda x, y: x and y(*args, **kw), funcs, True)
    #return reduce(operator.and_, (f(*args, **kw) for f in funcs))
def modify_args(funcs, *args, **kw):
    for f in funcs: args, kw = f(*args, **kw), {}
    return args
def last_only(funcs, *args, **kw):
    return funcs[0](*args, **kw)
def replacement(funcs, *args, **kw):
    # XXX This is UGLY!
    player = funcs[0].im_self
    replace = [(txt,i+1) for i,(func,txt,marked) in enumerate(funcs[1:]) if not marked]
    if not len(replace) == 0:
        if len(replace) > 1:
            i = player.getSelection(replace, numselections=1, isCardlist=False, required=True, prompt="Choose replacement effect")
        else: i = replace[0][1]
        func = funcs[i][0]
        # Mark the function as having processed this event
        funcs[i][2] = True
        result = func(*args, **kw)
        funcs[i][2] = False
        return result
    # If everyone's touched this event then the original function is called
    else:
        func = funcs[0]
        return func(*args, **kw)

class stacked_function(object):
    import types
    stacked = True
    def __init__(self, orig_func, combiner, reverse = True):
        self.funcs = [orig_func]
        self.combiner = combiner
        if reverse: self.reverse = -1
        else: self.reverse = 1
    def add_func(self, func):
        self.funcs.append(func)
    def remove_func(self, func):
        self.funcs.remove(func)
    def stacking(self):
        return len(self.funcs) > 1
    def __call__(self, *args, **kw):
        return self.combiner(self.funcs[::self.reverse], *args, **kw)
    def __get__(self, obj, objtype=None):
        return stacked_function.types.MethodType(self, obj, objtype)

