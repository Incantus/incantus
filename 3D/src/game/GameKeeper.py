
from GameObjects import MtGObject
from Action import PassPriority
import Match
from GameEvent import *
from Zone import Zone
from CardLibrary import CardLibrary

#class Stack(Zone):
class Stack(MtGObject):
    def __init__(self):
        self.stack = []
        self.triggered_abilities = []
        self.curr_player = None
    def reset(self):
        self.stack[:] = []
        self.triggered_abilities[:] = []
        self.register(lambda player: setattr(self, "curr_player", player), NewTurnEvent(), weak=False)
        self.register(self.process_triggered, HasPriorityEvent())
    def add_triggered(self, ability):
        self.triggered_abilities.append(ability)
    def process_triggered(self):
        # Check if there are any triggered abilities waiting
        if len(self.triggered_abilities) > 0:
            # group all triggered abilities by player
            triggered_sets = [[],[]]
            for ability in self.triggered_abilities:
                if ability.card.controller == self.curr_player: triggered_sets[0].append(ability)
                else: triggered_sets[1].append(ability)
            # Now ask the player to order them if there are more than one
            for player, triggered in zip((self.curr_player, self.curr_player.opponent), triggered_sets):
                # XXX Must use the index of the ability, since we can't pickle abilities for network games
                abilities = [(str(a), i) for i, a in enumerate(triggered)]
                results = []
                if len(abilities) > 1:
                    results = player.getSelection(abilities, len(abilities), required=False, prompt="Order triggered abilities")
                if not results: results = range(len(triggered))
                # Now reorder
                for i in results: self.announce(triggered[i])
            self.triggered_abilities[:] = []
            return True
        else: return False
    def announce(self, ability):
        # Do all the stuff in rule 409.1 like pick targets, pay
        # costs, etc
        self.send(AbilityAnnounced(), ability=ability)
        success = True
        if hasattr(ability, "cost"):
            success = ability.precompute_cost()
            if success and ability.needs_target(): success = ability.get_target()
            if success: success = ability.compute_cost() and ability.pay_cost()
        else:
            if ability.needs_target(): success = ability.get_target()
        if success: self.push(ability)
        else:
            self.send(AbilityCanceled(), ability=ability)
            del ability
        return success
    def skip_announce(self, ability):
        self.send(AbilityAnnounced(), ability=ability)
        self.push(ability)
    def stackless(self, ability):
        success = True
        if hasattr(ability, "cost"):
            success = ability.precompute_cost()
            if success and ability.needs_target(): success = ability.get_target()
            if success: success = ability.compute_cost() and ability.pay_cost()
        else:
            if ability.needs_target(): success = ability.get_target()
        if success:
            ability.played()
            ability.do_resolve()
        del ability
        return success
    def push(self, ability):
        self.stack.append(ability)
        self.send(AbilityPlacedOnStack(), ability=ability)
        #self.send(CardEnteredZone(), card=ability.card)
        ability.played()
    def on_stack(self, ability):
        return ability in self.stack
    def pop(self):
        ability = self.stack.pop()
        self.send(AbilityRemovedFromStack(), ability=ability)
        #self.send(CardLeftZone(), card=ability.card)
        return ability
    def counter(self, ability):
        self.stack.remove(ability)
        self.send(AbilityRemovedFromStack(), ability=ability)
    def empty(self):
        return len(self.stack) == 0
    def __iter__(self): return iter(self.stack)
    def find(self, obj): # XXX This is needed for pickling Abilities on the stack (when they are targets of counterspells)
        return self.stack.index(obj)
    def __str__(self):
        return str(self.stack)

