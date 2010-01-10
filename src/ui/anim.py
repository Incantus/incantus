from math import *

_time = 0

class Animator(object):
    def __init__(self):
        self.dx = 0
        self.dv = 0
    def final(self): pass
    def get(self): pass
    # Arithmetic methods
    def __add__(self, other):
        pass
    def __sub__(self, other):
        pass
    def __mul__(self, other):
        pass
    def __div__(self, other):
        pass
    # Coercion methods
    #def __coerce__(self, other):
    #    return (self.get(), other)
    #def __float__(self):
    #    return float(self.get())
    #def __long__(self):
    #    return long(self.get())
    #def __int__(self):
    #    return int(self.get())
    #def __str__(self):
    #    return str(self.get())

class ConstantAnimator(Animator):
    def __init__(self, val=None):
        super(ConstantAnimator,self).__init__()
        self._val = val
    def set(self, val):
        self._val = val
    def get(self):
        return self._val
    def final(self): return self._val

# Time handling functions
def constant(t):
    if t < 0: t = 0
    elif t > 1: t = 1
    return t

def extrapolate(t):
    return t

def repeat(t):
    if t > 1: t = t - int(t)
    elif t < 0: t = 1 + t - int(t)
    return t

def reverse(t):
    if t < 0: t = -t
    if int(t) % 2 == 1: t = 1-(t-int(t))
    else: t = t - int(t)
    return t


# Interpolation functions
def step(t):
    if t != 1: return 0
    else: return 1
def reverse_step(t):
    if t != 1: return 1
    else: return 0
def linear(t): return t
def cosine(t): return 1-cos(t*pi/2)
def sine(t): return sin(t*pi/2)
def exponential(t): return (exp(t)-1)/(exp(1)-1)
def ease_out(t): return sqrt(sin(t*pi/2))
def ease_in_elastic(t, a=None, p=None):
    if not p: p = 0.3
    if not a or a < 1.0:
        a = 1.0
        s = p/4.
    else:
        s = p/(2*pi)*asin(1.0/a)
    if t == 0 or t == 1: return t
    return -(a*pow(2,10*(t-1))*sin(((t-1)-s)*(2*pi)/p))
def ease_out_back(t, s=None):
    if not s: s = 1.70158
    t -= 1
    return t*t*((s+1)*t+s)+1
def ease_in_out_circ(t):
    t = t*2
    if t < 1.0: return 0.5*(1-sqrt(1-t*t));
    else:
        t = t-2
        return 0.5*(sqrt(1-t*t)+1)
def ease_in_circ(t):
    return 1 - sqrt(1 - t*t)
def ease_out_circ(t):
    t -= 1
    return sqrt(1 - t*t)
def oscillate(t):
    return pow(sin(t*pi),2)
def oscillate_n(t, n=2):
    return sin(t*n*pi)

_funcs = ["step", "reverse_step", "linear", "cosine", "sine", "exponential", "ease_out_back", "ease_in_circ", "ease_out_circ", "ease_out", "oscillate", "oscillate_n"]
_time_extension = ["constant", "extrapolate", "reverse", "repeat"]

_funcs = dict([(l, globals()[l]) for l in _funcs])
_time_extension = dict([(l, globals()[l]) for l in _time_extension])


