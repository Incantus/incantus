from engine.Match import isLand
from Subtypes import all_basic_lands

def domain(player):
    landtypes = reduce(lambda s, l: s.union(l.subtypes.current), player.play.get(isLand))
    return landtypes.intersection_update(all_basic_lands)
