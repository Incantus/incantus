import weakref
from GameEvent import AbilitiesModifiedEvent
from Util import isiterable
from Ability.Limit import MultipleLimits, InstantLimit

__all__ = ["abilities", "stacked_abilities"]

class abilities(object):
    # Internally stored as a list
    def __init__(self):
        self._abilities = []
        self._keywords = {}
    def add(self, ability, tag=''):
        if isiterable(ability):
            self._abilities.extend(ability)
        else:
            ability.tag = tag
            self._abilities.append(ability)
            if ability.keyword: self._keywords[ability.keyword] = ability
    def _check_zone(self, ability, zone):
        ability_zone = ability.zone
        return (ability_zone == "all" or 
                (ability_zone == "non-battlefield" and not zone == "battlefield") or
                ability_zone == zone)
    def enable(self, zone, source):
        for ability in self._abilities:
            if self._check_zone(ability, zone): ability.enable(source)
    def disable(self, zone):
        for ability in self._abilities:
            if self._check_zone(ability, zone): ability.disable()
    def toggle(self, zone, val):
        for ability in self._abilities:
            if self._check_zone(ability, zone): ability.toggle(val)
    abilities = property(fget=lambda self: [ability for ability in self._abilities if ability.enabled])
    def attached(self):
        # Need to return both enabled/disabled abilities, so they can be toggled
        return [ability for ability in self._abilities if ability.zone == "attached"]
    def cast(self): return [ability for ability in self._abilities if hasattr(ability, "cast")]
    def activated(self): return [ability for ability in self.abilities if hasattr(ability, "activated") and ability.playable()]
    def __repr__(self): return '\n'.join(map(repr, self._abilities))
    def __str__(self): return '\n'.join([str(ability) for ability in self.abilities if str(ability)])
    def __len__(self): return len(self.abilities)
    def __iter__(self): return iter(self.abilities)
    def __contains__(self, keyword): # This is to match keyword abilities
        return keyword in self._keywords
    def copy(self):
        newabilities = abilities()
        for ability in self._abilities: newabilities.add(ability.copy())
        return newabilities

class additional_abilities(abilities):
    def __init__(self, *abilities):
        super(additional_abilities, self).__init__()
        self._abilities.extend(abilities)
        for ability in abilities:
            if ability.keyword: self._keywords[ability.keyword] = ability

# This is only valid in a single zone
# Abilities are stored in reverse - the front of the list has the most recently added abilities (the end of the list contains the original card defined abilities)
class stacked_abilities(object):
    def __init__(self, source, abilities):
        abilities._copyable = True
        self._stacking = [abilities]
        self.source = weakref.ref(source)
        self.zone = None
    def _current():
        def fget(self):
            for group in self._stacking:
                yield group
                if hasattr(group, "_copyable"): break
        return locals()
    _current = property(**_current())

    def add(self, *abilities):
        abilities = additional_abilities(*abilities)
        self._stacking.insert(0, abilities)
        abilities.enable(self.zone, self.source())
        attached = False
        if (hasattr(self.source(), "attached_to") and self.source().attached_to):
            abilities.enable("attached", self.source())
            attached = True
        self.source().send(AbilitiesModifiedEvent())
        def restore():
            if not self.source().is_LKI:
                self._stacking.remove(abilities)
                abilities.disable(self.zone)
                if attached: abilities.disable("attached")
        return restore
    def remove(self, keyword):
        disabled = []
        for group in self._stacking:
            if keyword in group:
                ability = group._keywords[keyword]
                ability.toggle(False)
                disabled.append(ability)
        self.source().send(AbilitiesModifiedEvent())
        def restore():
            if not self.source().is_LKI:
                for ability in disabled: ability.toggle(True)
        return restore
    def remove_by_tag(self, tag):
        found = False
        for group in self._stacking:
            for ability in group:
                if hasattr(ability, "tag") and tag == ability.tag:
                    found = True
                    break
            if found: break
        else: raise Exception("Trying to remove a specific ability that doesn't exist")
        ability.toggle(False)
        self.source().send(AbilitiesModifiedEvent())
        return lambda: not self.source().is_LKI and ability.toggle(True)
    def remove_all(self):
        # first disable all previous abilities
        disabled = []
        for group in self._stacking:
            disabled.append(group)
            group.toggle(self.zone, False)
        self.source().send(AbilitiesModifiedEvent())
        def remove():
            if not self.source().is_LKI:
                for group in disabled: group.toggle(self.zone, True)
        return remove
    copyable = property(fget=lambda self: tuple(self._current)[-1])
    def set_copy(self, abilities, extra_abilities=None):
        # abilities is an abilities object (a group of abilities)
        abilities = abilities.copy()
        if extra_abilities:
            if type(extra_abilities) == list or type(extra_abilities) == tuple: extra_abilities = [ability.copy() for ability in extra_abilities]
            else: extra_abilities = [extra_abilities.copy()]
            abilities.add(*extra_abilities)
        abilities._copyable = True

        for i, group in enumerate(self._stacking):
            if hasattr(group, "_copyable"): break
        disabled = []
        for group in self._stacking[::-1]:
            if not hasattr(group, "_copyable"): break
            disabled.append(group)
            group.toggle(self.zone, False)
        abilities.enable(self.zone, self.source())
        self._stacking.insert(i, abilities)
        self.source().send(AbilitiesModifiedEvent())
        def restore():
            if not self.source().is_LKI:
                self._stacking.remove(abilities)
                abilities.disable(self.zone)
                for group in disabled: group.toggle(self.zone, True)
        return restore
    def process_stacked(self, func, total, *args):
        for group in self._current:
            total += getattr(group, func).__call__(*args)
        return total
    def cast(self):
        # XXX Only return the most recent?
        return self.process_stacked("cast", [])[-1]
    def attached(self): return self.process_stacked("attached", [])
    def activated(self): return self.process_stacked("activated", [])
    def mana_abilities(self): return [ability for ability in self.activated() if hasattr(ability, "mana_ability") and not (isinstance(ability.limit, InstantLimit) or (isinstance(ability.limit, MultipleLimits) and any((True for limit in ability.limit.limits if isinstance(limit, InstantLimit)))))]
    def __len__(self): return self.process_stacked("__len__", 0)
    def __contains__(self, keyword): return self.process_stacked("__contains__", False, keyword) > 0
    def __iter__(self):
        for group in self._current:
            for ability in group: yield ability
    def find_tag(self, tag):
        for ability in self:
            if tag == ability.tag: return True
        else: return False
    def enteringZone(self):
        # This is only called when the card is moved to a new zone
        source = self.source()
        self.zone = str(source.zone)
        for group in self._current: group.enable(self.zone, source)
    def leavingZone(self):
        for group in self._current: group.disable(self.zone)
        self.zone = None
    def __str__(self):
        return '\n'.join([str(group) for group in self._current if str(group)])
    def __repr__(self): return "[%s]"%('\n%s\n'%('-'*80)).join(map(repr, self._stacking))
