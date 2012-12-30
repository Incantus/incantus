from engine.Util import isiterable
from engine.Match import isPermanent, isPlayer, PlayerMatch, OpponentMatch, PlayerOrCreatureMatch
from engine.GameEvent import InvalidTargetEvent

# XXX Fix the targeting code when i do multiplayer
__all__ = ["NoTarget", "InvalidTarget", "MultipleTargets",
           "Target", "StackTarget"]

class NoTarget(object):
    def __init__(self): pass
    def get(self, source): return True
    def check_target(self, source): return True
    def get_targeted(self): return None

class InvalidTarget(object):
    def __init__(self, original):
        self.original = original
    def no_op(self, *args, **kw): pass
    def __getattr__(self, attr): return self.no_op

class MultipleTargets(object):
    def __init__(self, target_types, number=1, up_to=False, distribute=0, distribute_type='', msg='', selector="controller", player=None, zone="battlefield", min=0):
        self.number = number
        self.distribute = distribute
        self.distribute_type = distribute_type
        # When you can distribute N among any number of targets
        if self.distribute > 0 and self.number == -1:
            self.number = self.distribute
        self.target = []
        self.up_to = up_to
        if msg and not isiterable(msg): self.msg = (msg,)
        else: self.msg = msg
        self.selector = selector
        self.player = player
        if not isiterable(target_types): self.target_types = (target_types,)
        else: self.target_types = tuple(target_types)
        def match_type(card):
            for match in self.target_types:
                if match(card): return True
            else: return False
        self.match_type = match_type
        self.zone = zone
        self.min = min # Sometimes you get "up to three target blahs", and sometimes you get "between two or three target blahs". Hopefully this should cover both.
    def get_targeted(self):
        if self.distribute == 0: return self.target
        else: return [(target, self.distribution.get(target, 0)) for target in self.target] # only return valid targets
    def check_target(self, source):
        # Remove any targets no longer in the correct zone, or no longer matching the original condition
        final_targets = []
        for target in self.target:
            if (not isinstance(target, InvalidTarget) and
               (isPlayer(target) or not target.is_LKI) and
               self.match_type(target) and
               target.canBeTargetedBy(source)): final_targets.append(target)
            else: final_targets.append(InvalidTarget(target))
        self.target = final_targets
        return len(self.target) == 0 or any([True for target in self.target if not isinstance(target, InvalidTarget)])
    def get_prompt(self, curr, source):
        number = self.number-curr
        if curr > 0: another = "another "
        else: another = ""
        if self.up_to: another = "up to "+another

        if self.zone == "battlefield":
            if isPlayer(self.player): zl = " %s controls"%self.player
            elif self.player == None: zl = ""
            elif self.player == "you": zl = " you control"
            else: zl = " opponent controls"
        else:
            if isPlayer(self.player): zl = " in %s's %s"%(self.player, self.zone)
            elif self.player == None: zl = " in any %s"%self.zone
            elif self.player == "you": zl = " in your %s"%self.zone
            else: zl = " in opponent's %s"%self.zone

        if self.msg:
            if curr <= len(self.msg): prompt=self.msg[curr]
            else: prompt = self.msg[-1]
        elif self.target_types: prompt="Target %s%d %s(s) %s for %s"%(another,number, ' or '.join([str(t) for t in self.target_types]),zl,source)
        else: prompt = "Select %s%d target(s) %s for %s"%(another,number,zl,source)
        return prompt
    def get(self, source):
        if isinstance(self.selector, str):
            if self.selector == "opponent": selector = source.controller.choose_opponent()
            elif self.selector == "active_player":
                import engine.GameKeeper
                selector = engine.GameKeeper.Keeper.active_player
            else: selector = source.controller
        if isPlayer(self.selector): selector = self.selector
        else: selector = source.controller
        i = 0
        targets = []
        while i < self.number:
            target = selector.getTarget(self.target_types,zone=self.zone,from_player=self.player,required=False,prompt=self.get_prompt(i, source.name))
            if target == False:
                if not self.up_to or len(targets) < self.min: return False
                else: break
            elif target.canBeTargetedBy(source) and not target in targets:
                targets.append(target)
                i += 1
            else: selector.send(InvalidTargetEvent(), target=target)

        # Now distribute among them if we need to
        if self.distribute > 0:
            self.distribution = selector.getDistribution(amount=self.distribute, targets=targets, prompt="Distribute %d %s among targets"%(self.distribute, self.distribute_type))

        # Got our targets, now save info:
        for target in targets:
            target.isTargetedBy(source)
        self.target = targets
        return True

