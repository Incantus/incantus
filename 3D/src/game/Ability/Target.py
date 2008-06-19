from game.GameObjects import MtGObject
from game.Match import isPermanent, isPlayer, SelfMatch, PlayerMatch, OpponentMatch, PlayerOrCreatureMatch
from game.GameEvent import InvalidTargetEvent

#class Target(MtGObject):
#    def __init__(self):
#        self.target = None
#    def copy(self):
#        pass
#    def check_target(self, card):
#        return True
#    def get(self, card):
#        return True

class AllPlayerTargets(MtGObject):
    def __init__(self):
        self.target = []
    def copy(self):
        return AllPlayerTargets()
    def check_target(self, card):
        return True
    def get(self, card):
        if self.target: return
        self.target = [card.controller, card.controller.opponent]
        return True

class AllPermanentTargets(MtGObject):
    def __init__(self, target_types=isPermanent):
        self.zones = []
        self.target = []
        if not (type(target_types) == tuple or type(target_types) == list):
            self.target_types = [target_types]
        else: self.target_types = target_types
    def copy(self):
        return AllPermanentTargets(self.target_types)
    def check_target(self, card):
        perm = []
        for ttype in self.target_types:
            perm1 = card.controller.play.get(ttype)
            perm2 = card.controller.opponent.play.get(ttype)
            perm.extend(perm1+perm2)
        self.zones = [p.zone for p in perm]
        self.target = perm
        return True
    def get(self, card):
        # XXX AllTargets are not actually targeted, so they are only created upon resolution
        #self.card = card
        return True

class MultipleTargets(MtGObject):
    def __init__(self, number, target_types=None, exact=True, msg='', selector="controller", untargeted=False):
        self.number = number
        self.zones = []
        self.target = []
        self.exact = exact
        self.msg = msg
        self.selector = selector
        self.untargeted = untargeted
        if not (type(target_types) == tuple or type(target_types) == list):
            self.target_types = [target_types]
        else: self.target_types = target_types
        def match_type(card):
            for match in self.target_types:
                if match(card): return True
            else: return False
        self.match_type = match_type
    def copy(self):
        return MultipleTargets(self.number, self.target_types, self.exact, self.msg, self.selector, self.untargeted)
    def check_target(self, card):
        # Remove any targets no longer in the correct zone, or no longer matching the original condition
        # XXX This is wrong - since it won't match up with the number requested
        final_targets = []
        for target, zone in zip(self.target, self.zones):
            if not isPlayer(target):
                if target.zone == zone and self.match_type(target) and target.canBeTargetedBy(card): final_targets.append(target)
            else:
                if target.canBeTargetedBy(card): final_targets.append(target)
        self.target = final_targets
        self.zone = []
        return True
    def get_prompt(self, curr, card):
        number = self.number-curr
        if curr > 0: another = "another "
        else: another = ""
        if not self.exact: another = "up to "+another
        
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
        while i < self.number:
            target = selector.getTarget(self.target_types,required=False,prompt=self.get_prompt(i, card.name))
            if target == False:
                if self.exact or len(targets) == 0: return False
                else: break
            elif target.canBeTargetedBy(card) and not target in targets:
                targets.append(target)
                i += 1
            else: player.send(InvalidTargetEvent(), target=target)
        # Got our targets, now save info:
        for target in targets:
            # The zone
            if not isPlayer(target): self.zones.append(target.zone)
            else: self.zones.append(None)
            if not self.untargeted: target.isTargetedBy(card)
        self.target = targets
        return True


