__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import pyglet

fontname = "Dumbledor 1"

import ConfigParser
config = ConfigParser.ConfigParser()
config.read("data/incantus.ini")

class ImageCache(object):
    cache = {}
    @staticmethod
    def get(key): return ImageCache.cache[key]
    @staticmethod
    def _load(filename, key):
        cache = ImageCache.cache
        value = pyglet.resource.image(filename)
        cache[key] = value
    @staticmethod
    def _load_multi(filename, labels, rows, columns):
        cache = ImageCache.cache
        multiimage = pyglet.image.ImageGrid(pyglet.resource.image(filename), rows, columns)
        for label, texture in zip(labels, multiimage):
            key = label
            cache[key] = texture
    @staticmethod
    def load_images():
        colors = ["red", "white", "black", "colorless", "green", "blue"]
        ImageCache._load_multi("mana.png", colors, 2, 3)
        status = ["exile", "graveyard", "library", "hand"]
        ImageCache._load_multi("status.png", status, 2, 2)
        ImageCache._load("life.png", "life")
        status = ['Untap','Upkeep','Draw','Main1','BeginCombat','Attack','Block','Damage','EndCombat','Main2','EndStep','Cleanup']
        ImageCache._load_multi("phases.png", status, 4, 3)
        fx = ["ring", "spiral", "targeting", "glow"]
        ImageCache._load_multi("fx.png", fx, 2, 2)

class ColorDict(object):
    def __init__(self, default=(1.0, 1.0, 1.0)):
        self.colors = dict(Black=(0.2,0.2,0.2),White=(1.,1.,1.),Red=(0.85,0.13,0.13),Green=(0.35,0.85,0.35),Blue=(0.55, 0.80, 0.90))
        self.colors[''] = (0.6, 0.6, 0.6)
        self.gold = (0.85, 0.85, 0.)
        self.default = default
    def get(self, color):
        if color in self.colors: return self.colors[color]
        else: return self.gold
            # multicolor - blend the colors
            #colors = color.split()
            #color = reduce(lambda x, y: (x[0]+y[0], x[1]+y[1], x[2]+y[2]) ,[self.colors[c] for c in colors])
            #return tuple([val/len(colors) for val in color])
        #else: return self.default
    def get_multi(self, color):
        if color in self.colors: return [self.colors[color]]
        else:
            colors = color.split()
            if len(colors) > 2: return [self.gold]
            else: return [self.colors[c] for c in colors]
