
class characteristic(object):
    is_characteristic = True
    # Internally stored as a set
    def __init__(self, init_val): 
        if not (type(init_val) == tuple or type(init_val) == list): init_val = [init_val]
        self.characteristics = set(init_val)
    def intersects(self, other):
        if not hasattr(other, "characteristics"): return other.intersects(self)
        else: return len(self.characteristics.intersection(other.characteristics)) > 0
    def __eq__(self, other):
        if type(other) == str: return other in self
        else: return other == self
    def __contains__(self, val):
        return val in self.characteristics
    def __str__(self):
        return str(', '.join(self.characteristics))
    def __repr__(self):
        return "['%s']"%str(self)
    def copy(self):
        newchar = characteristic([])
        newchar.characteristics = self.characteristics.copy()
        return newchar

class all_characteristics(object):
    is_characteristic = True
    # This characteristic matches everything
    def __init__(self): pass
    def __eq__(self, other): return True
    def __contains__(self, val): return True
    def intersects(self, other): return True
    def copy(self): return all_characteristics()
    def __str__(self): return "All"
    def __repr__(self): return repr("All")

class no_characteristic(object):
    is_characteristic = True
    # This characterisitic matches nothing
    def __init__(self): pass
    def intersects(self, other): return False
    def __eq__(self, other): return False
    def copy(self): return no_characteristics()
    def __contains__(self, val): return False
    def __str__(self): return "None"
    def __repr__(self): return repr("None")

# These are only used internally
class add_characteristic(object):
    is_characteristic = True
    def __init__(self, init_val):
        self.characteristic = init_val
    def __eq__(self, other):
        if other == self.characteristic: return True
        else: return None
    def intersects(self, other):
        if self.characteristic in other: return True
        else: return None
    def __str__(self):
        return "Add %s"%str(self.characteristic)
    def __repr__(self):
        return  "'%s'"%str(self)
    def copy(self): return add_characteristic(self.characteristic)

class remove_characteristic(object):
    is_characteristic = True
    def __init__(self, init_val):
        self.characteristic = init_val
    def __eq__(self, other):
        if other == self.characteristic: return False
        else: return None
    def intersects(self, other):
        raise NotImplementedError()
        #if self.characteristic in other: return False
        #else: return None
    def __str__(self):
        return "Remove %s"%str(self.characteristic)
    def __repr__(self):
        return "'%s'"%str(self)
    def copy(self): return remove_characteristic(self.characteristic)

class stacked_characteristic(object):
    stacked = True
    def __init__(self, orig):
        self.characteristics = [orig]
    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)
    def remove_characteristic(self, characteristic):
        for i, c in enumerate(self.characteristics):
            if characteristic is c: break
        else: raise ValueError
        self.characteristics.pop(i)
    def stacking(self):
        return len(self.characteristics) > 1
    def __eq__(self, other):
        result = False
        for char in self.characteristics:
            check =  char == other
            if check == True: result = True
            elif check == False: result = False
            elif check == None: pass
        return result
    def intersects(self, other):
        result = False
        for char in self.characteristics:
            check = char.intersects(other)
            if check == True: result = True
            elif check == False: result = False
            elif check == None: pass
        return result
    def __repr__(self):
        return "[stacked_characteristic: %s]"%repr(self.characteristics)


if __name__ == "__main__":

    subtypes = characteristic(["Goblin", "Warrior"])
    changeling = all_characteristics()
    clear = no_characteristic()
    no_elf = remove_characteristic("Elf")
    add_merfolk = add_characteristic("Merfolk")

    Elf = characteristic(["Elf", "Warrior"])

    def check(msg, subtype):
        print "%s: %s"%(msg, subtype.characteristics)
        for t in ["Elf", "Goblin", "Merfolk"]:
            print "\tcard is %s:"%t, subtype == t
        print "\tCard intersect [%s]"%Elf, subtype.intersects(Elf)

    stacked = stacked_characteristic(subtypes)
    check("Starting %s"%subtypes, stacked)
    stacked.add_characteristic(changeling)
    check("Adding %s"%changeling, stacked)
    stacked.add_characteristic(no_elf)
    check("Adding %s"%no_elf, stacked)
    stacked.add_characteristic(clear)
    check("Adding %s"%clear, stacked)
    stacked.add_characteristic(add_merfolk)
    check("Adding %s"%add_merfolk, stacked)
    stacked.remove_characteristic(changeling)
    check("Removing %s"%changeling, stacked)
    stacked.remove_characteristic(clear)
    check("Removing %s"%clear, stacked)
