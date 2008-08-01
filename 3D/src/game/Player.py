
from CardLibrary import CardLibrary
from GameObjects import MtGObject, Card
from GameEvent import GameFocusEvent, DrawCardEvent, DiscardCardEvent, CardUntapped, PlayerDamageEvent, LifeChangedEvent, TargetedByEvent, InvalidTargetEvent, DealsDamageEvent, LogEvent, AttackerSelectedEvent, BlockerSelectedEvent, AttackersResetEvent, BlockersResetEvent
from Mana import ManaPool
from Zone import Library, Hand, Play, Graveyard, Removed
from Action import ActivateForMana, PlayAbility, PlayLand, CancelAction, PassPriority, OKAction
from Match import isCreature, isPlayer, isGameObject, isCard, isLandType
from data_structures import keywords

class Player(MtGObject):
    def in_play():
        doc = "Old reference to play zone"
        def fget(self):
            import warnings
            warnings.warn("Usage of 'in_play' is deprecated. Use 'play' instead.", category=DeprecationWarning, stacklevel=2)
            return self.play
        return locals()
    in_play = property(**in_play())

    def life():
        doc = "Player life property"
        def fget(self):
            return self._life
        def fset(self, value):
            amount = value - self._life
            self._life = value
            if amount != 0: self.send(LifeChangedEvent(), amount=amount)
        return locals()
    life = property(**life())

    def __init__(self,name):
        self.name = name
        self._life = 20
        self.poison = 0
        self.library = Library(self)
        self.hand = Hand(self)
        self.graveyard = Graveyard(self)
        self.removed = Removed(self)
        self.play = Play(self)
        self.manapool = ManaPool()
        self.allowable_actions = [PassPriority]
        self.land_actions = -1
        self.hand_limit = 7
        self.draw_empty = False
        self.opponent = None
        self.decklist = []
        self.keywords = keywords()
        self.current_role = self    # XXX This is an ugly hack to get targetting to work uniformly
        #self.targeted = False
    def match_role(self, role): return False    # XXX This is an ugly hack to get targetting to work uniformly
    def init(self):
        self.play.init()
        self.library.init()
        self.graveyard.init()
    def __str__(self):
        return self.name
        #return "Player: %s"%self.name
    def __repr__(self):
        return "%s at %s"%(self.name, id(self))
    def setOpponent(self, opponent):
        self.opponent = opponent
    def setDeck(self, decklist):
        #XXX Check to make sure the deck is valid
        self.decklist = decklist
    def resetLandActions(self):
        self.land_actions = 1
    def reset(self):
        library = self.library
        for from_location in [self.hand, self.play, self.graveyard, self.removed]:
            for card in from_location:
                to_location = card.owner.library
                card.owner.moveCard(card, from_location, to_location)
    def loadDeck(self):
        for num, name in self.decklist:
            num = int(num)
            for n in range(num):
                card = CardLibrary.createCard(name, self)
                self.library.setup_card(card)
    def shuffleDeck(self):
        self.library.shuffle()
    def draw(self):
        card = self.library.top()
        if card == None: self.draw_empty = True
        else:
            self.moveCard(card, from_location=self.library, to_location=self.hand)
            self.send(DrawCardEvent())
            #self.send(LogEvent(), msg="%s draws a card"%self)
    def discard(self, card):
        self.moveCard(card, from_location=self.hand, to_location=self.graveyard)
        self.send(DiscardCardEvent())
        self.send(LogEvent(), msg="%s discards %s"%(self, card))
    def mulligan(self):
        number = 7
        self.library.disable_ordering()
        while True:
            number -= 1
            if self.getIntention("", "Would you like to mulligan?"): #, "Would you like to mulligan?"):
                self.send(LogEvent(), msg="%s mulligans"%self)
                for card in self.hand:
                    self.moveCard(card, from_location=self.hand, to_location=self.library)
                self.shuffleDeck()
                for i in range(number): self.draw()
            else: break
            if number == 0: break
        self.library.enable_ordering()
    def moveCard(self, card, from_location=None, to_location=None, position="top"):
        # Trigger card moved event
        # move the actual card
        # location can be library, hand, play, graveyard, outofgame
        # XXX what about moving cards to other players?
        if position=="bottom": position = 0
        elif position == "top": position = -1
        to_location.move_card(card, from_location, position)

    # Who should handle these? Player or GameKeeper?
    def untapCards(self):
        for card in self.play:
            # XXX The player should be able to select with cards to Untap (possibly?)
            if card.tapped and card.canUntap(): card.untap()
    def upkeep(self):
        # Trigger upkeep events - shouldn't affect other player
        # XXX I don't think I need this - the player doesn't handle upkeep
        pass
    def canBeDamagedBy(self, damager):
        return True
    def assignDamage(self, amt, source, combat=False):
        if amt > 0:
            self.life -= amt
            source.send(DealsDamageEvent(), to=self, amount=amt)
            self.send(PlayerDamageEvent(), source=source, amount=amt)
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
    def attackingIntention(self):
        # First check to make sure you have cards in play
        # XXX although if you have creatures with Flash this might not work since you can play it anytime
        has_creature = False
        for creature in self.play.get(isCreature):
            if creature.canAttack():
                has_creature = True
        if not has_creature: return False
        else: return True #self.getIntention("Declare intention to attack", msg="...attack this turn?")
    def declareAttackers(self):
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
            if isGameObject(sel)  and sel.controller == self:
                if isLandType(sel) and not action.zone == self.play: return PlayLand(sel)
                else: return PlayAbility(sel)
                #zone = action.zone
                #if zone == self.play: return PlayAbility(sel)
                #else: return sel.play_action(sel)
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
    def getIntention(self, prompt='', msg="", notify=False):
        def filter(action):
            if not (isinstance(action, OKAction) or isinstance(action, CancelAction)): return False
            else: return action
        context = {'get_choice': True, 'msg': msg, 'notify': notify, 'process': filter}
        if not prompt: prompt = "Declare intention"
        if not msg: msg = prompt
        result = self.input(context, "%s: %s"%(self.name,prompt))
        return isinstance(result, OKAction)
    def getSelection(self, sellist, numselections, required=True, idx=True, msg='', prompt=''):
        def filter(action):
            if isinstance(action, CancelAction) and not required: return action
            if not isinstance(action, PassPriority): return action.selection
            return False
        if msg == '': msg = prompt
        if idx == True: sellist = [(val, i) for i, val in enumerate(sellist)]
        context = {'get_selection': True, 'list':sellist, 'numselections': numselections, 'required': required, 'msg': msg, 'process': filter}
        sel = self.input(context,"%s: %s"%(self.name,prompt))
        if isinstance(sel, CancelAction): return False
        elif idx == True: return sellist[sel][0]
        else: return sel
    def getCardSelection(self, sellist, numselections, from_zone, from_player, card_types=isGameObject, required=True, prompt=''):
        def filter(action):
            if isinstance(action, CancelAction):
                if not required: return action
                else: return False
            if not isinstance(action, PassPriority): return action.selection
            else: return False
        if not (type(card_types) == list or type(card_types) == tuple): card_types = [card_types]
        def check_card(card):
            valid = True
            for ctype in card_types:
                if ctype(card): break
            else: valid = False
            return valid
        if numselections > len(sellist): numselections = len(sellist)
        context = {'get_cards': True, 'list':sellist, 'numselections': numselections, 'required': required, 'process': filter, 'from_zone': from_zone, 'from_player': from_player, 'check_card': check_card}
        sel = self.input(context, "%s: %s"%(self.name,prompt))
        if isinstance(sel, CancelAction): return False
        else: return sel
    def getCombatCreature(self, mine=True, prompt='Select target'):
        def filter(action):
            if isinstance(action, CancelAction) or isinstance(action, PassPriority):
                return action

            target = action.selection
            if isCreature(target) and ((mine and target.zone == self.play) or
                (not mine and target.zone == self.opponent.play)): return target
            else:
                self.send(InvalidTargetEvent(), target=target)
                return False
        context = {'get_target': True, 'process': filter}
        target = self.input(context, "%s: %s"%(self.name,prompt))

        if isinstance(target, PassPriority): return True
        elif isinstance(target, CancelAction): return False
        else: return target
    def getTarget(self, target_types, zone=[], required=True, prompt='Select target'):
        # If required is True (default) then you can't cancel the request for a target
        def filter(action):
            # This function is really convoluted
            # If I return False here then the input function will keep cycling until valid input
            if isinstance(action, CancelAction):
                if not required: return action
                else: return False
            elif isinstance(action, PassPriority): return False

            target = action.selection
            if not (type(target_types) == list or type(target_types) == tuple): t_types = [target_types]
            else: t_types = target_types
            if not (type(zone) == list or type(zone) == tuple): t_zone = [zone]
            else: t_zone = zone
            if isPlayer(target) or t_zone==[] or (hasattr(target,"zone") and (target.zone in t_zone)):
                for target_type in t_types:
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
            if isGameObject(sel):
                zone = action.zone
                if zone == self.play: return ActivateForMana(sel)
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