class GamePhases(object):
    def __init__(self, gamekeeper, players):
        self.state_map = dict([(p,i) for i, p in enumerate(["BeginTurn", "Main1", "Combat", "Main2", "EndPhase"])])
        self.game_phases = [self.makeBeginningPhase(gamekeeper), gamekeeper.mainPhase1, gamekeeper.combatPhase, gamekeeper.mainPhase2, gamekeeper.endPhase]
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
    def __init__(self):
        self.ready_to_start = False
        self.stack = Stack()

    def init(self, player1, player2):
        CardLibrary.clear()
        self.game_phases = GamePhases(self, (player1, player2))
        self.stack.reset()
        self.tokens_out_play = []
        self.register(lambda sender: self.tokens_out_play.append(sender), TokenLeavingPlay(), weak=False)
        self.players = (player1, player2)
        player1.init()
        player2.init()
        player1.stack = self.stack
        player2.stack = self.stack
        player1.loadDeck()
        player2.loadDeck()
        player1.shuffleDeck()
        player2.shuffleDeck()
        starting_draw = 7
        for i in range(starting_draw): player1.draw()
        for i in range(starting_draw): player2.draw()
        self.game_ended = False
        self.ready_to_start = True

    def run(self):
        if not self.ready_to_start: raise Exception("Players not added - not ready to start")
        # XXX This is hacky - need a better way to signal end of game
        for player in [self.game_phases.curr_player, self.game_phases.other_player]:
            self.curr_player = player
            player.mulligan()
        try:
            while True:
                self.singleTurn()
        except GameOver, g:
            # Return all cards to library
            for player in [self.game_phases.curr_player, self.game_phases.other_player]:
                player.reset()
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
                     "EndPhase": EndPhaseEvent, "Cleanup": CleanupEvent, "EndTurn": EndTurnEvent}
        self.send(GameStepEvent(), state=state)
        self.send(state_map[state]())
    def manaBurn(self):
        while not self.curr_player.manaBurn():
            self.playInstantaneous()
        while not self.other_player.manaBurn():
            self.playInstantaneous()
    def checkSBE(self):
        #State-Based Effects - rule 420.5
        # check every time someone gets priority (rule 408.1b)
        # Also during cleanup step - if there is an effect, player gets priority
        self.send(TimestepEvent())
        players = [self.curr_player, self.other_player]
        actions = 0
        # 420.5a A player with 0 or less life loses the game.
        for player in players:
            if player.life <= 0: raise GameOver("%s wins the game!"%player.opponent.name)

        # 420.5b and 420.5c are combined
        # 420.5b A creature with toughness 0 or less is put into its owner's graveyard. Regeneration can't replace this event.
        # 420.5c A creature with lethal damage, but greater than 0 toughness, is destroyed. Lethal damage is an amount of damage greater than or equal to a creature's toughness. Regeneration can replace this event.
        for player in players:
            for creature in player.play.get(Match.isCreature):
                if creature.toughness <= 0:
                    player.moveCard(creature, player.play, creature.owner.graveyard)
                    actions += 1
                elif creature.shouldDestroy():
                    creature.destroy()
                    actions += 1
        # 420.5d An Aura attached to an illegal object or player, or not attached to an object or player, is put into its owner's graveyard.
        for player in players:
            for aura in player.play.get(Match.isAura):
                if not aura.attached_to or not (aura.attached_to.zone == players[0].play or aura.attached_to.zone == players[1].play) or not aura.target_types.match(aura.attached_to):
                    aura.unattach()
                    player.moveCard(aura, player.play, aura.owner.graveyard)
                    actions += 1
        # 420.5e If two or more legendary permanents with the same name are in play, all are put into their owners' graveyards. This is called the "legend rule." If only one of those permanents is legendary, this rule doesn't apply.
        legendaries = []
        for player in players: legendaries.extend(player.play.get(Match.isLegendaryPermanent))
        # XXX There's got to be a better way to find multiples
        remove = []
        for i, l1 in enumerate(legendaries):
            for l2 in legendaries[i+1:]:
                if l1.name == l2.name:
                    remove.extend([l1,l2])
                    break
        if len(remove) > 0:
            for legend in remove:
                player = legend.controller
                player.moveCard(legend, player.play, legend.owner.graveyard)
            actions += 1

        # 420.5f A token in a zone other than the in-play zone ceases to exist.
        if len(self.tokens_out_play) > 0:
            for token in self.tokens_out_play: token.zone.remove_card(token, trigger=False)
            # XXX Now only CardLibrary has a reference to the token - we need to delete it somehow
            self.tokens_out_play[:] = []
            actions += 1
        # 420.5g A player who attempted to draw a card from an empty library since the last time state-based effects were checked loses the game.
        for player in players:
            if player.draw_empty: raise GameOver("%s draws from an empty library and loses!"%player.name)
        # 420.5h A player with ten or more poison counters loses the game.
        for player in players:
            if player.poison >= 10: raise GameOver("%s is poisoned and loses"%player.name)
        # 420.5i If two or more permanents have the supertype world, all except the one that has been a permanent with the world supertype in play for the shortest amount of time are put into their owners' graveyards. In the event of a tie for the shortest amount of time, all are put into their owners' graveyards. This is called the "world rule."
        # 420.5j A copy of a spell in a zone other than the stack ceases to exist. A copy of a card in any zone other than the stack or the in-play zone ceases to exist.
        # 420.5k An Equipment or Fortification attached to an illegal permanent becomes unattached from that permanent. It remains in play.
        # 420.5m A permanent that's neither an Aura, an Equipment, nor a Fortification, but is attached to another permanent, becomes unattached from that permanent. It remains in play.
        # 420.5n If a permanent has both a +1/+1 counter and a -1/-1 counter on it, N +1/+1 and N -1/-1 counters are removed from it, where N is the smaller of the number of +1/+1 and -1/-1 counters on it. 

        if actions:
            self.stack.process_triggered()
            return True
        else: return False
    def beginningPhase(self):
        self.setState("BeginTurn")
    def untapStep(self):
        # untap all cards
        self.setState("Untap")
        # XXX Do phasing - nothing that phases in will trigger any "when ~this~ comes 
        # into play..." effect, though they will trigger "When ~this~ leaves play" effects
        self.curr_player.untapCards()
        # perform upkeep
    def upkeepStep(self):
        self.setState("Upkeep")
        self.curr_player.upkeep()
        self.playInstantaneous()
        # draw card
    def drawStep(self):
        self.curr_player.draw()
        # XXX If you have a card that let's you draw more than one card, you get priority
        # before each draw
        self.setState("Draw")
        self.playInstantaneous()
    def mainPhase1(self):
        self.setState("Main1")
        self.playSpells()
        #self.setState("EndMain")
    def calculateDamage(self, blocking_list):
        new_combat_list = []
        # Remove all attackers and blockers that are no longer valid
        for attacker, blockers in blocking_list:
            # Do the attacker first - make sure it is still valid
            if Match.isCreature(attacker) and attacker.zone == self.curr_player.play and attacker.in_combat:
                newblockers = []
                # Remove any blockers that are no longer in combat
                for blocker in blockers:
                    if Match.isCreature(blocker) and blocker.zone == self.other_player.play and blocker.in_combat:
                        newblockers.append(blocker)
                new_combat_list.append((attacker, newblockers))
        # These guys are still valid
        damage_assignment = {}

        tramplers = []
        for attacker, blockers in new_combat_list:
            if not attacker.blocked:
                # XXX I should check that the attacker can damage the player
                damage = {self.other_player: attacker.combatDamage()}
            else:
                if "trample" in attacker.keywords:
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
            for b in blockers:
                # XXX Check whether the blocker can assign damage to attacker
                damage = {attacker: b.combatDamage()}
                # Handles the case where one blocker can block multiple creatures
                if damage_assignment.has_key(b): damage_assignment[b].update(damage)
                else: damage_assignment[b] = damage

        # Build combat damage
        first_strike_damage = {}
        regular_combat_damage = {}
        for damager, damage_assn in damage_assignment.iteritems():
            if "first-strike" in damager.keywords or "double-strike" in damager.keywords:
                first_strike_damage[damager] = dict(damage_assn)
                if "double-strike" in damager.keywords: regular_combat_damage[damager] = dict(damage_assn)
            else: regular_combat_damage[damager] = dict(damage_assn)

        return tramplers, first_strike_damage, regular_combat_damage
    def combatDamageStep(self):
        from Ability import AssignDamage
        self.setState("Damage")

        def handle_trample(tramplers, damage_assn):
            for t in tramplers:
                if not damage_assn.get(t,None) == None:
                    damage_assn[t][self.other_player] = t.trample(damage_assn[t])

        tramplers, first_strike_damage, regular_combat_damage = self.calculateDamage(self.blocking_list)
        if first_strike_damage:
            # Handle trample
            if tramplers: handle_trample(tramplers, first_strike_damage)
            self.stack.skip_announce(AssignDamage(first_strike_damage.items(),"First Strike Damage"))
            # Send message about damage going on stack
            self.playInstantaneous()
            # Now make sure that the creatures doing damage in the second step still exist
            remove_damager = []
            for damager, damage_assn in regular_combat_damage.items():
                if not (Match.isCreature(damager) and damager.in_combat): remove_damager.append(damager)
            for d in remove_damager: del regular_combat_damage[d]

        # Handle trample
        if tramplers: handle_trample(tramplers, regular_combat_damage)
        if regular_combat_damage:
            self.stack.skip_announce(AssignDamage(regular_combat_damage.items(), "Regular Combat Damage"))
            # Send message about damage going on stack
        self.playInstantaneous()
    def combatPhase(self):
        # Beginning of combat
        self.setState("PreCombat")
        self.playInstantaneous()
        self.blocking_list = []
        if self.curr_player.attackingIntention():
            # Attacking
            self.setState("Attack")
            attackers = self.curr_player.declareAttackers()
            self.send(DeclareAttackersEvent(), attackers=attackers)
            self.playInstantaneous()
            # After playing instants, the list of attackers could be modified (if a creature was put into play "attacking", so we regenerate the list
            attackers = self.curr_player.play.get(Match.isCreature.with_condition(lambda c: c.attacking))
            if attackers:
                # Blocking
                self.setState("Block")
                self.blocking_list = self.other_player.declareBlockers(attackers)
                self.send(DeclareBlockersEvent(), blocking_list=self.blocking_list)
                self.playInstantaneous()
                # Damage
                self.combatDamageStep()
        # End of Combat
        # trigger effects that happen at end of combat
        # Clear off attacking and blocking status?
        self.setState("EndCombat")
        for attacker, blockers in self.blocking_list:
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
        #self.setState("EndMain")
    def endPhase(self):
        # End of turn
        self.setState("EndPhase")
        #  - trigger "at end of turn" abilities - if new "at end of turn" event occurs doesn't happen until next turn
        #  - can play instants or abilities
        self.playInstantaneous()

        # Cleanup
        # - discard down to current hand limit
        # - expire abilities that last "until end of turn" or "this turn"
        # - clear non-lethal damage
        self.setState("Cleanup")
        self.send(HasPriorityEvent(), player=self.curr_player)
        while True:
            numcards = len(self.curr_player.hand)
            diff = numcards - self.curr_player.hand_limit
            if diff > 1: a = 's'
            else: a = ''
            for i in range(diff):
                card = self.curr_player.getTarget(Match.isCard, zone=self.curr_player.hand, required=True,prompt="Select card%s to discard: %d left of %d"%(a, diff-i,diff))
                self.curr_player.discard(card)

            # Clear all nonlethal damage
            for player in [self.curr_player, self.other_player]:
                for creature in player.play.get(Match.isCreature):
                    creature.clearDamage()
            triggered_once = False
            while self.checkSBE():
                triggered_once = True
                self.playInstantaneous()

            if not triggered_once: break
        self.setState("EndTurn")

    # The next set of functions deals with the operation of the stack
    # It may seem recursive but it's not
    def playSpells(self):
        stack_less_action = self.playStackSpells()
        # Time to unwind
        while not self.stack.empty() or stack_less_action:
            if not stack_less_action:
                ability = self.stack.pop()
                ability.do_resolve()
                del ability
            # Now it's the active player's turn to play something
            if self.stack.empty(): stack_less_action = self.playStackSpells()
            else: self.playStackInstant()
    def playStackSpells(self):
        while self.checkSBE():
            if not self.stack.empty():
                self.playStackInstant()
                return False
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
            ability = self.stack.pop()
            ability.do_resolve()
            del ability
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
            self.send(HasPriorityEvent(), player=player)
            action = player.getAction()
            if not isinstance(action, PassPriority):
                action.perform(player)
                responding = True    # if card is played in response
            else: priorityPassed = True
        return responding

Keeper = GameKeeper()
