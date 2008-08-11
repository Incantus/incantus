
def _find_stacked(card, attr):
    original = getattr(card, attr)
    if hasattr(original, "stacked"): stacked = original
    else: stacked = stacked_characteristic(card, attr, None)
    return stacked
def set_characteristic(card, name, characteristic):
    stacked = _find_stacked(card, name)
    return stacked.set_characteristic(characteristic)
def add_characteristic(card, name, characteristic):
    stacked = _find_stacked(card, name)
    return stacked.add_characteristic(characteristic)
def add_all(card, name):
    stacked = _find_stacked(card, name)
    return stacked.add_all()
def remove_all(card, name):
    stacked = _find_stacked(card, name)
    return stacked.remove_all()

class _base_characteristic(object):
    pass
    #def set_characteristic(self, characteristic):
    #    return self._insert_into_stacking(characteristic(characteristic))
    #def add_characteristic(self, characteristic):
    #    return self._insert_into_stacking(additional_characteristic(characteristic))
    #def add_all(self):
    #    return self._insert_into_stacking(all_characteristics())
    #def remove_all(self):
    #    return self._insert_into_stacking(no_characteristic())

class characteristic(_base_characteristic):
    # Internally stored as a set
    def __init__(self, init_val):
        if not (type(init_val) == tuple or type(init_val) == list): init_val = [init_val]
        self.characteristics = set(init_val)
    def intersects(self, other):
        if not isinstance(other, characteristic): return other.intersects(self)
        else: return len(self.characteristics.intersection(other.characteristics)) > 0
    def __eq__(self, other): return other in self.characteristics
    def __contains__(self, val): return self == val
    def __str__(self): return str(' '.join(self.characteristics))
    def __repr__(self): return "characteristic([%s])"%', '.join(map(repr, self.characteristics))
    def make_text_line(self, fields): fields[:] = self.characteristics

class all_characteristics(_base_characteristic):
    # This characteristic matches everything
    def __eq__(self, other): return True
    def __contains__(self, val): return self == val
    def intersects(self, other): return True
    def __str__(self): return "All"
    def __repr__(self): return "all_characteristics()"
    def make_text_line(self, fields): fields[:] = ["All"]

class no_characteristic(_base_characteristic):
    # This characterisitic matches nothing
    def __eq__(self, other): return False
    def __contains__(self, val): return self == val
    def intersects(self, other): return False
    def __str__(self): return ""
    def __repr__(self): return "no_characteristic()"
    def make_text_line(self, fields): fields[:] = []

# These are only used internally
class additional_characteristic(characteristic):
    def __eq__(self, other):
        if super(additional_characteristic, self).__eq__(other): return True
        else: return None
    def intersects(self, other):
        if super(additional_characteristic, self).intersects(other): return True
        else: return None
    def __repr__(self): return  "Add '%s'"%str(self)
    def make_text_line(self, fields): fields.extend(self.characteristics)

#class remove_characteristic(characteristic):
#    def __eq__(self, other):
#        if other in self: return False
#        else: return None
#    def intersects(self, other):
#        raise NotImplementedError()
#        #if self.characteristic in other: return False
#        #else: return None
#    def __repr__(self): return "Remove '%s'"%str(self)
#    def make_text_line(self, fields):
#        if self.characteristic in fields: fields.remove(self.characteristic)

class stacked_characteristic(object):
    stacked = True
    def __init__(self, card, attr, change_event):
        self._stacking = [getattr(card, attr)]
        setattr(card, attr, self)
        self.card = card
        self.attr = attr
        self.change_event = change_event
    def _insert_into_stacking(self, char):
        self._stacking.append(char)
        self.card.send(self.change_event)
        def remove():
            if char in self._stacking:
                self._stacking.remove(char)
                self.card.send(self.change_event)
            if not self.stacking(): self.restore_original()
        return remove
    def set_characteristic(self, characteristic):
        return self._insert_into_stacking(characteristic(characteristic))
    def add_characteristic(self, characteristic):
        return self._insert_into_stacking(additional_characteristic(characteristic))
    def add_all(self):
        return self._insert_into_stacking(all_characteristics())
    def remove_all(self):
        return self._insert_into_stacking(no_characteristic())
    def stacking(self): return len(self._stacking) > 1
    def restore_original(self): setattr(self.card, self.attr, self._stacking.pop())
    def process_stacked(self, other, operator):
        result = False
        for char in self._stacking:
            check = operator(char, other)
            if check == True: result = True
            elif check == False: result = False
            elif check == None: pass
        return result
    def __eq__(self, other): return self.process_stacked(other, operator=lambda char, other: char == other)
    def __contains__(self, val): return self == val
    def intersects(self, other): return self.process_stacked(other, operator=lambda char, other: char.intersects(other))
    def __str__(self):
        fields = []
        for char in self._stacking: char.make_text_line(fields)
        return ' '.join(fields)
    def __repr__(self):
        return "stacked: %s"%repr(self._stacking)

if __name__ == "__main__":

    class Creature(object):
        def __init__(self, name, subtypes):
            self.name = name
            self.subtypes = characteristic(subtypes)
        def __str__(self):
            return "%s: %s"%(self.name, repr(self.subtypes))
        def send(self, *args, **kw): pass

    goblin = Creature("Hobgolin", ["Goblin", "Warrior"])
    elf = Creature("Llanowar Elves", ["Elf", "Warrior"])

    def check(msg, creature):
        print "%s:\n %s"%(msg, creature)
        for subtype in ["Elf", "Goblin", "Merfolk"]:
            print "\tcreature is %s:"%subtype, creature.subtypes == subtype
        print "\tCreature intersects (%s)"%elf, creature.subtypes.intersects(elf.subtypes)

    check("Starting", goblin)
    rem1 = add_all(goblin, "subtypes")
    check("Adding changeling", goblin)
    rem2 = remove_all(goblin, "subtypes")
    check("Removing all", goblin)
    add_characteristic(goblin, "subtypes", "Merfolk")
    check("Adding Merfolk", goblin)
    rem1()
    check("Removing changeling", goblin)
    rem2()
    check("Clearing no subtypes", goblin)
