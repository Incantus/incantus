import random
import ConfigParser
from engine.GameKeeper import Keeper
from engine.Player import Player

def playerInput(prompt, player):
    print "** %s **"%Keeper.game_state
    while True:
        text = raw_input(player.name+": "+prompt)
        # right now return text
        task = actions.get(text, None)
        if not task: break
        else: task(player)
    return text

def list_hand(player):
    print "\n".join([c.name for c in player.hand])+"\n"

def help(player):
    print "\n".join(actions.keys())+"\n*******\n"+"\n".join(map(str,player.allowable_actions))

actions = {"list": list_hand,
           "help": help}

if __name__ == "__main__":
    random.seed()
    conf = ConfigParser.ConfigParser()
    conf.read("incantus.ini")
    player1 = self.conf.get("main", "playername")
    player2 = self.conf.get("solitaire", "playername")
    my_deck, sideboard = self.read_deckfile(self.conf.get("main", "deckfile"))
    other_deck, other_sideboard = self.read_deckfile(self.conf.get("solitaire", "deckfile"))

    players = [Player(player1, my_deck), Player(player2, other_deck)]

    for player in players:
        player.dirty_input = playerInput

    Keeper.init(players)
    Keeper.start()
