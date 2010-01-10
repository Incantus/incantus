from engine.Util import isiterable

def flatten(_tup):
    for t in _tup:
        if isiterable(t):
            for t2 in t: # It's only one level of nesting
                yield t2
        else: yield t

def unflatten(_tup, demux):
    i = 0
    for size in demux:
        yield (tuple(_tup[i:i+size]) if size > 1 else _tup[i])
        i += size
