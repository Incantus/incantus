
from GameObjects import MtGObject
from Action import PassPriority
import Match
from GameEvent import *
from Zone import Play
from Stack import Stack

class GamePhases(object):
    players = property(fget=lambda self: [self.curr_player, self.other_player])
    def __init__(self, gamekeeper, players):
        self.state_map = dict([(p,i) for i, p in enumerate(["BeginTurn", "Main1", "Combat", "Main2", "EndPhase"])])
        self.game_phases = [self.makeBeginningPhase(gamekeeper), gamekeeper.mainPhase1, gamekeeper.combatPhase, gamekeeper.mainPhase2, gamekeeper.endPhase]
        self.num_players = len(players)
        self.curr_player, self.other_player = players[0], players[1]
        GamePhases.newTurn = GamePhases.firstTurn
    def makeBeginningPhase(self, gamekeeper):
        return [gamekeeper.beginningPhase, gamekeeper.untapStep, gamekeeper.upkeepStep, gamekeeper.drawStep]
    def copyPhases(self):
        newphases = self.game_phases[:]
        newphases[0] = self.game_phases[0][:]
        return newphases
    def __iter__(self):
        for i, phase in enumerate(self.curr_phases):
            self.current = i
            yield phase
    def nextTurn(self):
        self.curr_player, self.other_player = self.other_player, self.curr_player
        self.curr_phases = self.copyPhases()
        return self.curr_player, self.other_player
    def firstTurn(self):
        GamePhases.newTurn = GamePhases.nextTurn
        self.curr_phases = self.copyPhases()
        del self.curr_phases[0][-1]
        return self.curr_player, self.other_player
    def addPhases(self, phases, after_phase=None):
        if not (type(phases) == list or type(phases) == tuple): phases = [phases]
        if after_phase == None: position = self.current+1
        elif after_phase == "EndPhase": position=-1
        else: position = self.state_map[after_phase]+1
        for phase in phases[::-1]:
            self.curr_phases.insert(position, self.game_phases[self.state_map[phase]])
    def skipPhase(self, phase):
        pass

