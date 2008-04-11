__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet.gl import *
from pyglet import image
from pyglet import font

import math
import anim
import euclid
from anim_euclid import AnimatedVector3, AnimatedQuaternion

font.add_directory("./data/fonts")
#fontlist = ["Vinque", "Moderna", "Legrand MF", "Grange MF", "Cry Uncial", "BoisterBlack", "Aniron", "Thaleia", "AlfredDrake"]
fontname = "Dumbledor 1 Thin" #"Legrand MF" #"Dumbledor 1" #Grantham Roman" #Legrand MF"
fontincr = 5 #0 # 5

class ImageCache(object):
    cache = {}
    @staticmethod
    def get(key): return ImageCache.cache[key]
    @staticmethod
    def _load(filename, path, key):
        cache = ImageCache.cache
        value = image.load(path+filename)
        cache[key] = value
    @staticmethod
    def _load_multi(filename, path, labels, rows, columns):
        cache = ImageCache.cache
        multiimage = image.ImageGrid(image.load(path+filename), rows, columns)#.texture_sequence
        for label, texture in zip(labels, multiimage):
            key = label
            cache[key] = texture
    @staticmethod
    def load_images():
        path = "./data/images/"
        colors = ["red", "white", "black", "colorless", "green", "blue"]
        ImageCache._load_multi("mana.png", path, colors, 2, 3)
        status = ["removed", "graveyard", "library", "hand"]
        ImageCache._load_multi("status.png", path, status, 2, 2)
        ImageCache._load("life.png", path, "life")
        status = ['Untap','Upkeep','Draw','Main1','PreCombat','Attack','Block','Damage','EndCombat','Main2','EndPhase','Cleanup']
        ImageCache._load_multi("phases.png", path, status, 4, 3)
        path = "./data/images/fx/"
        for key in ["ring", "glow", "star", "targeting"]:
            ImageCache._load(key+".png", path, key)

class Widget(anim.Animable):
    def pos():
        def fget(self): return euclid.Vector3(self._pos.x, self._pos.y, self._pos.z)
        def fset(self, val):
            self._pos.x = val.x
            self._pos.y = val.y
            self._pos.z = val.z
        return locals()
    pos = property(**pos())
    visible = anim.Animatable()
    rotatex = anim.Animatable()
    rotatey = anim.Animatable()
    rotatez = anim.Animatable()
    _scale = anim.Animatable()
    def scale():
        def fget(self): return self._scale
        def fset(self, value):
            if isinstance(value, anim.Animator): self._final_scale = value.final()
            else: self._final_scale = value
            self._scale = value
        return locals()
    scale = property(**scale())

    def __init__(self, pos=euclid.Vector3(0,0,0)):
        self._pos = AnimatedVector3(pos)
        self._pos.set_transition(dt=0.5, method="linear")
        self.orig_pos = pos
        self.visible = anim.animate(0, 1, dt=1.0)
        self.rotatex = anim.animate(0,0,dt=1.0)
        self.rotatey = anim.animate(0,0,dt=1.0)
        self.rotatez = anim.animate(0,0,dt=1.0)
        self._final_scale = 1.0
        self._scale = anim.animate(self._final_scale, self._final_scale, dt=0.25, method="linear")
    def show(self):
        self.visible = 1.0
    def hide(self):
        self.visible = 0.0
    def render(self):
        if self.visible > 0:
            glPushMatrix()
            glTranslatef(self.pos.x, self.pos.y, self.pos.z)
            glRotatef(self.rotatex, 1, 0, 0)
            glRotatef(self.rotatey, 0, 1, 0)
            glRotatef(self.rotatez, 0, 0, 1)
            glScalef(self.scale, self.scale, self.scale)
            self.render_after_transform()
            glPopMatrix()
    #def render_after_transform(self): pass

