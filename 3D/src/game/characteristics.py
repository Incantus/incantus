
from GameEvent import ControllerChanged

class stacked_variable(object):
    _val = property(fget=lambda self: self._characteristics[-1][0])
    def __init__(self, initial):
        self._characteristics = [(initial,)]
    def cda(self, var):
        new = (var,)
        self._characteristics.insert(1, new)
        return lambda: self._characteristics.remove(new)
    def set_copy(self, var):
        new = (var,)
        self._characteristics.append(new)
        return lambda: self._characteristics.remove(new)
    def __getattr__(self, attr): return getattr(self._val, attr)
    def __eq__(self, other): return self._val == other
    def __str__(self): return str(self._val)
    def __repr__(self): return repr(self._val)
    def __int__(self): return int(self._val)

class stacked_controller(object):
    _val = property(fget=lambda self: self._characteristics[-1][0])
    def __init__(self, perm, initial):
        self.perm = perm
        self._controllers = [(initial,)]
        self.perm.summoningSickness()
    def set(self, new_controller):
        old_controller = self._val
        contr = (new_controller,)
        self._controllers.append(contr)
        if not new_controller == old_controller: self.controller_change(old_controller)
        def remove():
            orig = self._val
            self._controllers.remove(contr)
            if orig != self._val: self.controller_change(orig)
        return remove
    def controller_change(self, old_controller):
        self.perm.summoningSickness()
        self.perm.send(ControllerChanged(), original=old_controller)

# PowerToughnessChanged isn't needed, because the power/toughness is invalidated every timestep (and the gui calculates it)
class PTModifiers(object):
    def __init__(self):
        self._modifiers = []
    def add(self, PT):
        self._modifiers.append(PT)
        #self.subrole.send(PowerToughnessChangedEvent())
        def remove():
            self._modifiers.remove(PT)
            #self.subrole.send(PowerToughnessChangedEvent())
        return remove
    def calculate(self, power, toughness):
        return reduce(lambda PT, modifier: modifier.calculate(PT[0], PT[1]), self._modifiers, (power, toughness))
    def __str__(self):
        return ', '.join([str(modifier) for modifier in self._modifiers])

class _base_characteristic(object): pass

class no_characteristic(_base_characteristic):
    # This characterisitic matches nothing
    def __eq__(self, other): return False
    def __contains__(self, val): return self == val
    def intersects(self, other): return False
    def __str__(self): return ""
    def __repr__(self): return "no_characteristic()"
    def evaluate(self, fields): fields.clear()

class characteristic(_base_characteristic):
    # Internally stored as a set
    def __init__(self, *init_val):
        self.characteristics = set(init_val)
    def intersects(self, other): return len(self.characteristics.intersection(other)) > 0
    def __eq__(self, other): return other in self.characteristics
    def __contains__(self, val): return self == val
    def __str__(self): return str(' '.join(sorted(self.characteristics)))
    def __repr__(self): return "characteristic(%s)"%', '.join(map(repr, self.characteristics))
    def __len__(self): return len(self.characteristics)
    def __iter__(self): return iter(self.characteristics)
    def evaluate(self, fields):
        fields.clear()
        fields.update(self.characteristics)

# These are only used internally
class all_characteristic(characteristic):
    def __init__(self, *init_val):
        super(all_characteristic, self).__init__(*init_val)
        self.text = 'all'
    def set_text(self, text):
        self.text = text
    def __str__(self): return self.text
    def __repr__(self): return "characteristic(%s)"%self.txt

class additional_characteristics(characteristic):
    def __eq__(self, other):
        if super(additional_characteristics, self).__eq__(other): return True
        else: return None
    def intersects(self, other):
        raise NotImplementedError()
    def __repr__(self): return  "Add '%s'"%str(self)
    def evaluate(self, fields): fields.update(self.characteristics)

class remove_characteristics(characteristic):
    def __eq__(self, other):
        if other in self: return False
        else: return None
    def intersects(self, other):
        raise NotImplementedError()
    def __repr__(self): return "Remove '%s'"%str(self)
    def evaluate(self, fields): fields.difference_update(self.characteristics)

class stacked_characteristic(object):
    stacked = True
    def __init__(self, card, orig, change_event):
        self._stacking = [orig]
        orig._copy_effect = True
        self.card = card
        self.change_event = change_event
    def _insert_into_stacking(self, char, pos=-1):
        if pos == -1: self._stacking.append(char)
        else: self._stacking.insert(pos, char)
        self.card.send(self.change_event)
        def remove():
            if char in self._stacking:
                self._stacking.remove(char)
                self.card.send(self.change_event)
        return remove
    def cda(self, *char):
        # Stick this after the card defined one
        return self._insert_into_stacking(characterstic(*char), 1)
    def set_copy(self, copy_char):
        # find last copy effect
        copy_char._copy_effect = True
        for i, char in enumerate(self._stacking):
            if not hasattr(char, "_copy_effect"): break
        else: i += 1
        return self._insert_into_stacking(copy_char, pos=i)
    def set(self, *new_char):
        return self._insert_into_stacking(characteristic(*new_char))
    def add(self, *new_char):
        return self._insert_into_stacking(additional_characteristics(*new_char))
    def add_all(self, all_char, text):
        char = all_characteristic(*all_char)
        char.set_text(text)
        return self._insert_into_stacking(char)
    def remove(self, *old_char):
        return self._insert_into_stacking(remove_characteristics(*old_char))
    def remove_all(self):
        return self._insert_into_stacking(no_characteristic())
    def stacking(self): return len(self._stacking) > 1
    def __eq__(self, other): return other in self.current
    def __contains__(self, val): return self == val
    def intersects(self, other):
        if isinstance(other, _base_characteristic): return other.intersects(self.current)
        else: return len(self.current.intersection(other)) > 0
    def __str__(self):
        curr = sorted(self.current)
        if len(curr) > 10: return '%s...'%' '.join(curr[:10])
        else: return ' '.join(curr)
    def __len__(self): return len(self.current)
    def __iter__(self): return iter(self.current)
    def __repr__(self):
        return "stacked: %s"%repr(self._stacking)
    current = property(fget = lambda self: self._get_unique())
    def _get_unique(self):
        # XXX Todo - add caching
        final = set()
        for char in self._stacking: char.evaluate(final)
        return final

class stacked_type(stacked_characteristic):
    def __init__(self, card, orig, change_event):
        super(stacked_type, self).__init__(card, orig, change_event)
    def _insert_into_stacking(self, char, pos=-1):
        if pos == -1: self._stacking.append(char)
        else: self._stacking.insert(pos, char)
        # Make sure the type isn't already that type
        self.card.add_basecls()
        self.card.send(self.change_event)
        def remove():
            if char in self._stacking:
                self._stacking.remove(char)
                self.card.send(self.change_event)
        return remove
