import itertools, random
from MtGObject import MtGObject
import Match
from GameEvent import *
from Zone import BattlefieldZone
from Stack import StackZone
from stacked_function import overridable, override, most_recent

state_map = {"Untap": UntapStepEvent, "Upkeep": UpkeepStepEvent, "Draw": DrawStepEvent,
             "Main1": MainPhase1Event, "Main2": MainPhase2Event, "EndMain": EndMainPhaseEvent,
             "BeginCombat": BeginCombatEvent, "Attack": AttackStepEvent,
             "Block": BlockStepEvent, "Damage": AssignDamageEvent, "EndCombat": EndCombatEvent,
             "EndStep": EndTurnStepEvent, "Cleanup": CleanupPhase}

class player_order(object):
    active = property(lambda self: self._current[0])
    def __init__(self, players):
        self._current = tuple(players)

        self._insertions = []
        self._peek = None
    def determine_starting(self):
        players = list(self)
        random.shuffle(players)
        self._current = tuple(players)
        for idx, player in enumerate(players[:-1]):
            if player.getIntention("Would you like to go first?"):
                break
        else: idx = len(players) - 1
        self._current = tuple(players[idx:]+players[:idx])
        self._cycler = itertools.cycle(self._current)
    def __str__(self):
        return "Player order: %s"%', '.join(map(str, self._current))
    def __len__(self):
        return len(self._current)
    def __iter__(self):
        return iter(self._current)
    def __getitem__(self, idx):
        return self._current[idx]
    def cycle(self):
        return itertools.cycle(self)
    def next(self):
        if self._peek:
            next_player, self._peek = self._peek, None
        else:
            if not self._insertions: next_player = self._cycler.next()
            else: next_player = self._insertions.pop()
        # Now rearrange the list of players
        players = list(self._current)
        idx = players.index(next_player)
        self._current = tuple(players[idx:]+players[:idx])
        return next_player

    def insert(self, player):
        self._insertions.append(player)
    def peek(self):
        self._peek = self.next()
        return self._peek

