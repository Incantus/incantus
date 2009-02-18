
from GameObjects import Card, GameToken, characteristic
import zipfile
#import cPickle as pickle
#from Util import uuid

class _CardLibrary:
    datapath = "./data/cards/"

    acceptable_keys = set(['name', 'zone', '_last_known_role', 'color', 'text', '_current_role', 'expansion', 'supertype', 'controller', 'cost', 'cardnum', 'key', 'owner', 'subtypes', 'type', 'in_play_role', 'out_play_role', 'play_action'])

    cardfile = zipfile.ZipFile("./data/cards.zip")

    def __init__(self):
        #cardsets = [s.strip() for s in file(self.datapath+"cardsets").readlines()]
        cardsets = [s.strip() for s in self.cardfile.read("cards/cardsets").splitlines()]
        total = 0
        self.cardinfo = {}
        #for cs in cardsets:
        #    total += self.load_set(cs)
        self.clear()
        #self.numberCards = total

    def clear(self):
        self.cardsInGame = {}
        self.counter = 0
        self.tokencounter = 0

    #def load_set(self, cardset):
    #    import string
    #    f = file(self.datapath+cardset+"/oracle.pkl")
    #    cards = pickle.load(f)
    #    f.close()
    #    self.cardinfo[cardset] = dict([(c["name"], c) for c in cards])
    #    return len(cards)

    def createToken(self, name, player, color, type, subtypes):
        token = GameToken()
        token.owner = player
        token.name = name
        token.color = characteristic(color)
        token.type = characteristic(type)
        token.subtypes = characteristic(subtypes)
        token.key = (self.tokencounter, color)
        self.cardsInGame[token.key] = token
        self.tokencounter += 1
        return token

    def createCard(self, cardset, name, player):
        # Currently I recreate each card as it is created
        # I should add them to a factory and return a deepcopy
        card = Card()
        card.owner = player
        # Now load the card's abilities
        try:
            self.loadCardObj(card, cardset, name)
        except IOError, SyntaxError:
            print "Card not implemented"
            #self.loadCardOracle(card, cardset, name)

        card._current_role = card.out_play_role

        #card.uid = uuid(card.key)
        self.cardsInGame[card.key] = card
        self.counter += 1
        return card

    def loadCardOracle(self, card, cardset, name):
        import CardEnvironment
        print "%s not implemented yet"%name
        data = self.cardinfo[cardset][name]
        card.name = data["name"]
        card.cost = data.get("cost", "")
        card.text = data["text"]
        card.color = characteristic(data.get("color"))
        card.type = characteristic(data["type"])
        card.supertype = characteristic(data.get("supertype", None))
        card.subtypes = characteristic(data.get("subtypes", []))
        card.key = (self.counter, cardset, data["cardnum"])

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

    def loadCardObj(self, card, cardset, name):
        import CardEnvironment
        #print "***** Loading %s"%name
        #file_text = open(self.datapath+cardset+"/obj/"+name.replace(" ", "_")).read()
        file_text = self.cardfile.read("cards/"+cardset+"/obj/"+name.replace(" ", "_"))

        card.out_play_role = CardEnvironment.Spell(card)

        # Now set up the card
        # This is a bit of a hack to get everything to load properly
        card.card = card
        exec file_text in vars(CardEnvironment), vars(card)
        #del vars(card)["card"]
        # Get rid of non-standard attributes
        for k in card.__dict__.keys():
            if k not in self.acceptable_keys: del card.__dict__[k]
        card.key = (self.counter, cardset, card.cardnum)
        # XXX This should be set in each card file
        if type(card.cost) == str: card.cost = CardEnvironment.ManaCost(card.cost)

        # Set up the current role and casting abilities
        if not hasattr(card, "play_action"):
            card.play_action = CardEnvironment.PlaySpell
            if card.type == "Instant": card.play_action = CardEnvironment.PlayInstant
            elif card.type == "Land": card.play_action = CardEnvironment.PlayLand

        if (card.type == "Instant" or card.type == "Sorcery"):
            #if not isinstance(card.out_play_role.abilities[0], CardEnvironment.CastNonPermanentSpell):
            #    card.out_play_role.abilities = [CardEnvironment.CastNonPermanentSpell(card, cost=card.cost, effects=card.out_play_role.abilities)]
            card.in_play_role = CardEnvironment.NoRole(card)
        elif not card.type == "Land" and card.out_play_role and len(card.out_play_role.abilities) == 0:    # This takes care of Basic and other Lands, since they aren't considered spells
            card.out_play_role.abilities = [CardEnvironment.CastPermanentSpell(card, card.cost)]

    def __getitem__(self, key):
        # This is for unpickling during network transfer - we don't want to send the card across
        # but we need to identify the corresponding Card object based on key id.
        return self.cardsInGame[key]


CardLibrary = _CardLibrary()
