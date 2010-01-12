from engine.Util import isiterable

__all__ = ["flatten"]

def count_nested(iterable):
    for t in iterable:
        if isiterable(t): yield len(t)
        else: yield 1

def demultiplex(iterable):
    for t in iterable:
        if isiterable(t):
            for t2 in t: # It's only one level of nesting
                yield t2
        else: yield t

def flatten(iterable):
    iterable = tuple(iterable)
    demux = tuple(count_nested(iterable))
    flattened = tuple(demultiplex(iterable))

    def unflatten(flat):
        i = 0
        for size in demux:
            yield (tuple(flat[i:i+size]) if size > 1 else flat[i])
            i += size

    return flattened, unflatten
