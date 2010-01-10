#!/usr/bin/python
import sys, random, pudb, pdb
from network import replaydump
from engine.Player import Player
from engine.GameKeeper import Keeper
from engine.pydispatch import dispatcher

debug = pdb

replayfile = "game.replay"

if len(sys.argv) == 1: slow = False
else: slow = True #replayfile = sys.argv[1]

def userinput(context, prompt):
    global slow
    try:
        result = dump.read()
        print "(%d) %s -- %s"%(dump.lastpos, prompt, result)
        if slow:
            input = raw_input("Press a key")
            if input == "d": debug.set_trace()
            elif input == "f": slow = False
        if not result is False: return result
    except:
        debug.set_trace()

dump = replaydump.ReplayDump(replayfile, False)

sserver = dump.read()
seed = dump.read()
player1_name = dump.read()
my_deck = dump.read()
player2_name = dump.read()
other_deck = dump.read()

player1 = Player(player1_name, my_deck)
player2 = Player(player2_name, other_deck)
player1.dirty_input = userinput
player2.dirty_input = userinput

# Choose starting player
random.seed(seed)

dispatcher.reset()
Keeper.init([player1, player2])

# This is hacky
replaydump.players = dict([(player.name,player) for player in [player1, player2]])
replaydump.stack = Keeper.stack

msg = Keeper.start()
print msg
