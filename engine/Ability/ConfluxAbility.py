from engine.Match import isLand
from engine.symbols.subtypes import all_basic_lands

def domain(player):
    landtypes = reduce(lambda s, l: s.union(l.subtypes.current), player.battlefield.get(isLand), set())
    landtypes.intersection_update(all_basic_lands)
    return landtypes
