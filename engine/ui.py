
from GameKeeper import Keeper

def playerInput(prompt, player):
    yield None

def playerInput1(prompt,player):
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

