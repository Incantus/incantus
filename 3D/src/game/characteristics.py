import copy

class characteristic(object):
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
    def __repr__(self): return "%s"%str(self)
    def copy(self): return copy.copy(self)
    def make_text_line(self, fields): fields[:] = self.characteristics

class all_characteristics(object):
    # This characteristic matches everything
    def __eq__(self, other): return True
    def __contains__(self, val): return self == val
    def intersects(self, other): return True
    def copy(self): return all_characteristics()
    def __str__(self): return "All"
    def __repr__(self): return repr("All")
    def make_text_line(self, fields): fields[:] = ["All"]

class no_characteristic(object):
    # This characterisitic matches nothing
    def __eq__(self, other): return False
    def __contains__(self, val): return self == val
    def intersects(self, other): return False
    def copy(self): return no_characteristic()
    def __str__(self): return ""
    def __repr__(self): return repr("None")
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
    def __init__(self, orig):
        self._stacking = [orig]
    def add(self, characteristic):
        self._stacking.append(characteristic)
    def remove(self, characteristic):
        for i, c in enumerate(self._stacking):
            if characteristic is c: break
        else: raise ValueError
        self._stacking.pop(i)
    def stacking(self): return len(self._stacking) > 1
    def pop(self): return self._stacking.pop()
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
        return "[stacked_characteristic: %s]"%repr(self._stacking)

if __name__ == "__main__":

    subtypes = characteristic(["Goblin", "Warrior"])
    changeling = all_characteristics()
    clear = no_characteristic()
    #no_elf = remove_characteristic("Elf")
    add_merfolk = additional_characteristic("Merfolk")

    Elf = characteristic(["Elf", "Warrior"])

    def check(msg, subtype):
        print "%s: %s"%(msg, subtype.characteristics)
        for t in ["Elf", "Goblin", "Merfolk"]:
            print "\tcard is %s:"%t, subtype == t
        print "\tCard intersect [%s]"%Elf, subtype.intersects(Elf)

    stacked = stacked_characteristic(subtypes)
    check("Starting %s"%subtypes, stacked)
    stacked.add(changeling)
    check("Adding %s"%changeling, stacked)
    #stacked.add(no_elf)
    #check("Adding %s"%no_elf, stacked)
    stacked.add(clear)
    check("Adding %s"%clear, stacked)
    stacked.add(add_merfolk)
    check("Adding %s"%add_merfolk, stacked)
    stacked.remove(changeling)
    check("Removing %s"%changeling, stacked)
    stacked.remove(clear)
    check("Removing %s"%clear, stacked)
