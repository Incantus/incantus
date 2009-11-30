#!/usr/bin/python
import sys, random, pdb
from network import replaydump
import engine
from engine.pydispatch import dispatcher

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
            if input == "d": pdb.set_trace()
            elif input == "f": slow = False
        if not result is False: return result
    except:
        pdb.set_trace()

dump = replaydump.ReplayDump(replayfile, False)

sserver = dump.read()
seed = dump.read()
player1_name = dump.read()
my_deck = dump.read()
player2_name = dump.read()
other_deck = dump.read()

player1 = engine.Player(player1_name, my_deck)
player2 = engine.Player(player2_name, other_deck)
player1.dirty_input = userinput
player2.dirty_input = userinput

# Choose starting player
random.seed(seed)

dispatcher.reset()
engine.Keeper.init([player1, player2])

# This is hacky
replaydump.players = dict([(player.name,player) for player in [player1, player2]])
replaydump.stack = engine.Keeper.stack

msg = engine.Keeper.start()
print msg
