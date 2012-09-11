__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet import resource, font, image
from pyglet.gl import *

fontname = "Dumbledor 1"
fontname = "MPlantin"
fontname = "Arial"

import ConfigParser
config = ConfigParser.ConfigParser()
config.read("data/incantus.ini")

resource.path.append("./data/images")
resource.path.append("./data/compositing")
resource.path.append("./data/avatars")
resource.path.append("./data/images/fx")
font.add_file("./data/fonts/dum1.ttf")
font.add_file("./data/fonts/MPlantin.ttf")
font.add_file("./data/fonts/MPlantinI.ttf")
font.add_file("./data/fonts/MatrixB.ttf")
font.add_file("./data/fonts/MatrixBSmallCaps.ttf")
font.add_file("./data/fonts/Pixelmix.ttf")

resource.reindex()

class ImageCache(object):
    cache = {}
    @staticmethod
    def get(key): return ImageCache.cache.get(key,None)
    @staticmethod
    def _load(filename, key, anchor=False):
        cache = ImageCache.cache
        value = resource.image(filename)
        if anchor:
            value.anchor_x = value.width / 2
            value.anchor_y = value.height / 2
        cache[key] = value
    @staticmethod
    def _load_multi(filename, labels, rows, columns, anchor=False):
        cache = ImageCache.cache
        multiimage = image.ImageGrid(resource.image(filename), rows, columns)
        for key, texture in zip(labels, multiimage):
            if anchor:
                texture.anchor_x = texture.width / 2
                texture.anchor_y = texture.height / 2
            cache[key] = texture
    @staticmethod
    def load_images():
        colors = ["red", "white", "black", "colorless", "green", "blue"]
        ImageCache._load_multi("mana/cmana.png", "BCGRUWXYZ", 3, 3, anchor=True)
        ImageCache._load_multi("text_symbols.png", map(lambda l: 's'+l, 'BCGQRTUWXYZ '), 4, 3, anchor=True)
        #status = ["exile", "graveyard", "library", "hand"]
        status = ["graveyard", "exile", "hand", "library"]
        ImageCache._load_multi("status1.png", status, 2, 2)
        ImageCache._load("life.png", "life")
        ImageCache._load("9partbox1.png", "box1")
        ImageCache._load("9partbox2.png", "box2")
        ImageCache._load("9partbox3.png", "box3")
        ImageCache._load("9partbox4.png", "box4")
        ImageCache._load("9partbox5.png", "box5")
        ImageCache._load("9partbox6.png", "box6")
        ImageCache._load("button1.png", "button1")
        ImageCache._load("button2.png", "button2")
        ImageCache._load("button3.png", "button3")
        status = ['Untap','Upkeep','Draw','Main1','BeginCombat','Attack','Block','Damage','EndCombat','Main2','EndStep','Cleanup']
        ImageCache._load_multi("phases.png", status, 4, 3)
        fx = ["ring", "spiral", "targeting", "glow"]
        ImageCache._load_multi("fx.png", fx, 2, 2)
    @staticmethod
    def get_texture(fname):
        cache = ImageCache.cache
        tex = cache.get(fname, None)
        if not tex:
            tex = resource.image(fname).texture
            ImageCache.cache[fname] = tex
        return tex

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

def render_9_part(name, width, height, x=0, y=0, xs=None, ys=None):
    texture = ImageCache.get(name)
    w, h = float(texture.width), float(texture.height)
    if xs == None: x_1, x_2 = w/2., w/2.
    else: x_1, x_2 = xs
    if ys == None: y_1, y_2 = h/2., h/2.
    else: y_1, y_2 = ys

    x0, x1, x2, x3 = x+0, x+x_1, x+width-x_2, x+width
    y0, y1, y2, y3 = y+0, y+y_1, y+height-y_2, y+height

    tc = texture.tex_coords
    tx0, tx3, ty0, ty3 = tc[0], tc[3], tc[1], tc[7]
    tx1, tx2, ty1, ty2 = (x_1*(tx3-tx0)/w+tx0), (x_2*(tx3-tx0)/w+tx0), (y_1*(ty3-ty0)/h+ty0), (y_2*(ty3-ty0)/h+ty0)

    #print tc, width, height, w, h, x_1, x_2, y_1, y_2
    #print tx0, tx1, tx2, tx3
    #print ty0, ty1, ty2, ty3
    rounded_array = (
        # Top left
        tx0, ty2, 0,  1,  x0,  y2,  0,  1,
        tx1, ty2, 0,  1,  x1,  y2,  0,  1,
        tx1, ty3, 0,  1,  x1,  y3,  0,  1,
        tx0, ty3, 0,  1,  x0,  y3,  0,  1,
        # Top stretch
        tx1, ty2, 0,  1,  x1,  y2,  0,  1,
        tx2, ty2, 0,  1,  x2,  y2,  0,  1,
        tx2, ty3, 0,  1,  x2,  y3,  0,  1,
        tx1, ty3, 0,  1,  x1,  y3,  0,  1,
        # Top right
        tx2, ty2, 0,  1,  x2,  y2,  0,  1,
        tx3, ty2, 0,  1,  x3,  y2,  0,  1,
        tx3, ty3, 0,  1,  x3,  y3,  0,  1,
        tx2, ty3, 0,  1,  x2,  y3,  0,  1,
        # Middle left
        tx0, ty1, 0,  1,  x0,  y1,  0,  1,
        tx1, ty1, 0,  1,  x1,  y1,  0,  1,
        tx1, ty2, 0,  1,  x1,  y2,  0,  1,
        tx0, ty2, 0,  1,  x0,  y2,  0,  1,
        # Middle stretch
        tx1, ty1, 0,  1,  x1,  y1,  0,  1,
        tx2, ty1, 0,  1,  x2,  y1,  0,  1,
        tx2, ty2, 0,  1,  x2,  y2,  0,  1,
        tx1, ty2, 0,  1,  x1,  y2,  0,  1,
        # Middle right
        tx2, ty1, 0,  1,  x2,  y1,  0,  1,
        tx3, ty1, 0,  1,  x3,  y1,  0,  1,
        tx3, ty2, 0,  1,  x3,  y2,  0,  1,
        tx2, ty2, 0,  1,  x2,  y2,  0,  1,
        # Bottom left
        tx0, ty0, 0,  1,  x0,  y0,  0,  1,
        tx1, ty0, 0,  1,  x1,  y0,  0,  1,
        tx1, ty1, 0,  1,  x1,  y1,  0,  1,
        tx0, ty1, 0,  1,  x0,  y1,  0,  1,
        # Bottom stretch
        tx1, ty0, 0,  1,  x1,  y0,  0,  1,
        tx2, ty0, 0,  1,  x2,  y0,  0,  1,
        tx2, ty1, 0,  1,  x2,  y1,  0,  1,
        tx1, ty1, 0,  1,  x1,  y1,  0,  1,
        # Bottom right
        tx2, ty0, 0,  1,  x2,  y0,  0,  1,
        tx3, ty0, 0,  1,  x3,  y0,  0,  1,
        tx3, ty1, 0,  1,  x3,  y1,  0,  1,
        tx2, ty1, 0,  1,  x2,  y1,  0,  1)
    glPushAttrib(GL_ENABLE_BIT)
    glEnable(texture.target)
    glBindTexture(texture.target, texture.id)

    glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
    glInterleavedArrays(GL_T4F_V4F, 0, (GLfloat*len(rounded_array))(*rounded_array))
    glDrawArrays(GL_QUADS, 0, 4*9)
    glPopClientAttrib()
    glPopAttrib()
