''' Everything to do with Mana
'''

from GameObjects import MtGObject
from GameEvent import ManaAdded, ManaSpent, ManaCleared

class Colors:
    numberOfColors = 6
    WHITE = 0
    BLUE = 1
    BLACK = 2
    RED = 3
    GREEN = 4
    COLORLESS = 5
    __colors = [(WHITE, "white"), (BLUE, "blue"), (BLACK, "black"),
                (RED, "red"), (GREEN, "green"), (COLORLESS, "colorless"),
                 (WHITE, "W"), (BLUE, "U"), (BLACK, "B"),
                 (RED, "R"), (GREEN, "G"), (COLORLESS, "C")]
    realColors = set(["W", "U", "B", "R", "G"])
    ColorMap = dict([(c[0], c[1]) for c in __colors])
    ReverseMap = dict([(c[1], c[0]) for c in __colors])

def compareMana(req_manastr, comp_manastr):
    if type(req_manastr) == str: req = convert_mana_string(req_manastr)
    if type(comp_manastr) == str: comp = convert_mana_string(comp_manastr)
    enoughMana = True
    if not sum(req) == sum(comp): enoughMana = False
    # Now check the required colors
    for i, val in enumerate(req[:-1]):
        if comp[i] < val: enoughMana = False
    return enoughMana

def convert_to_mana_string(mana):
    colorless = str(mana[Colors.COLORLESS])
    manastr = ''.join([color*mana[Colors.ReverseMap[color]] for color in "WUBRG"])
    if colorless == "0" and len(manastr) > 0: colorless = ''
    return colorless+manastr

def combine_mana_strings(*manastr):
    mana = [0]*Colors.numberOfColors
    hasX = False
    for manastring in manastr:
        tens = 0
        for c in manastring:
            # XXX This doesn't work for colorless mana over 10
            if c not in Colors.realColors:
                # colorless mana
                if c == "X": hasX = True
                elif type(c) == str:
                    c = int(c)
                    mana[Colors.COLORLESS] += c + 10*tens-tens
                    tens = c
            else:
                mana[Colors.ReverseMap[c]] += 1
    string = convert_to_mana_string(mana)
    if hasX: string = "X"+string
    return string

def convert_mana_string(manastr, X=0):
    mana = [0]*Colors.numberOfColors
    tens = 0
    for c in manastr:
        # XXX This doesn't work for colorless mana over 10
        if c not in Colors.realColors:
            # colorless mana
            if c == "X": v = X
            elif type(c) == str: 
                v = int(c)
            mana[Colors.COLORLESS] += v + 10*tens-tens
            if type(c) != 'X': tens = v
        else:
            mana[Colors.ReverseMap[c]] += 1
    return mana

def converted_mana_cost(mana=None):
    if type(mana) == str: mana = convert_mana_string(mana)
    return sum(mana)

class ManaPool(MtGObject):
    def __init__(self):
        # Should the manapool have a reference to the player so it can ask for more mana if needed?
        self._mana = [0]*Colors.numberOfColors
    def clear(self):
        self._mana = [0]*Colors.numberOfColors
        self.send(ManaCleared())
    def addMana(self, mana):
        if type(mana) == str: mana = self.convert_mana_string(mana)
        for i, amount in enumerate(mana):
            self._mana[i] += amount
        if sum(mana) > 0: self.send(ManaAdded(), amount=mana)
    def spend(self, mana):
        # This function assumes that you have enough mana
        if type(mana) == str: mana = self.convert_mana_string(mana)
        for i, amount in enumerate(mana):
            if not amount <= self._mana[i]: raise Exception("Not enough %s mana"%Colors.ColorMap[i])
            self._mana[i] -= amount
        self.send(ManaSpent(), amount=mana)
    def checkX(self, mana):
        if type(mana) == str: return "X" in mana
        else: return False
    def checkMana(self, mana):
        enoughMana = True
        if type(mana) == str: mana = self.convert_mana_string(mana)
        # Now check the required colors
        for i, amount in enumerate(mana[:-1]):
            if not amount <= self._mana[i]: enoughMana = False
        if not sum(mana) <= sum(self._mana): enoughMana = False
        return enoughMana
    def distributeMana(self, mana):
        # At this point I know I have enough mana
        if type(mana) == str: mana = self.convert_mana_string(mana)
        # First, if no colorless mana, don't need to distribute
        if mana[-1] == 0: return mana

        pool_copy = [x for x in self._mana]
        cost_copy = [x for x in mana]

        colorless = 0
        # Handle the required mana:
        for i, amount in enumerate(mana):
            pool_copy[i] -= amount
            cost_copy[i] -= amount
        # Now any available colorless
        if pool_copy[-1] < 0:
            colorless = -1*pool_copy[-1]
            pool_copy[-1] = 0
        else: colorless = 0

        # If we've payed all the costs - This should handle most cases
        if (sum(cost_copy) == 0 and colorless == 0): return mana
        if (sum(pool_copy) == colorless): return [x for x in self._mana]
        # Now the only other case is if there is only one type left and it satisfies the requirement
        for i, amt in enumerate(pool_copy):
            if amt: cost_copy[i] = amt - colorless
        if sum(pool_copy) == sum(cost_copy)+colorless: return [x-y for x,y in zip(self._mana, cost_copy)]

        # We can't distribute the mana
        return False

    def convertedManaCost(self, mana=None):
        if mana == None: return sum(self._mana)
        if type(mana) == str: mana = self.convert_mana_string(mana)
        return sum(mana)
    def manaBurn(self):
        return sum(self._mana)
    def getMana(self, mana, attr):
        return mana[Colors.ReverseMap[attr]]
    def __getattr__(self, attr):
        if Colors.ReverseMap.has_key(attr):
            return self._mana[Colors.ReverseMap[attr]]
        else: super(ManaPool, self).__getattr__(attr)
    def convert_mana_string(self,manastr): return convert_mana_string(manastr)
    def convert_to_mana_string(self, cost): return convert_to_mana_string(cost)
