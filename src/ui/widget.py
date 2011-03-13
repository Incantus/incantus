__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet.gl import *
from pyglet import font

import anim
import euclid
from anim_euclid import AnimatedVector3, AnimatedQuaternion
from resources import ImageCache, render_9_part, fontname as global_fontname
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

class Image(Widget):
    alpha = anim.Animatable()
    width = property(fget=lambda self: self.img.width*self._final_scale)
    height = property(fget=lambda self: self.img.height*self._final_scale)

    def __init__(self,value,pos=euclid.Vector3(0,0,0)):
        super(Image,self).__init__(pos)
        if isinstance(value, str): self.img = ImageCache.get(value)
        else: self.img = value
        self.alpha = anim.animate(1.0,1.0,dt=1,method="sine")
        self.color = (1.0, 1.0, 1.0)
        self._scale = anim.animate(self._final_scale, self._final_scale, dt=0.25, method="sine")
    def render_after_transform(self):
        glColor4f(self.color[0], self.color[1], self.color[2], self.alpha)
        img = self.img
        img.blit(-img.width/2,-img.height/2,0)

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

    def __init__(self, value, size=20, color=(1,1,1,1), shadow=True, halign="left", valign="bottom", background=False, pos=euclid.Vector3(0,0,0), border=False, width=None, fontname=None):
        super(Label,self).__init__(pos)
        self._fixed_width = width
        self._value = None
        self.shadow = shadow
        self.halign = halign
        self.valign = valign
        self.background = background
        self.color = color
        self.fontname = fontname if fontname else global_fontname
        self.size = size
        self.font = font.load(self.fontname, self.size, dpi=96)
        self.visible = anim.constant(1)
        self.render_border = border
        self.border = 5
        self.set_text(value)
    def set_size(self, size):
        if not size == self.size:
            self.size = size
            self.font = font.load(self.fontname, size, dpi=96)
            self.value = self.value
    def set_text(self, v, width=None):
        if width:
            self._fixed_width = width
            if self.background: self._fixed_width -= self.border
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

        x -= border; y -= border
        w = width+2*border; h = height+2*border
        render_9_part("box2", w, h, x, y)
    def render_after_transform(self):
        if not self._value: return
        if self.background or self.render_border:
            self.render_background()
            glTranslatef(0,0,0.001)
        if self.shadow:
            self.shadow.draw()
            glTranslatef(-0.1*(self.width/(self.scale*len(self.value))), 0.1*(self.main_text.height/self.scale), 0.001)
        self.main_text.draw()
