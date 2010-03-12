#!/usr/bin/python
from optparse import OptionParser
import readline, pudb, pdb, gc
import time, random
from itertools import chain, repeat, izip
import ConfigParser
from engine.GameKeeper import Keeper
from engine.Player import Player
from engine import Action, Mana
from network import replaydump

# Recursively expand slist's objects
# into olist, using seen to track
# already processed objects.
def _getr(slist, olist, seen):
  for e in slist:
    if id(e) in seen:
      continue
    seen[id(e)] = None
    olist.append(e)
    tl = gc.get_referents(e)
    if tl:
      _getr(tl, olist, seen)

# The public function.
def get_all_objects():
  """Return a list of all live Python
  objects, not including the list itself."""
  gc.collect()
  gcl = gc.get_objects()
  olist = []
  seen = {}
  # Just in case:
  seen[id(gcl)] = None
  seen[id(olist)] = None
  seen[id(seen)] = None
  # _getr does the real work.
  _getr(gcl, olist, seen)
  return olist


def grouper(n, iterable, padvalue=None):
    "grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')"
    return izip(*[chain(iterable, repeat(padvalue, n-1))]*n)

class Printer:
    _pfx = '  '

    prefix = property(lambda self: ''.join(self._prefixes))
    def __init__(self):
        self.level = 0;
        self._prefixes = []
    def indent(self, pfx=None):
        if not pfx: pfx = Printer._pfx
        self.level+=1
        self._prefixes.append(pfx)
    def unindent(self):
        self.level-=1
        self._prefixes.pop()
    def __call__(self, s):
        print self.prefix+s

class Indenter:
    def __init__(self, printer, pfx=None):
        self._p = printer
        self.pfx = pfx
    def __enter__(self):
        self._p.indent(self.pfx)
        return self._p
    def __exit__(self, type, value, traceback):
        self._p.unindent()
        return False

printer = Printer()

card_map = {}

def text_input(msg):
    while True:
        text = raw_input(printer.prefix+msg)
        if (text and text[0] == '!'): # Helper functions
            if text == "!d": pdb.set_trace()
            elif text == "!pu": pudb.set_trace()
            elif text[:2] == "!c":
                try:
                    card = card_map.get(int(text[2:]), None)
                    if card: printer("%s"%card.info)
                    else: printer("Invalid card")
                except: pass
            elif text == "!g": print gc.collect()
        else: break
    return text

def hand_card_str(card):
    card_map[card.key[0]] = card
    if str(card.cost):
        text = "%s:%s"%(card.cost, card.name)
    else: text = str(card.name)
    if card.types == "Creature":
        text += "(%d/%d)"%(card.power, card.toughness)
    return "%3d) %s"%(card.key[0], text)

def battlefield_card_str(card):
    card_map[card.key[0]] = card
    text = []
    if card.tapped: text.append("*T* ")
    text.append("%s"%(card.name))
    if card.types == "Creature":
        text += "(%d/%d)"%(card.power, card.toughness)
    return "%3d) %s"%(card.key[0], ''.join(text))

def nonbattlefield_card_str(card):
    card_map[card.key[0]] = card
    text = str(card.name)
    if card.types == "Creature":
        text += "(%d/%d)"%(card.power, card.toughness)
    return "%3d) %s"%(card.key[0], text)

def print_zone(zone, pp):
    printer("[%10s:%3d]"%(str(zone).title(), len(zone)))
    printer.indent()
    for cards in grouper(2, zone):
        printer(" ".join(["%-35s"%pp(card) for card in cards if card]))
    printer.unindent()

def print_stack():
    stack = Keeper.stack
    printer("[%10s:%3d]"%(str(stack).title(), len(stack)))
    printer.indent()
    for ability in stack._abilities:
        printer("** %s - %s"%(ability.source, ability))
    printer.unindent()
    print

def print_player(idx, player):
    active = Keeper.players.active == player
    if active: act = '*'
    else: act = ' '
    txt = ["[%d) %-14s%3d]"%(idx, player.name+":", player.life)]
    txt.append("[Mana: %s]"%player.manapool)
    txt.append("[Library: %3d]"%len(player.library))
    if not active: txt.append("[Hand: %3d]"%len(player.hand))
    else: txt.append("="*11)
    txt.append("="*10)
    printer("=".join(txt))
    printer.indent()
    print_zone(player.hand, hand_card_str)
    print_zone(player.battlefield, battlefield_card_str)
    print_zone(player.graveyard, nonbattlefield_card_str)
    print_zone(player.exile, nonbattlefield_card_str)
    printer.unindent()

def print_header():
    printer("-"*70)
    printer("Phase: %s\n"%Keeper.current_phase.upper())
    print_stack()
    for i, player in enumerate(Keeper.players):
        print_player(i, player)
        print
    printer("-"*70)
    #printer("*******************************")
    #printer("** %-25s **"%Keeper.current_phase)
    #printer("*******************************")

def replayInput(context, prompt=''):
    process = context['process']
    try:
        result = dump_to_replay.read()
    except replaydump.ReplayFinishedException:
        # Switch the input to the greenlet_input
        for player in players: player.dirty_input = playerInput
        result = playerInput(context, prompt)
    return result

