import itertools, random
from GameObjects import MtGObject
from Action import PassPriority
import Match
from GameEvent import *
from Zone import Play
from Stack import Stack
import stacked_function as stacked
from Ability.AssignDamage import AssignDamage

state_map = {"Untap": UntapStepEvent, "Upkeep": UpkeepStepEvent, "Draw": DrawStepEvent,
             "Main1": MainPhase1Event, "Main2": MainPhase2Event, "EndMain": EndMainPhaseEvent,
             "BeginCombat": BeginCombatEvent, "Attack": AttackStepEvent,
             "Block": BlockStepEvent, "Damage": AssignDamageEvent, "EndCombat": EndCombatEvent,
             "EndTurn": EndTurnStepEvent, "Cleanup": CleanupPhase}

class player_cycler(object):
    def __init__(self, players):
        self._cyclers = itertools.cycle(players)
        self._insertions = []
        self._peek = None
    def next(self):
        if self._peek:
            player, self._peek = self._peek, None
            return player
        else:
            if not self._insertions: return self._cyclers.next()
            else: return self._insertions.pop()
    def insert(self, player):
        self._insertions.append(player)
    def peek(self):
        self._peek = self.next()
        return self._peek

class GameKeeper(MtGObject):
    keeper = True
    players = property(fget=lambda self: self._player_order)
    other_player = property(fget=lambda self: self._player_order[1])

    def current_player():
        def fget(self): return self._player_order[0]
        def fset(self, player):
            players = list(self._player_order)
            idx = players.index(player)
            self._player_order = tuple(players[idx:]+players[:idx])
        return locals()
    current_player = property(**current_player())

    def init(self, players):
        self.current_phase = "Pregame"
        self.stack = Stack(self)
        self.play = Play(self)

        self.loadMods()
        self._tokens_out_play = []
        self.register(lambda sender: setattr(sender, "is_LKI", True) or self._tokens_out_play.append(sender), TokenLeavingPlay(), weak=False)

        all_players = set(players)
        for player in players:
            player.init(self.play, self.stack, all_players-set((player,)))
        self._player_order = players

    # Determine starting player
    def start(self):
        players = list(self.players)
        random.shuffle(players)
        for idx, start_player in enumerate(players):
            if idx == (len(players)-1) or start_player.getIntention("", "Would you like to go first?"):
                break
        self._player_order = tuple(players[idx:]+players[:idx])
        self.player_cycler = player_cycler(self.players)

        self.send(TimestepEvent())
        for player in self.players:
            player.draw(7)
        self.send(TimestepEvent())
        for player in self.players:
            for did_mulligan in player.mulligan():
                self.send(TimestepEvent())
                if did_mulligan == False: break
        try:
            self.run()
        except GameOverException, g:
            self.send(GameOverEvent())
            self.cleanup()
            return g.msg

    def loadMods(self):
        import glob, traceback, CardEnvironment
        for mod in glob.glob("./data/rulemods/*.py"):
            code = open(mod, "r").read()
            try:
                exec code in vars(CardEnvironment)
            except Exception:
                code = code.split("\n")
                print "\n%s\n"%'\n'.join(["%03d\t%s"%(i+1, line) for i, line in zip(range(len(code)), code)])
                traceback.print_exc(4)
            file.close()

    def cleanup(self):
        for player in self.players: player.reset()

    def run(self):
        self.send(GameStartEvent())

        # skip the first draw step
        def skipDraw(self): skipDraw.expire()
        stacked.override(self, "drawStep", skipDraw, stacked.most_recent)

        _phases = ("newTurn", ("untapStep", "upkeepStep", "drawStep"), "mainPhase1", "combatPhase", "mainPhase2", "endPhase")
        for phase in itertools.cycle(_phases):
            if type(phase) == tuple:
                for step in phase: getattr(self, step)()
            else: getattr(self, phase)()
            self.manaBurn()

    def setState(self, state):
        # Send notice that state changed
        self.current_phase = state
        self.send(GameStepEvent(), state=state)
        self.send(state_map[state](), player=self.current_player)
    def manaBurn(self):
        for player in self.players:
            while not player.manaBurn():
                self.playInstantaneous()
    def checkSBE(self):
        #State-Based Effects - rule 420.5
        # check every time someone gets priority (rule 408.1b)
        # Also during cleanup step - if there is an effect, player gets priority
        players = self.players
        actions = []
        # 420.5a A player with 0 or less life loses the game.
        def LoseGame(player, msg):
            def SBE(): player.lose(msg)
            return SBE
        for player in players:
            if player.life <= 0: 
                actions.append(LoseGame(player, "has less than 0 life"))

        # 420.5b and 420.5c are combined
        # 420.5b A creature with toughness 0 or less is put into its owner's graveyard. Regeneration can't replace this event.
        # 420.5c A creature with lethal damage, but greater than 0 toughness, is destroyed. Lethal damage is an amount of damage greater than or equal to a creature's toughness. Regeneration can replace this event.
        def MoveToGraveyard(permanent):
            def SBE(): permanent.move_to("graveyard")
            return SBE
        for creature in self.play.get(Match.isCreature):
            if creature.toughness <= 0:
                actions.append(MoveToGraveyard(creature))
            elif creature.shouldDestroy():
                actions.append(creature.destroy)
        for walker in self.play.get(Match.isPlaneswalker):
            if walker.shouldDestroy():
                actions.append(walker.destroy)

        # 420.5d An Aura attached to an illegal object or player, or not attached to an object or player, is put into its owner's graveyard.
        for aura in self.play.get(Match.isAura):
            if not aura.isValidAttachment():
                actions.append(MoveToGraveyard(aura))
        # 420.5e If two or more legendary permanents with the same name are in play, all are put into their owners' graveyards. This is called the "legend rule." If only one of those permanents is legendary, this rule doesn't apply.
        legendaries = self.play.get(Match.isLegendaryPermanent)
        # XXX There's got to be a better way to find multiples
        remove_dup = []
        for i, l1 in enumerate(legendaries):
            for l2 in legendaries[i+1:]:
                if l1.name == l2.name:
                    remove_dup.extend([l1,l2])
                    break
        # 2 or more Planeswalkers with the same name
        planeswalkers = self.play.get(Match.isPlaneswalker)
        for i, l1 in enumerate(planeswalkers):
            for l2 in planeswalkers[i+1:]:
                if l1.subtypes.intersects(l2.subtypes):
                    remove_dup.extend([l1,l2])
                    break
        # Now remove all the cards in remove_dup
        if len(remove_dup) > 0:
            def SBE():
                for card in remove_dup:
                    player = card.controller
                    card.move_to("graveyard")
            actions.append(SBE)

        # 420.5f A token in a zone other than the in-play zone ceases to exist.
        if len(self._tokens_out_play) > 0:
            def SBE():
                for token in self._tokens_out_play: token.zone.cease_to_exist(token)
                # XXX Now only GameObjects.cardmap has a reference to the token - we need to delete it somehow
                self._tokens_out_play[:] = []
            actions.append(SBE)
        # 420.5g A player who attempted to draw a card from an empty library since the last time state-based effects were checked loses the game.
        for player in players:
            if player.draw_empty:
                actions.append(LoseGame(player, "draws from an empty library"))
        # 420.5h A player with ten or more poison counters loses the game.
        for player in players:
            if player.poison >= 10:
                actions.append(LoseGame(player, "is poisoned"))

        # 420.5i If two or more permanents have the supertype world, all except the one that has been a permanent with the world supertype in play for the shortest amount of time are put into their owners' graveyards. In the event of a tie for the shortest amount of time, all are put into their owners' graveyards. This is called the "world rule."
        # 420.5j A copy of a spell in a zone other than the stack ceases to exist. A copy of a card in any zone other than the stack or the in-play zone ceases to exist.
        # 420.5k An Equipment or Fortification attached to an illegal permanent becomes unattached from that permanent. It remains in play.
        for equipment in self.play.get(Match.isEquipment):
            if equipment.attached_to and not equipment.isValidAttachment():
                actions.append(equipment.unattach)
        # 420.5m A permanent that's neither an Aura, an Equipment, nor a Fortification, but is attached to another permanent, becomes unattached from that permanent. It remains in play.
        for permanent in self.play.get(Match.isPermanent):
            if hasattr(permanent, "attached_to") and permanent.attached_to and not Match.isAttachment(permanent):
                actions.append(permanent.unattach)
        # 420.5n If a permanent has both a +1/+1 counter and a -1/-1 counter on it, N +1/+1 and N -1/-1 counters are removed from it, where N is the smaller of the number of +1/+1 and -1/-1 counters on it.
        def RemoveCounters(perm, num):
            def SBE():
                perm.remove_counters("+1+1", num)
                perm.remove_counters("-1-1", num)
            return SBE
        for perm in self.play.get(Match.isPermanent):
            if perm.num_counters() > 0:
                plus = perm.num_counters("+1+1")
                minus = perm.num_counters("-1-1")
                numremove = min(plus, minus)
                if numremove: actions.append(RemoveCounters(perm, numremove))

        if actions:
            for action in actions: action()
        self.send(TimestepEvent())
        return not len(actions) == 0

    def newTurn(self):
        # Next player is current player
        self.current_player = self.player_cycler.next()
        self.send(NewTurnEvent(), player=self.current_player)
        self.current_player.newTurn()
    def untapStep(self):
        # untap all cards
        self.setState("Untap")
        # XXX Do phasing - nothing that phases in will trigger any "when ~this~ comes 
        # into play..." effect, though they will trigger "When ~this~ leaves play" effects
        self.current_player.untapStep()
    def upkeepStep(self):
        self.setState("Upkeep")
        self.playInstantaneous()
    def drawStep(self):
        self.setState("Draw")
        self.current_player.draw()
        self.playInstantaneous()
    def mainPhase1(self):
        self.setState("Main1")
        self.playSpells()
        self.setState("EndMain")
    def calculateDamage(self, combat_assignment, is_first_strike=False):
        new_combat_list = []
        # Remove all attackers and blockers that are no longer valid
        for attacker, blockers in combat_assignment.items():
            # Do the attacker first - make sure it is still valid
            if Match.isCreature(attacker) and str(attacker.zone) == "play" and attacker.in_combat:
                newblockers = []
                # Remove any blockers that are no longer in combat
                for blocker in blockers:
                    if Match.isCreature(blocker) and str(blocker.zone) == "play" and blocker.in_combat:
                        newblockers.append(blocker)
                new_combat_list.append((attacker, newblockers))
        # These guys are still valid
        damage_assignment = {}

        tramplers = []
        for attacker, blockers in new_combat_list:
            if attacker.canStrike(is_first_strike):
                attacker.didStrike()
                if not attacker.blocked:
                    # XXX I should check that the attacker can damage the player
                    damage = {attacker.opponent: attacker.combatDamage()}
                else:
                    if "trample" in attacker.abilities:
                        trampling = True
                        tramplers.append(attacker)
                    else: trampling = False
                    if len(blockers) > 1 or trampling:
                        # Ask the player how to distribute damage
                        # XXX I should check whether the attacker can assign damage to blocker
                        damage = self.current_player.getDamageAssignment([(attacker, blockers)], trample=trampling)
                    elif len(blockers) == 1:
                        # XXX I should check whether the attacker can assign damage to blocker
                        damage = {blockers[0]: attacker.combatDamage()}
                    else: damage = {} # attacker was blocked, but there are no more blockers
                damage_assignment[attacker] = damage
            # attacker receives all damage from blockers
            for blocker in blockers:
                if blocker.canStrike(is_first_strike):
                    blocker.didStrike()
                    # XXX Check whether the blocker can assign damage to attacker
                    damage = {attacker: blocker.combatDamage()}
                    # Handles the case where one blocker can block multiple creatures
                    if damage_assignment.has_key(blocker): damage_assignment[blocker].update(damage)
                    else: damage_assignment[blocker] = damage

        return tramplers, damage_assignment
    def handle_trample(self, tramplers, damage_assn):
        for attacker in tramplers:
            if not damage_assn.get(attacker,None) == None:
                damage_assn[attacker][attacker.opponent] = attacker.trample(damage_assn[attacker])
    def combatDamageStep(self, combat_assignment):
        self.setState("Damage")

        tramplers, first_strike_damage = self.calculateDamage(combat_assignment, is_first_strike=True)
        if first_strike_damage:
            # Handle trample
            if tramplers: self.handle_trample(tramplers, first_strike_damage)
            damages = AssignDamage(first_strike_damage.items(),"First Strike Damage")
            self.stack.push(damages)
            # Send message about damage going on stack
            self.playInstantaneous()

        tramplers, regular_combat_damage = self.calculateDamage(combat_assignment)
        # Handle trample
        if regular_combat_damage:
            if tramplers: self.handle_trample(tramplers, regular_combat_damage)
            damages = AssignDamage(regular_combat_damage.items(), "Regular Combat Damage")
            self.stack.push(damages)
            # Send message about damage going on stack
            self.playInstantaneous()
    def combatPhase(self):
        # Beginning of combat
        self.setState("BeginCombat")
        self.playInstantaneous()
        combat_assignment = {}
        if self.current_player.attackingIntention():
            # Attacking
            self.setState("Attack")
            # Get all the players/planeswalkers
            opponents = sum([player.play.get(Match.isPlaneswalker) for player in self.current_player.opponents], list(self.current_player.opponents))
            attackers = self.current_player.declareAttackers(opponents)
            if attackers: self.send(DeclareAttackersEvent(), attackers=attackers)
            self.playInstantaneous()
            # After playing instants, the list of attackers could be modified (if a creature was put into play "attacking", so we regenerate the list
            attackers = self.play.get(Match.isCreature.with_condition(lambda c: c.attacking))
            if attackers:
                # Blocking
                self.setState("Block")
                combat_assignment = self.other_player.declareBlockers(attackers)
                self.send(DeclareBlockersEvent(), combat_assignment=combat_assignment)
                self.playInstantaneous()
                # Damage
                self.combatDamageStep(combat_assignment)
        # End of Combat
        # trigger effects that happen at end of combat
        # Clear off attacking and blocking status?
        self.setState("EndCombat")
        for attacker, blockers in combat_assignment.items():
            attacker.clearCombatState()
            for blocker in blockers: blocker.clearCombatState()
        self.playInstantaneous()
    def mainPhase2(self):
        self.setState("Main2")
        self.playSpells()
        self.setState("EndMain")
    def endPhase(self):
        # End of turn
        self.setState("EndTurn")
        #  - trigger "at end of turn" abilities - if new "at end of turn" event occurs doesn't happen until next turn
        #  - can play instants or abilities
        self.playInstantaneous()

        # Cleanup
        # - discard down to current hand limit
        # - expire abilities that last "until end of turn" or "this turn"
        # - clear non-lethal damage
        self.setState("Cleanup")
        while True:
            self.current_player.discard_down()
            # Clear all nonlethal damage
            self.send(CleanupEvent())
            self.send(TimestepEvent())
            for creature in self.play.get(Match.isCreature):
                creature.clearDamage()
            triggered_once = False
            while self.checkSBE(): triggered_once = True
            if self.stack.process_triggered(): triggered_once = True
            if triggered_once: self.playInstantaneous()
            else: break
        self.send(TurnFinishedEvent(), player=self.current_player)

    # The next set of functions deals with the operation of the stack
    # It may seem recursive but it's not
    def playSpells(self):
        stack_less_action = self.playStackSpells()
        # Time to unwind
        while not self.stack.empty() or stack_less_action:
            if not stack_less_action: self.stack.resolve()
            # Now it's the active player's turn to play something
            if self.stack.empty(): stack_less_action = self.playStackSpells()
            else: self.playStackInstant()
    def playStackSpells(self):
        while self.checkSBE():
            if not self.stack.empty():
                self.playStackInstant()
                return False
        self.stack.process_triggered()
        self.send(HasPriorityEvent(), player=self.current_player)
        action = self.current_player.getMainAction()
        if not isinstance(action, PassPriority):
            action.perform(self.current_player)
            if not self.stack.empty(): self.playStackInstant()
            else: return True
        else: self.playStackInstant(skip_first=True)
        return False
    def playInstantaneous(self):
        self.playStackInstant()
        # Time to unwind
        while not self.stack.empty():
            self.stack.resolve()
            # Now it's the active player's turn to play something
            self.playStackInstant()
    def playStackInstant(self, skip_first=False):
        if not skip_first: self.continuePlay(self.current_player)
        response = self.continuePlay(self.other_player)
        while response:
            response = self.continuePlay(self.current_player)
            if not response: break
            response = self.continuePlay(self.other_player)
    def continuePlay(self, player):
        responding = False
        priorityPassed = False
        while not priorityPassed:
            while self.checkSBE(): pass
            self.stack.process_triggered()
            self.send(HasPriorityEvent(), player=player)
            action = player.getAction()
            if not isinstance(action, PassPriority):
                # if something is done in response
                responding = action.perform(player)
            else: priorityPassed = True
        return responding

Keeper = GameKeeper()
