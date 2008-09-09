#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import math
from pyglet.gl import *

import anim
import euclid
from anim_euclid import AnimatedVector3, AnimatedQuaternion
from widget import Label
from resources import ColorDict
from counter import Counter

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
        if not self.__class__.cardlist: self.build_displaylist()
    def build_displaylist(self):
        cls = self.__class__
        width = self.width/2.0; height=self.height/2.0
        cls.vertlist = [euclid.Point3(-width, -height, 0), euclid.Point3(width, -height, 0), euclid.Point3(width, height, 0), euclid.Point3(-width, height, 0)]
        vertlist = cls.vertlist
        tc = self._texture.tex_coords
        cardlist = glGenLists(1)
        cls.cardlist = cardlist
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
            glColor4f(self.alpha, self.alpha, self.alpha, self.alpha)
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
    def copy(self): return Card(self.gamecard, self.front, self.back)
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
    def __init__(self, gamecard, front, back, bordered=False, border=None):
        super(StackCard,self).__init__(gamecard,front,back)
        self.highlighting = anim.animate(0, 0, dt=0.2)
        self.size = anim.animate(self.size, self.size, dt=0.2, method="sine")
        self.alpha = anim.animate(0, 0, dt=1.0, method="ease_out_circ")
        #self.color = self.COLORS.get(str(gamecard.color))
        colors = self.COLORS.get_multi(str(gamecard.color))
        if len(colors) == 1: self.color = colors[0]
        else:
            self.color = colors
            self.draw = self.draw_multi
        self.bordered = bordered
        self.border = border
        if bordered and not self.__class__.borderedlist: self.build_borderedlist()
    def build_borderedlist(self):
        cls = self.__class__
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
            glCallList(self.cardlist)
            if self.bordered:
                color = self.color
                glBindTexture(self.border.target, self.border.id)
                glColor4f(color[0], color[1], color[2], self.alpha)
                glCallList(self.borderedlist)
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



