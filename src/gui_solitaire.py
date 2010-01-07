#!/usr/bin/python -O
__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from network import pausingreactor; pausingreactor.install() # XXX DO NOT MOVE THIS - otherwise PausableReactor won't be installed
from twisted.internet import reactor

import pyglet
#from pyglet.resource import *
from cocos.director import director
from cocos.scene import Scene

from ui import anim
from ui.resources import config

@director.event
def on_exit():
    reactor.stop()
    reactor.resume()

from ui.Incantus import IncantusLayer, load_deckfile
from ui.resources import config

def start_solitaire():
    gamescene = Scene()
    gamelayer = IncantusLayer()
    p1_name = config.get("main", "playername")
    p2_name = config.get("solitaire", "playername")
    p1_deckfile = config.get("main", "deckfile")
    p2_deckfile = config.get("solitaire", "deckfile") 
    players = [(p1_name, load_deckfile(p1_deckfile)), (p2_name, load_deckfile(p2_deckfile))]
    gamescene.add(gamelayer, z=0, name="table")
    gamelayer.game_start(p1_name, pyglet.clock.time.time(), players, None)
    return gamescene

def main():
    pyglet.clock.schedule(lambda dt: reactor.resume())
    pyglet.clock.schedule(anim.add_time)

    director.init(resizable=True, width=1024, height=768)
    director.run(start_solitaire())
    #win.set_icon(pyglet.image.load("./data/Incantus.png"))

if __name__ == '__main__':
    main()
