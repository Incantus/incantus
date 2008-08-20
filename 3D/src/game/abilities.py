import copy

class abilities(object):
    # Internally stored as a list
    def __init__(self):
        self._abilities = []
        self._keywords = set()
        self.enabled = False
    def __len__(self): return len(self._abilities)
    def __contains__(self, keyword): # This is to match keyword abilities
        return keyword in self._keywords
    def add(self, ability):
        self._abilities.append(ability)
        if ability.keyword: self._keywords.add(ability.keyword)
    def attached(self): return [ability for ability in self._abilities if ability.zone == "attached"]
    def activated(self, source):
        return [ability for ability in self._abilities if hasattr(ability, "activated") and ability.playable(source)]
    def enteringZone(self, zone, source):
        if not self.enabled:
            self.enabled = True
            for ability in self._abilities:
                if (ability.zone == "all" or ability.zone == zone) and not hasattr(ability, "activated"): ability.enteringZone(source)
    def leavingZone(self, zone):
        if self.enabled:
            self.enabled = False
            for ability in self._abilities:
                if (ability.zone == "all" or ability.zone == zone) and not hasattr(ability, "activated"): ability.leavingZone()
    def __str__(self): return '\n'.join(map(str, self._abilities))

class additional_abilities(abilities):
    def __init__(self, abilities):
        super(additional_abilities, self).__init__()
        if not type(abilities) == list: abilities = [abilities]
        self._abilities.extend(abilities)
        for ability in abilities:
            if ability.keyword: self._keywords.add(ability.keyword)
class no_abilities(object): pass
class remove_ability(object):
    def __init__(self, keyword):
        self.keyword = keyword

# This is only valid in a single zone
class stacked_abilities(object):
    stacked = True
    def __init__(self, source, abilities):
        self._stacking = [abilities]
        self.source = source
    def __str__(self):
        s = []
        for a in self._stacking:
            if isinstance(a, no_abilities): break
            else: s.append(str(a))
        return '\n'.join(s)
    def add(self, abilities):
        abilities = additional_abilities(abilities)
        self._stacking.insert(0, abilities)
        abilities.enteringZone(self.zone, self.source)
        def remove():
            if abilities in self._stacking:
                self._stacking.remove(abilities)
                abilities.leavingZone(self.zone)
        return remove
    def remove_one(self, keyword):
        # XXX This logic is broken
        # disable up to the previous remove_all
        disabled = []
        for group in self._stacking:
            if isinstance(a, no_abilities): break
            for a in group:
                if a.txt == keyword:
                    disabled.append(a)
                    a.leavingZone(self.zone)
        rem_one = remove_ability(keyword)
        self._stacking.insert(0, rem_one)
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
                        else: a.enteringZone(self.zone, self.source)
        return remove
    def stacking(self): return len(self._stacking) > 1
    def pop(self): return self._stacking.pop()
    def process_stacked(self, func, total, *args):
        for a in self._stacking:
            if isinstance(a, no_abilities): break
            else: total += getattr(a, func).__call__(*args)
        return total
    def attached(self): return self.process_stacked("attached", [])
    def activated(self): return self.process_stacked("activated", [], self.source)
    def __len__(self): return self.process_stacked("__len__", 0)
    def __contains__(self, keyword): return self.process_stacked("__contains__", False, keyword) > 0
    def enteringZone(self, zone):
        self.zone = zone
        for a in self._stacking: a.enteringZone(zone, self.source)
    def leavingZone(self, zone):
        for a in self._stacking:
            if isinstance(a, no_abilities): break
            else: a.leavingZone(zone)
