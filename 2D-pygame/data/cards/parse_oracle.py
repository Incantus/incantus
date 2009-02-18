
import string
lines = file("./checklist.txt").readlines()
lines = [l.strip().split("\t") for l in lines if l[0] != "#"]
lines = [[int(l[0]), l[1]] for l in lines]
nummap = dict([(l[1], l[0]) for l in lines])

lines = file("./oracle.txt").readlines()
lines = [l.strip() for l in lines]
lines_iter = iter(lines)

color_dict = {'R': 'red', 'G':'green', 'B':'black', 'W':'white', 'U':'blue', 'C':'colorless'}

def convert_cost(cost):
    #return cost
    cost_array = dict(zip(['R', 'G', 'B', 'W', 'U', 'C'], [0]*6))
    for c in cost:
        if c not in ['R', 'G', 'B', 'W', 'U']:
            #colorless
            if c == "X": c = "-1"
            cost_array['C'] += int(c)
        else:
            cost_array[c] += 1
    return cost_array

def get_color(cost):
    cost = convert_cost(cost)
    colors = []
    for color in ['R', 'G', 'B', 'W', 'U']:
        val = cost[color]
        if val > 0: colors.append(color)

    # If no mana colors (only colorless) then this object is colorless
    if not colors:
        colors.append('C')
    return colors

import re
def parse_text(text):
    new_text = []
    for t in text:
        pos = t.find("Choose one")
        if pos != -1:
            choices = t.split(" - ")[1].split(";")
            temp = []
            for c in choices:
                newtemp = c.split(" or")
                if len(newtemp) == 1: newtemp = newtemp[0]
                else: newtemp = newtemp[1].strip()
                temp.append(newtemp)
            new_text.extend(temp)
        else:
            new_text.append(t)
    new_text = new_text[:-1]

    # Now get rid of apostrophes
    for i,t in enumerate(new_text):
        m = re.match('(.*) (\(.*\))',t)
        if m: new_text[i] = m.groups()[0]
    return new_text

def conv_pt(pt):
    try: pt = int(pt)
    except ValueError: pt = -1
    return pt

basic_lands = dict([("Island", "U"), ("Plains","W"), ("Swamp","B"), ("Forest","G"), ("Mountain", "R")])

cards = []
while True:
    is_creature = is_land = False
    try:
        l = lines_iter.next()
    except StopIteration:
        break
    if l == "": continue
    supertype = ""
    subtypes = []
    name = l
    cost = lines_iter.next()
    if "Land" in cost.split():
        # Either Basic Land or other type
        type = cost.split(" - ")
        cost = ''
        if type[0].strip() == "Basic Land":
            subtypes = type[1].split()
            color = [basic_lands[name]]
            supertype = type[0].split()[0]
        else: color = ["C"]
        type = "Land"
        conv_cost = convert_cost(cost)
        is_land = True
    else:
        conv_cost = convert_cost(cost)
        color = get_color(cost)
        type = lines_iter.next()
        if "Creature" in type.split():
            type = type.split(" - ")
            subtypes = type[1].split()
            type = type[0].split()
            if len(type) > 1:
                supertype, type = type[0], type[1]
                if supertype == "Artifact":
                    type = [type, supertype]
                    supertype = ''
            else: type = type[0]
            is_creature = True
            pt = lines_iter.next().split("/")
            power, toughness = map(conv_pt, pt)
        elif "Enchantment" in type.split() or "Artifact" in type.split():
            type = type.split(" - ")
            if len(type) > 1:
                subtypes = type[1].split()
                type = type[0].split()
                if len(type) > 1:
                    supertype, type = type[0], type[1]
                else: type = type[0]
            else: type = type[0]
            if supertype == "Tribal": supertype = ""
        elif "Tribal" in type.split():
            type = type.split(" - ")
            if len(type) > 1:
                subtypes = type[1].split()
                type = type[0].split()[1]

    text = []
    while not l == "":
        l = lines_iter.next()
        text.append(l)

    text = parse_text(text)

    if nummap.get(name, False):
        card = {"cardnum": nummap[name], "name": name, "color": color, "type": type, "cost": cost, "text": text}
        card["supertype"] = supertype
        card["subtypes"] = subtypes
        if is_creature:
            card["power"] = power
            card["toughness"] = toughness
        cards.append(card)

import cPickle as p
f = file("oracle.pkl", 'w')
p.dump(cards, f, True)
f.close()
