#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import math, re, itertools
from pyglet.gl import *
import ctypes

import anim
import euclid
from anim_euclid import AnimatedVector3, AnimatedQuaternion
from widget import Label
from resources import ColorDict, ImageCache
from counter import Counter
import mtg_decoder

from engine.symbols import Creature, Land, Artifact
from engine.GameEvent import TypesModifiedEvent, TimestepEvent, PowerToughnessModifiedEvent, CounterAddedEvent, CounterRemovedEvent
from engine.pydispatch import dispatcher

#from foil import foil

sixteenfv = GLfloat*16

class Card(anim.Animable):
    def pos():
        def fget(self): return euclid.Vector3(self._pos.x, self._pos.y, self._pos.z)
        def fset(self, val):
            self._pos.x = val.x
            self._pos.y = val.y
            self._pos.z = val.z
        return locals()
    pos = property(**pos())
    def orientation():
        def fget(self): return self._orientation.copy()
        def fset(self, val):
            self._orientation.x = val.x
            self._orientation.y = val.y
            self._orientation.z = val.z
            self._orientation.w = val.w
        return locals()
    orientation = property(**orientation())
    def hidden():
        def fget(self): return self._hidden
        def fset(self, hidden):
            self._hidden = hidden
            if hidden: self._texture = self.back
            else: self._texture = self.front
        return locals()
    hidden = property(**hidden())

    size = anim.Animatable()
    visible = anim.Animatable()
    alpha = anim.Animatable()

    vertlist = None
    cardlist = None
    renderlist = None
    fbo = None

    renderwidth, renderheight = 397, 553

    def __init__(self, gamecard, front, back):
        self.gamecard = gamecard
        self.front = front
        self.back = back
        self.hidden = False
        self.width, self.height = self.front.width, self.front.height
        self.size = anim.constant(1.0) 
        self._pos = AnimatedVector3(0,0,0)
        self.pos_transition = "ease_out_circ"
        self._orientation = AnimatedQuaternion()
        self.visible = anim.constant(1.0)
        self.alpha = anim.constant(1.0)
        if not Card.cardlist: Card.cardlist = self.build_displaylist(self.width, self.height)
        #self.renderwidth, self.renderheight = 736, 1050
        #self.renderwidth, self.renderheight = 368, 525
        #self.renderwidth, self.renderheight = 397, 553
        if not Card.fbo: Card.build_fbo()
        if not Card.renderlist: Card.renderlist = self.build_renderlist(self.renderwidth, self.renderheight)

    @classmethod
    def build_fbo(cls):
        id = ctypes.c_uint()
        glGenFramebuffersEXT(1, ctypes.byref(id))
        fbo = id.value

        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, fbo)

        width, height = cls.renderwidth, cls.renderheight
        #img = pyglet.image.Texture.create(self.width, self.height, force_rectangle=True)
        img = pyglet.image.Texture.create(width, height, force_rectangle=True)
        #glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, img.target, img.id, 0);
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        
        #status = glCheckFramebufferStatusEXT(GL_FRAMEBUFFER_EXT)
        #if not status == GL_FRAMEBUFFER_COMPLETE_EXT:
        #    raise Exception()
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0);
        cls.fbo = fbo
        cls._img = img
    def del_fbo(self):
        glDeleteFramebuffersEXT(1, self.fbo)

    def render_extra(self, width, height): pass
    def render(self):
        Card._render(Card._img, self._art, self.gamecard)

    @classmethod
    def _render(cls, img, front, gamecard, tiny=False):
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, cls.fbo)
        glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, img.target, img.id, 0);
        width, height = img.width, img.height
        wf, hf = (width/397.), (height/553.)
        tiny_font = "pixelmix"
        tfont_size = 6

        #//-------------------------
        glPushAttrib(GL_VIEWPORT_BIT);
        glViewport(0, 0, width, height)
        glPushAttrib(GL_TRANSFORM_BIT);
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0.0, width, 0.0, height, -1.0, 1.0)
        
        glClearColor(0.,0.,0.,0.)
        glClear(GL_COLOR_BUFFER_BIT)
        #glClearColor(1.,1.,1.,1.)
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        cmap = dict(zip(["White", "Blue", "Black", "Red", "Green"], "WUBRG"))
        cmap1 = dict(zip("WUBRG", range(5)))
        colors = tuple(sorted([cmap[str(c)] for c in gamecard.color], key=lambda c:cmap1[c]))
        num_colors = len(colors)

        blend_color = None
        overlay_color = None
        overlay_blend = None
        final_overlay = None
        if gamecard.types == Land:
            frame = ImageCache.get_texture("frames/Land.png")
            abilities = gamecard.text.split("\n") if tiny else map(str,gamecard.abilities)
            mana = list(itertools.chain(*[re.findall("{([WUBRG])}", a) for a in abilities if "Add " in a]))
            subtypes = map(str,gamecard.subtypes)
            for t, c in (("Plains", "W"), ("Island", "U"), ("Swamp", "B"), ("Mountain", "R"), ("Forest", "G")):
                if t in subtypes and not c in mana: mana.append(c)
            num_colors = len(mana)
            if num_colors == 0: pass
            elif num_colors <= 2:
                overlay_color = mana[0]
                if num_colors == 2: 
                    overlay_blend = mana[1]
                    final_overlay = "C"
            else:
                overlay_color = "Gld"

        elif gamecard.types == Artifact:
            frame = ImageCache.get_texture("frames/Art.png")
            if num_colors == 1: overlay_color = colors[0]
            elif num_colors == 2:
                overlay_color, overlay_blend = colors
                final_overlay = "Gld"
            elif num_colors > 2:
                overlay_color = "Gld"
        else:
            if num_colors == 0:
                frame = ImageCache.get_texture("frames/C.png")
            elif num_colors == 1:
                frame = ImageCache.get_texture("frames/%s.png"%colors[0])
            else:
                frame = ImageCache.get_texture("frames/Gld.png")
                if num_colors == 2:
                    overlay_color, overlay_blend = colors
                    final_overlay = "Gld"

        #glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        #glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_FALSE)
        frame.blit(0,0, width=width, height=height)
        #glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_FALSE)
   
        def blend(texture, width, height):
            tw, th = texture.width, texture.height
            
            glEnable(texture.target)
            glBindTexture(texture.target, texture.id)
            glBegin(GL_QUADS)
            glColor4f(1., 1., 1., 1.0)
            glTexCoord2f(0.65*tw, 0)
            glVertex3f(0.65*width, 0, 0)
            glTexCoord2f(tw, 0)
            glVertex3f(width, 0, 0)
            glTexCoord2f(tw, th)
            glVertex3f(width, height, 0)
            glTexCoord2f(0.65*tw, th)
            glVertex3f(0.65*width, height, 0)

            glColor4f(1., 1., 1., 0)
            glTexCoord2f(0.35*tw, 0)
            glVertex3f(0.35*width, 0, 0)
            glColor4f(1., 1., 1., 1)
            glTexCoord2f(0.65*tw, 0)
            glVertex3f(0.65*width, 0, 0)
            glColor4f(1., 1., 1., 1)
            glTexCoord2f(0.65*tw, th)
            glVertex3f(0.65*width, height, 0)
            glColor4f(1., 1., 1., 0)
            glTexCoord2f(0.35*tw, th)
            glVertex3f(0.35*width, height, 0)

            glEnd()
            glDisable(texture.target)
            glColor4f(1., 1., 1., 1.)
        
        if blend_color:
            blend(ImageCache.get_texture("frames/%s.png"%blend_color))
        
        if overlay_color:
            t = ImageCache.get_texture("overlays/%s.png"%overlay_color)
            t.blit(0,0,width=wf*t.width,height=hf*t.height)

            if overlay_blend:
                t = ImageCache.get_texture("overlays/%s.png"%overlay_blend)
                blend(t, width=width, height=height)
        
        if final_overlay:
            t = ImageCache.get_texture("overlays/%s-overlay.png"%final_overlay)
            t.blit(0,0,width=wf*t.width,height=hf*t.height)

        # draw card image
        #glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        front.get_region(8, 125, 185, 135).blit(0.087*width, 0.4484*height, width=0.824*width, height=0.4368*height)
        #glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_FALSE)
       
        # Draw all card text first
        name = unicode(gamecard.name)
        font_name = "MatrixBold" if not tiny else tiny_font
        font_size = 0.043*width if not tiny else tfont_size
        name_label = pyglet.text.Label(name,
                          font_name=font_name, font_size=font_size,
                          color=(0,0,0,255),
                          x=0.098*width, y=0.902*height)
        supertypes = unicode(gamecard.supertypes)
        types = unicode(gamecard.types)
        subtypes = unicode(gamecard.subtypes)
        typeline = u""
        if supertypes: typeline += supertypes + " "
        typeline += types
        if subtypes: typeline += u" - %s"%subtypes
        font_size = 0.038*width if not tiny else tfont_size
        type_label = pyglet.text.Label(typeline,
                          font_name=font_name, font_size=font_size,
                          color=(0,0,0,255),
                          x=0.098*width, y=0.40*height)
        text = unicode("\n\n".join([str(a).replace("~", name) for a in list(gamecard.abilities)]))
        if not text:
            text = gamecard.text.replace('~', name).split('\n')
            text = unicode('\n'.join(text[:4]))

        if text:
            document = mtg_decoder.decode_text(text)
            font_name = "Helvetica" if not tiny else tiny_font
            font_size = 0.035*width if not tiny else tfont_size
            document.set_style(0, len(document.text),
                dict(font_name=font_name, font_size=font_size, color=(0,0,0,255)))

            #textbox = pyglet.text.layout.IncrementalTextLayout(document,
            #                  int(0.82*width), int(0.25*height),
            #                  multiline=True)

            textbox = pyglet.text.DocumentLabel(document,
                    width=0.80*width, height=0.25*height,
                    multiline=True)

            textbox.x = int(0.501*width); textbox.y = int(0.25*height)
            textbox.anchor_x = "center"; textbox.anchor_y = "center"
            textbox.content_valign = 'center'
            textbox.draw()

        for text in [name_label, type_label]:
            text.draw()

        # mana costs
        tf = 1.9 if tiny else 1
        mana_x, mana_y, diff_x = 0.883*width, 0.916*height, 0.053*width*tf
        mana = set("BCGRUWXYZ")
        for c in str(gamecard.cost)[::-1]:
            if c in mana: 
                if tiny: c = 's%s'%c
                ms = ImageCache.get(c)
                ms.blit(mana_x, mana_y,
                        width=tf*wf*ms.width, height=tf*hf*ms.height)
            else: 
                ms = ImageCache.get("C" if not tiny else "sC")
                ms.blit(mana_x, mana_y,
                        width=tf*wf*ms.width, height=tf*hf*ms.height)
                font_name = "MPlantin"# if not tiny else tiny_font
                font_size = 0.043*width*tf
                pyglet.text.Label(c,
                   font_name=font_name, font_size=font_size,
                   color=(0,0,0,255),
                   x=mana_x, y=mana_y+1,
                   anchor_x="center", anchor_y="center").draw()

            mana_x -= diff_x

        if gamecard.types == Creature:
            if num_colors == 0: 
                if gamecard.types == Artifact: pt = ImageCache.get_texture("pt/Art.png")
                else: pt = ImageCache.get_texture("pt/C.png")
            elif num_colors == 1: pt = ImageCache.get_texture("pt/%s.png"%colors[0])
            elif num_colors > 1:
                if final_overlay: col = final_overlay
                elif overlay_color: col = overlay_color
                else: col = "Gld"
                pt = ImageCache.get_texture("pt/%s.png"%col)

            pt.blit(0,0,width=wf*pt.width,height=hf*pt.height)
        
            font_name = "MatrixBoldSmallCaps" if not tiny else tiny_font
            font_size = 0.051*width if not tiny else tfont_size+1
            ptbox = pyglet.text.Label('%s/%s'%(gamecard.power, gamecard.toughness),
                              font_name=font_name, font_size=font_size,
                              color=(0,0,0,255),
                              x=0.828*width, y=0.072*height,
                              anchor_x="center", anchor_y="baseline")

            ptbox.draw()

        # expansion symbol
        exp = ImageCache.get_texture("sets/M10_C.png")
        exp.anchor_x = exp.width / 2.
        exp.anchor_y = exp.height / 2.
        exp.blit(0.866*width, 0.413*height,
                 width=tf*wf*exp.width, height=tf*hf*exp.height)

        #self.render_extra(width, height)
        
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        glPopAttrib()
        glPopAttrib()
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)
        #if not tiny: img.save("%s.png"%gamecard.name)
    def build_renderlist(self, width, height):
        renderlist = glGenLists(1)
        width, height = width/2, height/2
        glNewList(renderlist, GL_COMPILE)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex3f(-width, -height, 0)
        glTexCoord2f(width*2, 0)
        glVertex3f(width, -height, 0)
        glTexCoord2f(width*2, height*2)
        glVertex3f(width, height, 0)
        glTexCoord2f(0, height*2)
        glVertex3f(-width, height, 0)
        glEnd()
        glEndList()
        return renderlist

    def build_displaylist(self, width, height):
        cls = Card
        width, height = width/2.0, height/2.0
        vertlist = [euclid.Point3(-width, -height, 0), euclid.Point3(width, -height, 0), euclid.Point3(width, height, 0), euclid.Point3(-width, height, 0)]
        cls.vertlist = vertlist
        tc = self._texture.tex_coords
        cardlist = glGenLists(1)
        glNewList(cardlist, GL_COMPILE)
        glBegin(GL_QUADS)
        glTexCoord2f(tc[0], tc[1])
        glVertex3f(*tuple(vertlist[0]))
        glTexCoord2f(tc[3], tc[4])
        glVertex3f(*tuple(vertlist[1]))
        glTexCoord2f(tc[6], tc[7])
        glVertex3f(*tuple(vertlist[2]))
        glTexCoord2f(tc[9], tc[10])
        glVertex3f(*tuple(vertlist[3]))
        glEnd()
        glEndList()
        return cardlist
    def shake(self):
        self._pos.set_transition(dt=0.25, method=lambda t: anim.oscillate_n(t, 3))
        self.pos += euclid.Vector3(0.05, 0, 0)
    def unshake(self):
        # XXX Need to reset position transition - this is a bit hacky - I need to be able to layer animations
        self._pos.set_transition(dt=0.4, method=self.pos_transition)
    def draw(self):
        if self.visible > 0:
            size = self.size
            glPushMatrix()
            glTranslatef(self.pos.x, self.pos.y, self.pos.z)
            glMultMatrixf(sixteenfv(*tuple(self.orientation.get_matrix())))
            glScalef(size, size, 1)
            glEnable(self._texture.target)
            glBindTexture(self._texture.target, self._texture.id)
            #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST) #LINEAR)
            glColor4f(self.alpha, self.alpha, self.alpha, 1.0) #self.alpha)
            glCallList(self.cardlist)
            glDisable(self._texture.target)
            glPopMatrix()
    def intersects(self, selectRay):
        # This is the slow way
        m = euclid.Matrix4()
        m.translate(*tuple(self.pos))
        m *= self.orientation.get_matrix()
        size = self.size
        m.scale(size,size,1)
        vertlist = [m*v for v in self.vertlist]
        for i in range(1, len(vertlist)-1):
            poly = euclid.Triangle(vertlist[0], vertlist[i], vertlist[i+1])
            result = poly.intersect(selectRay)
            if result: return result
        else: return False
    def __str__(self): return str(self.gamecard)
    def __repr__(self): return repr(self.gamecard)

