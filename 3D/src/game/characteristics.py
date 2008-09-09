
class _base_characteristic(object): pass

class characteristic(_base_characteristic):
    # Internally stored as a set
    def __init__(self, *init_val):
        self.characteristics = set(init_val)
    def intersects(self, other):
        if not isinstance(other, characteristic): return other.intersects(self)
        else: return len(self.characteristics.intersection(other.characteristics)) > 0
    def __eq__(self, other): return other in self.characteristics
    def __contains__(self, val): return self == val
    def __str__(self): return str(' '.join(self.characteristics))
    def __repr__(self): return "characteristic([%s])"%', '.join(map(repr, self.characteristics))
    def __len__(self): return len(self.characteristics)
    def make_text_line(self, fields): fields[:] = self.characteristics

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
    def set_copy(self, copy_char):
        # find last copy effect
        copy_char._copy_effect = True
        for i, char in enumerate(self._stacking):
            if not hasattr(char, "_copy_effect"): break
        else: i += 1
        return self._insert_into_stacking(copy_char, pos=i)
    def set(self, new_char):
        return self._insert_into_stacking(characteristic(new_char))
    def add(self, new_char):
        return self._insert_into_stacking(additional_characteristic(new_char))
    def add_all(self):
        return self._insert_into_stacking(all_characteristics())
    def remove_all(self):
        return self._insert_into_stacking(no_characteristic())
    def stacking(self): return len(self._stacking) > 1
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
    def __len__(self):
        fields = []
        for char in self._stacking: char.make_text_line(fields)
        return len(set(fields))
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
