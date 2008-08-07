import copy

class abilities(object):
    # Internally stored as a list
    def __init__(self, initial):
        if not (type(initial) == tuple or type(initial) == list): initial = [initial]
        self._abilities = initial
        self.enabled = False
    def __len__(self): return len(self._abilities)
    def add(self, ability):
        self._abilities.append(ability)
    def activated(self):
        return [ability for ability in self._abilities if hasattr(ability, "cost") and not ability.is_limited()]
    def enteringZone(self, zone):
        if not self.enabled:
            self.enabled = True
            for ability in self._abilities:
                if (ability.zone == "all" or ability.zone == zone) and not hasattr(ability, "cost"): ability.enteringZone()
    def leavingZone(self, zone):
        if self.enabled:
            self.enabled = False
            for ability in self._abilities:
                if (ability.zone == "all" or ability.zone == zone) and not hasattr(ability, "cost"): ability.leavingZone()
    #def copy(self, card):
    #    new_abilities = [a.copy(card) for a in self._abilities]
    #    return self.__class__(new_abilities)
    def __str__(self): return '\n'.join(map(str, self._abilities))

class no_abilities(object): pass
class additional_abilities(abilities): pass

# This is only valid in a single zone
class stacked_abilities(object):
    stacked = True
    def __init__(self, card):
        self._stacking = [card.abilities]
        self.card = card
        self.card.abilities = self
        self.zone = str(card.zone)
    def __str__(self):
        s = []
        for a in self._stacking:
            if isinstance(a, no_abilities): break
            else: s.append(str(a))
        return '\n'.join(s)
    def add_abilities(self, abilities):
        abilities = additional_abilities(abilities)
        self._stacking.insert(0, abilities)
        abilities.enteringZone(self.zone)
        def remove():
            if abilities in self._stacking:
                self._stacking.remove(abilities)
                abilities.leavingZone(self.zone)
            if not self.stacking(): self.card.abilities = self.pop()
        return remove
    def remove_all(self):
        # first disable all previously active abilities
        for a in self._stacking:
            if isinstance(a, no_abilities): break
            a.leavingZone(self.zone)
        no = no_abilities()
        self._stacking.insert(0, no)
        def remove():
            if no in self._stacking:
                # Restore previously disabled abilities
                restore = True
                i = self._stacking.index(no)
                for a in self._stacking[:i]:
                    if isinstance(a, no_abilities):
                        restore = False
                        break
                self._stacking.pop(i)
                if restore:
                    for a in self._stacking[i:]:
                        if isinstance(a, no_abilities): break
                        else: a.enteringZone(self.zone)
            if not self.stacking(): self.card.abilities = self.pop()
        return remove
    def stacking(self): return len(self._stacking) > 1
    def pop(self): return self._stacking.pop()
    def process_stacked(self, func, total):
        for a in self._stacking:
            if isinstance(a, no_abilities): break
            else: total += getattr(a, func).__call__()
        return total
    def activated(self): return self.process_stacked("activated", [])
    def __len__(self): return self.process_stacked("__len__", 0)
    #def enteringZone(self, zone):
    #    for a in self._stacking: a.enteringZone(zone)
    def leavingZone(self, zone):
        for a in self._stacking: 
            if isinstance(a, no_abilities): break
            else: a.leavingZone(zone)
