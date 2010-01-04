from zope.interface import implements
from twisted.spread import pb
from twisted.cred import checkers, portal, credentials, error
from twisted.internet import reactor, defer

from replaydump import loads, dumps

class GameServer(object):
    def __init__(self, num_players, seed):
        self.avatarTypes = {"player" : PlayerAvatar,
                            "observer" : ObserverAvatar}
        self.avatars = []
        self.decks = {}
        self.num_players = num_players
        self.seed = seed
        self.game_started = False
        self.actions = []
    def can_be_started(self): return not self.game_started and len(self.avatars) < self.num_players
    def get_avatar(self, nickname, clientRef):
        if self.can_be_started(): avatarType = "player"
        else: avatarType = "observer"
        avatar = self.avatarTypes[avatarType](nickname, self, clientRef)
        self.join(avatar)
        return avatar
    def playing_with(self, avatar, deckfile):
        # Check if the deckfile is valid
        self.decks[avatar.name] = deckfile
        return True
    def can_play(self, avatar, defers=[]):
        # XXX This might possibly have a race condition
        # I have to think about it some more
        if avatar.caught_up: defer.succeed(True)
        else: return defer.succeed(True).addCallback(lambda x: self.catch_up(avatar))
    def can_start(self, defers=[]):
        # XXX This might possibly have a race condition
        # I have to think about it some more
        if self.can_be_started():
            dfr = defer.Deferred()
            defers.append(dfr)
            return dfr
        elif len(self.avatars) == self.num_players:
            self.game_started = True
            self.players = [(a.name, self.decks[a.name]) for a in self.avatars]
            result = (self.seed, self.players)
            for dfr in defers: dfr.callback(result)
            # Signal the last one directly
            return result
        else: # Only observer
            return (self.seed, self.players)
    def catch_up(self, avatar):
        # XXX There is a race condition here
        if self.actions:
            for action in self.actions: dfr = avatar.call_client("network_action", action)
        else: dfr = defer.succeed(True)
        dfr.addCallback(lambda x: setattr(avatar, "caught_up", True))
    def propagate_action(self, sender, action):
        self.actions.append(action)
        for avatar in self.avatars:
            if not avatar == sender and avatar.caught_up:
                avatar.call_client("network_action", action)
    def join(self, avatar):
        self.remoteAll("message", "* %s joined the server *" % avatar.name)
        self.avatars.append(avatar)
    def leave(self, avatar):
        self.avatars.remove(avatar)
        self.remoteAll("message", " * %s left the server * " % avatar.name)
    def remoteAll(self, action, *args):
        dfs = []
        for avatar in self.avatars:
            dfs.append(avatar.call_client(action, *args))
        return dfs

class GameClientFactory(pb.PBClientFactory):
    def login(self, credentials, client=None):
        """
        Login and get perspective from remote PB server.

        Currently the following credentials are supported::

            L{INicknameToken}

        @rtype: L{Deferred}
        @return: A L{Deferred} which will be called back with a
            L{RemoteReference} for the avatar logged in to, or which will
            errback if login fails.
        """
        d = self.getRootObject()
        d.addCallback(self._cbSendToken, credentials.token, credentials.nickname, client)
        return d
    def _cbSendToken(self, root, token, nickname, client):
        return root.callRemote("login")

class Client(pb.Referenceable):
    def __init__(self, nickname, hostname, port):
        self.nickname = nickname
        self.hostname = hostname
        self.port = port
        self.avatar = None
    def connect(self):
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.hostname, self.port, factory)
        cred = credentials.UsernamePassword(self.nickname, TOKEN)
        defrd = factory.login(cred, self)
        #defrd.addErrback(self.shutdown)
        return defrd
    def shutdown(self, result):
        print result
        # XXX Add handling for when the server quits
    def send_action(self, action):
        return self.avatar.callRemote('send_action', dumps(action))
    def send_message(self, msg):
        return self.avatar.callRemote('message', msg)
    def send_decklist(self, decklist):
        return self.avatar.callRemote('decklist', decklist)
    def ready_to_start(self):
        return self.avatar.callRemote('can_start')
    def ready_to_play(self):
        return self.avatar.callRemote('can_play')
    def remote_message(self, msg):
        pass #self.msg_callback(msg)
    def remote_network_action(self, data):
        data = loads(data)
        self.call_action(data)

class ObserverAvatar(pb.Avatar):
    caught_up = False
    def __init__(self, name, server, clientRef):
        self.name = name
        self.server = server
        self.client = clientRef
    def detached(self):
        self.server.leave(self)
        self.server = None
        self.client = None
    def call_client(self, action, *args):
        return self.client.callRemote(action, *args)
    def perspective_can_start(self):
        return self.server.can_start()
    def perspective_can_play(self):
        return self.server.can_play(self)
    def perspective_message(self, msg):
        self.server.remoteAll('message', self.name + ": " + msg)

class PlayerAvatar(ObserverAvatar):
    caught_up = True
    def perspective_send_action(self, action):
        self.server.propagate_action(self, action)
    def perspective_decklist(self, decklist):
        return self.server.playing_with(self, decklist)

# Login stuff

class INicknameToken(credentials.ICredentials):
    """
    I encapsulate a nickname and a generated token

    This encapsulates a game generated with a particular token.

    @type nickname: C{str}
    @ivar nickname: The nickname associated with these credentials.

    @type token: C{str}
    @ivar token: The token associated with this game.
    """

    def checkToken(token):
        """Validate these credentials against the correct password.

        @param token: The token given to this user.

        @return: a deferred which becomes, or a boolean indicating if the 
        password matches.
        """

class NicknameToken(object):
    implements(INicknameToken)
    def __init__(self, nickname, token):
        self.nickname = nickname
        self.token = token
    def checkToken(self, token):
        return self.token == token

class TokenChecker(object):
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword, credentials.IUsernameHashedPassword)
    def __init__(self, token):
        self.nicknames = set()
        self.token = token
    def requestAvatarId(self, cred):
        if cred.checkPassword(self.token):
            nickname = cred.username
            while nickname in self.nicknames: nickname = nickname + "_"
            self.nicknames.add(nickname)
            return defer.succeed(nickname)
        else:
            return defer.fail(error.UnauthorizedLogin())

# XXX Replace this with a real token generator
TOKEN = "ABCDEFG"

class Realm(object):
    implements(portal.IRealm)
    def __init__(self, port, server):
        self.port = port
        self.server = server
    def start(self):
        c = TokenChecker(TOKEN)
        p = portal.Portal(self)
        p.registerChecker(c)
        reactor.listenTCP(self.port, pb.PBServerFactory(p))
    def requestAvatar(self, nickname, clientRef, *interfaces):
        assert pb.IPerspective in interfaces
        avatar = self.server.get_avatar(nickname, clientRef)
        return pb.IPerspective, avatar, lambda a=avatar:a.detached()

# XXX This is just for debugging interaction between twisted and pyglet
def start_echo():
    from twisted.internet.protocol import Factory
    from twisted.protocols.wire import Echo
    myFactory = Factory()
    myFactory.protocol = Echo
    reactor.listenTCP(8000, myFactory)
