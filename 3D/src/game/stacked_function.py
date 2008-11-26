import new, types

__all__ = ['global_override', 'override', 'replace', 'logical_or', 'logical_and', 'do_all', 'most_recent']

# this is probably where the static layering rules come into play
def logical_or(funcs, *args, **kw):
    return reduce(lambda x, y: x or y(*args, **kw), funcs, False)
def logical_and(funcs, *args, **kw):
    return reduce(lambda x, y: x and y(*args, **kw), funcs, True)
def do_all(funcs, *args, **kw):
    for f in funcs: f(*args, **kw)
def most_recent(funcs, *args, **kw):
    return funcs[0](*args, **kw)

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
def global_override(target, name, func):
    stacked, obj = find_stacked(target, name)
    return stacked.add_global_override(func, obj)

class stacked_function(object):
    stacked = True
    def __init__(self, f_name, f_class, combiner=logical_and):
        self.__name__ = "stacked_"+f_name
        self.f_name = f_name
        self.f_class = f_class
        self.combiner = combiner
        self.global_overrides = []
        self.overrides = []
        self.replacements = []
        self.unmark()
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
        if not (len(self.global_overrides) > 0 or len(self.overrides) > 0 or len(self.replacements) > 0):
            if self.is_derived: delattr(self.f_class, self.f_name)
            else: setattr(self.f_class, self.f_name, self.original)
    def _add(self, stacked_list, func, obj):
        stacked_list.append(func)
        if obj: func.obj = obj
        else: func.obj = "all"
        def restore():
            if func in stacked_list: # avoid being called twice
                stacked_list.remove(func)
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
    def add_global_override(self, func, obj=None):
        func.expire = self._add(self.global_overrides, func, obj)
        return func.expire
    def mark_as_seen(self, rpls):
        #print "Marking %s in %s"%(self.f_name, self.f_class)
        self._first_call = True
        self._seen.update(rpls)
    def unmark(self):
        #print "Unmarking %s in %s"%(self.f_name, self.f_class)
        self._first_call = False
        self._seen = set()
        self.__current_replacements = []
    def build_replacements(self, *args, **kw):
        obj = args[0]
        replacements = set()
        # Walk up the inheritance hierarchy
        for cls in self.f_class.mro():
            if self.f_name in cls.__dict__:
                func = getattr(cls, self.f_name)
                if hasattr(func, "stacked"):
                    rpls = [f for f in func.replacements if not f in func._seen and (f.obj == "all" or f.obj == obj) and f.cond(*args, **kw)]
                    replacements.update(rpls)
                    func.mark_as_seen(rpls)
        return replacements

    def __call__(self, *args, **kw):
        from Match import isPlayer, isCard
        obj = args[0]
        global_overrides = [f for f in self.global_overrides[::-1] if f.obj == "all" or f.obj == obj]
        if global_overrides: return global_overrides[0](*args, **kw)
        else:
            self.__current_replacements.extend(self.build_replacements(*args, **kw))
            funcs = self.__current_replacements
            #print funcs
            if funcs:
                if len(funcs) > 1:
                    if isPlayer(obj): player = affected = obj
                    elif hasattr(obj, "keeper"): player = affected = obj.current_player
                    # In this case it is a role
                    elif isCard(obj): player, affected = obj.controller, obj
                    func = player.make_selection([(f.msg, f) for f in funcs], number=1, prompt="Choose replacement effect to affect %s"%(affected))
                    funcs.remove(func)
                else: func = funcs.pop(0)
                # *** This where we could potentially recurse
                result = func(*args, **kw)
                # No more replacements - unmark this stacked_function
                #print func, self._first_call
                if self._first_call: self.unmark()
                return result
            else:
                overrides = [f for f in self.overrides[::-1] if f.obj == "all" or f.obj == obj]+[self.original]
                if self._first_call: self.unmark()
                return self.combiner(overrides, *args, **kw)

    def __get__(self, obj, objtype=None):
        return types.MethodType(self, obj, objtype)