class Image(Widget):
    alpha = anim.Animatable()
    width = property(fget=lambda self: self.img.width*self._final_scale)
    height = property(fget=lambda self: self.img.height*self._final_scale)

    def __init__(self,value,pos=euclid.Vector3(0,0,0)):
        super(Image,self).__init__(pos)
        if type(value) == str: self.img = ImageCache.get(value)
        else: self.img = value
        self.alpha = anim.animate(1.0,1.0,dt=1,method="sine")
        self.color = (1.0, 1.0, 1.0)
        self._pos.set_transition(dt=0.5, method="ease_out_back")
        self._scale = anim.animate(self._final_scale, self._final_scale, dt=0.25, method="sine")
        #width, height = self.img.width, self.img.height
        #self.vertlist = [euclid.Point3(-width / 2.0, -height / 2.0, 0), euclid.Point3(width / 2.0, -height / 2.0, 0), euclid.Point3(width / 2.0, height / 2.0, 0), euclid.Point3(-width / 2.0, height / 2.0, 0)]
    def render_after_transform(self):
        glColor4f(self.color[0], self.color[1], self.color[2], self.alpha)
        img = self.img
        img.blit(-img.width/2,-img.height/2,0)
        #tc = self.img.tex_coords
        #vertlist = self.vertlist
        #glBindTexture(self.img.target, self.img.id)
        #glBegin(GL_QUADS)
        #glTexCoord2f(tc[0], tc[1]); glVertex3f(*tuple(vertlist[0]))
        #glTexCoord2f(tc[3], tc[4]); glVertex3f(*tuple(vertlist[1]))
        #glTexCoord2f(tc[6], tc[7]); glVertex3f(*tuple(vertlist[2]))
        #glTexCoord2f(tc[9], tc[10]); glVertex3f(*tuple(vertlist[3]))
        #glEnd()

class Label(Widget):
    width = property(fget=lambda self: self._width*self._final_scale)
    height = property(fget=lambda self: self._height*self._final_scale)
    def value():
        def fget(self): return self._value
        def fset(self, value):
            self._value = value
            if self.shadow: self.shadow = font.Text(self.font, text=str(value), color=(0,0,0,1), width=self._fixed_width, halign=self.halign, valign=self.valign)
            self.main_text = font.Text(self.font, text=str(value), color=self.color, width=self._fixed_width, halign=self.halign, valign=self.valign)
            self._width, self._height = self.main_text.width, self.main_text.height
        return locals()
    value = property(**value())

    def __init__(self, value, size=20, color=(1,1,1,1), shadow=True, halign="left", valign="bottom", background=False, pos=euclid.Vector3(0,0,0), width=None):
        super(Label,self).__init__(pos)
        self._fixed_width = width
        self._value = None
        self.shadow = shadow
        self.halign = halign
        self.valign = valign
        self.background = background
        self.color = color
        self.fontname = fontname
        self.size = size+fontincr
        self.font = font.load(fontname, self.size, dpi=96)
        self._pos.set_transition(dt=0.5, method="ease_out_back")
        self.visible = anim.constant(1)
        self.border = 0
        self.set_text(value)
    def set_size(self, size):
        if not size == self.size:
            self.size = size
            self.font = font.load(fontname, size, dpi=96)
            self.value = self.value
    def set_text(self, v, width=None):
        self._fixed_width = width
        if width and self.background: self._fixed_width -= self.border
        v = str(v)
        if not v == self.value: self.value = v
    def render_background(self):
        scale = self.scale
        width, height, border = self.width/scale, self.height/scale, self.border/scale
        x = y = 0
        if self.halign == "right": x = -width
        elif self.halign == "center": x = -width/2
        if self.valign == "top": y = -height
        elif self.valign == "center": y = -height/2
        glColor4f(0.1, 0.1, 0.1, 0.8)
        glDisable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glVertex2f(x-border,y-border)
        glVertex2f(x+width+border,y-border)
        glVertex2f(x+width+border,y+height+border)
        glVertex2f(x-border,y+height+border)
        glEnd()
        glEnable(GL_TEXTURE_2D)
    def render_after_transform(self):
        if not self._value: return
        if self.background:
            self.render_background()
            glTranslatef(0,0,0.001)
        if self.shadow:
            self.shadow.draw()
            glTranslatef(-0.1*(self.width/(self.scale*len(self.value))), 0.1*(self.main_text.line_height/self.scale), 0.001)
        self.main_text.draw()