class InterpolatedAnimator(Animator):
    def __init__(self, start, end, startt, endt, extend=constant, method=linear, args={}):
        super(InterpolatedAnimator,self).__init__()
        self.start = start
        self.end = end
        self.startt = startt
        self.endt = endt
        self.extend = extend
        self.one_over_dt = 1./float(self.endt-self.startt)
        self.set_method(method,args)
        #self.prev_x = self.start
        self.cached_x = self.end
        if self.extend is constant: self.get = self.get_dirty
        else: self.get = self.get_always
    def set_method(self, method, args):
        self._interpolate = method
        self._args = args
    def final(self): return self.end
    def set(self, val):
        self.start = self.get()
        self.end = val
        dt = self.endt - self.startt
        self.startt = _time
        self.endt = self.startt + dt
        if self.extend is constant: self.get = self.get_dirty
        else: self.get = self.get_always
    def get_saved(self):
        return self.cached_x
    def get_always(self):
        t = self.extend((_time-self.startt)*self.one_over_dt)
        x = (self.end-self.start)*self._interpolate(t)+self.start
        return x
    def get_dirty(self):
        t = self.extend((_time-self.startt)*self.one_over_dt)
        x = (self.end-self.start)*self._interpolate(t)+self.start
        if t == 1: self.get = self.get_saved
        #self.dx = x - self.prev_x
        #self.prev_x = x
        #self.dv = self.dx*self.one_over_dt
        return x

class ChainedAnimator(Animator):
    def __init__(self, anims, extend=constant):
        self.curr_anim = 0
        self.anims = anims
        self.one_over_dt = 1./sum([(anim.endt-anim.startt) for anim in self.anims])
        self.times = [self.one_over_dt*sum([(anim.endt-anim.startt) for anim in self.anims[:i+1]]) for i in range(len(anims))]
        self.times[-1] = 1.0 # This is needed to avoid floating point error in the above times calculation
        self.startt = self.anims[0].startt
        self.extend = extend
        self.prev_x = self.anims[0].start
    def set(self, vals):
        assert len(vals) == len(self.anims)
        newstart = self.get()
        self.startt = _time
        for anim, val in zip(self.anims, vals):
            anim.start = newstart
            newstart = val
            anim.end = val
            anim.startt += self.startt
            anim.endt += self.startt
    def get(self):
        t = self.extend((_time-self.startt)*self.one_over_dt)
        if t > self.times[self.curr_anim]:
            self.curr_anim += 1
        elif self.curr_anim != 0 and t < self.times[self.curr_anim - 1]:
            self.curr_anim -= 1
        x = self.anims[self.curr_anim].get()
        self.dx = x - self.prev_x
        self.prev_x = x
        self.dv = self.dx*self.one_over_dt
        return x

class BezierPathAnimator(Animator):
    def __init__(self, p0, p1, p2, p3, startt, endt, extend, method=linear):
        super(BezierPathAnimator,self).__init__()
        self.animator = InterpolatedAnimator(0.0, 1.0, startt, endt, extend=extend, method=method)
        self.p0 = p0
        self.c = 3.0 * (p1 - p0)
        self.b = 3.0 * (p2 - p1) - self.c
        self.a = p3 - p0 - self.c - self.b
        self.prev_x = 0
    def get(self):
        t = self.animator.get()
        t_2 = t*t
        t_3 = t_2*t
        x = self.a*t_3 + self.b*t_2 + self.c*t + self.p0
        self.dx = x - self.prev_x
        self.prev_x = x
        self.dv = self.dx*self.animator.one_over_dt
        return x


def _handle_time_args(startt, endt, dt):
    if startt is None: startt = _time
    else: startt += _time
    if endt is None:
        if dt is None: raise ValueError("Either dt or endt must be given.")
        endt = startt + dt
    assert startt < endt
    return startt, endt


# ********************************************
# The functions below are exported
#

def set_time(t):
    global _time
    _time = t

def add_time(t):
    global _time
    _time += t
    return _time

class Animatable(object):
    # self.attr_name is assigned by the metaclass constructor
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.attr_name).get()
    def __set__(self, obj, value):
        if isinstance(value, Animator):
            setattr(obj, self.attr_name, value)
        else: getattr(obj, self.attr_name).set(value)
    def __delete__(self, obj):
        # Free the animator
        del self.anim

