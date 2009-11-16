import struct
import simplejson as json
from engine import Player, GameKeeper
from engine.Ability.Ability import Ability
from engine.GameObjects import GameObject
from engine.CardRoles import CardRole
from engine import Action

# This whole thing is ugly - i should probably replace it with a global object store with weakrefs (for the abilities)
# or find a better way to pass this data back and forth
players = {}
stack = None

def to_json(obj):
    if isinstance(obj,CardRole):
        return {'__class__': 'CardRole',
                '__value__': obj.key}
    elif isinstance(obj,Player):
        return {'__class__': 'Player',
                '__value__': obj.name}
    elif isinstance(obj,Ability):
        return {'__class__': 'Ability',
                '__value__': stack.index(obj)}
    elif isinstance(obj,Action.Action):
        return {'__class__': 'Action',
                '__value__': [obj.__class__.__name__, obj.__dict__]}
    else: raise TypeError(repr(obj) + 'is not JSON serializable')

def from_json(json):
    if '__class__' in json:
        cls, val = json['__class__'], json['__value__']
        if cls == "CardRole":
            return GameObject._current_roles[tuple(val)]
        elif cls == "Player":
            return players[val]
        elif cls == "Ability":
            return stack[val]
        elif cls == "Action":
            klass = getattr(Action, val[0])
            obj = klass.__new__(klass)
            obj.__dict__ = val[1]
            return obj
    return json

def dumps(data):
    return json.dumps(data, default=to_json)

def loads(str):
    return json.loads(str, object_hook=from_json)

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
    def close(self):
        self.dumpfile.close()
    def __call__(self, obj):
        if self.save:
            data = dumps(obj)
            data = struct.pack('>I', len(data)) + data
            self.dumpfile.write(data)
            self.dumpfile.flush()
    def read(self):
        try:
            self.lastpos = self.dumpfile.tell()
            size = struct.unpack('>I', self.dumpfile.read(4))
            data = self.dumpfile.read(size)
            return loads(data)
        except Exception: #(EOFError, TypeError, KeyError):
            self.app.replay = False
            if self.prompt_continue: start_dumping = GameKeeper.Keeper.current_player.getIntention(self.app.game_status.prompt.value, "...continue recording?")
            else: start_dumping = True
            if start_dumping:
                self.save = True
                self.dumpfile.close()
                self.dumpfile = open(self.filename, 'a+b')
                self.dumpfile.seek(self.lastpos, 0)
            else: self.dumpfile.close()
            return False
    def __del__(self):
        self.close()

