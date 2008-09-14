
from GameObjects import MtGObject, Card, Token
from GameEvent import GameFocusEvent, DrawCardEvent, DiscardCardEvent, CardUntapped, PlayerDamageEvent, LifeGainedEvent, LifeLostEvent, TargetedByEvent, InvalidTargetEvent, LogEvent, AttackerSelectedEvent, BlockerSelectedEvent, AttackersResetEvent, BlockersResetEvent, PermanentSacrificedEvent, TimestepEvent
from Mana import ManaPool
from Zone import Library, Hand, Graveyard, Removed
from Action import ActivateForMana, PlayAbility, PlayLand, CancelAction, PassPriority, OKAction
from Match import isCreature, isPermanent, isPlayer, isCard, isLandCard, isCardRole, isGameObject, isPlaneswalker

class Player(MtGObject):
    def life():
        doc = "Player life property"
        def fget(self):
            return self._life
        def fset(self, value):
            amount = value - self._life
            if amount > 0: self.gain_life(amount)
            elif amount < 0: self.lose_life(amount)
        return locals()
    life = property(**life())

    # For overriding by replacement effects
    def gain_life(self, amount):
        self._life += amount
        self.send(LifeGainedEvent(), amount=amount)
    def lose_life(self, amount):
        self._life += amount  # This seems weird, but amount is negative
        self.send(LifeLostEvent(), amount=amount)

    def __init__(self,name):
        self.name = name
        self._life = 20
        self.poison = 0
        self.allowable_actions = [PassPriority]
        self.land_actions = -1
        self.hand_limit = 7
        self.draw_empty = False
        self.decklist = []
    def init(self, play, stack):
        self.library = Library()
        self.hand = Hand()
        self.graveyard = Graveyard()
        self.removed = Removed()
        self.play = play.get_view(self)
        self.stack = stack
        self.manapool = ManaPool()

        self.loadDeck()
        self.shuffle()
    def setOpponents(self, *opponents):
        self.opponent = opponents[0] # XXX Get rid of this
        self.opponents = set(opponents)
    def setDeck(self, decklist):
        #XXX Check to make sure the deck is valid
        self.decklist = decklist
    def resetLandActions(self):
        self.land_actions = 1
    def reset(self):
        library = self.library
        for from_location in [self.hand, self.graveyard, self.removed]:
            for card in from_location:
                card.move_to(card.owner.library)
    def loadDeck(self):
        for num, name in self.decklist:
            num = int(num)
            for n in range(num):
                self.library.add_new_card(Card(name, owner=self))

    # The following functions are part of the card code DSL
    def add_mana(self, *amount):
        if len(amount) > 1:
            amount = self.getSelection(amount, 1, prompt="Select mana to add")
        else: amount = amount[0]
        self.manapool.add(amount)
    def shuffle(self):
        self.library.shuffle()
    def you_may(self, msg): return self.getIntention(prompt="You may %s"%msg,msg="Would you like to %s?"%msg)
    def you_may_pay(self, source, cost):
        intent = self.getIntention(prompt="You may pay %s"%cost, msg="Would you like to pay %s"%cost)
        if intent and cost.precompute(source, self) and cost.compute(source, self):
            cost.pay(source, self)
            return True
        else: return False
    def play_token(self, info, number=1):
        for n in range(number):
            token = Token(info, owner=self)
            token.move_to(self.play)
    def choose_opponent(self):
        if len(self.opponents) == 1:
            return self.opponents[0]
        else:
            raise NotImplementedError()
    def choose_from_zone(self, number=1, cardtype=isCard, zone="play", action='', required=True, all=False):
        cards_in_zone = getattr(self, zone).get(cardtype)
        if len(cards_in_zone) >= number: cards = cards_in_zone
        else:
            cards = []
            if zone == "play" or zone == "hand":
                a = 's' if number > 1 else ''
                total = number
                prompt = "Select %s%s to %s: %d left of %d"%(cardtype, a, action, number, total)
                while number > 0:
                    card = self.getTarget(cardtype, zone=zone, controller=None if all else self, required=required, prompt=prompt)
                    if card == False: break
                    if card in cards:
                        prompt = "Card already selected - select again"
                        self.send(InvalidTargetEvent(), target=card)
                    else:
                        cards.append(card)
                        number -= 1
                        prompt = "Select %s%s to %s: %d left of %d"%(cardtype, a, action, number, total)
            else:
                selection = getattr(self, zone).get()
                if number > 0:
                    if number == 1: a = 'a'
                    else: a = str(number)
                    if zone == "library" and not cardtype == isCard: required = False
                    cards = self.getCardSelection(selection, number=number, cardtype=cardtype, required=required, prompt="Search your %s for %s %s to %s."%(zone, a, cardtype, action))
                    if zone == "library": self.shuffle()
        return cards
    def draw(self):
        card = self.library.top()
        if card == None: self.draw_empty = True
        else:
            card.move_to(self.hand)
            self.send(DrawCardEvent())
    def discard(self, card):
        if str(card.zone) == "hand":
            card.move_to(self.graveyard)
            self.send(DiscardCardEvent(), card=card)
            return True
        else: return False
    def force_discard(self, number=1, cardtype=isCard):
        if number == -1: number = len(self.hand)
        cards = self.choose_from_zone(number, cardtype, "hand", "discard")
        for card in cards: self.discard(card)
        return len(cards)
    def discard_down(self):
        number = len(self.hand) - self.hand_limit
        if number > 0: self.force_discard(number)
    def sacrifice(self, perm):
        if perm.controller == self and str(perm.zone) == "play":
            perm.move_to(self.graveyard)
            self.send(PermanentSacrificedEvent(), card=perm)
            return True
        else: return False
    def force_sacrifice(self, number=1, cardtype=isPermanent):
        perms = self.choose_from_zone(number, cardtype, "play", "sacrifice")
        for perm in perms: self.sacrifice(perm)
        return len(perms)
    def mulligan(self):
        number = 7
        while number > 0:
            number -= 1
            if self.getIntention("", "Would you like to mulligan?"): #, "Would you like to mulligan?"):
                self.send(LogEvent(), msg="%s mulligans"%self)
                for card in self.hand: card.move_to(zone=self.library)
                self.shuffle()
                yield
                for i in range(number): self.draw()
                yield True
            else: break
        yield False
    # Who should handle these? Player or GameKeeper?
    def untapCards(self):
        for card in self.play.get():
            # XXX The player should be able to select with cards to Untap (possibly?)
            if card.untapDuringUntapStep(): card.untap()
    def canBeDamagedBy(self, damager):
        return True
    def assignDamage(self, amt, source, combat=False):
        if amt > 0:
            self.life -= amt
            self.send(PlayerDamageEvent(), source=source, amount=amt)
        return amt
    def canBeTargetedBy(self, targetter):
        # For protection spells - XXX these should be stackable
        return True
    def isTargetedBy(self, targeter):
        self.send(TargetedByEvent(), targeter=targeter)
    def manaBurn(self):
        manaburn = self.manapool.manaBurn()
        if manaburn > 0:
            #take_burn = self.getIntention("Take mana burn?", "Take mana burn?")
            #if not take_burn: return False
            self.manapool.clear()
            self.life -= manaburn
        return True
    def attackingIntention(self):
        # First check to make sure you have cards in play
        # XXX although if you have creatures with Flash this might not work since you can play it anytime
        has_creature = False
        for creature in self.play.get(isCreature):
            if creature.canAttack():
                has_creature = True
        if not has_creature: return False
        else: return True #self.getIntention("Declare intention to attack", msg="...attack this turn?")
    def declareAttackers(self, opponents):
        multiple_opponents = len(opponents) > 1
        all_on_attacking_side = self.play.get(isCreature)
        invalid_attack = True
        prompt = "Declare attackers (Enter to accept, Escape to reset)"
        while invalid_attack:
            attackers = set()
            done_selecting = False
            creature = self.getCombatCreature(mine=True, prompt=prompt)
            while not done_selecting:
                if creature == True:
                    done_selecting = True
                    break
                elif creature == False:
                    self.send(AttackersResetEvent())
                    break
                else:
                    if not creature in attackers and creature.canAttack():
                        attackers.add(creature)
                        self.send(AttackerSelectedEvent(), attacker=creature)

                        # Now select who to attack
                        if multiple_opponents:
                            while True:
                                target = self.getTarget(target_types=(isPlayer, isPlaneswalker), zone="play", prompt="Select opponent to attack")
                                if target in opponents:
                                    creature.setOpponent(target)
                                    target.send(TargetedByEvent(), targeter=creature)
                                    break
                                else: prompt = "Can't attack %s. Select again"%target
                        else: creature.setOpponent(opponents[0])
                        prompt = "%s selected - select another"%creature
                    elif creature in attackers:
                        self.send(InvalidTargetEvent(), target=creature)
                        prompt = "%s already in combat - select another"%creature
                    else:
                        self.send(InvalidTargetEvent(), target=creature)
                        prompt = "%s cannot attack - select another"%creature
                creature = self.getCombatCreature(mine=True, prompt=prompt)

            if done_selecting:
                not_attacking = set(all_on_attacking_side)-attackers
                invalid_attackers = [creature for creature in all_on_attacking_side if not creature.checkAttack(attackers, not_attacking)] + [creature for creature in attackers if not creature.computeAttackCost()]
                invalid_attack = len(invalid_attackers) > 0
                if not invalid_attack:
                    for creature in attackers:
                        creature.payAttackCost()
                        creature.setAttacking()
                else:
                    prompt = "Invalid attack - choose another"
                    for creature in invalid_attackers: self.send(InvalidTargetEvent(), target=creature)
            else: prompt = "Declare attackers (Enter to accept, Escape to reset)"
        return list(attackers)
    def declareBlockers(self, attackers):
        combat_assignment = dict([(attacker, []) for attacker in attackers])
        # Make sure you have creatures to block
        all_on_blocking_side = self.play.get(isCreature)
        if len(all_on_blocking_side) == 0: return combat_assignment.items()

        invalid_block = True
        blocker_prompt = "Declare blockers (Enter to accept, Escape to reset)"
        while invalid_block:
            total_blockers = set()
            done_selecting = False
            while not done_selecting:
                blocker = self.getCombatCreature(mine=True, prompt=blocker_prompt)
                if blocker == True:
                    done_selecting = True
                    break
                elif blocker == False:
                    # Reset the block
                    self.send(BlockersResetEvent())
                    combat_assignment = dict([(attacker, []) for attacker in attackers])
                    break
                else:
                    if blocker in total_blockers or not blocker.canBlock():
                        if blocker in total_blockers: reason = "already blocking"
                        elif not blocker.canBlock(): reason = "can't block"
                        self.send(InvalidTargetEvent(), target=blocker)
                        blocker_prompt = "%s %s - select another blocker"%(blocker, reason)
                    else:
                        # Select attacker
                        valid_attacker = False
                        attacker_prompt = "Select attacker to block"
                        while not valid_attacker:
                            attacker = self.getCombatCreature(mine=False, prompt=attacker_prompt)
                            if attacker == True: pass # XXX What does enter mean here?
                            elif attacker == False: break # Pick a new blocker
                            elif attacker.attacking and attacker.canBeBlocked() and blocker.canBlockAttacker(attacker) and attacker.canBeBlockedBy(blocker):
                                valid_attacker = True
                                total_blockers.add(blocker)
                                combat_assignment[attacker].append(blocker)
                                self.send(BlockerSelectedEvent(), attacker=attacker, blocker=blocker)
                                attacker_prompt = "Select attacker to block"
                                blocker_prompt = "Declare blockers (Enter to accept, Escape to reset)"
                            else:
                                if not attacker.attacking: reason = "cannot block non attacking %s"%attacker
                                else: reason = "cannot block %s"%attacker
                                self.send(InvalidTargetEvent(), target=blocker)
                                self.send(InvalidTargetEvent(), target=attacker)
                                attacker_prompt = "%s %s - select a new attacker"%(blocker,reason)

            if done_selecting:
                nonblockers = set(all_on_blocking_side)-total_blockers
                invalid_blockers = [creature for creature in attackers+all_on_blocking_side if not creature.checkBlock(combat_assignment, nonblockers)] + [creature for creature in total_blockers if not creature.computeBlockCost()]
                invalid_block = len(invalid_blockers) > 0
                if not invalid_block:
                    for attacker, blockers in combat_assignment.items():
                        attacker.setBlocked(blockers)
                        for blocker in blockers:
                            blocker.payBlockCost()
                            blocker.setBlocking(attacker)
                else:
                    blocker_prompt = "Invalid defense - choose another"
                    for creature in invalid_blockers: self.send(InvalidTargetEvent(), target=creature)
            else: blocker_prompt = "Declare blockers (Enter to accept, Escape to reset)"

        return combat_assignment.items()

    def __str__(self): return self.name
    def __repr__(self): return "%s at %s"%(self.name, id(self))
    # The following functions interface with the GUI of the game, and as a result they are kind
    # of convoluted. All interaction with the GUI is carried out through the input function (which
    # is set to dirty_input from the Incantus app) with a context object which indicates the action to perform
    # as well as a filtering function (process) that can convert user actions into game actions (or even
    # discard improper actions (see dirty_input).
    def input(self, context, prompt):
        self.send(GameFocusEvent())
        return self.dirty_input(context, prompt)
    def get(self, process=None, prompt=''):
        def convert_gui_action(action):
            if isinstance(action, PassPriority) or isinstance(action, CancelAction): return action
            sel = action.selection
            if not isPlayer(sel) and sel.controller == self:
                if isLandCard(sel) and not str(sel.zone) == "play": return PlayLand(sel)
                else: return PlayAbility(sel)
            else: return False
        if not process: process = convert_gui_action
        context = {"get_ability": True, "process": process}
        while True:
            action = self.input(context, "%s: %s"%(self.name,prompt))
            # check if action is valid
            allowed = False
            for a in self.allowable_actions:
                if isinstance(action, a):
                    allowed = True
                    break
            if allowed: break
            #else: print self.name, str(action)+" not allowed"
        return action
    def getMainAction(self):
        self.allowable_actions.extend([PlayLand, ActivateForMana, PlayAbility])
        num_added_actions = 3
        action = self.get(prompt="Play Spells or Activated Abilities")
        [self.allowable_actions.pop() for i in range(num_added_actions)]
        return action
    def getAction(self):
        self.allowable_actions.extend([ActivateForMana, PlayAbility])
        action = self.get(prompt="Play Instants or Activated Abilities")
        [self.allowable_actions.pop() for i in range(2)]
        return action
    def getIntention(self, prompt='', msg="", notify=False):
        def filter(action):
            if not (isinstance(action, OKAction) or isinstance(action, CancelAction)): return False
            else: return action
        context = {'get_choice': True, 'msg': msg, 'notify': notify, 'process': filter}
        if not prompt: prompt = "Declare intention"
        if not msg: msg = prompt
        result = self.input(context, "%s: %s"%(self.name,prompt))
        return isinstance(result, OKAction)
    def getSelection(self, sellist, numselections=1, required=True, idx=True, msg='', prompt=''):
        def filter(action):
            if isinstance(action, CancelAction) and not required: return action
            if not isinstance(action, PassPriority): return action.selection
            return False
        if msg == '': msg = prompt
        if idx == True: sellist = [(val, i) for i, val in enumerate(sellist)]
        context = {'get_selection': True, 'list':sellist, 'numselections': numselections, 'required': required, 'msg': msg, 'process': filter}
        sel = self.input(context,"%s: %s"%(self.name,prompt))
        if isinstance(sel, CancelAction): return False
        elif idx == True:
            if numselections == 1: return sellist[sel][0]
            elif numselections == -1: return [sellist[i][0] for i in sel]
            else: return [sellist[i][0] for i in sel][:numselections]
        else: return sel
    #XXX LKI - change isGameObject to isCardRole
    def getCardSelection(self, selection, number, cardtype=isGameObject, zone=None, player=None, required=True, prompt=''):
        def filter(action):
            if isinstance(action, CancelAction):
                if not required: return action
                else: return False
            if not isinstance(action, PassPriority): return action.selection
            else: return False
        if not (type(cardtype) == list or type(cardtype) == tuple): cardtype = [cardtype]
        def check_card(card):
            valid = True
            for ctype in cardtype:
                if ctype(card): break
            else: valid = False
            return valid
        if number > len(selection): number = len(selection)
        if not zone: zone = str(selection[0].zone)
        if not player: player = selection[0].controller
        context = {'get_cards': True, 'list':selection, 'numselections': number, 'required': required, 'process': filter, 'from_zone': zone, 'from_player': player, 'check_card': check_card}
        sel = self.input(context, "%s: %s"%(self.name,prompt))
        if isinstance(sel, CancelAction): return False
        else: return sel
    def getCombatCreature(self, mine=True, prompt='Select target'):
        def filter(action):
            if isinstance(action, CancelAction) or isinstance(action, PassPriority):
                return action

            target = action.selection
            if isCreature(target) and ((mine and target.controller == self) or
                (not mine and target.controller in self.opponents)): return target
            else:
                self.send(InvalidTargetEvent(), target=target)
                return False
        context = {'get_target': True, 'process': filter}
        target = self.input(context, "%s: %s"%(self.name,prompt))

        if isinstance(target, PassPriority): return True
        elif isinstance(target, CancelAction): return False
        else: return target
    def getTarget(self, target_types, zone=None, controller=None, required=True, prompt='Select target'):
        # If required is True (default) then you can't cancel the request for a target
        if not (type(target_types) == list or type(target_types) == tuple): target_types = [target_types]
        def filter(action):
            # This function is really convoluted
            # If I return False here then the input function will keep cycling until valid input
            if isinstance(action, CancelAction):
                if not required: return action
                else: return False
            elif isinstance(action, PassPriority): return False

            target = action.selection
            if isPlayer(target) or ((not zone or str(target.zone) == zone) and (not controller or target.controller == controller)):
                for target_type in target_types:
                    if target_type(target): return target
            # Invalid target
            self.send(InvalidTargetEvent(), target=target)
            return False
        context = {'get_target': True, 'process': filter}
        target = self.input(context, "%s: %s"%(self.name,prompt))

        if isinstance(target, CancelAction) or isinstance(target, PassPriority): return False
        return target
    def getMoreMana(self, required): # if necessary when paying a cost
        def convert_gui_action(action):
            if isinstance(action, PassPriority): return False
            if isinstance(action, CancelAction): return action
            sel = action.selection
            if not isPlayer(sel) and sel.controller == self and str(sel.zone) == "play":
                return ActivateForMana(sel)
            else: return False
        self.allowable_actions.extend([CancelAction, ActivateForMana])
        manaplayed = False
        cancel = False    # This is returned - it's a way to back out of playing an ability
        # This loop seems really ugly - is there a way to structure it better?
        while not manaplayed:
            action = self.get(process = convert_gui_action, prompt="Need %s - play mana abilities (Esc to cancel)"%required)
            # XXX Should this be done here?
            if isinstance(action, CancelAction):
                cancel = True
                break
            else: manaplayed = action.perform(self)
        [self.allowable_actions.pop() for i in range(2)]
        return not cancel
    def getManaChoice(self, manapool_str, total_required, prompt="Select mana to spend"):
        def filter(action):
            if isinstance(action, CancelAction): return action
            else: return action.mana
        context = {'get_mana_choice': True, 'manapool': manapool_str, 'required': total_required, "process": filter, "from_player": self}
        result = self.input(context, "%s: %s"%(self.name,prompt))
        if isinstance(result, CancelAction): return False
        else: return result
    def getX(self, prompt="Select amount for X"):
        def filter(action):
            if isinstance(action, CancelAction): return action
            if isinstance(action, PassPriority): return False
            else: return action.amount
        context = {'get_X': True, "process": filter, "from_player": self}
        result = self.input(context, "%s: %s"%(self.name,prompt))
        if isinstance(result, CancelAction): return -1
        else: return result
    def getDistribution(self, amount, targets, prompt=''):
        if not prompt: prompt = "Distribute %d to target permanents"%amount
        def filter(action):
            if isinstance(action, CancelAction): return False
            return action.assignment
        context = {'get_distribution': True, 'targets': targets, 'amount': amount, 'process': filter}
        return self.input(context, "%s: %s"%(self.name,prompt))
    def getDamageAssignment(self, blocking_list, prompt="Assign damage to blocking creatures", trample=False):
        def filter(action):
            if isinstance(action, CancelAction): return False
            return action.assignment
        context = {'get_damage_assign': True, 'blocking_list': blocking_list, 'trample': trample, 'process': filter}
        return self.input(context, "%s: %s"%(self.name,prompt))
    def revealCard(self, cards, msgs=[], title="Reveal cards", prompt=''):
        import operator
        if not operator.isSequenceType(cards): cards = [cards]
        if not prompt: prompt = "reveals card(s) "+', '.join(map(str,cards))
        context = {'reveal_card': True, 'cards': cards, 'msgs':msgs, 'process': lambda x: True}
        return self.input(context, "%s: %s"%(self.name,prompt))
    peek = revealCard # XXX Eventually, redo revealCard to reveal to all players at once
