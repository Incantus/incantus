from game.stacked_function import *
import new

class Permanent(object):
    def canBeTargetedBy(self, targeter):
        print "Can be targeted by %s"%targeter
        return True

class Player(object):
    def __init__(self, name):
        self.name = name
    def getSelection(self, sellist, numselections=1, required=True, prompt=''):
        print prompt
        for item, i, in sellist:
            print i, item
        while True:
            text = raw_input(self.name+"- Choose one:")
            index = int(text)
            if index >= 0 and index < len(sellist): break
            else: print "Incorrect choice"
        return index

class Creature(Permanent):
    def __init__(self):
        self.damage = 0
    def assignDamage(self, amt, source, combat=False):
        self.damage += amt
        print "Receiving %d damage from %s"%(amt, source)

def override_replace(target, name, func, combiner=replacement, reverse=False):
    obj = target
    cls = target.__class__

    is_derived = False
    # The function is defined in the superclass (which we don't override)
    if not name in cls.__dict__:
        is_derived = True
        # Bind the call to the superclass function
        orig_func = new.instancemethod(lambda self, *args, **named: getattr(super(cls, self), name).__call__(*args,**named), obj, cls)
    else:
        orig_func = getattr(obj, name)
    if not hasattr(orig_func, "stacked"):
        stacked_func = stacked_function(orig_func, combiner=combiner, reverse=reverse)
        setattr(target, name, stacked_func)
    else: stacked_func = orig_func
    # Add the replacement effect along with the card name (in case of multiple effects)
    new_func = [new.instancemethod(func, obj, cls), name, False] #card.name, False]
    stacked_func.add_func(new_func)
    def restore(stacked_func=stacked_func):
        stacked_func.remove_func(new_func)
        if not stacked_func.stacking():
            setattr(target, name, stacked_func.funcs[0])
            del stacked_func
    func.expire = restore
    return restore

def prevent_damage(subrole, amt):
    def shieldDamage(self, amt, source, combat=False):
        if shieldDamage.curr_amt != -1:
            shielded = min([amt,shieldDamage.curr_amt])
            shieldDamage.curr_amt -= amt
            if shieldDamage.curr_amt <= 0:
                self.assignDamage(-1*shieldDamage.curr_amt, source, combat)
                shieldDamage.curr_amt = 0
                shieldDamage.expire()
        else: shielded = amt
    shieldDamage.curr_amt = amt
    restore = override_replace(subrole, "assignDamage", shieldDamage)
    return restore

player = Player("Andrew")
goblin = Creature()
goblin.controller = player
prevent_damage(goblin, 2)
prevent_damage(goblin, 2)
goblin.assignDamage(3, "Andrew", False)
print goblin.damage