class AnimableMeta_old(type):
    def __new__(cls, name, bases, dict):
        # replace all the Animatable descriptors with new ones
        new_class = type.__new__(cls, name, bases, dict)
        new_class._animatable_slot_names = []
        for key, val in dict.items():
            if isinstance(val, Animatable):
                attr_name = "_animator_slot_%s"%key
                val.attr_name = attr_name
                new_class._animatable_slot_names.append(attr_name)
        return new_class

class AnimableMeta_new(type):
    def __new__(cls, name, bases, dict):
        # XXX This is broken
        animable_subclasses = [b for b in bases
                if hasattr(b, "_animatable_slot_names")]
        if len(animable_subclasses) > 1:
            raise TypeError(
                    "Cannot subclass from more than one Animable class.")

        new_class = type.__new__(cls, name, bases, dict)
        inherited_descriptors = []
        if animable_subclasses:
            a_cls = animable_subclasses[0]
            if hasattr(a_cls, "_animatable_slot_names"):
                inherited_descriptors.extend(a_cls._animatable_slot_names)
        new_descriptors = [(k, v) for k, v in dict.items()
                if isinstance(v, Animatable)]

        print name, inherited_descriptors + new_descriptors

        new_class._animatable_slot_names = []
        for key, val in inherited_descriptors+new_descriptors:
            attr_name = "_animator_slot_%s"%key
            val.attr_name = attr_name
            new_class._animatable_slot_names.append(attr_name)
        return new_class

AnimableMeta = AnimableMeta_old

class Animable(object):
    __metaclass__ = AnimableMeta
    def __new__(cls, *args, **kw):
        obj = object.__new__(cls, *args, **kw)
        for anim_slot in cls._animatable_slot_names:
            setattr(obj, anim_slot, ConstantAnimator())
        return obj

def constant(value):
    return ConstantAnimator(value)

def animate(start, end, startt=None, endt=None, dt=None, extend="constant", method="linear"):
    startt, endt = _handle_time_args(startt, endt, dt)
    extend = _time_extension[extend]
    if isinstance(method, str): method = _funcs[method]
    try:
        iter(start), iter(end)
    except TypeError:
        return InterpolatedAnimator(start, end, startt, endt, extend, method)
    else:
        return [InterpolatedAnimator(s, e, startt, endt, extend, method)
                for s,e in zip(start, end)]

def chain(anims, extend="constant"):
    assert len(anims) > 0
    extend = _time_extension[extend]
    time_incr = 0
    for animator in anims:
        animator.startt += time_incr
        animator.endt += time_incr
        time_incr += animator.endt-animator.startt
        animator.extend = extend
    return ChainedAnimator(anims, extend)

def bezier3(p0, p1, p2, p3, startt=None, endt=None, dt=None, extend="constant", method="linear"):
    startt, endt = _handle_time_args(startt, endt, dt)
    extend = _time_extension[extend]
    method = _funcs[method]

    try:
        [iter(p) for p in [p0,p1,p2,p3]]
    except TypeError:
        return BezierPathAnimator(p0, p1, p2, p3, startt, endt, extend, method)
    else:
        return [BezierPathAnimator(p0, p1, p2, p3, startt, endt, extend, method)
                for p0, p1, p2, p3 in zip(p0, p1, p2, p3)]

if __name__ == "__main__":
    class Obj(object):
        x = Animatable()
        def __init__(self):
            self.x = 0

    o = Obj()
    add_time(0)
    print o.x   # prints out 0.0
    #o.x.anim = animate("linear", start=5., end=10., dt=5) # this doesn't work
    o.x = animate("linear", start=0, end=1, dt=5)
    add_time(2.5)
    print o.x   # prints out 0.5
    add_time(2.5)
    print o.x # prints out 1.0
    o.x = 10  # Continue the linear interpolation, now from 1 to 10 with a dt of 5
    print o.x # prints out 1.0
    add_time(2.5)
    print o.x # prints out 5.5
    add_time(2.5)
    print o.x # prints out 10.0
    o.x = animate("sine", end=5, dt=5)


