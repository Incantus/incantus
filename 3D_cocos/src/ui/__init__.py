
import pyglet
pyglet.resource.path.append("./data/images")
pyglet.resource.path.append("./data/images/fx")
pyglet.font.add_file("./data/fonts/dum1.ttf")
pyglet.resource.reindex()

from resources import ImageCache
ImageCache.load_images()

import CardLibrary