def playerInput(context, prompt=''):
    print_header()
    printer(prompt)

    process = context['process']
    action = False

    if context.get("get_ability", False):
        while action == False:
            txt = text_input("What would you like to do\n(Enter to pass priority): ")
            if not txt: 
                action = process(Action.PassPriority())
            else:
                try:
                    cardnum = int(txt)
                    card = card_map.get(cardnum, None)
                    if card:
                        action = process(Action.CardSelected(card))
                        printer("You selected %s in %s"%(card, card.zone))
                except: pass
            if action == False: printer("Invalid action")
    elif context.get("get_target", False):
        while action == False:
            txt = text_input("Select target (P# for player): ").upper()
            if not txt: action = process(Action.PassPriority())
            elif txt == "/": action = process(Action.CancelAction())
            else:
                if txt[0] == "P":
                    try:
                        pnum = int(txt[1:])
                        if pnum < len(Keeper.players):
                            action = process(Action.PlayerSelected(Keeper.players[pnum]))
                    except: pass
                else:
                    try:
                        cardnum = int(txt)
                        card = card_map.get(cardnum, None)
                        if card:
                            action = process(Action.CardSelected(card))
                            printer("You selected %s in %s"%(card, card.zone))
                    except: pass
            if action == False: printer("Invalid target")
    elif context.get("get_cards", False):
        sellist = context['list']
        numselections = context['numselections']
        required = context['required']
        from_zone = context['from_zone']
        from_player = context['from_player']
        check_card = context['check_card']
        printer("Choose from %s"%', '.join(map(str, sellist)))
    elif context.get("reveal_card", False):
        sellist = context['cards']
        from_zone = context['from_zone']
        from_player = context['from_player']
        printer.indent()
        printer("%s reveals: %s"%(from_player, ', '.join(map(str,sellist))))
        printer.unindent()
        action = True
    elif context.get("get_selection", False):
        sellist = context['list']
        numselections = context['numselections']
        required = context['required']
        msg = context['msg']
        printer.indent()
        while action is False:
            map(printer, ["%d) %s"%(o[1], o[0]) for o in sellist])
            txt = text_input(msg+":")
            if txt:
                try:
                    num = int(txt)
                    if num < len(sellist):
                        action = process(Action.SingleSelected(num))
                except:
                    pass
        printer.unindent()
    elif context.get("get_choice", False):
        msg = context['msg']
        notify = context['notify']
        if notify: msg += " (Hit enter to continue)"
        else: msg += "([Y]/N):"
        text = text_input(msg).upper()
        if notify: action = Action.OKAction()
        elif not text or text == "Y": action = Action.OKAction()
        else: action = Action.CancelAction()
    elif context.get("get_mana_choice", False):
        required = context['required']
        manapool = context['manapool']
        from_player = context['from_player']
        while action == False:
            manastr = text_input("(Required: %s) Mana to use: "%required).upper()
            if not manastr:
                action = process(Action.CancelAction())
            else:
                # Make sure it's a valid string
                try: 
                    Mana.convert_mana_string(manastr)
                    if (Mana.compare_mana(required, manastr) and 
                        Mana.subset_in_pool(manapool, manastr)):
                        action = process(Action.ManaSelected(manastr))
                except: pass
    elif context.get("get_X", False):
        from_player = context['from_player']
        prompt = "Enter X: "
        while action == False:
            text = text_input(prompt)
            if not text:
                action = Action.CancelAction()
            else:
                try:
                    amount = int(text)
                    if amount >= 0: action = Action.XSelected(amount)
                    else: prompt = "Invalid input. Enter X: "
                except:
                    prompt = "Invalid input. Enter X: "
            action = process(action)
    elif context.get("get_distribution", False):
        amount = context['amount']
        targets = context['targets']
    elif context.get("get_damage_assign", False):
        blocking_list = context['blocking_list']
        trample = context['trample']

    dump_to_replay.write(action)

    return action



def read_deckfile(filename):
    deckfile = [l.strip().split() for l in file(filename, "rU").readlines() if l.strip() and not (l[0] == "#" or l[:2] == "//")]
    decklist = [(l[0], " ".join(l[1:])) for l in deckfile if l[0] != "SB:"]
    sideboard = [(l[1], " ".join(l[2:])) for l in deckfile if l[0] == "SB:"]
    return decklist, sideboard

if __name__ == "__main__":
    global players, dump_to_replay

    conf = ConfigParser.ConfigParser()
    conf.read("data/incantus.ini")

    parser = OptionParser()
    parser.add_option("-f", "--replayfile", dest="replay_file",
                              help="Name of replay file to use", metavar="FILE")
    parser.add_option("-r", "--replay",
                              action="store_true", dest="replay", default=False,
                                                help="replay from replay file")
    parser.add_option("-s", "--continue-saving",
                              action="store_true", dest="continue_saving", default=False,
                                                help="replay game, don't continue saving")

    (options, args) = parser.parse_args()

    if not options.replay_file:
        replay_file = conf.get("general", "replay")
    else:
        replay_file = options.replay_file

    if options.replay:
        # Do replay
        dump_to_replay = replaydump.ReplayDump(filename=replay_file, save=False, continue_save=options.continue_saving)
        dump_to_replay.read()
        seed = dump_to_replay.read()
        player1 = dump_to_replay.read()
        my_deck = dump_to_replay.read()
        player2 = dump_to_replay.read()
        other_deck = dump_to_replay.read()
        input = replayInput
    else:
        dump_to_replay = replaydump.ReplayDump(filename=replay_file, save=True)
        seed = time.time()
        player1 = conf.get("main", "playername")
        player2 = conf.get("solitaire", "playername")
        my_deck, sideboard = read_deckfile(conf.get("main", "deckfile"))
        other_deck, other_sideboard = read_deckfile(conf.get("solitaire", "deckfile"))
        input = playerInput

        dump_to_replay.write(True)
        dump_to_replay.write(seed)
        for name, deck in [(player1, my_deck), (player2, other_deck)]:
            dump_to_replay.write(name)
            dump_to_replay.write(deck)

    players = [Player(player1, my_deck)
             , Player(player2, other_deck)
             ]
    random.seed(seed)
    for player in players:
        player.dirty_input = input
        replaydump.players[player.name] = player

    Keeper.init(players)
    Keeper.start()
