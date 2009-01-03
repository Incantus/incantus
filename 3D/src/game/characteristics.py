import copy
from GameEvent import ControllerChanged, PowerToughnessModifiedEvent

class stacked_variable(object):
    current = property(fget=lambda self: self._characteristics[-1][0])
    def __init__(self, card, initial, change_event):
        self._characteristics = [(initial,)]
        self.card = card
        self.change_event = change_event
        self._copyable_index = 0
    def cda(self, var):
        new = (var,)
        self._characteristics.append(new)
        self.card.send(self.change_event)
        return lambda: not self.card.is_LKI and self._characteristics.remove(new)
    copyable = property(fget=lambda self: self._characteristics[self._copyable_index][0])
    def set_copy(self, var, extra=None):
        new = (var,)
        self._copyable_index += 1
        self._characteristics.insert(self._copyable_index, new)
        self.card.send(self.change_event)
        def reverse():
            if not self.card.is_LKI:
                self._characteristics.remove(new)
                self.card.send(self.change_event)
                self._copyable_index -= 1
        return reverse
    def __getattr__(self, attr): return getattr(self.current, attr)
    def __eq__(self, other): return self.current == other
    def __str__(self): return str(self.current)
    def __repr__(self): return repr(self._characteristics)
    def __int__(self): return int(self.current)

class stacked_controller(object):
    current = property(fget=lambda self: self._controllers[-1][0])
    def __init__(self, perm, initial):
        self.perm = perm
        self._controllers = [(initial,)]
        self.perm.summoningSickness()
    def set(self, new_controller):
        old_controller = self.current
        contr = (new_controller,)
        self._controllers.append(contr)
        if not new_controller == old_controller: self.controller_change(old_controller)
        def remove():
            if not self.perm.is_LKI:
                orig = self.current
                self._controllers.remove(contr)
                if orig != self.current: self.controller_change(orig)
        return remove
    def controller_change(self, old_controller):
        self.perm.summoningSickness()
        self.perm.send(ControllerChanged(), original=old_controller)

# PowerToughnessModified isn't needed, because the power/toughness is invalidated every timestep (and the gui calculates it)
class PTModifiers(object):
    def __init__(self, card):
        self._modifiers = []
        self.card = card
    def add(self, PT):
        self._modifiers.append(PT)
        self.card.send(PowerToughnessModifiedEvent())
        def remove():
            if not self.card.is_LKI:
                self._modifiers.remove(PT)
                self.card.send(PowerToughnessModifiedEvent())
        return remove
    def calculate(self, power, toughness):
        return reduce(lambda PT, modifier: modifier.calculate(PT[0], PT[1]), self._modifiers, (power, toughness))
    def __str__(self):
        return ', '.join([str(modifier) for modifier in self._modifiers])

class _base_characteristic(object): pass

class characteristic(_base_characteristic):
    # Internally stored as a set
    def __init__(self, *init_val):
        self.characteristics = set(init_val)
    def add(self, *additional):
        self.characteristics.update(set(additional))
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

class no_characteristic(characteristic):
    # This characteristic matches nothing
    # XXX I should really remove this, it's not needed anymore now that removal is based on sets
    # and no_characteristic() is just characteristic with no arguments (so an empty set)
    def __init__(self):
        super(no_characteristic, self).__init__()

# These are only used internally
class all_characteristic(characteristic):
    def __init__(self, *init_val):
        super(all_characteristic, self).__init__(*init_val)
        self.text = 'all'
    def set_text(self, text):
        self.text = text
    def __str__(self): return self.text
    def __repr__(self): return "characteristic(%s)"%self.text

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
    def __init__(self, card, orig, change_event):
        self._stacking = [orig]
        orig._copyable = True
        self.card = card
        self.change_event = change_event
    def _insert_into_stacking(self, char, pos=-1):
        if pos == -1: self._stacking.append(char)
        else: self._stacking.insert(pos, char)
        self.card.send(self.change_event)
        def remove():
            if not self.card.is_LKI and char in self._stacking:
                self._stacking.remove(char)
                self.card.send(self.change_event)
        return remove
    def _after_last_copyable_index():
        def fget(self):
            for i, char in enumerate(self._stacking):
                if not hasattr(char, "_copyable"): break
            else: i += 1
            return i
        return locals()
    _after_last_copyable_index = property(**_after_last_copyable_index())
    def cda(self, *char):
        # Stick this after the card defined one and all copy effects
        cda_char = characteristic(*char)
        return self._insert_into_stacking(cda_char, pos=self._after_last_copyable_index)
    copyable = property(fget = lambda self: self._stacking[self._after_last_copyable_index-1])
    def set_copy(self, chargroup, extra_chars=None):
        # find last copy effect
        chargroup = copy.copy(chargroup)
        if extra_chars:
            if not (type(extra_chars) == list or type(extra_chars) == tuple): extra_chars = (extra_chars,)
            chargroup.add(*extra_chars)
        chargroup._copyable = True
        return self._insert_into_stacking(chargroup, pos=self._after_last_copyable_index)
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
    def _insert_into_stacking(self, char, pos=-1):
        if pos == -1: self._stacking.append(char)
        else: self._stacking.insert(pos, char)
        if str(self.card.zone) == "play": self.card.add_basecls()
        self.card.send(self.change_event)
        def remove():
            if not self.card.is_LKI and char in self._stacking:
                self._stacking.remove(char)
                self.card.send(self.change_event)
        return remove