# When I add a new argument to constructor, make sure to add it to the copy function
# or use the copy module
class Target(MtGObject):
    def __init__(self, targeting=None, target_types=None, msg='', selector="controller", untargeted=False, zone="play", player_zone=None):
        self.target = None
        self.zone = zone
        self.player_zone = player_zone
        self.targeting = targeting
        if not (type(target_types) == tuple or type(target_types) == list): self.target_types = [target_types]
        else: self.target_types = target_types
        # It should still be able to match any target types in the spell
        # See oracle for Putrefy (http://ww2.wizards.com/Gatherer/CardDetails.aspx?name=Putrefy)
        def match_types(card):
            for match in self.target_types:
                if match(card): return True
            else: return False
        self.match_types = match_types
        for ttype in self.target_types:
            if sum([isinstance(ttype, match) for match in [PlayerMatch, OpponentMatch, PlayerOrCreatureMatch]]):
                self.targeting_player = True
                break
        else: self.targeting_player = False
        self.required = True
        self.msg = msg
        self.selector = selector
        self.untargeted = untargeted
    def copy(self):
        return Target(self.targeting, self.target_types, self.msg, self.selector, self.untargeted, self.zone, player_zone=self.player_zone)
    def check_target(self, card):
        # Make sure the target is still in the correct zone (only for cards (and tokens), not players) and still matches original condition
        if not isPlayer(self.target):
            return (self.target_zone == str(self.target.zone)) and self.match_role == self.target.current_role and self.match_types(self.target) and self.target.canBeTargetedBy(card)
        else: return self.target.canBeTargetedBy(card)
    def get(self, card):
        if not self.targeting:
            if self.msg: prompt=self.msg
            else:
                if self.zone != "play":
                    if self.player_zone == None: zl = " in any %s"%self.zone
                    elif self.player_zone == "controller": zl = " in your %s"%self.zone
                    else: zl == " in opponent %s"%self.zone
                else:
                    if self.player_zone == None: zl = ""
                    elif self.player_zone == "controller": zl = " you control"
                    else: zl == " opponent controls"
                prompt="Target %s%s for %s"%(' or '.join([str(t) for t in self.target_types]), zl, card)
            if self.selector == "opponent": selector = card.controller.opponent
            elif self.selector == "current_player":
                import game.GameKeeper
                selector = game.GameKeeper.Keeper.curr_player
            else: selector = card.controller
            sel_zone = getattr(selector, self.zone)
            opponent_zone = getattr(selector.opponent, self.zone)
            if self.player_zone == None: zones = [sel_zone, opponent_zone]
            elif self.player_zone == "controller": zones = [sel_zone]
            else: zones = [opponent_zone]
            # If required, make sure there is actually a target available
            if self.required and not self.targeting_player:
                perm = []
                for ttype in self.target_types:
                    for zone in zones:
                        perm.extend([p for p in zone.get(ttype) if self.untargeted or p.canBeTargetedBy(card)])
                numtargets = len(perm)
                if numtargets == 0: return False
                elif numtargets == 1: self.target = perm[0]
                else:
                    while True:
                        self.target = selector.getTarget(self.target_types,zone=zones,required=self.required,prompt=prompt)
                        if self.untargeted or self.target.canBeTargetedBy(card): break
            else:
                self.target = selector.getTarget(self.target_types,zone=zones,required=self.required,prompt=prompt)
                if self.target == False: return False
            # Save the zone if we are targetting a permanent (not a player)
            if not isPlayer(self.target):
                self.target_zone = str(self.target.zone)
                self.match_role = self.target.current_role
            if self.untargeted:
                return True
            elif self.target.canBeTargetedBy(card):
                self.target.isTargetedBy(card)
                return True
            else: 
                selector.send(InvalidTargetEvent(), target=self.target)
                return False
        # XXX This is kind of hacky - I don't know if it can generalize
        elif self.targeting == "self":
            self.target = card
            self.target_zone = str(self.target.zone)
            self.match_types = SelfMatch(card)
            self.match_role = card.current_role
            return True
        elif self.targeting == "you":
            self.target = card.controller
            return True
        elif self.targeting == "owner":
            self.target = card.owner
            return True
        elif self.targeting == "current_player":
            import game.GameKeeper
            self.target = game.GameKeeper.Keeper.curr_player
            return True
        elif self.targeting == "opponent":
            self.target = card.controller.opponent
            return True
        else: return False

class SpecialTarget(MtGObject):
    def __init__(self, targeting):
        if not callable(targeting): raise Exception("Argument to SpecialTarget must be a function")
        self.targeting = targeting
        self.target = None
    def copy(self):
        return SpecialTarget(self.targeting)
    def check_target(self, card):
        # This is a final catchall for lambda functions
        self.target = self.targeting()
        return True
    def get(self, card):
        return True

class TriggeredTarget(MtGObject):
    def __init__(self, trigger, attribute, sender=False):
        self.trigger = trigger
        self.attribute = attribute
        self.sender = sender
        self.triggered = False
    def check_target(self, card):
        # Make sure the target is still in the correct zone (only for cards (and tokens), not players) and still matches original condition
        if not isPlayer(self.target):
            return (self.target_zone == str(self.target.zone)) and self.target.current_role == self.match_role
        else: return True
    def get(self, card):
        if not self.triggered:
            if not self.sender: self.target = getattr(self.trigger, self.attribute)
            else: self.target = getattr(self.trigger.sender, self.attribute)
            if not isPlayer(self.target):
                self.target_zone = str(self.target.zone)
                self.match_role = self.target.current_role
            self.triggered = True
        return True
    def copy(self):
        return TriggeredTarget(self.trigger, self.attribute)

class CounterTarget(MtGObject):
    def __init__(self, target_types=None, msg=''):
        self.target = None
        if not (type(target_types) == tuple or type(target_types) == list):
            self.target_types = [target_types]
        else: self.target_types = target_types
        self.msg = msg
    def copy(self):
        return CounterTarget(self.target_types, self.msg)
    def check_target(self, card):
        # Make sure the target is still in the correct zone (only for cards, not players) and still matches original condition
        return card.controller.stack.on_stack(self.target)
    def get(self, card):
        if self.msg: prompt=self.msg
        elif self.target_types: prompt="Target %s for %s"%(' or '.join([str(t) for t in self.target_types]), card)
        else: prompt = "Select target for %s"%(card)
        self.target = card.controller.getTarget(self.target_types,required=False,prompt=prompt)
        if self.target == False: return False
        return self.target.can_be_countered()
