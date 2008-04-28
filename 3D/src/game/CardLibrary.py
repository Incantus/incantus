
from GameObjects import Card, GameToken, characteristic
import bsddb, os, glob, cPickle as pickle
#from Util import uuid

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
    def __getitem__(self, key):
        key = self._convkey(key)
        for db in self._dbs:
            if key in db:
                text, impl, tested, error = pickle.loads(db[key])
                return (text.encode("rot13"), impl, tested, error)
        else: raise KeyError
    def keys(self): return sum([[self._convkey(k) for k in db.keys()] for db in self._dbs])
    def __contains__(self, key): return self._convkey(key) in self.db
    def close(self): return self.db.close()

class _CardLibrary:
    acceptable_keys = set(['name', 'zone', '_last_known_info', 'color', 'text', '_current_role', 'expansion', 'supertype', 'controller', 'cost', 'cardnum', 'key', 'owner', 'subtypes', 'type', 'in_play_role', 'out_play_role', 'play_action'])
    def __init__(self):
        self.cardfile = CardDatabase()
        total = 0
        self.cardinfo = {}
        self.clear()

    def clear(self):
        self.cardsInGame = {}
        self.counter = 0
        self.tokencounter = 0

    def createToken(self, name, player, color, type, subtypes, supertype='', cost="0"):
        import CardEnvironment
        token = GameToken(player)
        token.name = name
        token.cost = CardEnvironment.ManaCost(cost)
        token.base_color = token.color = characteristic(color)
        token.base_type = token.type = characteristic(type)
        token.base_subtypes = token.subtypes = characteristic(subtypes)
        token.base_supertype = token.supertype = characteristic(supertype)
        token.key = (self.tokencounter, token.name+" Token")
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
            #self.loadCardOracle(card, name)

        card._current_role = card.out_play_role

        #card.uid = uuid(card.key)
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

        card.out_play_role = CardEnvironment.Spell(card)
        card.play_action = CardEnvironment.PlaySpell
        card.out_play_role.abilities = [CardEnvironment.CastPermanentSpell(card, card.cost)]

        # XXX This is just hackery to get it working with arbitrary cards
        subrole = CardEnvironment.Artifact()
        card.in_play_role = CardEnvironment.Permanent(card, subrole)

    def loadCardOracle(self, card, name):
        import CardEnvironment
        print "%s not implemented yet"%name
        data = self.cardinfo[cardset][name]
        card.name = data["name"]
        card.cost = data.get("cost", "")
        card.text = data["text"]
        card.base_color = card.color = characteristic(data.get("color"))
        card.base_type = card.type = characteristic(data["type"])
        card.base_supertype = card.supertype = characteristic(data.get("supertype", None))
        card.base_subtypes = card.subtypes = characteristic(data.get("subtypes", []))
        card.key = (self.counter, data["name"])

        card.out_play_role = CardEnvironment.Spell(card)
        card.play_action = CardEnvironment.PlaySpell
        if card.type == "Instant": card.play_action = CardEnvironment.PlayInstant
        elif card.type == "Land": card.play_action = CardEnvironment.PlayLand

        if card.type == "Instant" or card.type == "Sorcery":
            card.out_play_role.abilities = [CardEnvironment.CastNonPermanentSpell(card, card.cost)]
        else:
            card.out_play_role.abilities = [CardEnvironment.CastPermanentSpell(card, card.cost)]

        # XXX This is just hackery to get it working with arbitrary cards
        if card.type == "Creature":
            card.in_play_role = CardEnvironment.Permanent(card, CardEnvironment.Creature(data["power"], data["toughness"]))
        elif card.type != "Instant" or card.type != "Sorcery":
            card.in_play_role = CardEnvironment.Permanent(card, CardEnvironment.NoRole())
            #XXX This is just to give non implemented cards some kind of ability
            card.in_play_role.abilities = [CardEnvironment.ManaAbility(card, CardEnvironment.TapCost(), effects=CardEnvironment.AddMana("WW"))]

    def loadCardObj(self, card, name):
        import CardEnvironment
        card_desc = self.cardfile[name]
        card_text = card_desc[0]
        if card_desc[3] == True: print "%s is marked with an error"%name

        # XXX This should be changed because out of play roles are different depending on the Zone
        card.out_play_role = CardEnvironment.Spell(card)

        # Now set up the card
        # This is a bit of a hack to get everything to load properly
        card.card = card
        try:
            exec card_text in vars(CardEnvironment), vars(card)
        except Exception, e:
            print name, e
            raise
        # Get rid of non-standard attributes
        for k in card.__dict__.keys():
            if k not in self.acceptable_keys: del card.__dict__[k]

        # Build default characteristics
        card.base_color = card.color
        card.base_type = card.type
        card.base_subtypes = card.subtypes
        card.base_supertype = card.supertype

        card.key = (self.counter, card.name)
        # XXX This should be set in each card file
        if type(card.cost) == str: card.cost = CardEnvironment.ManaCost(card.cost)
        # Set up the current role and casting abilities
        if not hasattr(card, "play_action"):
            card.play_action = CardEnvironment.PlaySpell
            if card.type == "Instant": card.play_action = CardEnvironment.PlayInstant
            elif card.type == "Land": card.play_action = CardEnvironment.PlayLand

        if (card.type == "Instant" or card.type == "Sorcery"):
            card.in_play_role = CardEnvironment.NoRole(card)
        elif not card.type == "Land" and card.out_play_role and len(card.out_play_role.abilities) == 0:
            # This takes care of Basic and other Lands, since they aren't considered spells
            card.out_play_role.abilities = [CardEnvironment.CastPermanentSpell(card, card.cost)]

    def __getitem__(self, key):
        # This is for unpickling during network transfer - we don't want to send the card across
        # but we need to identify the corresponding Card object based on key id.
        return self.cardsInGame[key]


CardLibrary = _CardLibrary()
