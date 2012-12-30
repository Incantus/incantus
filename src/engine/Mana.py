''' Everything to do with Mana
'''
from symbols.colors import *
from MtGObject import MtGObject
from GameEvent import ManaAdded, ManaSpent, ManaCleared

__all__ = ["ManaPool",
           "convert_to_color", "subset_in_pool", "compare_mana",
           "convert_to_mana_string", "combine_mana_strings",
           "convert_mana_string", "converted_mana_cost",
           ]

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

def convert_to_color(manastr, color_dict = dict(W=White,U=Blue,B=Black,R=Red,G=Green)):
    return [color for c, color in color_dict.items() if c in manastr]

def subset_in_pool(pool_manastr, comp_manastr):
    pool = convert_mana_string(pool_manastr)
    comp = convert_mana_string(comp_manastr)
    enoughMana = sum(comp) <= sum(pool)
    # Now check the required colors
    for c, p in zip(comp, pool):
        if c > p:
            enoughMana = False
            break
    return enoughMana

def compare_mana(req_manastr, comp_manastr):
    req = convert_mana_string(req_manastr)
    comp = convert_mana_string(comp_manastr)
    enoughMana = (sum(req) == sum(comp))
    # Now check the required colors
    for i, val in enumerate(req[:-1]):
        if comp[i] < val: enoughMana = False
    return enoughMana

def convert_to_mana_string(mana):
    manastr = ''.join([color*mana[Colors.ReverseMap[color]] for color in "WUBRG"])
    colorless = str(mana[Colors.COLORLESS])
    if colorless == "0" and len(manastr) > 0: colorless = ''
    return colorless+manastr

def combine_mana_strings(*manastr):
    total_mana = [0]*Colors.numberOfColors
    for manastring in manastr:
        mana = convert_mana_string(manastring)
        for i in range(len(mana)):
            total_mana[i] += mana[i]
    if any([True for ms in manastr if 'X' in ms]): X = "X"
    else: X = ''
    return X+convert_to_mana_string(total_mana)

def convert_mana_string(manastr):
    # This ignores all X's (ie they are equal to 0)
    mana = [0]*Colors.numberOfColors
    tens = 0
    for c in manastr:
        if c in Colors.realColors:
            mana[Colors.ReverseMap[c]] += 1
        elif not c == "X":
            # colorless mana
            v = int(c)
            mana[Colors.COLORLESS] += v + 10*tens-tens
            tens = v
    return mana

def converted_mana_cost(mana):
    if isinstance(mana, str):
        if ("(" in mana or '{' in mana): mana = generate_hybrid_choices(mana)[0]
        mana = convert_mana_string(mana)
    return sum(mana)

def iterall(iterables):
    if iterables:
        for head in iterables[0]:
            for remainder in iterall(iterables[1:]):
                yield [head] + remainder
    else:
        yield []

def parse_hybrid(manastr):
    hybrid = []
    choices = []
    choice = ""
    parsing_hybrid = False
    for c in manastr:
        if not c in "()/{}":
            if not parsing_hybrid: choices.append([c])
            else: choice += c
        elif c == '(' or c == '{':
            parsing_hybrid = True
            hybrid = []
            choice = ""
        elif c == '/':
            hybrid.append(choice)
            choice = ""
        elif c == ')' or c == '}':
            parsing_hybrid = False
            hybrid.append(choice)
            choices.append(hybrid)
    return choices

def convert_hybrid_string(manastr):
    mana = {}
    v = 0
    for c in manastr:
        if not set(c).difference(set("0123456789")): v += int(c)
        #if not (c in Colors.realColors or c == 'X'): v += int(c)
        else:
            for char in c:
                if not char in mana: mana[char] = 0
                mana[char] += 1
    symbols = tuple(''.join([c*mana[c] for c in "XWUBRG" if c in mana]))
    if v: symbols = (str(v),)+symbols
    return symbols

def mana_key(symbol, color=dict([(c, val) for c, val in zip("XWUBRG", range(0, -6, -1))])):
    def convert(val):
        if val in color: return color.get(val)
        else: return int(val)
    return tuple([convert(val) for val in symbol])

def generate_hybrid_choices(manastr):
    choices = parse_hybrid(manastr)
    options = sorted(set([convert_hybrid_string(manastr) for manastr in iterall(choices)]), key=mana_key, reverse=True)
    return [''.join(option) for option in options]

class ManaPool(MtGObject):
    def __init__(self):
        self._mana = [0]*Colors.numberOfColors
    def clear(self):
        self._mana = [0]*Colors.numberOfColors
        self.send(ManaCleared())
    def manaBurn(self): return sum(self._mana)
    def add(self, mana):
        if isinstance(mana, str): mana = convert_mana_string(mana)
        for i, amount in enumerate(mana): self._mana[i] += amount
        if sum(mana) > 0: self.send(ManaAdded(), amount=mana)
    def spend(self, mana):
        # This function assumes that you have enough mana
        if isinstance(mana, str): mana = convert_mana_string(mana)
        for i, amount in enumerate(mana):
            if not amount <= self._mana[i]: raise Exception("Not enough %s mana"%Colors.ColorMap[i])
            self._mana[i] -= amount
        self.send(ManaSpent(), amount=[-1*m for m in mana])
    def enoughInPool(self, mana):
        cost = [val for val in mana]
        for i, amount in enumerate(self._mana):
            for j in range(amount):
                if cost[i] == 0: cost[-1] -= 1
                else: cost[i] -= 1
            cost[i] = max(cost[i], 0)
        coststr = convert_to_mana_string(cost)
        return coststr
    def distribute(self, mana):
        # At this point I know I have enough mana
        if isinstance(mana, str): mana = convert_mana_string(mana)
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
    def __str__(self):
        return convert_to_mana_string(self._mana)