class HandCard(Card):
    zooming = anim.Animatable()
    def __init__(self, gamecard, front, back):
        super(HandCard, self).__init__(gamecard, front, back)
        self.zooming = 0

class StackCard(Card):
    highlighting = anim.Animatable()
    borderedlist = None
    COLORS = ColorDict()
    def __init__(self, gamecard, front, back, art, text="", style="regular"):
        super(StackCard,self).__init__(gamecard,front,back)
        self._art = art
        self.highlighting = anim.animate(0, 0, dt=0.2, method="step")
        self.size = anim.animate(self.size, self.size, dt=0.2, method="sine")
        self.alpha = anim.animate(0, 0, dt=1.0, method="ease_out_circ")
        self.style = style
        self.stackwidth, self.stackheight = 368, 414
        if self.style == "regular":
            self._texture = pyglet.image.Texture.create(self.renderwidth, self.renderheight, force_rectangle=True)
            Card._render(self._texture, self._art, self.gamecard)
        else:
            self._texture = pyglet.image.Texture.create(self.stackwidth, self.stackheight, force_rectangle=True)
            self.text = text
            self.render_special()
        if not StackCard.borderedlist: StackCard.borderedlist = self.build_renderlist(self.stackwidth, self.stackheight)
        
        #self.color = self.COLORS.get(str(gamecard.color))
        #colors = self.COLORS.get_multi(str(gamecard.color))
        #if len(colors) == 1: self.color = colors[0]
        #else:
        #    self.color = colors
        #    self.draw = self.draw_multi
        #self.bordered = bordered
        #self.border = border
        #if bordered and not StackCard.borderedlist: self.build_borderedlist()
    def build_borderedlist(self):
        cls = StackCard
        width = self.border.width/2.0; height=self.border.height/2.0
        vertlist = [euclid.Point3(-width, -height, 0), euclid.Point3(width, -height, 0), euclid.Point3(width, height, 0), euclid.Point3(-width, height, 0)]
        tc = self.border.tex_coords
        cardlist = glGenLists(1)
        cls.borderedlist = cardlist
        glNewList(cardlist, GL_COMPILE)
        glBegin(GL_QUADS)
        glTexCoord2f(tc[0], tc[1])
        glVertex3f(*tuple(vertlist[0]))
        glTexCoord2f(tc[3], tc[4])
        glVertex3f(*tuple(vertlist[1]))
        glTexCoord2f(tc[6], tc[7])
        glVertex3f(*tuple(vertlist[2]))
        glTexCoord2f(tc[9], tc[10])
        glVertex3f(*tuple(vertlist[3]))
        glEnd()
        glEndList()
    def multicolored_border(self):
        width = self.border.width/2.0; height=self.border.height/2.0
        vertlist = [euclid.Point3(-width, -height, 0), euclid.Point3(width, -height, 0), euclid.Point3(width, height, 0), euclid.Point3(-width, height, 0)]
        tc = self.border.tex_coords
        color1, color2 = self.color
        glBegin(GL_QUADS)
        glColor4f(color1[0], color1[1], color1[2], self.alpha)
        glTexCoord2f(tc[0], tc[1])
        glVertex3f(*tuple(vertlist[0]))
        glColor4f(color2[0], color2[1], color2[2], self.alpha)
        glTexCoord2f(tc[3], tc[4])
        glVertex3f(*tuple(vertlist[1]))
        glColor4f(color2[0], color2[1], color2[2], self.alpha)
        glTexCoord2f(tc[6], tc[7])
        glVertex3f(*tuple(vertlist[2]))
        glColor4f(color1[0], color1[1], color1[2], self.alpha)
        glTexCoord2f(tc[9], tc[10])
        glVertex3f(*tuple(vertlist[3]))
        glEnd()
    def render_special(self):
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.fbo)
        img = self._texture
        glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, img.target, img.id, 0);

        width, height = self.stackwidth, self.stackheight
        #//-------------------------
        glPushAttrib(GL_VIEWPORT_BIT);
        glViewport(0, 0, width, height)
        glPushAttrib(GL_TRANSFORM_BIT);
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0.0, width, 0.0, height, -1.0, 1.0)
        
        glClearColor(1.,1.,1.,1.)
        glClear(GL_COLOR_BUFFER_BIT)

        # draw card image
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glColor4f(1., 1., 1., 1.0)
        #art = self.front.get_region(8, 125, 185, 135)
        #art.blit(0.054*width, 0.2428*height, width=0.889*width, height=0.5857*height)
       
        blend_frac = 0.5
        blend_y = blend_frac*135
        artsolid = self._art.get_region(8, 125+blend_y, 185, 135-blend_y)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        artsolid.blit(0.054*width, 0.54564*height, width=0.889*width, height=(0.5857*height)*blend_frac)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_FALSE)

        artfade = self._art.get_region(8, 125, 185, blend_y)
    
        tc = artfade.tex_coords
        glEnable(artfade.target)
        glBindTexture(artfade.target, artfade.id)
        glBegin(GL_QUADS)
        glColor4f(1., 1., 1., 0.0)
        glTexCoord2f(tc[0], tc[1])
        glVertex3f(0.054*width, 0.2428*height, 0)
        glTexCoord2f(tc[3], tc[4])
        glVertex3f(0.943*width, 0.2428*height, 0)
        glColor4f(1., 1., 1., 1.0)
        glTexCoord2f(tc[6], tc[7])
        glVertex3f(0.943*width, 0.54564*height, 0) 
        glTexCoord2f(tc[9], tc[10])
        glVertex3f(0.054*width, 0.54564*height, 0)
        glEnd()
        glDisable(artfade.target)

        x, y, x2, y2 = 20, 44, 345, 152
        glBegin(GL_QUADS)
        glColor4f(1., 1., 1., 1.0)
        glVertex3f(x, y, 0)
        glVertex3f(x2, y, 0)
        glColor4f(1., 1., 1., 0.0)
        glVertex3f(x2, y2, 0)
        glVertex3f(x, y2, 0)
        glEnd()

        glColor4f(1., 1., 1., 1.)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        ImageCache.get_texture("frames/Gld-stack.png").blit(0,0)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_FALSE)

        name = str(self.gamecard.name)
        header = "%s ability of\n%s"%(self.style.capitalize(), name)
        document = pyglet.text.decode_text(header)
        document.set_style(0, len(document.text), dict(font_name="MatrixBold",
                          font_size=0.047*width, leading=0, color=(0,0,0,255)))
        namebox = pyglet.text.DocumentLabel(document, multiline=True,
                          width = width*0.85,
                          x = width/2.05, y=0.91*height,
                          anchor_x="center", anchor_y="baseline")

        document = mtg_decoder.decode_text(self.text.replace('~', name))
        document.set_style(0, len(document.text), dict(bold=True, font_name="MPlantin", font_size=0.0353*width, color=(0,0,0,255)))
        textbox = pyglet.text.DocumentLabel(document,
                              multiline=True, width=width*0.85,
                              x=width/2, y=height*.23,
                              anchor_x="center", anchor_y="center")

        for text in [namebox, textbox]:
            text.draw()
        
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        glPopAttrib()
        glPopAttrib()
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)
        #img.save("%s_ability.png"%self.gamecard.name)
    def highlight(self):
        if self.highlighting == 0:
            self.highlighting = anim.animate(0,1,dt=0.75)
            #self.old_size = self.size
            self.size = anim.animate(self.size,1.5*self.size,dt=0.5,method="oscillate", extend="repeat")
    def unhighlight(self):
        self.highlighting = 0.0
        self.size = anim.animate(self.size, self.size, dt=0.2, method="sine")
    def draw(self):
        if self.visible > 0:
            size = self.size
            glPushMatrix()
            glTranslatef(self.pos.x, self.pos.y, self.pos.z)
            glMultMatrixf(sixteenfv(*tuple(self.orientation.get_matrix())))
            glScalef(size, size, 1)
            glEnable(self._texture.target)
            glBindTexture(self._texture.target, self._texture.id)
            glColor4f(1, 1, 1, self.alpha)
            if self.style == "regular": glCallList(self.renderlist)
            else: glCallList(self.borderedlist)
            #if self.bordered:
            #    color = self.color
            #    glBindTexture(self.border.target, self.border.id)
            #    glColor4f(color[0], color[1], color[2], self.alpha)
            #    glCallList(self.borderedlist)
            glDisable(self._texture.target)
            glPopMatrix()
    def draw_multi(self):
        if self.visible > 0:
            size = self.size
            glPushMatrix()
            glTranslatef(self.pos.x, self.pos.y, self.pos.z)
            glMultMatrixf(sixteenfv(*tuple(self.orientation.get_matrix())))
            glScalef(size, size, 1)
            glEnable(self._texture.target)
            glBindTexture(self._texture.target, self._texture.id)
            glColor4f(1, 1, 1, self.alpha)
            glCallList(self.cardlist)
            if self.bordered:
                glBindTexture(self.border.target, self.border.id)
                self.multicolored_border()
            glDisable(self._texture.target)
            glPopMatrix()

