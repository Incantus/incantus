
from characteristics import characteristic, no_characteristic
from GameObjects import Card, GameToken
import bsddb, os, glob, cPickle as pickle

class CardDatabase(object):
    def __init__(self):
        dirname = "./data/"
        dbnames = glob.glob(dirname+"*.db")
        for name in dbnames:
            if os.path.basename(name) == "card_images.db":
                dbnames.remove(name)
                break
        self._dbs = []
        for filename in dbnames:
            self._dbs.append(bsddb.hashopen(filename))
    def _convkey(self, key):
        return key.encode("rot13")
    def __getitem__(self, name):
        key = self._convkey(name)
        for db in self._dbs:
            if key in db:
                text, impl, tested, error = pickle.loads(db[key])
                # Find all ~ (tilde's) and replace with name
                text = text.encode("rot13").replace("~", name)
                return (text, impl, tested, error)
        else: raise KeyError
    def keys(self): return sum([[self._convkey(k) for k in db.keys()] for db in self._dbs])
    def __contains__(self, key): return self._convkey(key) in self.db
    def close(self): return self.db.close()

class _CardLibrary:
    acceptable_keys = set(['name', 'zone', '_last_known_info', 'color', 'text', '_current_role', 'expansion', 'supertype', 'controller', 'cost', 'cardnum', 'key', 'owner', 'subtypes', 'type', 'in_play_role', 'out_play_role', 'stack_role'])
    def __init__(self):
        self.cardfile = CardDatabase()
        total = 0
        self.cardinfo = {}
        self.clear()

    def clear(self):
        self.cardsInGame = {}
        self.counter = 0
        self.tokencounter = 0

    def createToken(self, name, player, color, type, subtypes, supertype, cost="0"):
        import CardEnvironment
        token = GameToken(player)
        token.name = name
        token.cost = CardEnvironment.ManaCost(cost)
        characteristics = [("color", color), ("type", type), ("subtypes", subtypes), ("supertype", supertype)]
        for base, char in characteristics:
            if char: char = characteristic(char)
            else: char = no_characteristic()
            setattr(token, "base_"+base, char)
            setattr(token, base, char)
        token.key = (self.tokencounter, token.name+" Token")
        token.text = ["Token"]
        self.cardsInGame[token.key] = token
        self.tokencounter += 1
        return token

    def createCard(self, name, player):
        # Currently I recreate each card as it is created
        # XXX I should add them to a factory and return a deepcopy - this will never work with the lambda bindings
        card = Card(owner=player)
        card.controller = card.owner
        # Now load the card's abilities
        try:
            self.loadCardObj(card, name)
        except (KeyError):
            self.loadDefaultCard(card, name)

        card._current_role = card.out_play_role

        self.cardsInGame[card.key] = card
        self.counter += 1
        return card

    def loadDefaultCard(self, card, name):
        import CardEnvironment
        print "%s not implemented yet - object will be a '0' cost Artifact with no abilities"%name
        card.name = name
        card.cost = "0"
        card.text = "No card object found"
        card.base_color = card.color = characteristic('')
        card.base_type = card.type = characteristic("Artifact")
        card.base_supertype = card.supertype = characteristic('')
        card.base_subtypes = card.subtypes = characteristic('')
        card.key = (self.counter, name)

        card.stack_role = CardEnvironment.SpellRole(card)
        card.out_play_role = CardEnvironment.CardRole(card)
        card.out_play_role.abilities = [CardEnvironment.CastPermanentSpell(card, card.cost)]

        # XXX This is just hackery to get it working with arbitrary cards
        subrole = CardEnvironment.Artifact()
        card.in_play_role = CardEnvironment.Permanent(card, subrole)

    def loadCardObj(self, card, name):
        import CardEnvironment
        card_desc = self.cardfile[name]
        card_text = card_desc[0]
        if card_desc[3] == True: print "%s is marked with an error"%name

        card.stack_role = CardEnvironment.SpellRole(card)
        # XXX This should be changed because out of play roles are different depending on the Zone
        card.out_play_role = CardEnvironment.CardRole(card)

        # Now set up the card
        # This is a bit of a hack to get everything to load properly
        card.card = card
        try:
            exec card_text in vars(CardEnvironment), vars(card)
        except Exception, e:
            print name, e
            raise KeyError()
        # Get rid of non-standard attributes
        for k in card.__dict__.keys():
            if k not in self.acceptable_keys: del card.__dict__[k]

        # Build default characteristics
        card.base_color = card.color
        card.base_type = card.type
        card.base_subtypes = card.subtypes
        card.base_supertype = card.supertype

        card.key = (self.counter, card.name)

        if type(card.cost) == str: card.cost = CardEnvironment.ManaCost(card.cost)

        if (card.type == "Instant" or card.type == "Sorcery"):
            card.in_play_role = CardEnvironment.NoRole(card)

    def __getitem__(self, key):
        # This is for unpickling during network transfer - we don't want to send the card across
        # but we need to identify the corresponding Card object based on key id.
        return self.cardsInGame[key]


CardLibrary = _CardLibrary()
