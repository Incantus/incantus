import new, types
from Match import isPlayer

# this is probably where the static layering rules come into play
def logical_or(funcs, *args, **kw):
    return reduce(lambda x, y: x or y(*args, **kw), funcs, False)
def logical_and(funcs, *args, **kw):
    return reduce(lambda x, y: x and y(*args, **kw), funcs, True)
def do_all(funcs, *args, **kw):
    for f in funcs: f(*args, **kw)

def find_stacked(target, name):
    if type(target) == types.TypeType:
        obj = None
        cls = target
    else:
        obj = target
        cls = obj.__class__
    original = None
    if name in cls.__dict__: original = getattr(cls, name)
    if original and hasattr(original, "stacked"):
        stacked = original
    else:
        stacked = stacked_function(name, cls)
    return stacked, obj

def override(target, name, func, combiner=logical_and):
    stacked, obj = find_stacked(target, name)
    stacked.set_combiner(combiner)
    return stacked.add_override(func, obj)
def replace(target, name, func, msg='', condition=None):
    stacked, obj = find_stacked(target, name)
    return stacked.add_replacement(func, obj, msg, condition)

class stacked_function(object):
    stacked = True
    empty = set()
    def __init__(self, f_name, f_class, combiner=logical_and):
        self.__name__ = "stacked_"+f_name
        self.f_name = f_name
        self.f_class = f_class
        self.combiner = combiner
        self.overrides = []
        self.replacements = []
        self._first_call = True
        self.setup_overrides(f_name, f_class)
    def set_combiner(self, combiner):
        self.combiner = combiner
    def setup_overrides(self, f_name, f_class):
        if not f_name in f_class.__dict__:
            # If the function is defined in a parent, bind a call to function in the superclass
            self.original = new.instancemethod(lambda self, *args, **named: getattr(super(f_class, self), f_name).__call__(*args,**named), None, f_class)
            self.is_derived = True
        else:
            self.original = getattr(f_class, f_name)
            self.is_derived = False
        # Install the stacked function
        setattr(f_class, f_name, self)
    def revert(self):
        if not (len(self.overrides) > 0 or len(self.replacements) > 0):
            if self.is_derived: delattr(self.f_class, self.f_name)
            else: setattr(self.f_class, self.f_name, self.original)
    def _add(self, stacked_list, func, obj):
        stacked_list.append(func)
        if obj: obj._overrides.add(func)
        else: func.all = True
        def restore():
            if func in stacked_list: # avoid being called twice
                stacked_list.remove(func)
                if obj: obj._overrides.remove(func)
                self.revert()
        return restore
    def add_replacement(self, func, obj=None, msg='', condition=None):
        if not condition: condition = lambda *args, **kw: True
        func.msg = msg
        func.cond = condition
        func.expire = self._add(self.replacements, func, obj)
        return func.expire
    def add_override(self, func, obj=None):
        func.expire = self._add(self.overrides, func, obj)
        return func.expire
    def mark(self):
        self._first_call = False
        self.__current_replacements = set()
    def build_replacements(self, obj):
        replacements = set()
        # Walk up the inheritance hierarchy
        for cls in self.f_class.mro():
            if self.f_name in cls.__dict__:
                func = getattr(cls, self.f_name)
                if hasattr(func, "stacked"):
                    func.mark()
                    replacements.update([f for f in func.replacements if hasattr(f, "all") or f in getattr(obj, "_overrides", self.empty)])
        self.__current_replacements = replacements

    def do_replacement(self, *args, **kw):
        obj = args[0]
        replacements = self.__current_replacements
        funcs = [func for func in replacements if func.cond(*args, **kw)]
        if funcs:
            if len(funcs) > 1:
                if isPlayer(obj): player = affected = obj
                # In this case it is either a Permanent or a subrole
                # XXX I've only seen the subrole case for Creatures, not sure if anything else can be replaced
                else: player, affected = obj.card.controller, obj.card
                i = player.getSelection([(f.msg, i) for i, f in enumerate(funcs)], numselections=1, required=True, idx=False, prompt="Choose replacement effect to affect %s"%(affected))
            else: i = 0
            func = funcs[i]
            # Remove the selected replacement function
            replacements.remove(func)
            # *** This where we could potentially recurse
            return func(*args, **kw)
        else:
            # No more replacements - unmark this stacked_function
            self._first_call = True
            del self.__current_replacements
            overrides = [f for f in self.overrides[::-1] if hasattr(f, "all") or f in getattr(obj, "_overrides", self.empty)]+[self.original]
            return self.combiner(overrides, *args, **kw)

    def __call__(self, *args, **kw):
        if self._first_call: self.build_replacements(args[0])
        # This is the start of the recursive calls
        return self.do_replacement(*args, **kw)
    def __get__(self, obj, objtype=None):
        return types.MethodType(self, obj, objtype)
