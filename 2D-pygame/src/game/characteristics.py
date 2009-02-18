class characteristic(object):
    is_characteristic = True
    # Internally stored as a set
    def __init__(self, init_val): 
        if not (type(init_val) == tuple or type(init_val) == list): init_val = [init_val]
        self.characteristics = set(init_val)
    def add(self, val):
        if type(val) == list or type(val) == tuple:
            for v in val: self.characteristics.add(v)
        else: self.characteristics.add(val)
    def remove(self, val):
        if type(val) == list or type(val) == tuple:
            for v in val: self.characteristics.remove(v)
        else: self.characteristics.remove(val)
    def intersects(self, other):
        if not hasattr(other, "characteristics"): return other.intersects(self)
        else: return len(self.characteristics.intersection(other.characteristics)) > 0
    def __eq__(self, other):
        if type(other) == str: return other in self
        else: return other == self
    def __neq__(self, other):
        return not self.characteristics == other
    def __contains__(self, val):
        return val in self.characteristics
    def __str__(self):
        return str(', '.join(self.characteristics))
    def __repr__(self):
        return "['%s']"%str(self)
    #def __iter__(self):
    #    return iter(self.characteristics)
    #def __copy__(self):
    #    return characteristic(self.characteristics)

class all_characteristics(object):
    is_characteristic = True
    # This characteristic matches everything
    def __init__(self): pass
    def add(self, val): pass
    def remove(self, val): pass
    def __eq__(self, other): return True
    def __neq__(self, other): return False
    def __contains__(self, val): return True
    def intersects(self, other): return True
    def __str__(self):
        return "All"
    def __repr__(self):
        return repr("All")

class no_characteristic(object):
    is_characteristic = True
    # This characterisitic matches nothing
    def __init__(self): pass
    def add(self, val): pass
    def remove(self, val): pass
    def intersects(self, other): return False
    def __eq__(self, other): return False
    def __neq__(self, other): return True
    def __contains__(self, val): return False
    def __str__(self):
        return "None"
    def __repr__(self):
        return repr("None")

