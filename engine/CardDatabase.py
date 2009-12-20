import bsddb, os, glob, traceback
import cPickle as pickle

class CardNotImplemented(Exception): pass

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
        self._invalid = set()
    def _convkey(self, key):
        return key.encode("rot13")
    def __getitem__(self, name):
        if not name in self._invalid:
            key = self._convkey(name)
            for db in self._dbs:
                if key in db:
                    text, impl, tested, error = pickle.loads(db[key])
                    # Find all ~ (tilde's) and replace with name
                    text = text.encode("rot13").replace("~", name)
                    return (text, impl, tested, error)
            else:
                self.unimplemented(name)
                print "%s not implemented"%name
        return (default_tmpl%repr(name), True, False, False)
    def keys(self): return sum([[self._convkey(k) for k in db.keys()] for db in self._dbs])
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
    if type(card.cost) == str: card.base_cost = CardEnvironment.ManaCost(card.cost)
    else: card.base_cost = card.cost

    # Build default characteristics
    card.base_name = card.name
    card.base_text = code
    card.base_color = card.color
    card.base_types = card.types
    card.base_subtypes = card.subtypes
    card.base_supertypes = card.supertypes
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
types = %(types)s
supertypes = %(supertypes)s
subtypes = %(subtypes)s
color = %(color)s
cost = NoCost()
%(extra)s
%(abilities)s'''
    fields = {}
    for attr in ["types", "supertypes", "subtypes", "color"]:
        char = card_dict.get(attr, None)
        if not char: fields[attr] = "characteristic()"
        else:
            if not (type(char) == list or type(char) == tuple): char = (char,)
            fields[attr] = "characteristic(%s)"%', '.join(map(str,char))

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
        if not (type(subtypes) == list or type(subtypes) == tuple): subtypes = (subtypes,)
        name = " ".join(map(str, subtypes))
    fields["name"] = repr(name)

    # Now process abilities (should only be simple keyword abilities)
    abilities = card_dict.get("abilities", '')
    if abilities:
        if not (type(abilities) == list or type(abilities) == tuple): abilities = (abilities,)
        abilities = "\n".join(["abilities.add(%s())"%a for a in abilities])
    fields["abilities"] = abilities
    return tmpl%fields

default_tmpl = '''
name = %s
types = characteristic(Artifact)
supertypes = characteristic()
subtypes = characteristic()
color = characteristic()
cost = ManaCost("0")
'''
