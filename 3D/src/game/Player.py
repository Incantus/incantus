
from CardLibrary import CardLibrary
from GameObjects import MtGObject, Card
from GameEvent import GameFocusEvent, DrawCardEvent, DiscardCardEvent, CardUntapped, PlayerDamageEvent, LifeChangedEvent, TargetedByEvent, InvalidTargetEvent
from Mana import ManaPool
from Zone import Library, Hand, Play, Graveyard, Removed
from Action import PlaySpell, ActivateForMana, PlayInstant, PlayAbility, PlayLand, CancelAction, PassPriority, OKAction
from Match import isCreature, isPlayer, isGameObject, isCard
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
        self.library = Library()
        self.hand = Hand()
        self.graveyard = Graveyard()
        self.removed = Removed()
        self.play = Play()
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
    def discard(self, card):
        self.moveCard(card, from_location=self.hand, to_location=self.graveyard)
        self.send(DiscardCardEvent())
    def mulligan(self):
        number = 7
        while True:
            number -= 1
            if self.getIntention("", "Would you like to mulligan"): #, "Would you like to mulligan?"):
                for card in self.hand:
                    self.moveCard(card, from_location=self.hand, to_location=self.library)
                self.shuffleDeck()
                for i in range(number): self.draw()
            else: break
            if number == 0: break
    def moveCard(self, card, from_location=None, to_location=None):
        # Trigger card moved event
        # move the actual card
        # location can be library, hand, play, graveyard, outofgame
        # XXX what about moving cards to other players?
        #from_location.remove_card(card, trigger=trigger)
        #to_location.add_card(card, trigger=trigger)
        to_location.move_card(card, from_location)

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
            source.send(DealsDamageEvent(), to=target, amount=amount)
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
        self.allowable_actions.extend([PlayLand, PlaySpell, ActivateForMana, PlayInstant, PlayAbility])
        num_added_actions = 5
        action = self.get(prompt="Play Spells or Activated Abilities")
        [self.allowable_actions.pop() for i in range(num_added_actions)]
        return action
    def getAction(self):
        self.allowable_actions.extend([ActivateForMana, PlayInstant, PlayAbility])
        action = self.get(prompt="Play Instants or Activated Abilities")
        [self.allowable_actions.pop() for i in range(3)]
        return action
    def attackingIntention(self):
        # First check to make sure you have cards in play
        # XXX although if you have creatures with Flash this might not work since you can play it anytime
        has_creature = False
        for creature in self.play.get(isCreature):
            if creature.canAttack():
                if creature.mustAttack(): return True
                has_creature = True
        if not has_creature: return False
        else: return True #self.getIntention("Declare intention to attack", msg="...attack this turn?")
    def declareAttackers(self):
        attackers = []
        # XXX First check requirements for all creatures that must attack
        num_creatures = 0
        for creature in self.play.get(isCreature):
            if creature.canAttack():
                if creature.mustAttack():
                    attackers.append(creature)
                    creature.setAttacking()
                else: num_creatures += 1

        prompt = "Select creatures for attack"
        while num_creatures > 0:
            creature = self.getTarget(isCreature, zone=self.play, spell=False, required = False, prompt=prompt)
            # Make sure the creature can attack and is not tapped
            # XXX also the creature must have been controlled from the beginning of the turn
            if creature == False: break
            if creature.canAttack():
                if creature.computeAttackCost() and creature.payAttackCost():
                    attackers.append(creature)
                    creature.setAttacking()
                    prompt = "%s selected - Select another creature for attack"%creature.name
                    num_creatures -= 1
                else:
                    self.send(InvalidTargetEvent(), target=target)
                    prompt = "Attack cost not paid for %s"%creature.name
            elif creature.in_combat:
                prompt = "%s already in combat"%creature.name
                self.send(InvalidTargetEvent(), target=creature)
            else:
                prompt = "%s cannot attack - Select another"%creature.name
                self.send(InvalidTargetEvent(), target=creature)
        # XXX Pay costs for attacking (rule 308.2d)
        #for creature in attackers: creature.setAttacking()
        # XXX Send AttackerDeclaredEvent with creature as data
        return attackers
    def declareBlockers(self, attackers):
        blocking_list = dict([(c, []) for c in attackers])
        #all_blockers = []
        # Make sure you have blockers
        creatures = self.play.get(isCreature)
        num_creatures = len(creatures)
        if num_creatures == 0: return blocking_list.items()
        num_attackers = len(attackers)
        
        for attacker in attackers:
            if attacker.mustBeBlocked():
                blockers = []
                # Add all available blockers to block this attacker
                for blocker in creatures:
                    if not blocker.tapped and blocker.canBlock() and blocker.canBlockAttacker(attacker) and attacker.canBeBlockedBy(blocker): # and some other stuff
                        blockers.append(blocker)
                        num_creatures -= 1
                        blocker.setBlocking(attacker)
                blocking_list[attacker] = blockers
                if blockers:
                    num_attackers -= 1
                    attacker.setBlocked(blockers)
        
        # Now get the remaining blockers:
        attack_prompt = "Select attacking creature to defend against"
        while num_creatures > 0 and num_attackers > 0:
            # select a creature that is attacking
            creature = self.getTarget(isCreature, zone=self.opponent.play, spell=False, required=False, prompt=attack_prompt)
            if not creature: break # Finished or not blocking
            if not creature.attacking:
                attack_prompt = "%s is not attacking"%creature.name
                self.send(InvalidTargetEvent(), target=creature)
                continue
            if creature.blocked:
                attack_prompt = "%s is already blocked"%creature.name
                self.send(InvalidTargetEvent(), target=creature)
                continue
            if not creature.canBeBlocked():
                attack_prompt = "%s cannot be blocked"%creature.name
                self.send(InvalidTargetEvent(), target=creature)
                continue
            if creature.attacking and not creature.blocked:
                blockers = []
                blocker = self.getTarget(isCreature, zone=self.play, spell=False, required=False, prompt="Select creature(s) to block %s"%creature.name)
                while blocker:
                    # XXX Make sure that the creature can be blocked and this is a valid block
                    if blocker.in_combat or blocker.tapped or not blocker.canBlock() or not blocker.canBlockAttacker(creature) or not creature.canBeBlockedBy(blocker): # and some other stuff
                        if blocker.in_combat: reason = "already blocking"
                        elif blocker.tapped: reason = "tapped"
                        elif not blocker.canBlock(): reason = "can't block"
                        else: reason = "can't block this creature"
                        self.send(InvalidTargetEvent(), target=blocker)
                        block_prompt = "%s cannot block (%s) - Select again"%(blocker.name,reason)
                    else: # Add to list of blockers
                        blockers.append(blocker)
                        num_creatures -= 1
                        blocker.setBlocking(creature)
                        #all_blockers.append(blocker)
                        block_prompt="Select another creature to block %s"%creature.name
                    if num_creatures > 0: blocker = self.getTarget(isCreature, zone=self.play, spell=False, required=False, prompt=block_prompt)
                    else: blocker = False
                blocking_list[creature] = blockers
                if blockers:
                    num_attackers -= 1
                    creature.setBlocked(blockers)

        #for b in all_blockers: b.pay_blocking_costs()
        #for b in all_blockers: 
        #    b.setBlocking()

        # XXX Send BlockerDeclaredEvent with creature as data
        return blocking_list.items()

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
                zone = action.zone
                if zone == self.play: return PlayAbility(sel)
                else: return sel.play_action(sel)
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
    def getIntention(self, prompt='', msg=""):
        def filter(action):
            if not (isinstance(action, OKAction) or isinstance(action, CancelAction)): return False
            else: return action
        context = {'get_choice': True, 'msg': msg, 'process': filter}
        if not prompt: prompt = "Declare intention"
        if not msg: msg = prompt
        result = self.input(context, "%s: %s"%(self.name,prompt))
        return isinstance(result, OKAction)
    def getSelection(self, sellist, numselections, required=True, msg='', prompt=''):
        def filter(action):
            if isinstance(action, CancelAction) and not required: return action
            if not isinstance(action, PassPriority): return action.selection
            return False
        if msg == '': msg = prompt
        context = {'get_selection': True, 'list':sellist, 'numselections': numselections, 'required': required, 'msg': msg, 'process': filter}
        sel = self.input(context,"%s: %s"%(self.name,prompt))
        if isinstance(sel, CancelAction): return False
        else: return sel
    def getCardSelection(self, sellist, numselections, from_zone, from_player, card_types=isCard, required=True, prompt=''):
        def filter(action):
            if isinstance(action, CancelAction) and not required: return action
            if not isinstance(action, PassPriority): return action.selection
            return False
        if numselections > len(sellist): numselections = len(sellist)
        context = {'get_cards': True, 'list':sellist, 'numselections': numselections, 'required': required, 'process': filter, 'from_zone': from_zone, 'from_player': from_player}
        get_selection = True
        if not (type(card_types) == list or type(card_types) == tuple): card_types = [card_types]
        while get_selection:
            sel = self.input(context,"%s: %s"%(self.name,prompt))
            if isinstance(sel, CancelAction): return False
            invalid = False
            for card in sel:
                for ctype in card_types:
                    if ctype(card):
                        break
                else: invalid = True
                if not invalid:
                    get_selection = False
                else: break
        return sel
    def getTarget(self, target_types, zone=[], required=True, spell=True, prompt='Select target'):
        # If required is True (default) then you can't cancel the request for a target
        def filter(action):
            # This function is really convoluted
            # If I return False here then the input function will keep cycling until valid input
            if spell:  # Disable Pass
                if isinstance(action, CancelAction):
                    if not required: return action
                    else: return False
                elif isinstance(action, PassPriority): return False
            else:
                # Not a spell - then for attacking or blocking
                if isinstance(action, CancelAction): return False
                elif isinstance(action, PassPriority):
                    if required: return False
                    else: return action

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
        else: return target
    def getMoreMana(self): # if necessary when paying a cost
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
            action = self.get(process = convert_gui_action, prompt="Not enough mana - Play Mana Abilities")
            # XXX Should this be done here?
            if isinstance(action, CancelAction):
                cancel = True
                break
            else: manaplayed = action.perform(self)
        [self.allowable_actions.pop() for i in range(2)]
        return not cancel
    def getManaChoice(self, required="0", prompt="Select mana to spend"):
        def filter(action):
            if isinstance(action, CancelAction): return action
            else: return action.mana
        context = {'get_mana_choice': True, 'manapool': self.manapool, 'required': required, "process": filter}
        result = self.input(context, "%s: %s"%(self.name,prompt))
        if isinstance(result, CancelAction): return False
        else: return result
    def getX(self, prompt="Select amount for X"):
        def filter(action):
            if isinstance(action, CancelAction): return action
            if isinstance(action, PassPriority): return False
            else: return action.amount
        context = {'get_X': True, "process": filter}
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
