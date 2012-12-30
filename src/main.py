__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import warnings
warnings.simplefilter("ignore",DeprecationWarning) # Stop annoying DeprecationWarnings... remove this if and when we start the move to 3.x. In the meantime, too many things are reliant on 2.6 libraries and syntax.

from network import pausingreactor; pausingreactor.install() # XXX DO NOT MOVE THIS - otherwise PausableReactor won't be installed
from twisted.internet import reactor

import pyglet
from cocos.director import director
from cocos.scene import Scene

from ui import anim
from ui.menu import HierarchicalMenu, MainMenu

@director.event
def on_exit():
    reactor.stop()
    #reactor.resume()

def main():
    # Allow print statements to go to the log
    import sys
    sys.stdout = sys.stderr

    pyglet.clock.schedule(lambda dt: reactor.resume())
    pyglet.clock.schedule(anim.add_time)

    director.init(resizable=True, width=1024, height=768)
    menu_scene = Scene(HierarchicalMenu(MainMenu()))
    director.run(menu_scene)
    #win.set_icon(pyglet.image.load("./data/Incantus.png"))

if __name__ == '__main__':
    main()
