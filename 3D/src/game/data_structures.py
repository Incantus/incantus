class keywords(object):
    def __init__(self, counts=[]):
        self.counts = dict([(k,1) for k in counts])
    def add(self, keyword):
        if self.counts.has_key(keyword): self.counts[keyword] += 1
        else: self.counts[keyword] = 1
    def remove(self, keyword):
        self.counts[keyword] -= 1
        if self.counts[keyword] == 0: del(self.counts[keyword])
    def clear(self):
        self.counts.clear()
    def __contains__(self, keyword):
        return self.counts.__contains__(keyword)
    def __iter__(self):
        return iter(self.counts)
    def __str__(self):
        return ', '.join([k.title() for k in self.counts.keys()])
    def __repr__(self):
        return repr(self.counts.keys())

if __name__ == "__main__":
    import copy
    k = keywords()
    k.add("haste")
    k.add("forestwalk")
    k2 = copy.deepcopy(k)
    k2.add("first-strike")