class PlayCard(Card):
    tapping = anim.Animatable()
    zooming = anim.Animatable()
    highlighting = anim.Animatable()
    def spacing():
        def fget(self):
            if self.is_tapped: return self.height
            else: return self.width
        return locals()
    spacing = property(**spacing())

    def __init__(self, gamecard, front, back):
        super(PlayCard, self).__init__(gamecard, front, back)
        self.is_creature = False
        self.draw = self.draw_permanent
        #self.info_box = Label("", size=12, background=True, shadow=False, valign="top")
        #self.info_box._pos.set_transition(dt=0.4, method="sine")
        #self.info_box.pos = euclid.Vector3(self.width/2+self.info_box.border, self.height/2-self.info_box.border, 0.005)
        #self.info_box.visible = False
    def type_modified(self, sender):
        is_creature = self.gamecard.types == Creature
        if is_creature and not self.is_creature:
            self.setup_creature_role()
        elif not is_creature and self.is_creature:
            self.remove_creature_role()
    def setup_creature_role(self):
        self.is_creature = True
        gamecard = self.gamecard
        self.power = 0 #gamecard.power
        self.toughness = 0 #gamecard.toughness
        self.damage = 0 #gamecard.currentDamage()
        #dispatcher.connect(self.change_value, signal=PowerToughnessModifiedEvent(), sender=gamecard)
        # XXX This will lead to a lot of events each time priority is passed
        # but I'm not sure how to do it otherwise for cards like "Coat of Arms", which use a lambda function
        # or for damage
        self.text = Label("", size=34, background=True, shadow=False, halign="center", valign="center")
        #self.text._scale = anim.animate(0, 2.0, dt=0.25, method="sine")
        self.text.scale = 2.0
        #self.text._pos.set(euclid.Vector3(0,0,0)) #_transition(dt=0.25, method="sine")
        self.text.orig_pos = euclid.Vector3(0,-self.height*0.25,0.001)
        self.text.zoom_pos = euclid.Vector3(self.width*1.375,-self.height*0.454, 0.01)
        self.text.pos = self.text.orig_pos
        #self.damage_text = Label("", size=34, background=True, shadow=False, halign="center", valign="center", color=(1., 0., 0., 1.))
        #self.damage_text._scale = anim.animate(0.0, 0.0, dt=0.25, method="sine")
        #self.damage_text.scale = 0.4
        #self.damage_text.visible = 0
        #self.damage_text._pos.set(euclid.Vector3(0,0,0)) #_transition(dt=0.25, method="sine")
        #self.damage_text.zoom_pos = euclid.Vector3(self.width*(1-.375),-self.height*0.454, 0.01)
        #self.damage_text.pos = self.damage_text.zoom_pos
        self.change_value()
        self.draw = self.draw_creature
        dispatcher.connect(self.change_value, signal=TimestepEvent())
    def remove_creature_role(self):
        self.is_creature = False
        self.draw = self.draw_permanent
        dispatcher.disconnect(self.change_value, signal=TimestepEvent())
    def entering_play(self):
        self.is_tapped = False
        self.tapping = anim.animate(0, 0, dt=0.3)
        self.highlighting = anim.animate(0, 0, dt=0.2)
        self.zooming = anim.animate(0, 0, dt=0.2)
        self.pos_transition = "ease_out_circ" #"ease_out_back"
        self._pos.set_transition(dt=0.4, method=self.pos_transition)
        #self._pos.y = anim.animate(guicard._pos.y, guicard._pos.y, dt=0.4, method="ease_out")
        self._orientation.set_transition(dt=0.3, method="sine")
        self.can_layout = True
        if self.gamecard.types == Creature: self.setup_creature_role()
        # Check for counters
        dispatcher.connect(self.add_counter, signal=CounterAddedEvent(), sender=self.gamecard)
        dispatcher.connect(self.remove_counter, signal=CounterRemovedEvent(), sender=self.gamecard)
        dispatcher.connect(self.type_modified, signal=TypesModifiedEvent(), sender=self.gamecard)
        self.counters = [Counter(counter.ctype) for counter in self.gamecard.counters]
        self.layout_counters()
    def leaving_play(self):
        if self.is_creature:
            self.remove_creature_role()
        dispatcher.disconnect(self.add_counter, signal=CounterAddedEvent(), sender=self.gamecard)
        dispatcher.disconnect(self.remove_counter, signal=CounterRemovedEvent(), sender=self.gamecard)
        dispatcher.disconnect(self.type_modified, signal=TypesModifiedEvent(), sender=self.gamecard)
    def layout_counters(self):
        numc = len(self.counters)
        if numc > 0:
            spacing = self.counters[0].radius*2.2
            y = self.height/4
            max_per_row = int(self.width/spacing)
            num_rows = int(math.ceil(float(numc)/max_per_row))
            x = -spacing*(max_per_row-1)*0.5
            row = j = 0
            for counter in self.counters:
                counter.pos = euclid.Vector3(x+j*spacing, y-row*spacing, counter.height/2)
                j += 1
                if j == max_per_row:
                    j = 0
                    row += 1
                    if row == num_rows-1:
                        num_per_row = numc%max_per_row
                        if num_per_row ==0: num_per_row = max_per_row
                        x = -spacing*(num_per_row-1)*0.5
    def add_counter(self, counter):
        self.counters.append(Counter(counter.ctype))
        self.layout_counters()
    def remove_counter(self, counter):
        for c in self.counters:
            if c.ctype == counter.ctype:
                break
        else: raise Exception
        self.counters.remove(c)
        self.layout_counters()
    def change_value(self):
        p, t = self.gamecard.power, self.gamecard.toughness
        d = self.gamecard.currentDamage()
        if not (self.power == p and self.toughness == t and self.damage == d):
            self.power, self.toughness, self.damage = p, t, d
            self.text.set_text("%d/%d"%(p, t-d))
            #if d > 0: self.damage_text.set_text("-%d"%d)
            #else: self.damage_text.set_text("")
    def tap(self):
        if self.tapping == 0.0:
            self.is_tapped = True
            self.tapping = 1.0 #anim.animate(0, 1, dt=0.3)
            self.untapped_orientation = self.orientation
            self.orientation *= euclid.Quaternion.new_rotate_axis(math.pi/2, euclid.Vector3(0,0,-1))
    def untap(self):
        self.is_tapped = False
        self.orientation = self.untapped_orientation
        self.tapping = 0.0
    def flash(self):
        self.highlighting = anim.animate(1,0,dt=0.75, method="step")
        self.highlight_alpha = anim.animate(0.0, 0.8, dt=0.75, method="oscillate")
    def select(self):
        self.highlighting = 1.0
        self.highlight_alpha = anim.animate(0., 1., dt=0.2, method="linear")
    def deselect(self):
        self.highlighting = 0.0
    def highlight(self):
        if self.highlighting == 0:
            self.highlighting = anim.animate(0,1,dt=0.75)
            self.old_pos = self.pos
            self.pos += euclid.Vector3(0,3,0)
            self.highlight_alpha = anim.animate(0.0, 0.8, dt=1, method="oscillate", extend="repeat")
            #self.old_size = self.size
            #self.size = anim.animate(self.size,1.05*self.size,dt=2.0,method="oscillate", extend="repeat")
    def unhighlight(self):
        self.highlighting = 0.0
        self.pos = self.old_pos
        #self.size = anim.animate(self.old_size, self.old_size, dt=0.2, method="sine")
    def shake(self):
        self._pos.set_transition(dt=0.25, method=lambda t: anim.oscillate_n(t, 3))
        self.pos += euclid.Vector3(0.05, 0, 0)
    def unshake(self):
        # XXX Need to reset position transition - this is a bit hacky - I need to be able to layer animations
        self._pos.set_transition(dt=0.4, method=self.pos_transition)
    def zoom_to_camera(self, camera, z, size=0.02, show_info = True, offset = euclid.Vector3(0,0,0)):
        if self.zooming == 0.0:
            self._texture = self._img
            self._old_list, self.cardlist = self.cardlist, self.renderlist
            self.zooming = 1.0
            self.old_pos = self.pos
            self._pos.set_transition(dt=0.2, method="ease_out") #self.pos_transition)
            #self._pos.y = anim.animate(self._pos.y, self._pos.y, dt=0.4, method="sine")
            #self._orientation.set_transition(dt=0.5, method="sine")
            if show_info: offset = offset + euclid.Vector3(-self.width*size/2, 0, 0)
            self.pos = camera.pos - camera.orientation*euclid.Vector3(0,0,camera.vis_distance) - euclid.Vector3(0,0,z) + offset
            self.orig_orientation = self.orientation
            
            new_orient = camera.orientation
            if self.is_tapped: new_orient *= euclid.Quaternion.new_rotate_axis(math.pi/10, euclid.Vector3(0,0,-1)) 
            self.orientation = new_orient
            self.old_size = self.size
            self.size = size*0.7
            if self.is_creature:
                self.text.visible = False
                self.text.set_text("%d/%d"%(self.power, self.toughness))
                self.text.pos = self.text.zoom_pos
                self.text.scale = 0.4
                #self.damage_text.visible = True
            #if show_info:
            #    self.info_box.visible = True
            #    self.info_box.set_text('\n'.join(self.gamecard.info.split("\n")[:17]), width=self.width)
            #    self.info_box._height = self.height-self.info_box.border
            #else: self.info_box.visible = False
    def restore_pos(self):
        self.zooming = 0.0 #anim.animate(self.zooming, 0.0, dt=0.2)
        self._texture = self.front
        self.cardlist = self._old_list
        self._pos.set_transition(dt=0.4, method=self.pos_transition)
        #self._pos.y = anim.animate(self._pos.y, self._pos.y, dt=0.4, method="sine")
        # XXX old self._pos.set_transition(dt=0.2, method="ease_out_circ")
        #self._orientation.set_transition(dt=0.3, method="sine")
        self.pos = self.old_pos
        self.orientation = self.orig_orientation
        self.size = self.old_size
        if self.is_creature:
            self.text.visible = True
            self.text.set_text("%d/%d"%(self.power, self.toughness - self.damage))
            self.text.pos = self.text.orig_pos
            self.text.scale = 2.0
            #self.damage_text.scale = 0.4
            #self.damage_text.pos = self.damage_text.zoom_pos
            #self.damage_text.visible = 0.0
        #self.info_box.visible = False
    def render_extra(self, width, height):
        if hasattr(self, "damage") and self.damage != 0:
            ImageCache.get_texture("overlays/damage.png").blit(0.59*width,-0.01*height)
            pyglet.text.Label("%d"%self.damage, 
                              #font_name="MPlantin",
                              font_size=0.073*width,
                              x = 0.69*width, y = 0.073*height,
                              anchor_x="center", anchor_y="center").draw()
    def draw_permanent(self):
        if self.visible > 0:
            size = self.size
            glPushMatrix()
            if self.highlighting != 0:
                glPushMatrix()
                glTranslatef(self.pos.x, self.pos.y-0.0005, self.pos.z)
                glMultMatrixf(sixteenfv(*tuple(self.orientation.get_matrix())))
                glScalef(size*1.1, size*1.1, size*1.1)
                glColor4f(1.0, 1.0, 1.0, self.highlight_alpha.get())
                glCallList(self.cardlist)
                glPopMatrix()
            glTranslatef(self.pos.x, self.pos.y, self.pos.z)
            glMultMatrixf(sixteenfv(*tuple(self.orientation.get_matrix())))
            #glScalef(size, size, size)
            glScalef(size, size, 1)
            glEnable(self._texture.target)
            glBindTexture(self._texture.target, self._texture.id)
            glColor4f(self.alpha, self.alpha, self.alpha, self.alpha)
            #foil.install()
            glCallList(self.cardlist)
            #foil.uninstall()
            #self.info_box.render()
            glDisable(self._texture.target)
            for c in self.counters: c.draw()
            glPopMatrix()
    def draw_creature(self):
        if self.visible > 0:
            size = self.size
            glPushMatrix()
            if self.highlighting:
                glPushMatrix()
                glTranslatef(self.pos.x, self.pos.y-0.0005, self.pos.z)
                glMultMatrixf(sixteenfv(*tuple(self.orientation.get_matrix())))
                glScalef(size*1.1, size*1.1, size*1.1)
                #glScalef(size*1.1, size*1.1, 1)
                glColor4f(1.0, 1.0, 1.0, self.highlight_alpha.get())
                glCallList(self.cardlist)
                glPopMatrix()
            glTranslatef(self.pos.x, self.pos.y, self.pos.z)
            glMultMatrixf(sixteenfv(*tuple(self.orientation.get_matrix())))
            #glScalef(size, size, size)
            glScalef(size, size, 1)
            glEnable(self._texture.target)
            glBindTexture(self._texture.target, self._texture.id)
            glColor4f(self.alpha, self.alpha, self.alpha, self.alpha)
            glCallList(self.cardlist)
            #self.info_box.render()
            #self.text.render()
            #self.damage_text.render()
            glDisable(self._texture.target)
            for c in self.counters: c.draw()
            glPopMatrix()
