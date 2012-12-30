from engine.characteristics import characteristic
from engine.Util import isiterable
import bsddb, os, glob, traceback
import cPickle as pickle

class CardNotImplemented(Exception): pass

CARD_DELIM = "-"*5

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
        #self._txtcards = set(os.path.basename(c) for c in glob.glob("./data/cards/*"))
        self._txts = {}
        for dirpath, dirnames, filenames in os.walk("./data/cards/", topdown=False):
            for filename in filenames:
                file = open(os.path.join(dirpath, filename))
                current = []
                for line in file:
                    if not line.startswith(CARD_DELIM): current.append(line.rstrip())
                    else:
                        name = line[line.index(" ")+1:].strip()
                        if not name in self._txts:
                            self._txts[name] = '\n'.join(current)
                        current = []
                file.close()
        self._invalid = set()
    def _convkey(self, key):
        return key.encode("rot13")
    def __getitem__(self, name):
        if not name in self._invalid:
            # Check txt files
            if name in self._txts:
                #return (self._txts[name].replace("~", name), True, False, False)
                # Let's start doing runtime replacement...
                return (self._txts[name], True, False, False)
            #altname = name.replace(" ", "_").replace("'","").replace(",","")
            #if altname in self._txtcards:
            #    return (file("./data/cards/%s"%altname).read(), True, False, False)
            key = self._convkey(name)
            for db in self._dbs:
                if key in db:
                    text, impl, tested, error = pickle.loads(db[key])
                    ## Find all ~ (tilde's) and replace with name
                    #text = text.encode("rot13").replace("~", name)
                    # Not anymore... runtime replacement is far better.
                    text = text.encode("rot13")
                    return (text, impl, tested, error)
            else:
                self.unimplemented(name)
                print "%s not implemented"%name
        return (default_tmpl%repr(name), True, False, False)
    def keys(self): return sum([[self._convkey(k) for k in db.keys()] for db in self._dbs]) + [name for name in self._txts]
    def __contains__(self, key): return self._convkey(key) in self.db
    def unimplemented(self, name): self._invalid.add(name)
    def close(self): return self.db.close()

carddb = CardDatabase()

def execCode(card, code):
    import CardEnvironment

    acceptable_keys = set(card.__dict__.keys())

    # Now set up the card
    # This is a bit of a hack to get the abilities loaded properly
    card.abilities = card.base_abilities
    try:
        exec str(code) in vars(CardEnvironment), vars(card)
    except ZeroDivisionError:
        raise
    except Exception:
        code = code.split("\n")
        print ''
        print '\n'.join(["%03d\t%s"%(i+1, line) for i, line in zip(range(len(code)), code)])
        print ''
        traceback.print_exc(4)
        for k in card.__dict__.keys():
            if k not in acceptable_keys: del card.__dict__[k]
        raise CardNotImplemented()

    # For converted manacost comparisons
    if hasattr(card, "cost"):
        if isinstance(card.cost, str): 
            cost = card.cost
            card.base_cost = CardEnvironment.ManaCost(cost)
            # Get colors from mana cost
            card.base_color = characteristic(*card.base_cost.colors())
        else: card.base_cost = card.cost
    else: card.base_cost = CardEnvironment.NoCost()

    # Build default characteristics
    card.base_name = card.name
    card.base_text = '\n'.join(card.text) if hasattr(card, "text") else ""
    # characteristics
    for char_name in ["color", "types", "subtypes", "supertypes"]:
        if hasattr(card, char_name):
            char = getattr(card, char_name)
            if not isinstance(char, tuple): char = (char,)
            setattr(card, "base_"+char_name, characteristic(*char))

    if hasattr(card, "power"): card.base_power = card.power
    if hasattr(card, "toughness"): card.base_toughness = card.toughness
    if hasattr(card, "loyalty"): card.base_loyalty = card.loyalty

    # Get rid of non-standard attributes
    for k in card.__dict__.keys():
        if k not in acceptable_keys: del card.__dict__[k]

    return card

def loadCardFromDB(card, name):
    try:
        desc = carddb[name]
        code = desc[0]
        if desc[3] == True: print "%s is marked with an error"%name
        execCode(card, code)
    except CardNotImplemented:
        print "Execution error with %s"%name
        carddb.unimplemented(name)
        execCode(card, default_tmpl%repr(name))

def convertToTxt(card_dict):
    tmpl = '''\
name = %(name)s
%(char)s
%(extra)s
%(abilities)s'''
    fields = {}
    fields["char"] = ''
    for attr in ["types", "supertypes", "subtypes", "color"]:
        char = card_dict.get(attr, None)
        if char:
            if not isiterable(char): char = (char,)
            fields["char"] += "%s = %s\n"%(attr, ', '.join(map(str,char)))

    if "P/T" in card_dict:
        power, toughness = card_dict["P/T"]
        fields["extra"] = "power = %d\ntoughness = %d\n"%(power, toughness)
    elif "loyalty" in card_dict:
        fields["extra"] = "loyalty = %d\n"%card_dict["loyalty"]
    else:
        fields["extra"] = ''

    name = card_dict.get("name", None)
    if not name:
        subtypes = card_dict.get("subtypes", ())
        if not isiterable(subtypes): subtypes = (subtypes,)
        name = " ".join(map(str, subtypes))
    fields["name"] = repr(name)

    # Now process abilities (should only be simple keyword abilities)
    abilities = card_dict.get("abilities", '')
    if abilities:
        if not isiterable(abilities): abilities = (abilities,)
        abilities = "\n".join(["abilities.add(%s())"%a for a in abilities])
    fields["abilities"] = abilities
    return tmpl%fields

default_tmpl = '''
name = %s
types = Artifact
cost = "0"
'''