class GameKeeper(MtGObject):
    keeper = True

    active_player = property(fget=lambda self: self.players.active)
    current_player = active_player

    mods_loaded = False

    def init(self, players):
        self.current_phase = "Pregame"
        self.stack = StackZone(self)
        self.battlefield = BattlefieldZone(self)

        self.loadMods()
        self._non_card_leaving_zone = []
        self.register(lambda sender: self._non_card_leaving_zone.append(sender), NonCardLeavingZone(), weak=False)

        all_players = set(players)
        for player in players:
            player.init(self.battlefield, self.stack, all_players-set((player,)))
        self.players = player_order(players)

    def start(self):
        self.players.determine_starting()

        self.send(TimestepEvent())
        for player in self.players:
            player.draw(7)
        self.send(TimestepEvent())

        another_mulligan = True
        players = list(self.players)
        mulligan_count = 7
        while another_mulligan:
            players = [player for player in players 
                       if player.getIntention("Would you like to mulligan?")]
            if len(players) > 0:
                mulligan_count -= 1
                for player in players:
                    player.mulligan(mulligan_count)
            else: another_mulligan = False

        try:
            self.run()
        except GameOverException, g:
            self.send(GameOverEvent())
            self.cleanup()
            #self.send(TimestepEvent())
            raise g

    def loadMods(self):
        if not self.mods_loaded:
            import glob, traceback, CardEnvironment
            for mod in glob.glob("./data/rulemods/*.py"):
                code = open(mod, "r").read()
                try:
                    exec code in vars(CardEnvironment)
                except Exception:
                    code = code.split("\n")
                    print "\n%s\n"%'\n'.join(["%03d\t%s"%(i+1, line) for i, line in zip(range(len(code)), code)])
                    traceback.print_exc(4)
            self.mods_loaded = True

    def cleanup(self):
        for player in self.players: player.reset()

    def run(self):
        self.send(GameStartEvent())

        # skip the first draw step
        def skipDraw(self): skipDraw.expire()
        override(self, "drawStep", skipDraw)

        _phases = ("newTurn", ("untapStep", "upkeepStep", "drawStep"), "mainPhase1", "combatPhase", "mainPhase2", "endPhase")
        for phase in itertools.cycle(_phases):
            if isinstance(phase, tuple):
                for step in phase:
                    getattr(self, step)()
                    self.emptyManaPools()
            else: 
                getattr(self, phase)()
                self.emptyManaPools()

    def isSorceryTiming(self, player):
        return (self.stack.empty() and player == self.active_player and
               (self.current_phase == "Main1" or self.current_phase == "Main2"))

    def setState(self, state):
        # Send notice that state changed
        self.current_phase = state
        self.send(GameStepEvent(), state=state)
        self.send(state_map[state](), player=self.active_player)
    def emptyManaPools(self):
        for player in self.players:
            player.manapool.clear()
            #while not player.manaBurn():
            #    self.playInstants()
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
                actions.append(LoseGame(player, "has less than 1 life"))

        # 420.5b and 420.5c are combined
        # 420.5b A creature with toughness 0 or less is put into its owner's graveyard. Regeneration can't replace this event.
        # 420.5c A creature with lethal damage, but greater than 0 toughness, is destroyed. Lethal damage is an amount of damage greater than or equal to a creature's toughness. Regeneration can replace this event.
        def MoveToGraveyard(permanent):
            def SBE(): permanent.move_to("graveyard")
            return SBE
        for creature in self.battlefield.get(Match.isCreature):
            if creature.toughness <= 0:
                actions.append(MoveToGraveyard(creature))
            elif creature.shouldDestroy() or creature.deathtouched:
                creature.deathtouched = False
                actions.append(creature.destroy)
        for walker in self.battlefield.get(Match.isPlaneswalker):
            if walker.shouldDestroy():
                actions.append(walker.destroy)

        # 420.5d An Aura attached to an illegal object or player, or not attached to an object or player, is put into its owner's graveyard.
        for aura in self.battlefield.get(Match.isAura):
            if not aura.isValidAttachment():
                actions.append(MoveToGraveyard(aura))
        # 420.5e If two or more legendary permanents with the same name are on the battlefield, all are put into their owners' graveyards. This is called the "legend rule." If only one of those permanents is legendary, this rule doesn't apply.
        legendaries = self.battlefield.get(Match.isLegendaryPermanent)
        # XXX There's got to be a better way to find multiples
        remove_dup = []
        for i, l1 in enumerate(legendaries):
            for l2 in legendaries[i+1:]:
                if l1.name == l2.name:
                    remove_dup.extend([l1,l2])
                    break
        # 2 or more Planeswalkers with the same name
        planeswalkers = self.battlefield.get(Match.isPlaneswalker)
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

        # 420.5f A token in a zone other than the battlefield zone ceases to exist.
        # 704.5e. If a copy of a spell is in a zone other than the stack, it ceases to exist. If a copy of a card is in any zone other than the stack or the battlefield, it ceases to exist.
        if len(self._non_card_leaving_zone) > 0:
            def SBE():
                for noncard in self._non_card_leaving_zone: noncard.zone.cease_to_exist(noncard)
                # XXX Now only GameObjects.cardmap has a reference to the token - we need to delete it somehow
                self._non_card_leaving_zone[:] = []
            actions.append(SBE)
        # 420.5g A player who attempted to draw a card from an empty library since the last time state-based effects were checked loses the game.
        for player in players:
            if player.draw_empty:
                actions.append(LoseGame(player, "draws from an empty library"))
        # 420.5h A player with ten or more poison counters loses the game.
        for player in players:
            if player.poison >= 10:
                actions.append(LoseGame(player, "is poisoned"))

        # 420.5i If two or more permanents have the supertype world, all except the one that has been a permanent with the world supertype on the battlefield for the shortest amount of time are put into their owners' graveyards. In the event of a tie for the shortest amount of time, all are put into their owners' graveyards. This is called the "world rule."
        # 420.5j A copy of a spell in a zone other than the stack ceases to exist. A copy of a card in any zone other than the stack or the battlefield zone ceases to exist.
        # 420.5k An Equipment or Fortification attached to an illegal permanent becomes unattached from that permanent. It remains on the battlefield.
        for equipment in self.battlefield.get(Match.isEquipment):
            if equipment.attached_to and not equipment.isValidAttachment():
                actions.append(equipment.unattach)
        # 420.5m A permanent that's neither an Aura, an Equipment, nor a Fortification, but is attached to another permanent, becomes unattached from that permanent. It remains on the battlefield .
        for permanent in self.battlefield.get(Match.isPermanent):
            if hasattr(permanent, "attached_to") and permanent.attached_to and not Match.isAttachment(permanent):
                actions.append(permanent.unattach)
        # 420.5n If a permanent has both a +1/+1 counter and a -1/-1 counter on it, N +1/+1 and N -1/-1 counters are removed from it, where N is the smaller of the number of +1/+1 and -1/-1 counters on it.
        def RemoveCounters(perm, num):
            def SBE():
                perm.remove_counters("+1+1", num)
                perm.remove_counters("-1-1", num)
            return SBE
        for perm in self.battlefield.get(Match.isPermanent):
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
        active = self.players.next()
        self.send(NewTurnEvent(), player=active)
        active.newTurn()
    def untapStep(self):
        # untap all cards
        self.setState("Untap")
        # XXX Do phasing - nothing that phases in will trigger any "when ~this~ comes 
        # on the battlefield..." effect, though they will trigger "When ~this~ leaves battlefield" effects
        self.active_player.untapStep()
    def upkeepStep(self):
        self.setState("Upkeep")
        self.playInstants()
    @overridable(most_recent)
    def drawStep(self):
        self.setState("Draw")
        self.active_player.draw()
        self.playInstants()
    def mainPhase1(self):
        self.setState("Main1")
        self.playNonInstants()
        self.setState("EndMain")
    def calculateCombatDamage(self, combat_assignment, is_first_strike=False):
        new_combat_list = []
        # Remove all attackers and blockers that are no longer valid
        for attacker, blockers in combat_assignment.items():
            # Do the attacker first - make sure it is still valid
            if Match.isCreature(attacker) and attacker.in_combat and not attacker.is_LKI:
                newblockers = [blocker for blocker in blockers if Match.isCreature(blocker) and blocker.in_combat and not blocker.is_LKI]
                new_combat_list.append((attacker, newblockers))

        # These guys are still valid
        damage_assignment = {}
        for attacker, blockers in new_combat_list:
            if attacker.canStrike(is_first_strike):
                attacker.didStrike()
                if not attacker.blocked:
                    # XXX I should check that the attacker can damage the player
                    damage = {attacker.opponent: attacker.combatDamage()}
                else:
                    trampling = "trample" in attacker.abilities
                    if len(blockers) > 1 or trampling:
                        # Ask the player how to distribute damage
                        # XXX I should check whether the attacker can assign damage to blocker
                        damage = self.active_player.getDamageAssignment([(attacker, blockers)], trample=trampling, deathtouch="deathtouch" in attacker.abilities)
                    elif len(blockers) == 1:
                        # XXX I should check whether the attacker can assign damage to blocker
                        damage = {blockers[0]: attacker.combatDamage()}
                    else: damage = {} # attacker was blocked, but there are no more blockers
                    if trampling:
                        damage[attacker.opponent] = attacker.trample(damage)
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
        return damage_assignment
    def assignCombatDamage(self, damages):
        for damager, damage_assn in damages.iteritems():
            for damagee, amt in damage_assn.iteritems():
                damager.deal_damage(damagee, amt, combat=True)

    def combatDamageStep(self, combat_assignment):
        self.setState("Damage")

        first_strike_damage = self.calculateCombatDamage(combat_assignment, is_first_strike=True)
        if first_strike_damage:
            self.assignCombatDamage(first_strike_damage)
            self.playInstants()

        regular_combat_damage = self.calculateCombatDamage(combat_assignment)
        if regular_combat_damage:
            self.assignCombatDamage(regular_combat_damage)
            self.playInstants()
    def combatPhase(self):
        # Beginning of combat
        self.setState("BeginCombat")
        self.playInstants()
        combat_assignment = {}
        attacking_player = self.active_player
        if attacking_player.attackingIntention():
            # Attacking
            self.setState("Attack")
            defending_player = attacking_player.declareDefendingPlayer()
            # Get all the players/planeswalkers
            opponents = [defending_player] + defending_player.battlefield.get(Match.isPlaneswalker)
            attackers = attacking_player.declareAttackers(opponents)
            if attackers: self.send(DeclareAttackersEvent(), attackers=attackers)
            self.playInstants()
            # After playing instants, the list of attackers could be modified (if a creature was put onto the battlefield "attacking", so we regenerate the list
            attackers = self.battlefield.get(Match.isCreature.with_condition(lambda c: c.attacking))
            if attackers:
                # Blocking
                self.setState("Block")
                combat_assignment = defending_player.declareBlockers(attackers)
                # Ask attacking player to reorder 
                combat_assignment = attacking_player.reorderBlockers(combat_assignment)
                self.send(DeclareBlockersEvent(), combat_assignment=combat_assignment)
                self.playInstants()
                # Damage
                self.combatDamageStep(combat_assignment)
        # End of Combat
        # trigger effects that happen at end of combat
        # Clear off attacking and blocking status?
        self.setState("EndCombat")
        for attacker, blockers in combat_assignment.items():
            attacker.clearCombatState()
            for blocker in blockers: blocker.clearCombatState()
        self.playInstants()
    def mainPhase2(self):
        self.setState("Main2")
        self.playNonInstants()
        self.setState("EndMain")
    def endPhase(self):
        # End of turn
        self.setState("EndStep")
        #  - trigger "at end of turn" abilities - if new "at end of turn" event occurs doesn't happen until next turn
        #  - can play instants or abilities
        self.playInstants()

        # Cleanup
        # - discard down to current hand limit
        # - expire abilities that last "until end of turn" or "this turn"
        # - clear non-lethal damage
        self.setState("Cleanup")
        while True:
            self.active_player.discard_down()
            # Clear all nonlethal damage
            self.send(CleanupEvent())
            self.send(TimestepEvent())
            for creature in self.battlefield.get(Match.isCreature):
                creature.clearDamage()
            triggered_once = False
            while self.checkSBE(): triggered_once = True
            if self.stack.process_triggered(): triggered_once = True
            if triggered_once: self.playInstants()
            else: break
        self.send(TurnFinishedEvent(), player=self.active_player)

    def givePriority(self, player):
        # Check SBEs - rule 704.3
        repeat_SBE = True
        while repeat_SBE:
            while self.checkSBE(): pass
            repeat_SBE = self.stack.process_triggered()
        # Now player gets priority
        self.send(HasPriorityEvent(), player=player)

    def playNonInstants(self):
        # Loop for playing spells when non-instants can be played
        active_player = self.active_player
        while True:
            self.givePriority(active_player)
            if self.stack.empty():
                played = active_player.doNonInstantAction()
            else:
                played = active_player.doInstantAction()
            self.playStackInteraction(played)
            # All players have passed
            if not self.stack.empty(): self.stack.resolve()
            else: break

    def playInstants(self):
        # A round of playing instants - returns when the stack is empty
        while True:
            self.playStackInteraction()
            if not self.stack.empty(): self.stack.resolve()
            else: break

    def playStackInteraction(self, do_active=True):
        # One back and forth stack interaction until all players pass
        # do_active is for when the stack is empty and the active player passes
        player_cycler = self.players.cycle()

        # Keep track of active player first
        last_to_play = player_cycler.next()
        if do_active: self.continuePlay(last_to_play)

        for player in player_cycler:
            # If we've cycled back to the last player to play
            # (everybody passed without playing) then exit
            if player == last_to_play: break
            if self.continuePlay(player): last_to_play = player

    def continuePlay(self, player):
        # Allows player to keep playing valid spells/abilities
        # Returns whether the player responded before passing
        responding = False
        while True:
            self.givePriority(player)
            if player.doInstantAction(): responding = True
            else: break
        return responding

Keeper = GameKeeper()