class GameKeeper(MtGObject):
    players = property(fget=lambda self: self.game_phases.players)
    def __init__(self):
        self.ready_to_start = False

    def init(self, player1, player2):
        self.game_phases = GamePhases(self, (player1, player2))
        self.stack = Stack(self.game_phases)
        self.play = Play(self.game_phases)
        player1.init(self.play, self.stack)
        player2.init(self.play, self.stack)
        self.tokens_out_play = []
        self.register(lambda sender: self.tokens_out_play.append(sender), TokenLeavingPlay(), weak=False)
        self.ready_to_start = True

    def run(self):
        if not self.ready_to_start: raise Exception("Players not added - not ready to start")
        # XXX This is hacky - need a better way to signal end of game
        self.send(GameStartEvent())
        self.send(TimestepEvent())
        for player in self.game_phases.players:
            for i in range(7): player.draw()
        self.send(TimestepEvent())
        for player in self.game_phases.players:
            for did_mulligan in player.mulligan():
                self.send(TimestepEvent())
                if did_mulligan == False: break
        try:
            while True:
                self.singleTurn()
        except GameOver, g:
            self.send(GameOverEvent())
            # Return all cards to library
            for card in self.play:
                card.move_to(card.owner.library)
            for player in self.game_phases.players:
                player.reset()
            self.ready_to_start = False
            return g.msg

    def singleTurn(self):
        # See http://www.starcitygames.com/php/news/expandnews.php?Article=4367
        # Phases - beginning
        #          pre-combat main,
        #          combat - combat declaration, fast effects, declaration of 
        # attackers, fast effects, declaration of blockers, fast effects, first strike 
        # damage on the stack, fast effects, first strike damage, fast effects,
        # non-first strike damage on the stack, fast effects, regular damage
        #          post combat main
        #          end step
        self.curr_player, self.other_player = self.game_phases.newTurn()
        self.send(NewTurnEvent(), player=self.curr_player)
        self.curr_player.resetLandActions()
        for phase in self.game_phases:
            if type(phase) == list:
                for step in phase: step()
            else: phase()
            self.manaBurn()
    def setState(self, state):
        # Send notice that state changed
        #print "******\nGame state:", state
        state_map = {"BeginTurn": BeginTurnEvent, "Untap": UntapStepEvent, "Upkeep": UpkeepStepEvent, "Draw": DrawStepEvent,
                     "Main1": MainPhaseEvent, "Main2": MainPhaseEvent, "EndMain": EndMainPhaseEvent,
                     "PreCombat": PreCombatEvent, "Attack": AttackStepEvent,
                     "Block": BlockStepEvent, "Damage": AssignDamageEvent, "EndCombat": EndCombatEvent,
                     "EndTurn": EndTurnStepEvent, "Cleanup": CleanupPhase}
        self.send(GameStepEvent(), state=state)
        self.send(state_map[state](), player=self.curr_player)
    def manaBurn(self):
        for player in self.game_phases.players:
            while not player.manaBurn():
                self.playInstantaneous()
    def checkSBE(self):
        #State-Based Effects - rule 420.5
        # check every time someone gets priority (rule 408.1b)
        # Also during cleanup step - if there is an effect, player gets priority
        players = self.game_phases.players
        actions = []
        # 420.5a A player with 0 or less life loses the game.
        def EndGame(player, msg):
            def SBE(): raise GameOver("%s %s and loses the game!"%(player, msg))
            return SBE
        for player in players:
            if player.life <= 0: 
                actions.append(EndGame(player, "has less than 0 life"))

        # 420.5b and 420.5c are combined
        # 420.5b A creature with toughness 0 or less is put into its owner's graveyard. Regeneration can't replace this event.
        # 420.5c A creature with lethal damage, but greater than 0 toughness, is destroyed. Lethal damage is an amount of damage greater than or equal to a creature's toughness. Regeneration can replace this event.
        def MoveToGraveyard(creature):
            def SBE(): creature.move_to(creature.owner.graveyard)
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
        def DestroyAura(aura):
            def SBE():
                aura.unattach()
                aura.move_to(aura.owner.graveyard)
            return SBE
        for aura in self.play.get(Match.isAura):
            if not aura.isValidAttachment():
                actions.append(DestroyAura(aura))
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
                    card.move_to(card.owner.graveyard)
            actions.append(SBE)

        # 420.5f A token in a zone other than the in-play zone ceases to exist.
        if len(self.tokens_out_play) > 0:
            def SBE():
                for token in self.tokens_out_play: token.zone.cease_to_exist(token)
                # XXX Now only GameObjects.cardmap has a reference to the token - we need to delete it somehow
                self.tokens_out_play[:] = []
            actions.append(SBE)
        # 420.5g A player who attempted to draw a card from an empty library since the last time state-based effects were checked loses the game.
        for player in players:
            if player.draw_empty:
                actions.append(EndGame(player, "draws from an empty library"))
        # 420.5h A player with ten or more poison counters loses the game.
        for player in players:
            if player.poison >= 10:
                actions.append(EndGame(player, "is poisoned"))

        # 420.5i If two or more permanents have the supertype world, all except the one that has been a permanent with the world supertype in play for the shortest amount of time are put into their owners' graveyards. In the event of a tie for the shortest amount of time, all are put into their owners' graveyards. This is called the "world rule."
        # 420.5j A copy of a spell in a zone other than the stack ceases to exist. A copy of a card in any zone other than the stack or the in-play zone ceases to exist.
        # 420.5k An Equipment or Fortification attached to an illegal permanent becomes unattached from that permanent. It remains in play.
        def Unattach(equipment):
            def SBE():
                equipment.unattach()
            return SBE
        for equipment in self.play.get(Match.isEquipment):
            if equipment.attached_to and not equipment.isValidAttachment():
                actions.append(Unattach(equipment))
        # 420.5m A permanent that's neither an Aura, an Equipment, nor a Fortification, but is attached to another permanent, becomes unattached from that permanent. It remains in play.
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
    def beginningPhase(self):
        self.setState("BeginTurn")
    def untapStep(self):
        # untap all cards
        self.setState("Untap")
        # XXX Do phasing - nothing that phases in will trigger any "when ~this~ comes 
        # into play..." effect, though they will trigger "When ~this~ leaves play" effects
        self.curr_player.untapCards()
    def upkeepStep(self):
        self.setState("Upkeep")
        self.playInstantaneous()
    def drawStep(self):
        self.curr_player.draw()
        # XXX If you have a card that let's you draw more than one card, you get priority
        # before each draw
        self.setState("Draw")
        self.playInstantaneous()
    def mainPhase1(self):
        self.setState("Main1")
        self.playSpells()
        self.setState("EndMain")
    def calculateDamage(self, combat_assignment, first_strike=False):
        new_combat_list = []
        # Remove all attackers and blockers that are no longer valid
        for attacker, blockers in combat_assignment:
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
        def check_strike(card):
            return ((first_strike and ("first strike" in card.abilities or "double strike" in card.abilities)) or
               (not first_strike and not ("first strike" in card.abilities)))
        for attacker, blockers in new_combat_list:
            if check_strike(attacker):
                if not attacker.blocked:
                    # XXX I should check that the attacker can damage the player
                    damage = {self.other_player: attacker.combatDamage()}
                else:
                    if "trample" in attacker.abilities:
                        trampling = True
                        tramplers.append(attacker)
                    else: trampling = False
                    if len(blockers) > 1 or trampling:
                        # Ask the player how to distribute damage
                        # XXX I should check whether the attacker can assign damage to blocker
                        damage = self.curr_player.getDamageAssignment([(attacker, blockers)], trample=trampling)
                    elif len(blockers) == 1:
                        # XXX I should check whether the attacker can assign damage to blocker
                        damage = {blockers[0]: attacker.combatDamage()}
                    else: damage = {} # attacker was blocked, but there are no more blockers
                damage_assignment[attacker] = damage
            # attacker receives all damage from blockers
            for blocker in blockers:
                if not check_strike(blocker): continue
                # XXX Check whether the blocker can assign damage to attacker
                damage = {attacker: blocker.combatDamage()}
                # Handles the case where one blocker can block multiple creatures
                if damage_assignment.has_key(blocker): damage_assignment[blocker].update(damage)
                else: damage_assignment[blocker] = damage

        return tramplers, damage_assignment
    def combatDamageStep(self, combat_assignment):
        from Ability.AssignDamage import AssignDamage
        self.setState("Damage")

        def handle_trample(tramplers, damage_assn):
            for t in tramplers:
                if not damage_assn.get(t,None) == None:
                    damage_assn[t][self.other_player] = t.trample(damage_assn[t])

        tramplers, first_strike_damage = self.calculateDamage(combat_assignment, first_strike=True)
        if first_strike_damage:
            # Handle trample
            if tramplers: handle_trample(tramplers, first_strike_damage)
            damages = AssignDamage(first_strike_damage.items(),"First Strike Damage")
            self.stack.push(damages)
            # Send message about damage going on stack
            self.playInstantaneous()

        tramplers, regular_combat_damage = self.calculateDamage(combat_assignment)
        # Handle trample
        if regular_combat_damage:
            if tramplers: handle_trample(tramplers, regular_combat_damage)
            damages = AssignDamage(regular_combat_damage.items(), "Regular Combat Damage")
            self.stack.push(damages)
            # Send message about damage going on stack
            self.playInstantaneous()
    def combatPhase(self):
        # Beginning of combat
        self.setState("PreCombat")
        self.playInstantaneous()
        combat_assignment = []
        if self.curr_player.attackingIntention():
            # Attacking
            self.setState("Attack")
            attackers = self.curr_player.declareAttackers()
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
        for attacker, blockers in combat_assignment:
            # Make sure attackers and blockers are still in play
            # XXX this is really ugle, but i don't know how else to do it
            # What property can I check to make sure they are still in play?
            if hasattr(attacker, "clearCombatState"): attacker.clearCombatState()
            for b in blockers:
                if hasattr(b, "clearCombatState"): b.clearCombatState()
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
            self.curr_player.discard_down()
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
        self.send(TurnFinishedEvent(), player=self.curr_player)

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
        self.send(HasPriorityEvent(), player=self.curr_player)
        action = self.curr_player.getMainAction()
        if not isinstance(action, PassPriority):
            action.perform(self.curr_player)
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
        if not skip_first: self.continuePlay(self.curr_player)
        response = self.continuePlay(self.other_player)
        while response:
            response = self.continuePlay(self.curr_player)
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
