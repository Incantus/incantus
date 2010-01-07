# The next set of functions deals with the operation of the stack
# It may seem recursive but it's not
import itertools
import random
import readline

random.seed()

class Printer:
    _pfx = '  '

    prefix = property(lambda self: ''.join(self._prefixes))
    def __init__(self):
        self.level = 0;
        self._prefixes = []
    def indent(self, pfx=None):
        if not pfx: pfx = Printer._pfx
        self.level+=1
        self._prefixes.append(pfx)
    def unindent(self):
        self.level-=1
        self._prefixes.pop()
    def __call__(self, s):
        print self.prefix+s

class Indenter:
    def __init__(self, printer, pfx=None):
        self._p = printer
        self.pfx = pfx
    def __enter__(self):
        self._p.indent(self.pfx)
        return self._p
    def __exit__(self, type, value, traceback):
        self._p.unindent()
        return False

printer = Printer()

def get_input(prompt):
    return raw_input(printer.prefix+prompt+": ")

class Player:
    def __init__(self, name, stack):
        self.name = name
        self.stack = stack
    def get(self, prompt, filter):
        done = False
        while True:
            printer("(%s)"%self.stack)
            action = get_input(prompt+" (ENTER to pass)")
            if not action:
                printer("(%s passes)"%self)
                break
            else:
                action = action.upper()
                t = action[0]
                if t == 'T':
                    self.stack.add_triggered(action)
                elif (filter(t)):
                    self.stack.push((self, action))
                    printer("(%s puts %s on stack)"%(self, action))
                    done = True
                    break
                else: printer("!! Invalid action !!")
        print
        return done
    def getIntention(self, msg):
        while True:
            action = get_input("%s -- %s ([Y], N)"%(self,msg)).upper()
            if not action or action == "Y": return True
            elif action == "N": return False
            else: printer("!! Invalid response !!")
    def doNonInstantAction(self):
        filter = lambda s: s == "S" or s == "I"
        return self.get("%s -- Play Non-instant"%self, filter)
    def doInstantAction(self):
        filter = lambda s: s == "I"
        return self.get("%s -- Play Instant"%self, filter)
    def __repr__(self):
        return self.name

class Stack:
    def __init__(self):
        self.stack = []
        self.pending = []
    def empty(self):
        return len(self.stack)==0
    def add_triggered(self, action):
        self.pending.append(("Trigger", action))
    def resolve(self):
        a = self.stack.pop()
        printer("*** (Resolving %s - %s)\n"%(a, self))
    def push(self, action):
        self.stack.append(action)
    def process_triggered(self):
        # Sometimes randomly trigger an action
        action = random.random()
        if action < 0.01:
            self.add_triggered(action)
            printer("(Triggering %s)"%action)
        if self.pending:
            for a in self.pending: self.push(a)
            self.pending[:] = []
            printer("(Placing triggered onto stack %s)"%self)
            return True
        else: return False
    def __str__(self):
        return "Stack: %s"%self.stack

# Everything above this line can be thrown out

class player_order(object):
    def __init__(self, players):
        self._current = tuple(players)

        self._insertions = []
        self._peek = None
    def determine_starting(self):
        players = list(self)
        random.shuffle(players)
        for idx, player in enumerate(players[:-1]):
            if player.getIntention("Would you like to go first?"):
                break
        else: idx = len(players) - 1
        self._current = tuple(players[idx:]+players[:idx])
        self._cycler = itertools.cycle(self._current)
        printer(str(self))
    def __str__(self):
        return "Player order: %s"%', '.join(map(str, self._current))
    def __len__(self):
        return len(self._current)
    def __iter__(self):
        return iter(self._current)
    def cycle(self):
        return itertools.cycle(self)
    active = property(lambda self: self._current[0])

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

    def insert(self, player):
        self._insertions.append(player)
    def peek(self):
        self._peek = self.next()
        return self._peek

class Keeper:
    def start(self):
        self.players.determine_starting()
        self.run()

    def run(self):
        _phases = ("newTurn", ("untapStep", "upkeepStep", "drawStep"), "mainPhase1", "combatPhase", "mainPhase2", "endPhase")
        for phase in itertools.cycle(_phases):
            if type(phase) == tuple:
                for step in phase:
                    self.printStep(step)
                    getattr(self, step)()
            else:
                if phase == "newTurn":
                    getattr(self, phase)()
                    self.printStep(phase)
                else:
                    self.printStep(phase)
                    getattr(self, phase)()

    def printStep(self, step):
        self.step = step
        printer("********************")
        printer("** %s: in %s **"%(self.players.active, step))
        printer("********************")
    def untapStep(self): pass
    def upkeepStep(self): self.printAndPlayInstants()
    def drawStep(self): self.printAndPlayInstants()
    def mainPhase1(self): self.printAndPlayNonInstants()
    def combatPhase(self):
        with Indenter(printer):
            self.printStep("DeclareAttackers")
            self.printAndPlayInstants()
            self.printStep("DeclareBlockers")
            self.printAndPlayInstants()
            self.printStep("CombatDamage")
            self.printAndPlayInstants()
            self.printStep("EndCombat")
    def mainPhase2(self): self.printAndPlayNonInstants()
    def endPhase(self):
        self.printAndPlayInstants()
    def checkSBE(self): return False
    def printAndPlayInstants(self):
        pfx = "(%s - %s): "%(self.players.active, self.step)
        with Indenter(printer, pfx):
            self.playInstants()
    def printAndPlayNonInstants(self):
        pfx = "(%s - %s): "%(self.players.active, self.step)
        with Indenter(printer, pfx):
            self.playNonInstants()




    def __init__(self, stack, players):
        self.stack = stack
        self.players = player_order(players)
    
    active_player = property(fget=lambda self: self.players.active) 

    def givePriority(self, player):
        # Check SBEs - rule 704.3
        repeat_SBE = True
        while repeat_SBE:
            #printer("*** Checking SBE and triggered ***")
            while self.checkSBE(): pass
            repeat_SBE = self.stack.process_triggered()
        # Now player gets priority
        #printer("*** %s has priority ***" % player)
    def newTurn(self):
        # Cycle through players
        self.players.next()
    def playNonInstants(self):
        # Loop for playing spells when non-instants can be played
        active = self.players.active
        while True:
            self.givePriority(active)
            if self.stack.empty():
                played = active.doNonInstantAction()
            else:
                played = active.doInstantAction()
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
        # skip_first is when the active player has already passed
        players = self.players.cycle()
        # Keep track of active player first
        last_to_play = players.next()
        if do_active: self.continuePlay(last_to_play)

        for player in players:
            # If we've cycled back to the last player to play
            # something (everybody passed) then exit
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

if __name__ == "__main__":
    stack = Stack()
    players = [Player("A", stack)
               , Player("B", stack)
    #           , Player("C", stack)
    #           , Player("D", stack)
              ]
    keeper = Keeper(stack, players)
    keeper.start()

