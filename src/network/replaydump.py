import struct
import simplejson as json
from engine.Player import Player
from engine.Ability.StackAbility import StackAbility
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
    elif isinstance(obj,StackAbility):
        return {'__class__': 'StackAbility',
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
        elif cls == "StackAbility":
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

class ReplayFinishedException(Exception): pass

class ReplayDump(object):
    def __init__(self, filename="game.replay", save=False, continue_save=False):
        self.filename = filename
        self.continue_save = continue_save
        if save:
            flags = 'wb'
            self.write = self.do_write
            self.read = lambda: False
        else: 
            flags = 'rb'
            self.write = lambda obj: None
            self.read = self.do_read

        self.dumpfile = open(self.filename, flags, 0)
        self.lastpos = self.dumpfile.tell()
    def close(self):
        self.dumpfile.close()
    def do_write(self, obj):
        self.write_raw(dumps(obj))
    def write_raw(self, data):
        data = struct.pack('>I', len(data)) + data
        self.dumpfile.write(data)
        self.dumpfile.flush()
    def do_read(self):
        return loads(self.read_raw())
    def read_raw(self):
        try:
            self.lastpos = self.dumpfile.tell()
            size = struct.unpack('>I', self.dumpfile.read(4))[0]
            data = self.dumpfile.read(size)
            return data
        except Exception: #(EOFError, TypeError, KeyError):
            self.reset_append()
            raise ReplayFinishedException()
    def reset_append(self):
        self.close()
        self.dumpfile = open(self.filename, 'a+b')
        self.dumpfile.seek(self.lastpos, 0)
        self.read = lambda: False
        if self.continue_save: self.write = self.do_write
    def __del__(self):
        self.close()