# Since visual cards are recycled once they are created (by CardLibrary) the event triggers below will still
# be active when the card leaves play. However, since the actual gamecard won't be generating any of the events
# until the card is back in play this should be fine
# XXX This is no longer the case - the card unregisters the events it listens to
from game.Match import isCreature
from game.GameEvent import HasPriorityEvent, PowerToughnessChangedEvent, CounterAddedEvent, CounterRemovedEvent, SubRoleAddedEvent, SubRoleRemovedEvent
from game.pydispatch import dispatcher
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
        self.info_box = Label("", size=12, background=True, shadow=False, valign="top")
        self.info_box._pos.set_transition(dt=0.4, method="sine")
        self.info_box.pos = euclid.Vector3(self.width/2+self.info_box.border, self.height/2-self.info_box.border, 0.005)
        self.info_box.visible = False
    def add_role(self, sender):
        if isCreature(self.gamecard):
            self.setup_creature_subrole()
    def remove_role(self, sender):
        if not isCreature(self.gamecard) and self.is_creature:
            self.remove_creature_subrole()
    def setup_creature_subrole(self):
        self.is_creature = True
        gamecard = self.gamecard
        self.power = 0 #gamecard.power
        self.toughness = 0 #gamecard.toughness
        self.damage = 0 #gamecard.currentDamage()
        #dispatcher.connect(self.change_value, signal=PowerToughnessChangedEvent(), sender=gamecard)
        # XXX This will lead to a lot of events each time priority is passed
        # but I'm not sure how to do it otherwise for cards like "Coat of Arms", which use a lambda function
        # or for damage
        self.text = Label("", size=34, background=True, shadow=False, halign="center", valign="center")
        self.text._scale = anim.animate(0, 0, dt=0.25, method="sine")
        self.text.scale = 2.0
        self.text._pos.set(euclid.Vector3(0,0,0)) #_transition(dt=0.25, method="sine")
        self.text.orig_pos = euclid.Vector3(0,-self.height*0.25,0.001)
        self.text.zoom_pos = euclid.Vector3(self.width*1.375,-self.height*0.454, 0.01)
        self.text.pos = self.text.orig_pos
        self.damage_text = Label("", size=34, background=True, shadow=False, halign="center", valign="center", color=(1., 0., 0., 1.))
        #self.damage_text._scale = anim.animate(0.0, 0.0, dt=0.25, method="sine")
        self.damage_text.scale = 0.4
        self.damage_text.visible = 0
        self.damage_text._pos.set(euclid.Vector3(0,0,0)) #_transition(dt=0.25, method="sine")
        self.damage_text.zoom_pos = euclid.Vector3(self.width*(1-.375),-self.height*0.454, 0.01)
        self.damage_text.pos = self.damage_text.zoom_pos
        self.change_value()
        self.draw = self.draw_creature
        dispatcher.connect(self.change_value, signal=HasPriorityEvent())
    def remove_creature_subrole(self):
        self.is_creature = False
        self.draw = self.draw_permanent
        dispatcher.disconnect(self.change_value, signal=HasPriorityEvent())
    def entering_play(self):
        self.is_tapped = False
        self.tapping = anim.animate(0, 0, dt=0.3)
        self.highlighting = anim.animate(0, 0, dt=0.2)
        self.zooming = anim.animate(0, 0, dt=0.4)
        self.pos_transition = "ease_out_circ" #"ease_out_back"
        self._pos.set_transition(dt=0.4, method=self.pos_transition)
        #self._pos.y = anim.animate(guicard._pos.y, guicard._pos.y, dt=0.4, method="ease_out")
        self._orientation.set_transition(dt=0.3, method="sine")
        self.can_layout = True
        if isCreature(self.gamecard):
            self.setup_creature_subrole()
        # Check for counters
        dispatcher.connect(self.add_counter, signal=CounterAddedEvent(), sender=self.gamecard)
        dispatcher.connect(self.remove_counter, signal=CounterRemovedEvent(), sender=self.gamecard)
        dispatcher.connect(self.add_role, signal=SubRoleAddedEvent(), sender=self.gamecard)
        dispatcher.connect(self.remove_role, signal=SubRoleRemovedEvent(), sender=self.gamecard)
        self.counters = [Counter(counter.ctype) for counter in self.gamecard.counters]
        self.layout_counters()
    def leaving_play(self):
        if self.is_creature:
            self.remove_creature_subrole()
        dispatcher.disconnect(self.add_counter, signal=CounterAddedEvent(), sender=self.gamecard)
        dispatcher.disconnect(self.remove_counter, signal=CounterRemovedEvent(), sender=self.gamecard)
        dispatcher.disconnect(self.add_role, signal=SubRoleAddedEvent(), sender=self.gamecard)
        dispatcher.disconnect(self.remove_role, signal=SubRoleRemovedEvent(), sender=self.gamecard)
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
            if d > 0: self.damage_text.set_text("-%d"%d)
            else: self.damage_text.set_text("")
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
            self.zooming = 1.0
            self.old_pos = self.pos
            self._pos.set_transition(dt=0.4, method="ease_out_back") #self.pos_transition)
            #self._pos.y = anim.animate(self._pos.y, self._pos.y, dt=0.4, method="sine")
            #self._orientation.set_transition(dt=0.5, method="sine")
            if show_info: offset = offset + euclid.Vector3(-self.width*size/2, 0, 0)
            self.pos = camera.pos - camera.orientation*euclid.Vector3(0,0,camera.vis_distance) - euclid.Vector3(0,0,z) + offset
            self.orig_orientation = self.orientation
            self.orientation = camera.orientation
            self.old_size = self.size
            self.size = size
            if self.is_creature:
                self.text.set_text("%d/%d"%(self.power, self.toughness))
                self.text.pos = self.text.zoom_pos
                self.text.scale = 0.4
                self.damage_text.visible = 1.0
            if show_info:
                self.info_box.visible = True
                self.info_box.set_text('\n'.join(self.gamecard.info.split("\n")[:17]), width=self.width)
                self.info_box._height = self.height-self.info_box.border
            else: self.info_box.visible = False
    def restore_pos(self):
        self.zooming = 0.0 #anim.animate(self.zooming, 0.0, dt=0.2)
        self._pos.set_transition(dt=0.4, method=self.pos_transition)
        #self._pos.y = anim.animate(self._pos.y, self._pos.y, dt=0.4, method="sine")
        # XXX old self._pos.set_transition(dt=0.2, method="ease_out_circ")
        #self._orientation.set_transition(dt=0.3, method="sine")
        self.pos = self.old_pos
        self.orientation = self.orig_orientation
        self.size = self.old_size
        if self.is_creature:
            self.text.set_text("%d/%d"%(self.power, self.toughness-self.damage))
            self.text.pos = self.text.orig_pos
            self.text.scale = 2.0
            self.damage_text.scale = 0.4
            self.damage_text.pos = self.damage_text.zoom_pos
            self.damage_text.visible = 0.0
        self.info_box.visible = False
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
            self.info_box.render()
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
            self.info_box.render()
            self.text.render()
            self.damage_text.render()
            glDisable(self._texture.target)
            for c in self.counters: c.draw()
            glPopMatrix()
    def copy(self): return PlayCard(self.gamecard, self.front, self.back)
