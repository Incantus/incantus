# Communication code (the import communcation statements)
from socket import *
import struct
import types
import cPickle as pickle
from cStringIO import StringIO
import select
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

def send(channel, args):
    src = StringIO()
    p = pickle.Pickler(src)
    p.persistent_id = persistent_id
    p.dump(args)
    buf = src.getvalue()
    value = htonl(len(buf))
    size = struct.pack("L", value)
    channel.send(size)
    channel.send(buf)

def receive(channel):
    size = struct.calcsize("L")
    size = channel.recv(size)
    size = ntohl(struct.unpack("L", size)[0])
    dst = StringIO()
    numread = 0
    while numread < size:
        buf = channel.recv(size - numread)
        numread += len(buf)
        dst.write(buf)
    dst.seek(0)
    p = pickle.Unpickler(dst)
    p.persistent_load = persistent_load
    obj = p.load()
    return obj

class Comm(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.channel = socket(AF_INET, SOCK_STREAM, 0)
    def send(self, args):
        send(self.channel, args)
    def receive(self):
        return receive(self.channel)
    def poll_other(self):
        result = self.poll.poll(50)
        if not result: return False
        else: return True
    def __del__(self):
        self.channel.close()

class Client(Comm):
    def __init__(self, ip, port):
        super(Client,self).__init__(ip, port)
        self.channel.connect((self.ip, self.port))
        self.poll = select.poll()
        self.poll.register(self.channel, select.POLLIN)

class Server(Comm):
    def __init__(self, ip, port):
        ip = ''
        super(Server,self).__init__(ip, port)
        self.channel.bind((ip, port))
        self.channel.listen(50)
        self.info = self.channel.getsockname()
        client = self.channel.accept()[0]
        self.channel.close()
        self.channel = client
        self.poll = select.poll()
        self.poll.register(self.channel, select.POLLIN)