# When I add a new argument to constructor, make sure to add it to the copy function
# or use the copy module
class Target(object):
    def __init__(self, target_types, msg='', selector="controller", zone="battlefield", player=None):
        self.is_valid = False
        self.target = None
        self.zone = zone
        self.player = player
        if not isiterable(target_types): self.target_types = (target_types,)
        else: self.target_types = tuple(target_types)
        # It should still be able to match any target types in the spell
        # See oracle for Putrefy (http://ww2.wizards.com/Gatherer/CardDetails.aspx?name=Putrefy)
        def match_types(card):
            for match in self.target_types:
                if match(card): return True
            else: return False
        self.match_types = match_types
        self.targeting_player = any(isinstance(ttype, match) for match in (PlayerMatch, OpponentMatch, PlayerOrCreatureMatch) for ttype in self.target_types)
        self.msg = msg
        self.selector = selector
        self.required = True
    def copy(self):
        return Target(self.target_types, self.msg, self.selector, self.zone, self.player)
    def get_targeted(self): 
        if self.is_valid: return self.target
        else: return InvalidTarget(self.target)
    def check_target(self, source):
        # Make sure the target is still in the correct zone (only for cards (and tokens), not players) and still matches original condition
        if not isPlayer(self.target):
            self.is_valid = (not self.target.is_LKI and self.match_types(self.target) and self.target.canBeTargetedBy(source))
        else: self.is_valid = self.target.canBeTargetedBy(source)
        return self.is_valid
    def get(self, source):
        if self.msg: prompt=self.msg
        else:
            if self.zone != "battlefield":
                if self.player == None: zl = " in any %s"%self.zone
                elif self.player == "you": zl = " in your %s"%self.zone
                else: zl = " in opponent %s"%self.zone
            else:
                if self.player == None: zl = ""
                elif self.player == "you": zl = " you control"
                else: zl = " opponent controls"
            prompt="Target %s%s for %s"%(' or '.join([str(t) for t in self.target_types]), zl, source)
        if self.selector == "opponent": selector = source.controller.choose_opponent()
        elif self.selector == "active_player":
            from engine.GameKeeper import Keeper
            selector = Keeper.active_player
        else: selector = source.controller
        # If required, make sure there is actually a target available
        if self.required and not self.targeting_player:
            perm = []
            if self.zone != "battlefield":
                zones = [getattr(selector, self.zone)] + [getattr(opponent, self.zone) for opponent in selector.opponents]
                if self.player == "you": zones = zones[:1]
                elif self.player == "opponent": zones = zones[1:]
                for ttype in self.target_types:
                    for zone in zones:
                        perm.extend([p for p in zone.get(ttype) if p.canBeTargetedBy(source)])
            else:
                for ttype in self.target_types:
                    if self.player == None:
                        perm.extend([p for p in selector.battlefield.get(ttype, all=True) if p.canBeTargetedBy(source)])
                    elif self.player == "you":
                        perm.extend([p for p in selector.battlefield.get(ttype) if p.canBeTargetedBy(source)])
                    else:
                        for opponent in selector.opponents:
                            perm.extend([p for p in opponent.battlefield.get(ttype) if p.canBeTargetedBy(source)])

            numtargets = len(perm)
            if numtargets == 0: return False
            elif numtargets == 1: self.target = perm[0]
            else:
                while True:
                    self.target = selector.getTarget(self.target_types,zone=self.zone,from_player=self.player,required=self.required,prompt=prompt)
                    if self.target.canBeTargetedBy(source): break
        else:
            self.target = selector.getTarget(self.target_types,zone=self.zone,from_player=self.player,required=False,prompt=prompt)
            if self.target == False: return False
        if self.target.canBeTargetedBy(source):
            self.target.isTargetedBy(source)
            self.is_valid = True
            return True
        else:
            selector.send(InvalidTargetEvent(), target=self.target)
            return False

class StackTarget(object):
    def __init__(self, target_types=None, msg=''):
        self.is_valid = False
        self.target = None
        if not isiterable(target_types): self.target_types = (target_types,)
        else: self.target_types = tuple(target_types)
        self.msg = msg
    def get_targeted(self):
        if self.is_valid: return self.target
        else: return InvalidTarget(self.target)
    def check_target(self, source):
        self.is_valid = self.target in source.controller.stack
        return self.is_valid
    def get(self, source):
        if self.msg: prompt=self.msg
        elif self.target_types: prompt="Target %s for %s"%(' or '.join([str(t) for t in self.target_types]), source)
        else: prompt = "Select target for %s"%(source)
        self.target = source.controller.getTarget(self.target_types,required=False,prompt=prompt)
        if self.target == False: return False
        self.is_valid = self.target.can_be_countered()
        return self.is_valid
