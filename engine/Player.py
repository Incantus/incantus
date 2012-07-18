
from GameObjects import MtGObject, Card, Token
from GameKeeper import Keeper
from GameEvent import GameFocusEvent, DrawCardEvent, DiscardCardEvent, CardUntapped, LifeGainedEvent, LifeLostEvent, TargetedByEvent, InvalidTargetEvent, LogEvent, AttackerSelectedEvent, BlockerSelectedEvent, AttackersResetEvent, BlockersResetEvent, PermanentSacrificedEvent, TimestepEvent, AbilityPlayedEvent, CardSelectedEvent, AllDeselectedEvent, GameOverException, DealsDamageToEvent
from Mana import ManaPool, generate_hybrid_choices
from Zone import Library, Hand, Graveyard, Removed
from Action import CancelAction, PassPriority, OKAction
from Match import isCreature, isPermanent, isPlayer, isCard, isLandCard, isPlaneswalker, OpponentMatch
from stacked_function import replace
from Ability.Cost import ManaCost

class life(int):
    def __add__(self, other):
        if other < 0: other = 0
        return super(life,self).__add__(other)
    def __sub__(self, other):
        if other < 0: other = 0
        return super(life,self).__sub__(other)

class Player(MtGObject):
    def life():
        doc = "Player life property"
        def fget(self):
            return life(self._life)
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

    def __init__(self, name, deck):
        self.name = name
        self._life = 20
        self.poison = 0
        self.land_actions = -1
        self.hand_limit = 7
        self.draw_empty = False
        self.decklist = deck
    def init(self, play, stack, opponents):
        self.opponents = opponents
        self.library = Library()
        self.hand = Hand()
        self.graveyard = Graveyard()
        self.removed = Removed()
        self.play = play.get_view(self)
        self.stack = stack
        self.manapool = ManaPool()

        self.loadDeck()
        self.shuffle()
    def newTurn(self):
        self.land_actions = 1
    def reset(self):
        # return all cards to library
        for from_location in [self.play, self.hand, self.graveyard, self.removed]:
            for card in from_location: card.move_to("library")
    def loadDeck(self):
        for num, name in self.decklist:
            num = int(num)
            for n in range(num):
                self.library.add_new_card(Card.create(name, owner=self))

    # The following functions are part of the card code DSL
    def win(self, msg=''):
        if msg: msg = " %s and"%msg
        raise GameOverException("%s%s wins the game!"%(self, msg))
    def lose(self, msg=''):
        if msg: msg = " %s and"%msg
        raise GameOverException("%s%s loses the game!"%(self, msg))
    def add_mana(self, *amount):
        if len(amount) > 1:
            amount = self.make_selection(amount, 1, prompt="Choose mana to add")
        else: amount = amount[0]
        # XXX This is a bit hacky - used by, ex Calciform Pools
        # Add X mana in any combination of W and/or U to your manapool
        if "(" in amount:
            amount = self.make_selection(generate_hybrid_choices(amount), 1, prompt="Choose mana to add")
        self.manapool.add(amount)
    def shuffle(self):
        self.library.shuffle()
    def you_may(self, msg): return self.getIntention(prompt="You may %s"%msg,msg="Would you like to %s?"%msg)
    def you_may_pay(self, source, cost):
        if type(cost) == str: cost = ManaCost(cost)
        intent = self.getIntention(prompt="You may pay %s"%cost, msg="Would you like to pay %s"%cost)
        if intent and cost.precompute(source, self) and cost.compute(source, self):
            cost.pay(source, self)
            return True
        else: return False
    def play_card(self, card):
        ability = card.play_spell
        # XXX I need to return the new object on the stack somehow
        if ability.announce(card, self):
            self.send(AbilityPlayedEvent(), ability=ability)
            return True
        else:
            return False
    def create_tokens(self, info, number=1, tag=''):
        return [self.removed.add_new_card(Token.create(info, owner=self)) for _ in range(number)]
    def play_tokens(self, info, number=1, tag=''):
        return [token.move_to("play") for token in self.create_tokens(info, number)]
    def make_selection(self, sellist, number=1, required=True, prompt=''):
        if type(sellist[0]) == tuple: idx=False
        else: idx=True
        return self.getSelection(sellist, numselections=number, required=required, idx=idx, prompt=prompt)
    # A hack to make cards like Door of Destinies work. -MageKing17
    def choose_creature_type(self):
        subtypes = set()
        creature_types = lambda c: c.types.intersects(set(("Creature", "Tribal")))
        for cards in (getattr(player, zone).get(creature_types) for zone in ["play", "graveyard", "removed", "library", "hand"] for player in Keeper.players):
            for card in cards: subtypes.update(card.subtypes.current)
        return self.make_selection(sorted(subtypes), prompt='Choose a creature type')
    def choose_opponent(self):
        if len(self.opponents) == 1:
            return tuple(self.opponents)[0]
        else:
            return self.getTarget(target_types=OpponentMatch(self), required=True, prompt="Select an opponent")
    def choose_player(self):
        return self.getTarget(target_types=isPlayer, required=True, prompt="Select player")
    def reveal_cards(self, cards, msg=''):
        # XXX I can't do a true asynchronous reveal until i move to the new networking
        # You can only reveal from hand or library
        self.doRevealCard(cards, all=True)
    def look_at(self, cards):
        # You can only look at cards from hand or library
        self.doRevealCard(cards, all=False, prompt="look at %s"%', '.join(map(str, cards)))
    def reveal_hand(self):
        pass
    def choose_from(self, cards, number, cardtype=isCard, required=True, prompt=''):
        if not prompt: prompt = "Choose %d card(s)"%number
        selected = self.getCardSelection(cards, number, cardtype=cardtype, required=required, prompt=prompt)
        if number == 1: return selected[0] if selected else None
        else: return selected
    def choose_from_zone(self, number=1, cardtype=isCard, zone="play", action='', required=True, all=False):
        cards_in_zone = getattr(self, zone).get(cardtype)
        if zone == "library" and not cardtype == isCard: required = False
        if number >= len(cards_in_zone) and required: cards = cards_in_zone
        else:
            cards = []
            if zone == "play" or zone == "hand":
                a = 's' if number > 1 else ''
                total = number
                prompt = "Select %s%s to %s: %d left of %d"%(cardtype, a, action, number, total)
                while number > 0:
                    card = self.getTarget(cardtype, zone=zone, from_player=None if all else "you", required=required, prompt=prompt)
                    if card == False: break
                    if card in cards:
                        prompt = "Card already selected - select again"
                        self.send(InvalidTargetEvent(), target=card)
                    else:
                        cards.append(card)
                        number -= 1
                        prompt = "Select %s%s to %s: %d left of %d"%(cardtype, a, action, number, total)
            else:
                selection = list(getattr(self, zone))
                if number >= -1:
                    if number == 1: a = 'a'
                    elif number == -1: a = 'any number of'
                    else: a = str(number)
                    cards = self.getCardSelection(selection, number=number, cardtype=cardtype, required=required, prompt="Search your %s for %s %s to %s."%(zone, a, cardtype, action))
                    if zone == "library": self.shuffle()
        return cards
    def draw(self, number=1):
        return sum([self.draw_single() for i in range(number)])
    def draw_single(self):
        card = self.library.top()
        num = 0
        if card == None: self.draw_empty = True
        else:
            num = 1
            card.move_to("hand")
            self.send(DrawCardEvent())
        return num
    def discard(self, card):
        if str(card.zone) == "hand":
            card = card.move_to("graveyard")
            self.send(DiscardCardEvent(), card=card)
            return card
        else: return None
    def force_discard(self, number=1, cardtype=isCard):
        if number == -1: number = len(self.hand)
        cards = self.choose_from_zone(number, cardtype, "hand", "discard")
        return [self.discard(card) for card in cards]
    def discard_down(self):
        number = len(self.hand) - self.hand_limit
        if number > 0: return self.force_discard(number)
        else: return []
    def sacrifice(self, perm):
        if perm.controller == self and str(perm.zone) == "play":
            card = perm.move_to("graveyard")
            self.send(PermanentSacrificedEvent(), card=perm)
            return card
        else: return None
    def force_sacrifice(self, number=1, cardtype=isPermanent):
        perms = self.choose_from_zone(number, cardtype, "play", "sacrifice")
        for perm in perms: self.sacrifice(perm)
        return len(perms)
    def skip_next_turn(self, msg):
        def condition(keeper):
            if keeper.player_cycler.peek() == self:
                keeper.nextActivePlayer()
                return True
            else: return False
        def skipTurn(keeper):
            keeper.newTurn()
            skipTurn.expire()
        return replace(Keeper, "newTurn", skipTurn, condition=condition, msg=msg)
    def take_extra_turn(self):
        Keeper.player_cycler.insert(self)
    def setup_special_action(self, action):
        #408.2i. Some effects allow a player to take an action at a later time, usually to end a continuous effect or to stop a delayed triggered ability. This is a special action. A player can stop a delayed triggered ability from triggering or end a continuous effect only if the ability or effect allows it and only when he or she has priority. The player who took the action gets priority after this special action.
        #408.2j. Some effects from static abilities allow a player to take an action to ignore the effect from that ability for a duration. This is a special action. A player can take an action to ignore an effect only when he or she has priority. The player who took the action gets priority after this special action. (Only 3 cards use this: Damping Engine, Lost in Thought, Volrath's Curse)
        raise NotImplementedError()

    # Rule engine functions
    def mulligan(self):
        number = 7
        while number > 0:
            number -= 1
            if self.getIntention("", "Would you like to mulligan?"): #, "Would you like to mulligan?"):
                self.send(LogEvent(), msg="%s mulligans"%self)
                for card in self.hand: card.move_to(self.library)
                self.shuffle()
                yield
                self.draw(number)
                yield True
            else: break
        yield False
    def checkUntapStep(self, cards): return True
    def untapStep(self):
        permanents = untapCards = set([card for card in self.play if card.canUntapDuringUntapStep()])
        prompt = "Select cards to untap"
        valid_untap = self.checkUntapStep(permanents)
        while not valid_untap:
            permanents = set()
            done_selecting = False
            perm = self.getPermanentInPlay(prompt=prompt)
            while not done_selecting:
                if perm == True:
                    done_selecting = True
                    self.send(AllDeselectedEvent())
                    break
                elif perm == False:
                    # reset untap
                    permanents = untapCards
                    self.send(AllDeselectedEvent())
                    prompt = "Selection canceled - select cards to untap"
                    break
                else:
                    if not perm in permanents and perm in untapCards:
                        permanents.add(perm)
                        self.send(CardSelectedEvent(), card=perm)
                        prompt = "%s selected - select another"%perm
                    elif perm in permanents:
                        self.send(InvalidTargetEvent(), target=perm)
                        prompt = "%s already selected - select another"%perm
                    else:
                        self.send(InvalidTargetEvent(), target=perm)
                        prompt = "%s can't be untapped - select another"%perm
                perm = self.getPermanentInPlay(prompt=prompt)
            if done_selecting:
                valid_untap = self.checkUntapStep(permanents)
                if not valid_untap:
                    prompt = "Invalid selection - select again"
        for card in permanents: card.untap()
    def assignDamage(self, amt, source, combat=False):
        # amt is greater than 0
        self.life -= amt
        source.send(DealsDamageToEvent(), to=self, amount=amt, combat=combat)
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
    def declareDefendingPlayer(self):
        return self.choose_opponent()
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
                                target = self.getTarget(target_types=(OpponentMatch(self), isPlaneswalker), zone="play", prompt="Select opponent to attack")
                                if target in opponents:
                                    creature.setOpponent(target)
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
        if len(all_on_blocking_side) == 0: return combat_assignment

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
                        if blockers:
                            attacker.setBlocked(blockers)
                            for blocker in blockers:
                                blocker.payBlockCost()
                                blocker.setBlocking(attacker)
                else:
                    blocker_prompt = "Invalid defense - choose another"
                    for creature in invalid_blockers: self.send(InvalidTargetEvent(), target=creature)
            else: blocker_prompt = "Declare blockers (Enter to accept, Escape to reset)"

        return combat_assignment

    def doNonInstantAction(self):
        return self.getAction(prompt="Play Spells or Activated Abilities")
    def doInstantAction(self):
        return self.getAction(prompt="Play Instants or Activated Abilities")
    def chooseAndDoAbility(self, card, abilities):
        numabilities = len(abilities)
        if numabilities == 0: return False
        elif numabilities == 1: ability = abilities[0]
        else:
            ability = self.make_selection(abilities, 1, required=False, prompt="%s: Select ability"%card)
            if ability == False: return False
        return ability.copy().announce(card, self)


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
    def getMoreMana(self, required): # if necessary when paying a cost
        def convert_gui_action(action):
            if isinstance(action, PassPriority): return False
            elif isinstance(action, CancelAction): return action
            sel = action.selection
            if not isPlayer(sel) and sel.controller == self: return action
            else: return False
        
        context = {"get_ability": True, "process": convert_gui_action}
        prompt = "Need %s - play mana abilities (Esc to cancel)"%required
        # This loop seems really ugly - is there a way to structure it better?
        cancel = False    # This is returned - it's a way to back out of playing an ability
        while True:
            action = self.input(context, "%s: %s"%(self.name, prompt))
            if isinstance(action, CancelAction):
                cancel = True
                break
            card = action.selection
            abilities = [ability for ability in card.abilities.activated() if hasattr(ability, "mana_ability")]
            if self.chooseAndDoAbility(card, abilities): break
        return not cancel
    def getAction(self, prompt=''):
        def convert_gui_action(action):
            if isinstance(action, PassPriority): return action
            elif isinstance(action, CancelAction): return False
            sel = action.selection
            if not isPlayer(sel) and sel.controller == self: return action
            else: return False

        context = {"get_ability": True, "process": convert_gui_action}
        # This loop seems really ugly - is there a way to structure it better?
        passed = False
        while True:
            action = self.input(context, "%s: %s"%(self.name,prompt))
            if isinstance(action, PassPriority):
                passed = True
                break
            card = action.selection
            abilities = card.abilities.activated()
            # Include the casting ability
            if card.play_spell and card.play_spell.playable(card): abilities.append(card.play_spell)
            if self.chooseAndDoAbility(card, abilities): break
        return not passed

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
        if idx == True: idx_sellist = [(val, i) for i, val in enumerate(sellist)]
        else:
            idx_sellist = [(val[0], i) for i, val in enumerate(sellist)]
            sellist = [val[1] for val in sellist]
        context = {'get_selection': True, 'list':idx_sellist, 'numselections': numselections, 'required': required, 'msg': msg, 'process': filter}
        # get_selection only returns indices into the given list
        sel = self.input(context,"%s: %s"%(self.name,prompt))
        if isinstance(sel, CancelAction): return False
        if numselections == 1: return sellist[sel]
        elif numselections == -1: return [sellist[i] for i in sel]
        else: return [sellist[i] for i in sel][:numselections]
    def getCardSelection(self, selection, number, cardtype=isCard, zone=None, player=None, required=True, prompt=''):
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
        if isinstance(sel, CancelAction): return []
        else: return sel
    def getPermanentInPlay(self, prompt='Select permanent'):
        def filter(action):
            if isinstance(action, CancelAction) or isinstance(action, PassPriority):
                return action

            card = action.selection
            if isPermanent(card) and (card.controller == self):
                return card
            else:
                self.send(InvalidTargetEvent(), target=card)
                return False
        context = {'get_target': True, 'process': filter}
        card = self.input(context, "%s: %s"%(self.name,prompt))

        if isinstance(card, PassPriority): return True
        elif isinstance(card, CancelAction): return False
        else: return card
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
    def getTarget(self, target_types, zone=None, from_player=None, required=True, prompt='Select target'):
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
            if isPlayer(target) or ((not zone or str(target.zone) == zone) and (not from_player or (from_player == "you" and target.controller == self) or (from_player == "opponent" and target.controller in self.opponents))):
                for target_type in target_types:
                    if target_type(target): return target
            # Invalid target
            self.send(InvalidTargetEvent(), target=target)
            return False
        context = {'get_target': True, 'process': filter}
        target = self.input(context, "%s: %s"%(self.name,prompt))

        if isinstance(target, CancelAction) or isinstance(target, PassPriority): return False
        return target
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
    def doRevealCard(self, cards, all=True, prompt=''):
        import operator
        if not operator.isSequenceType(cards): cards = [cards]
        if not prompt: prompt = "reveals card(s) "+', '.join(map(str,cards))
        zone = str(cards[0].zone)
        player = cards[0].controller
        context = {'reveal_card': True, 'cards': cards, 'from_zone': zone, 'from_player': player, 'all': all, 'process': lambda action: True} #isinstance(action, PassPriority)}
        return self.input(context, "%s: %s"%(self.name, prompt))
