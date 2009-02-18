import pickle
import game

def persistent_id(obj):
    persid = None
    if isinstance(obj,game.GameObjects.Card) or isinstance(obj,game.GameObjects.GameToken):
        persid = pickle.dumps(("Card", obj.key), 2)
    elif isinstance(obj,game.Player):
        persid = pickle.dumps(("Player", obj.name), 2)
    return persid

players = {}
def persistent_load(persid):
    id, val = pickle.loads(persid)
    if id == "Card":
        return game.CardLibrary.CardLibrary[val]
    elif id == "Player":
        return players[val]
    else:
        raise pickle.UnpicklingError("Invalid persistent id")

class ReplayDump(object):
    def __init__(self, app, save=True):
        self.filename = "game_run.pkl"
        self.app = app
        self.save = save
        if save: flags = 'w'
        else: flags = 'r'
        #flags = 'r+'
        self.dumpfile = open(self.filename, flags, 0)
        self.lastpos = self.dumpfile.tell()
        self.load_picklers()
    def load_picklers(self):
        self.pickler = pickle.Pickler(self.dumpfile)
        self.pickler.persistent_id = persistent_id
        self.unpickler = pickle.Unpickler(self.dumpfile)
        self.unpickler.persistent_load = persistent_load
    def close(self):
        self.dumpfile.close()
    def __call__(self, obj):
        if self.save:
            self.pickler.dump(obj)
    def read(self):
        try:
            self.lastpos = self.dumpfile.tell()
            return self.unpickler.load()
        except Exception: #(EOFError, TypeError, KeyError):
            self.app.replay = False
            start_dumping = game.GameKeeper.Keeper.curr_player.getIntention(self.app.logtxt, "...continue recording?")
            if start_dumping:
                self.save = True
                self.dumpfile.close()
                self.dumpfile = open(self.filename, 'a+')
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

if __name__ == "__main__":
    filename = "game_run.pkl"
    flags = 'r'
    dumpfile = open(filename, flags)
    p = test(dumpfile)
    while True:
        a = p.load()
        print a, dumpfile.tell()
