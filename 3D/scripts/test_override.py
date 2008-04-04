from game.stacked_function import *
import new

class Permanent(object):
    def canBeTargetedBy(self, targeter):
        print "Can be targeted by %s"%targeter
        return True

class Creature(Permanent):
    def dealDamage(self, target, amount, combat=False):
        print "Dealing %d damage to %s"%(amount, target)

def override(func, name, cls, obj=None, combiner=logical_and):
    if obj: target = obj
    else: target = cls
    is_derived = False
    if not name in target.__dict__:
        orig_func = new.instancemethod(lambda *args, **named: getattr(super(cls, args[0]), name).__call__(*args[1:],**named), obj, cls)
        is_derived = True
    else:
        orig_func = getattr(target, name)
    if not hasattr(orig_func, "stacked"):
        stacked_func = stacked_function(orig_func, combiner)
        setattr(target, name, stacked_func)
    else: stacked_func = orig_func
    new_func = new.instancemethod(func, obj, cls) 
    stacked_func.add_func(new_func)
    def restore(stacked_func=stacked_func):
        stacked_func.remove_func(new_func)
        if not stacked_func.stacking():
            #if not is_derived: setattr(target, name, stacked_func.funcs[0])
            #else: del target.__dict__[name]
            setattr(target, name, stacked_func.funcs[0])
            del stacked_func
    return restore

def canBeTargetedBy1(self, targeter):
    if targeter[:3] == "Bob": conj = "not"
    else: conj = ''
    print "Can%s be targeted by %s"%(conj,targeter)
    return not targeter[:3] == "Bob"

#goblin = Creature()
#print goblin.canBeTargetedBy("Bob")
#restore = override(canBeTargetedBy1, "canBeTargetedBy", Creature)
#restore()
#restore = override(canBeTargetedBy1, "canBeTargetedBy", Permanent, goblin)

#def canBeTargetedBy2(self, targeter):
#    if len(targeter) >= 6: conj = "not"
#    else: conj = ''
#    print "Can%s be targeted by %s"%(conj,targeter)
#    return not len(targeter) >= 6

#restore1 = override(canBeTargetedBy2, "canBeTargetedBy", Permanent)
#print goblin.canBeTargetedBy(targeter="Bob")
#print goblin.canBeTargetedBy("Robert")
#p = Permanent()
#print p.canBeTargetedBy("Robert")
#restore()
#print goblin.canBeTargetedBy(targeter="Bob")

#def dealDamage(self, target, amount, combat=False):
#    return (self, target, 2*amount, combat)
#restore1 = override(dealDamage, "dealDamage", Creature, combiner=modify_args)
#restore2 = override(dealDamage, "dealDamage", Creature, combiner=modify_args)
#goblin.dealDamage("Andrew", 20, combat=True)
#restore1()
#goblin.dealDamage("Andrew", 20)

class AddToken(object):
    def __init__(self, number):
        self.number = number
    def __call__(self):
        print self.number

a = AddToken(5)
a()

def double(self):
    return self.number*2

AddToken.number = property(fget=double)
#a()
del AddToken.number
a()
