class abilities(object):
    # Internally stored as a list
    def __init__(self):
        self._abilities = []
        self._keywords = {}
    def add(self, ability):
        if type(ability) == tuple:
            self._abilities.extend(ability)
        else:
            self._abilities.append(ability)
            if ability.keyword: self._keywords[ability.keyword] = ability
    def attached(self): return [ability for ability in self._abilities if ability.zone == "attached"]
    def activated(self, source): return [ability for ability in self._abilities if hasattr(ability, "activated") and ability.playable(source)]
    def enable(self, zone, source):
        for ability in self._abilities:
            if (ability.zone == "all" or ability.zone == zone): ability.enable(source)
    def disable(self, zone):
        for ability in self._abilities:
            if (ability.zone == "all" or ability.zone == zone): ability.disable()
    def toggle(self, zone, val):
        for ability in self._abilities:
            if (ability.zone == "all" or ability.zone == zone): ability.toggle(val)
    def __repr__(self): return ','.join([repr(a) for a in self._abilities])
    def __str__(self): return '\n'.join([str(a) for a in self._abilities if a.enabled if str(a)])
    def __len__(self): return len([a for a in self._abilities if a.enabled])
    def __contains__(self, keyword): # This is to match keyword abilities
        return keyword in self._keywords and self._keywords[keyword].enabled

class additional_abilities(abilities):
    def __init__(self, *abilities):
        super(additional_abilities, self).__init__()
        self._abilities.extend(abilities)
        for ability in abilities:
            if ability.keyword: self._keywords[ability.keyword] = ability

# This is only valid in a single zone
class stacked_abilities(object):
    stacked = True
    def __init__(self, source, abilities):
        abilities._copy_effect = True
        self._stacking = [abilities]
        self.source = source
        self.zone = None
    def __repr__(self): return "stacked: [%s]"%','.join(map(repr, self._stacking))
    def add(self, *abilities):
        abilities = additional_abilities(*abilities)
        self._stacking.insert(0, abilities)
        abilities.enable(self.zone, self.source)
        def restore():
            self._stacking.remove(abilities)
            abilities.disable(self.zone)
        return restore
    def remove(self, keyword):
        disabled = []
        for group in self._stacking:
            if keyword in group:
                a = group._keywords[keyword]
                a.toggle(self.zone, False)
                disabled.append(a)
        def restore():
            for a in disabled: a.toggle(self.zone, True)
        return restore
    def remove_all(self):
        # first disable all previous abilities
        disabled = []
        for a in self._stacking:
            disabled.append(a)
            a.toggle(self.zone, False)
        def remove():
            for a in disabled: a.toggle(self.zone, True)
        return remove
    def set_copy(self, abilities):
        abilities._copy_effect = True
        for i, ability in enumerate(self._stacking):
            if hasattr(ability, "_copy_effect"): break
        disabled = []
        if self.zone:
            for a in self._stacking[::-1]:
                if not hasattr(a, "_copy_effect"): break
                disabled.append(a)
                a.toggle(self.zone, False)
            abilities.enable(self.zone, self.source)
        self._stacking.insert(i, abilities)
        def restore():
            self._stacking.remove(abilities)
            abilities.disable(self.zone)
            for a in disabled: a.toggle(self.zone, True)
        return restore
    def stacking(self): return len(self._stacking) > 1
    def process_stacked(self, func, total, *args):
        for a in self._stacking:
            total += getattr(a, func).__call__(*args)
            if hasattr(a, "_copy_effect"): break
        return total
    def attached(self): return self.process_stacked("attached", [])
    def activated(self): return self.process_stacked("activated", [], self.source)
    def __len__(self): return self.process_stacked("__len__", 0)
    def __contains__(self, keyword): return self.process_stacked("__contains__", False, keyword) > 0
    def enteringZone(self, zone):
        # This is only called when the card is moved to a new zone
        self.zone = zone
        for a in self._stacking:
            a.enable(zone, self.source)
            if hasattr(a, "_copy_effect"): break
    def leavingZone(self, zone):
        for a in self._stacking:
            a.disable(zone)
            if hasattr(a, "_copy_effect"): break
        self.zone = None
    def __str__(self):
        string = []
        for a in self._stacking:
            string.append(str(a))
            if hasattr(a, "_copy_effect"): break
        return '\n'.join(string)
