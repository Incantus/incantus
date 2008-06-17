#import operator, itertools
import types, new
from Match import isPlayer

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
def replacement(funcs, obj, *args, **kw):
    # XXX This is UGLY! and very recursive
    #obj = args[0]
    #def check_condition(func, cond, *args, **kw):
    #    if func.im_self: return cond(*args, **kw)
    #    else: return cond(obj, *args, **kw)
    replace = [(txt,i+1) for i,(marked,func,txt,cond) in enumerate(funcs[1:]) if not marked and cond(obj, *args, **kw)] #check_condition(func, cond, *args, **kw)]
    if not len(replace) == 0:
        if len(replace) > 1:
            if isPlayer(obj): player = affected = obj
            # In this case it is either a Permanent or a subrole
            # XXX I've only seen the subrole case for Creatures, not sure if anything else can be replaced
            else: player, affected = obj.perm.card.controller, obj.perm.card
            i = player.getSelection(replace, numselections=1, required=True, idx=False, prompt="Choose replacement effect to affect %s"%(affected))
        else: i = replace[0][1]
        func = funcs[i][1]
        # Mark the function as having processed this event
        funcs[i][0] = True
        # *** This where we could potentially recurse
        if func.im_self: result = func(*args, **kw)
        else: result = func(obj, *args, **kw)
        # Unmark the function
        funcs[i][0] = False
        return result
    # If everyone's touched this event then the original function is called
    else:
        func = funcs[0]
        if func.im_self: return func(*args, **kw)
        else: return func(obj, *args, **kw)

class stacked_function(object):
    stacked = True
    def __init__(self, orig_func, combiner, reverse = True):
        self.funcs = [orig_func]
        self.combiner = combiner
        if reverse: self.reverse = -1
        else: self.reverse = 1
    def add_func(self, func):
        self.funcs.append(func)
    def remove_func(self, func):
        if func in self.funcs: self.funcs.remove(func)
    def stacking(self):
        return len(self.funcs) > 1
    def rebind(self, obj):
        # XXX This is really ugly
        # To truly emulate a method, i should save the obj in __get__ and keep unbound functions
        for i, func in enumerate(self.funcs):
            self.funcs[i] = new.instancemethod(func.im_func, obj, func.im_class)
    def __call__(self, *args, **kw):
        return self.combiner(self.funcs[::self.reverse], *args, **kw)
    def __get__(self, obj, objtype=None):
        return types.MethodType(self, obj, objtype)

class replacement_stacked_function(stacked_function):
    def __init__(self, obj, funcname, reverse = True):
        self.funcs = []
        self.obj = obj
        self.funcname = funcname
        self.combiner = replacement
        if reverse: self.reverse = -1
        else: self.reverse = 1
        self.first_call = True
    def stacking(self):
        return len(self.funcs) > 0
    def add_func(self, func):
        self.funcs.append(func)
    def remove_func(self, func):
        if func in self.funcs: self.funcs.remove(func)
    def rebind(self, obj):
        # XXX This is really ugly
        # To truly emulate a method, i should save the obj in __get__ and keep unbound functions
        self.obj = obj
        for i, func in enumerate(self.funcs):
            marked,old_func,txt,cond = func
            self.funcs[i] = [marked, new.instancemethod(old_func.im_func, obj, old_func.im_class),txt,cond]
    def __call__(self, *args, **kw):
        if self.first_call:
            # Build the replacement list
            classfunc = getattr(self.obj.__class__, self.funcname)
            bound_classfuncs = []
            if hasattr(classfunc, "stacked"):
                bound_classfuncs.append(new.instancemethod(classfunc.funcs[0], self.obj, self.obj.__class__))
                for val, f, txt, cond in classfunc.funcs[1:]:
                    bound_classfuncs.append([val, new.instancemethod(f, self.obj, self.obj.__class__), txt, cond])
            else:
                bound_classfuncs.append(new.instancemethod(classfunc, self.obj, self.obj.__class__))
            self.replacement_funcs = bound_classfuncs+self.funcs
            self.first_call = False
            # This is the start of the recursive calls
            result = self.combiner(self.replacement_funcs, self.obj, *args, **kw)
            self.first_call = True
            return result
        return self.combiner(self.replacement_funcs, self.obj, *args, **kw)
