from game.GameObjects import MtGObject
from game.Match import isPermanent, isPlayer, SelfMatch

#class Target(MtGObject):
#    def __init__(self):
#        self.target = None
#    def copy(self):
#        pass
#    def check_target(self):
#        return True
#    def get(self, card):
#        return True

class AllPlayerTargets(MtGObject):
    def __init__(self):
        self.target = []
    def copy(self):
        return AllPlayerTargets()
    def check_target(self):
        return True
    def get(self, card):
        self.target = [card.controller, card.controller.opponent]
        return True

class AllPermanentTargets(MtGObject):
    def __init__(self, target_types=isPermanent):
        self.zones = []
        self.target = []
        if not (type(target_types) == tuple or type(target_types) == list):
            self.target_types = [target_types]
        else: self.target_types = target_types
        def match_condition(card):
            for match in self.target_types:
                if match(card): return True
            else: return False
        self.match_condition = match_condition
    def copy(self):
        return AllPermanentTargets(self.target_types)
    def check_target(self):
        # Remove any targets no longer in the correct zone, or no longer matching the original condition
        final_targets = []
        for target, zone in zip(self.target, self.zones):
            if target.zone == zone and self.match_condition(target): final_targets.append(target)
        self.target = final_targets
        self.zone = []
        self.match_conditions = []
        return True #return len(final_targets) > 0
    def get(self, card):
        match_conditions = []
        perm = []
        for ttype in self.target_types:
            perm1 = card.controller.play.get(ttype)
            perm2 = card.controller.opponent.play.get(ttype)
            # The match conditions are wrong, since it should match any 
            match_conditions.extend([ttype]*(len(perm1)+len(perm2)))
            perm.extend(perm1+perm2)
        self.zones = [p.zone for p in perm]
        self.target = perm
        self.match_conditions = match_conditions
        return True

class MultipleTargets(MtGObject):
    def __init__(self, number, target_types=None, exact=True, msg='', selector="controller", untargeted=False):
        self.number = number
        self.zones = []
        self.target = []
        if not (type(target_types) == tuple or type(target_types) == list):
            self.target_types = [target_types]
        else: self.target_types = target_types
        self.exact = exact
        self.msg = msg
        self.selector = selector
        self.untargeted = untargeted
        def match_condition(card):
            for match in self.target_types:
                if match(card): return True
            else: return False
        self.match_condition = match_condition
    def copy(self):
        return MultipleTargets(self.number, self.target_types, self.exact, self.msg, self.selector, self.untargeted)
    def check_target(self):
        # Remove any targets no longer in the correct zone, or no longer matching the original condition
        final_targets = []
        for target, zone in zip(self.target, self.zones):
            if not isPlayer(target):
                if target.zone == zone and self.match_condition(target): final_targets.append(target)
            else:
                if self.match_condition(target): final_targets.append(target)
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
        # Got our targets, now save info:
        for target in targets:
            # The zone
            if not isPlayer(target): self.zones.append(target.zone)
            else: self.zones.append(None)
            if not self.untargeted: target.isTargetedBy(card)
        self.target = targets
        return True

class Target(MtGObject):
    def __init__(self, targeting=None, target_types=None, required=False, msg='', selector="controller", untargeted=False):
        self.target_zone = None
        self.target = None
        self.targeting = targeting
        if not (type(target_types) == tuple or type(target_types) == list):
            self.target_types = [target_types]
        else: self.target_types = target_types
        self.match_condition = lambda t: True
        self.required = required
        self.msg = msg
        self.selector = selector
        self.untargeted = untargeted
    def copy(self):
        return Target(self.targeting, self.target_types, self.required, self.msg, self.selector, self.untargeted)
    def check_target(self):
        # Make sure the target is still in the correct zone (only for cards (and tokens), not players) and still matches original condition
        if not isPlayer(self.target):
            return (self.target_zone == self.target.zone) and self.match_condition(self.target)
        else: return self.match_condition(self.target)
    def get(self, card):
        if not self.targeting:
            if self.msg: prompt=self.msg
            elif self.target_types: prompt="Target %s for %s"%(' or '.join([str(t) for t in self.target_types]), card)
            else: prompt = "Select target for %s"%(card)
            # If required, make sure there is actually a target available
            if self.selector == "opponent": selector = card.controller.opponent
            elif self.selector == "current_player":
                import game.GameKeeper
                selector = game.GameKeeper.Keeper.curr_player
            else: selector = card.controller
            if self.required:
                perm = []
                for ttype in self.target_types:
                    perm1 = card.controller.play.get(ttype)
                    perm1 = [p for p in perm1 if self.untargeted or p.canBeTargetedBy(card)]
                    perm2 = card.controller.opponent.play.get(ttype)
                    perm2 = [p for p in perm2 if self.untargeted or p.canBeTargetedBy(card)]
                    perm.extend(perm1+perm2)
                if len(perm) > 0:
                    while True:
                        self.target = selector.getTarget(self.target_types,required=self.required,prompt=prompt)
                        if self.untargeted or self.target.canBeTargetedBy(card): break
                else: return False
            else:
                self.target = selector.getTarget(self.target_types,required=self.required,prompt=prompt)
                if self.target == False: return False
            # Save the zone if we are targetting a permanent (not a player)
            if not isPlayer(self.target): self.target_zone = self.target.card.zone
            #self.target.current_role.targeted = True
            # It should still be able to match any target types in the spell
            # See oracle for Putrefy (http://ww2.wizards.com/Gatherer/CardDetails.aspx?name=Putrefy)
            def match_condition(card):
                for match in self.target_types:
                    if match(card): return True
                else: return False
            self.match_condition = match_condition
            if self.untargeted: return True
            elif self.target.canBeTargetedBy(card):
                self.target.isTargetedBy(card)
                return True
            else: return False
        # XXX This is kind of hacky - I don't know if it can generalize
        elif self.targeting == "self":
            self.target = card
            self.target_zone = self.target.zone
            self.match_condition = SelfMatch(card)
            return True
        elif self.targeting == "controller":
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
        # This is a final catchall for lambda functions
        elif callable(self.targeting):
            self.target = self.targeting()
            if not isPlayer(self.target):
                self.target_zone = self.target.zone
                self.match_condition = SelfMatch(self.target)
            return True
        else: return False

class CounterTarget(MtGObject):
    def __init__(self, target_types=None, msg=''):
        self.target = None
        if not (type(target_types) == tuple or type(target_types) == list):
            self.target_types = [target_types]
        else: self.target_types = target_types
        self.match_condition = lambda t: True
        self.msg = msg
    def copy(self):
        return CounterTarget(self.target_types, self.msg)
    def check_target(self):
        # Make sure the target is still in the correct zone (only for cards, not players) and still matches original condition
        return self.match_condition(self.target)
    def get(self, card):
        if self.msg: prompt=self.msg
        elif self.target_types: prompt="Target %s for %s"%(' or '.join([str(t) for t in self.target_types]), card)
        else: prompt = "Select target for %s"%(card)
        self.target = card.controller.getTarget(self.target_types,required=False,prompt=prompt)
        if self.target == False: return False
        self.match_condition=lambda target: card.controller.stack.on_stack(target)
        return self.target.can_be_countered()
