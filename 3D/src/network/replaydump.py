from pickletools import genops
#import pickle
import cPickle as pickle
from game import Player
from game.Ability.Ability import Ability
from game.GameObjects import GameObject

# This whole thing is ugly - i should probably replace it with a global object store with weakrefs (for the abilities)
# or find a better way to pass this data back and forth
players = {}
stack = None
def persistent_id(obj):
    persid = None
    if isinstance(obj,GameObject):
        persid = pickle.dumps(("Object", obj.key), 2)
    elif isinstance(obj,Player):
        persid = pickle.dumps(("Player", obj.name), 2)
    elif isinstance(obj,Ability):
        persid = pickle.dumps(("Ability", stack.find(obj)), 2)
    return persid

def persistent_load(persid):
    id, val = pickle.loads(persid)
    if id == "Object":
        return game.CardLibrary.CardLibrary[val]
    elif id == "Player":
        return players[val]
    elif id == "Ability":
        return stack.stack[val]
    else:
        raise pickle.UnpicklingError("Invalid persistent id")

def optimize(p):
    'Optimize a pickle string by removing unused PUT opcodes'
    gets = set()            # set of args used by a GET opcode
    puts = []               # (arg, startpos, stoppos) for the PUT opcodes
    prevpos = None          # set to pos if previous opcode was a PUT
    for opcode, arg, pos in genops(p):
        if prevpos is not None:
            puts.append((prevarg, prevpos, pos))
            prevpos = None
        if 'PUT' in opcode.name:
            prevarg, prevpos = arg, pos
        elif 'GET' in opcode.name:
            gets.add(arg)

    # Copy the pickle string except for PUTS without a corresponding GET
    s = []
    i = 0
    for arg, start, stop in puts:
        #j = stop if (arg in gets) else start
        if (arg in gets): j = stop
        else: j = start
        s.append(p[i:j])
        i = stop
    s.append(p[i:])            
    return ''.join(s)

class ReplayDump(object):
    def __init__(self, app, filename="game.replay", save=True, prompt_continue=True):
        self.filename = filename
        self.app = app
        self.save = save
        if save: flags = 'wb'
        else: flags = 'rb'
        self.prompt_continue = prompt_continue
        #flags = 'r+'
        self.dumpfile = open(self.filename, flags, 0)
        self.lastpos = self.dumpfile.tell()
        self.load_picklers()
    def load_picklers(self):
        self.pickler = pickle.Pickler(self.dumpfile, protocol=-1)
        self.pickler.persistent_id = persistent_id
        self.unpickler = pickle.Unpickler(self.dumpfile)
        self.unpickler.persistent_load = persistent_load
    def close(self):
        self.dumpfile.close()
    def __call__(self, obj):
        if self.save:
            self.pickler.dump(obj)
            self.dumpfile.flush()
    def read(self):
        try:
            self.lastpos = self.dumpfile.tell()
            obj = self.unpickler.load()
            return obj
        except Exception: #(EOFError, TypeError, KeyError):
            self.app.replay = False
            if self.prompt_continue: start_dumping = game.GameKeeper.Keeper.curr_player.getIntention(self.app.game_status.prompt.value, "...continue recording?")
            else: start_dumping = True
            if start_dumping:
                self.save = True
                self.dumpfile.close()
                self.dumpfile = open(self.filename, 'a+b')
                self.dumpfile.seek(self.lastpos, 0)
                self.load_picklers()
            else: self.dumpfile.close()
            return False
    def __del__(self):
        self.close()

def test(dumpfile):
    def persistent_load(persid):
        id, val = pickle.loads(persid)
        return id, val
    unpickler = pickle.Unpickler(dumpfile)
    unpickler.persistent_load = persistent_load
    return unpickler

import sys
if __name__ == "__main__":
    if len(sys.argv) == 1: filename = "game.replay"
    else: filename = sys.argv[1]
    if len(sys.argv) == 3: stoppoint = int(sys.argv[2])
    else: stoppoint = None
    flags = 'r+b'
    dumpfile = open(filename, flags)
    if stoppoint: dumpfile.truncate(stoppoint)
    p = test(dumpfile)
    try:
        while True:
            a = p.load()
            print a, dumpfile.tell()
    except EOFError:
        pass
