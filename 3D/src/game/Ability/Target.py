from game.Match import isPermanent, isPlayer, PlayerMatch, OpponentMatch, PlayerOrCreatureMatch
from game.GameEvent import InvalidTargetEvent

class NoTarget(object):
    def __init__(self): pass
    def get(self, card): return True
    def check_target(self, card): return True
    def get_targeted(self): return None

class MultipleTargets(object):
    def __init__(self, number, target_types, up_to=False, msg='', selector="controller"):
        self.number = number
        self.zones = []
        self.target = []
        self.up_to = up_to
        self.msg = msg
        self.selector = selector
        if not (type(target_types) == tuple or type(target_types) == list):
            self.target_types = [target_types]
        else: self.target_types = target_types
        def match_type(card):
            for match in self.target_types:
                if match(card): return True
            else: return False
        self.match_type = match_type
    def get_targeted(self): return self.target
    #def get_targeted(self): return [target.current_role if not isPlayer(target) else target for target in self.target]
    def check_target(self, card):
        # Remove any targets no longer in the correct zone, or no longer matching the original condition
        # XXX This is wrong - since it won't match up with the number requested
        final_targets = []
        for target, zone in zip(self.target, self.zones):
            if not isPlayer(target):
                if str(target.zone) == zone and self.match_type(target) and target.canBeTargetedBy(card): final_targets.append(target)
            else:
                if target.canBeTargetedBy(card): final_targets.append(target)
        self.target = final_targets
        self.zone = []
        return True
    def get_prompt(self, curr, card):
        number = self.number-curr
        if curr > 0: another = "another "
        else: another = "" 
        if self.up_to: another = "up to "+another
########
        if self.msg: prompt=self.msg
        elif self.target_types: prompt="Target %s%d %s(s) for %s"%(another,number, ' or '.join([str(t) for t in self.target_types]), card)
        else: prompt = "Select %s%d target(s) for %s"%(another,number,card)
        return prompt
    def get(self, card): 
        if self.selector == "opponent": selector = card.controller.opponent
        elif self.selector == "current_player":
            import game.GameKeeper
            selector = game.GameKeeper.Keeper.curr_player
        else: selector = card.controller
        i = 0
        targets = []
        while i <= self.number:
            target = selector.getTarget(self.target_types,zone="play",controller=card.controller,required=False,prompt=self.get_prompt(i, card.name))
            if target == False:
                if not self.up_to or len(targets) == 0: return False
                else: break
            elif target.canBeTargetedBy(card) and not target in targets:
                targets.append(target)
                i += 1
            else: player.send(InvalidTargetEvent(), target=target)
        # Got our targets, now save info:
        for target in targets:
            # The zone
            if not isPlayer(target): self.zones.append(str(target.zone))
            else: self.zones.append(None)
            target.isTargetedBy(card)
        self.target = targets
        return True

# When I add a new argument to constructor, make sure to add it to the copy function
# or use the copy module
class Target(object):
    def __init__(self, target_types=None, msg='', selector="controller", zone="play", player=None):
        self.target = None
        self.zone = zone
        self.player = player
        if not (type(target_types) == tuple or type(target_types) == list): self.target_types = [target_types]
        else: self.target_types = target_types
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
        self.untargeted = False
        self.required = True
    def get_targeted(self): return self.target
    #def get_targeted(self): return self.target.current_role if not isPlayer(self.target) else self.target
    def check_target(self, card):
        # Make sure the target is still in the correct zone (only for cards (and tokens), not players) and still matches original condition
        if not isPlayer(self.target):
            return (str(self.target.zone) == self.target_zone) and self.match_role == self.target.current_role and self.match_types(self.target) and (self.untargeted or self.target.canBeTargetedBy(card))
        else: return self.untargeted or self.target.canBeTargetedBy(card)
    def get(self, card):
        if self.msg: prompt=self.msg
        else:
            if self.zone != "play":
                if self.player == None: zl = " in any %s"%self.zone
                elif self.player == "you": zl = " in your %s"%self.zone
                else: zl = " in opponent %s"%self.zone
            else:
                if self.player == None: zl = ""
                elif self.player == "you": zl = " you control"
                else: zl = " opponent controls"
            prompt="Target %s%s for %s"%(' or '.join([str(t) for t in self.target_types]), zl, card)
        if self.selector == "opponent": selector = card.controller.opponent
        elif self.selector == "current_player":
            from game.GameKeeper import Keeper
            selector = Keeper.curr_player
        else: selector = card.controller
        if self.player == None: controller=None
        elif self.player == "you": controller=selector
        else: controller=selector.opponent
        # If required, make sure there is actually a target available
        if self.required and not self.targeting_player:
            perm = []
            sel_zone = getattr(selector, self.zone)
            opponent_zone = getattr(selector.opponent, self.zone)
            for ttype in self.target_types:
                if self.zone != "play":
                    if self.player == None: zones = [sel_zone, opponent_zone]
                    elif self.player == "you": zones = [sel_zone]
                    else: zones = [opponent_zone]
                    for zone in zones:
                        perm.extend([p for p in zone.get(ttype) if p.canBeTargetedBy(card)])
                else:
                    if self.player == None:
                        perm.extend([p for p in selector.play.get(ttype, all=True) if p.canBeTargetedBy(card)])
                    elif self.player == "you":
                        perm.extend([p for p in selector.play.get(ttype) if p.canBeTargetedBy(card)])
                    else:
                        perm.extend([p for p in selector.opponent.play.get(ttype) if p.canBeTargetedBy(card)])

            numtargets = len(perm)
            if numtargets == 0: return False
            elif numtargets == 1: self.target = perm[0]
            else:
                while True:
                    self.target = selector.getTarget(self.target_types,zone=self.zone,controller=controller,required=self.required,prompt=prompt)
                    if self.target.canBeTargetedBy(card): break
        else:
            self.target = selector.getTarget(self.target_types,zone=self.zone,controller=controller,required=False,prompt=prompt)
            if self.target == False: return False
        # Save the zone if we are targetting a permanent (not a player)
        if not isPlayer(self.target):
            self.target_zone = str(self.target.zone)
            self.match_role = self.target.current_role
        if self.target.canBeTargetedBy(card):
            self.target.isTargetedBy(card)
            return True
        else:
            selector.send(InvalidTargetEvent(), target=self.target)
            return False

class StackTarget(object):
    def __init__(self, target_types=None, msg=''):
        self.target = None
        if not (type(target_types) == tuple or type(target_types) == list):
            self.target_types = [target_types]
        else: self.target_types = target_types
        self.msg = msg
    def check_target(self, card):
        return card.controller.stack.on_stack(self.target)
    def get(self, card):
        if self.msg: prompt=self.msg
        elif self.target_types: prompt="Target %s for %s"%(' or '.join([str(t) for t in self.target_types]), card)
        else: prompt = "Select target for %s"%(card)
        self.target = card.controller.getTarget(self.target_types,required=False,prompt=prompt)
        if self.target == False: return False
        return self.target.can_be_countered()
