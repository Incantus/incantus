#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import pyglet
from pyglet.gl import *

import anim
import euclid
import GUIEvent
from widget import Widget, Label
from anim_euclid import BezierPath
from game.pydispatch import dispatcher

sixteenfv = GLfloat*16

import math
import CardLibrary

class CardView(Widget):
    focus_size = 1.0 #0.8
    def __init__(self, pos, reverse_draw=False):
        super(CardView,self).__init__(pos)
        self.cards = []
        self.focus_idx = 0
        self.focus_dir = 1
        self.visible = 0
        self.reverse_draw = reverse_draw
        self.pos_transition = "ease_out_back"
        self.orientation_transition = "sine"
    def clear(self):
        self.cards = []
        self.focus_idx = 0
        self.focus_dir = 1
    def show(self):
        super(CardView,self).show()
        for c in self.cards: c.alpha = 1.0
    def hide(self):
        super(CardView,self).hide()
        for c in self.cards: c.alpha = 0.0

    def focused():
        def fget(self):
            if self.cards: return self.cards[self.focus_idx]
            else: return None
        return locals()
    focused = property(**focused())

    def focus_next(self):
        if self.visible == 1 and self.focus_idx < len(self)-1:
            dispatcher.send(GUIEvent.FocusCard())
            self.focus_dir = 1
            self.focus_idx += self.focus_dir
            self.layout()
            return True
        else: return False
    def focus_previous(self):
        if self.visible == 1 and self.focus_idx > 0:
            dispatcher.send(GUIEvent.FocusCard())
            self.focus_dir = -1
            self.focus_idx += self.focus_dir
            self.layout()
            return True
        else: return False
    def render_after_transform(self):
        if not self.reverse_draw:
            for card in self.cards: card.draw()
        else:
            for card in self.cards[::-1]: card.draw()
    def __len__(self): return len(self.cards)

class HandView(CardView):
    zooming = anim.Animatable()
    def __init__(self, pos=euclid.Vector3(0,0,0), is_opponent=False):
        super(HandView,self).__init__(pos, reverse_draw=True)
        self._pos.set_transition(dt=0.3, method="sine") #"ease_out_back")
        if is_opponent: 
            self.dir = -1
            align="left"
        else:
            self.dir = 1
            align = "right"
        self.hand_size = Label("0", size=30, halign=align, valign="center")
        self.is_opponent = is_opponent
        self.small_size = 0.6
        self.played = []
        self.focus_idx = 0
        self.visible = 0.0
        self.zooming = 0
        self.layout = self.unfocused_layout
        self.render_after_transform = self.render_unfocused
        self.unfocused_size = (0.05, 0.30)
        self.unfocused_spacing = 1.025
        self.solitaire = False
    def set_solitaire(self):
        self.solitaire = True
    def resize(self, width, height, avail_width):
        self.screen_width = width
        self.avail_width = avail_width-10
        self.height = 85.5
        if not self.is_opponent: self.pos = euclid.Vector3(width-self.avail_width, 1.1*self.height/2, 0)
        else: self.pos = euclid.Vector3(0, height - 1.1*self.height/2, 0)
        self.layout()
    def show(self):
        #self.focus_idx = len(self)/2
        self.layout = self.layout_staggered
        self.render_after_transform = self.render_focused
        self.pos = euclid.Vector3(self.screen_width/2, 150, 0)
        for card in self.cards:
            card.alpha = 1.0
            card._pos.set_transition(dt=0.4, method=self.pos_transition)
        self.layout()
        #super(HandView,self).show()
    def hide(self):
        self.layout = self.unfocused_layout
        self.render_after_transform = self.render_unfocused
        for card in self.cards:
            #card.alpha = 0.85
            card._pos.set_transition(dt=0.4, method="sine")
        self.layout()
        #super(HandView,self).hide()
    def add_card(self, card):
        newcard = CardLibrary.CardLibrary.getHandCard(card)
        if self.is_opponent and not self.solitaire: newcard.hidden = True
        newcard._pos.set_transition(dt=0.8, method="sine") #self.pos_transition)
        newcard._orientation.set_transition(dt=0.2, method=self.orientation_transition)
        newcard.size = anim.animate(newcard.size, newcard.size, dt=0.2, method="sine")
        newcard.alpha = anim.animate(0, 1.0, dt=1.0, method="ease_out_circ")
        self.cards.append(newcard)
        if len(self.cards): self.visible = 1.0
        self.layout()
    def remove_card(self, card):
        card = CardLibrary.CardLibrary.getHandCard(card)
        # XXX This if statement is an ugly hack, I should remove it once I figure out
        # how to place cards from hand to the stack
        if card in self.cards:
            self.cards.remove(card)
            if self.focus_dir < 0: self.focus_idx += self.focus_dir
            if self.focus_idx > len(self)-1: self.focus_idx = len(self)-1
            elif self.focus_idx < 0: self.focus_idx = 0
            self.layout()
            if not len(self.cards): self.visible = 0
    def card_on_stack(self, ability):
        # XXX This is a big ugly hack
        from game.Ability import CastSpell
        if not isinstance(ability, CastSpell): return
        card = CardLibrary.CardLibrary.getHandCard(ability.card)
        if card in self.cards:
            self.cards.remove(card)
            if self.focus_dir < 0: self.focus_idx += self.focus_dir
            if self.focus_idx > len(self)-1: self.focus_idx = len(self)-1
            elif self.focus_idx < 0: self.focus_idx = 0
            self.played.append(card)
            self.layout()
    def card_off_stack(self, ability):
        # XXX This is a big ugly hack
        from game.Ability import CastSpell
        if not isinstance(ability, CastSpell): return
        card = CardLibrary.CardLibrary.getHandCard(ability.card)
        if card in self.played:
            self.played.remove(card)
            self.cards.append(card)
            self.layout()
    def shift_right(self, card):
        idx = self.cards.index(card)
        if idx != 0:
            self.cards[idx], self.cards[idx-1] = self.cards[idx-1], self.cards[idx]
    def shift_left(self, card):
        idx = self.cards.index(card)
        if idx != len(self.cards)-1:
            self.cards[idx+1], self.cards[idx] = self.cards[idx], self.cards[idx+1]
    def zoom_card(self, card):
        if card.zooming == 0:
            #self.zooming_card = card
            card.zooming = anim.animate(0, 1, dt=0.3, method="linear")
            card.old_pos = card.pos
            card.old_size = card.size
            if card.pos.x+card.width/2 > self.avail_width: pos_shift = self.avail_width - card.width/1.5
            else: pos_shift = card.pos.x
            card._pos.set_transition(dt=0.2, method="sine") #self.pos_transition)
            card.pos = euclid.Vector3(pos_shift, (self.height+card.height/2)*self.dir, 0)
            card.size = 1.0
    def restore_card(self, card):
        #if self.zooming == 1.0: # This will finish the zooming motion
        if True:
            card.zooming = anim.animate(1, 0, dt=0.3, method="linear")
            #card = self.zooming_card
            card.size = card.old_size
            card.pos = card.old_pos
    def unfocused_layout(self):
        numhand = len(self.cards)
        if numhand > 0:
            self.hand_size.set_text(numhand)
            if not self.is_opponent: self.hand_size.pos = euclid.Vector3(self.avail_width-10, 0, 0)
            else: self.hand_size.pos = euclid.Vector3(10, 0, 0)
            avail_width = self.avail_width - self.hand_size.width - 20
            size = self.unfocused_size[1]
            cardwidth = self.cards[0].width
            # First lay out, then overlap, and then scale
            spacing = self.unfocused_spacing
            numhand += .5
            while (numhand*cardwidth*size*spacing) > avail_width:
                # Figure out the spacing that will fit
                spacing = avail_width / (numhand*cardwidth*size)
                if spacing < 0.7:
                    spacing = self.unfocused_spacing
                    size -= 0.005
            x_incr = cardwidth*size*spacing*self.dir
            if not self.is_opponent: x, y = avail_width-cardwidth*size/2, 0
            else: x, y = self.hand_size.width + cardwidth*size/2 + 20, 0
            z = 0
            for card in self.cards:
                card.size = size
                card.orientation = euclid.Quaternion()
                card._pos.set_transition(dt=0.8, method="sine")
                card.pos = euclid.Vector3(x,y,z)
                x -= x_incr
            self.box = (-5, -self.height/2-5, self.avail_width, self.height/2+5)
    def layout_original(self):
        if len(self) > 0:
            if self.focus_idx == -1: self.focus_idx = len(self)-1
            cards = self.cards
            w, h = cards[0].width, cards[0].height
            radius = h*1.5
            incr_arc = math.pi/180*-2
            extra_arc = math.pi/180*-27
            Q = euclid.Quaternion.new_rotate_axis(incr_arc*(self.focus_idx-1)+extra_arc, euclid.Vector3(0,0,-1))
            i = 0.001
            for card in cards[:self.focus_idx]:
                card.orientation = Q
                card.pos = Q*euclid.Vector3(0,radius,0) - euclid.Vector3(0,radius,i)
                card.size = self.small_size
                Q.rotate_axis(incr_arc, euclid.Vector3(0,0,1))
                i += 0.001
            card = cards[self.focus_idx]
            card.pos = euclid.Vector3(0,0,i)
            i += 0.001
            card.orientation = euclid.Quaternion()
            card.size = self.focus_size
            Q = euclid.Quaternion.new_rotate_axis(-extra_arc, euclid.Vector3(0,0,-1))
            for card in cards[self.focus_idx+1:]:
                card.orientation = Q 
                card.pos = Q*euclid.Vector3(0,radius,0) - euclid.Vector3(0,radius,i)
                card.size = self.small_size
                Q.rotate_axis(incr_arc, euclid.Vector3(0,0,1))
                i += 0.001
    def layout_staggered(self):
        if len(self) > 0:
            if self.focus_idx == -1: self.focus_idx = len(self)-1
            cards = self.cards
            w, h = cards[0].width, cards[0].height
            radius = h*8#1.5
            incr_arc = math.pi/180*-0.75 #1
            extra_arc = math.pi/180*-4.5 #10 #-27
            Q = euclid.Quaternion.new_rotate_axis(incr_arc*(self.focus_idx-1)+extra_arc, euclid.Vector3(0,0,-1))
            i = 0.001
            y_incr = (self.focus_idx-1)*h*0.1*self.small_size
            size = self.small_size
            for card in cards[:self.focus_idx]:
                card.orientation = Q
                card.pos = Q*euclid.Vector3(0,radius,0) - euclid.Vector3(0,radius+y_incr,i)
                card.size = size
                Q.rotate_axis(incr_arc, euclid.Vector3(0,0,1))
                y_incr -= h*0.1*size
                #if size < self.small_size: size += 0.05
                i += 0.001
            card = cards[self.focus_idx]
            card.pos = euclid.Vector3(0,0,i)
            i += 0.001
            card.orientation = euclid.Quaternion()
            card.size = self.focus_size
            #Q = euclid.Quaternion.new_rotate_axis(incr_arc*(len(self)-self.focus_idx)+extra_arc, euclid.Vector3(0,0,1))
            #incr_arc *= -1
            #y_incr = (len(self)-self.focus_idx-1)*h*0.1*self.small_size
            Q = euclid.Quaternion.new_rotate_axis(-extra_arc, euclid.Vector3(0,0,-1))
            y_incr += h*0.1*self.small_size
            #for card in cards[-1:self.focus_idx:-1]:
            for card in cards[self.focus_idx+1:]:
                card.orientation = Q
                card.pos = Q*euclid.Vector3(0,radius,0) - euclid.Vector3(0,radius+y_incr,i)
                card.size = self.small_size
                Q.rotate_axis(incr_arc, euclid.Vector3(0,0,1))
                y_incr += h*0.1*self.small_size
                i += 0.001
    def render_unfocused(self):
        glColor4f(0.2,0.2,0.3,0.5)
        glDisable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        l, b, r, t = self.box
        glVertex2f(l, b)
        glVertex2f(r, b)
        glVertex2f(r, t)
        glVertex2f(l, t)
        glEnd()
        glColor3f(0,0,0)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(l, b)
        glVertex2f(r, b)
        glVertex2f(r, t)
        glVertex2f(l, t)
        glEnd()
        self.hand_size.render()
        for card in self.cards: card.draw()
    def render_focused(self):
        for card in self.cards[self.focus_idx::-1]: card.draw()
        for card in self.cards[self.focus_idx+1:]: card.draw()

from game.Ability.CastingAbility import CastSpell
class StackView(CardView):
    width = anim.Animatable()
    height = anim.Animatable()
    def __init__(self, pos=euclid.Vector3(0,0,0)):
        super(StackView,self).__init__(pos)
        self.is_focused = False
        self.visible = anim.constant(0)
        self.header = Label("Stack", halign="left", valign="top")
        self.header.pos = euclid.Vector3(0,0,0)
        self.text = Label("", halign="left", valign="center", background=True)
        self.text.visible = anim.animate(0, 0, dt=0.4, method="linear")
        self.width = anim.animate(0, 0, dt=0.4, method="sine")
        self.height = anim.animate(0, 0, dt=0.4, method="sine")
        self.layout()
    def add_ability(self, ability, startt=0):
        if ability.card == "Assign Damage":
            newcard = CardLibrary.CardLibrary.getFakeCard(ability)
            newcard.triggered = True
        else:
            triggered = not isinstance(ability, CastSpell)
            newcard = CardLibrary.CardLibrary.getStackCard(ability.card, triggered)
        newcard.ability = ability
        self.cards.append(newcard)
        self.focus_idx = len(self)-1
        newcard.size = anim.animate(0.2, 0.2, dt=0.2, method="cosine")
        if startt != 0:
            newcard.visible = anim.animate(0,1,dt=startt, method="step")
            self.header.dt = startt
        else: self.header.dt = 0.01
        self.layout()
        newcard._pos.set_transition(dt=0.2, method="linear") #self.pos_transition)
        newcard.alpha = anim.animate(0, 0.5, startt=startt, dt=1.0, method="ease_out_circ")
        newcard.announced = False
        return newcard
    def finalize_announcement(self, ability):
        for card in self.cards:
            if ability == card.ability:
                card.announced = True
                card.alpha = 1.0
    def remove_ability(self, ability):
        for idx, card in enumerate(self.cards):
            if ability == card.ability:
                self.cards.remove(card)
                if self.focus_idx >= len(self): self.focus_idx = len(self)-1
                break
        else: raise Exception
        self.layout()
    def get_card(self, ability):
        for card in self.cards:
            if ability == card.ability: return card
        else: return None
    def focus(self, idx=-1):
        self.is_focused = True
        if idx == -1: self.focus_idx = len(self)-1
        else: self.focus_idx = idx
        self.layout()
    def unfocus(self):
        self.is_focused = False
        self.unfocused_layout()
    def layout(self):
        if self.is_focused: self.focused_layout()
        else: self.unfocused_layout()
    def unfocused_layout(self):
        size = 0.25
        self.text.visible = anim.animate(0.0, 0.0, dt=0.1)
        if len(self.cards):
            self.visible = 1.0
            self.header.visible = anim.animate(self.header.visible, 1.0, dt=self.header.dt, method="linear")
            card = self.cards[0]
            x_incr, y_incr = card.width*size*0.15, -card.height*size*0.20
            x, y = card.width*size/2, -self.header.height-card.height*size/2
            z = 0
            for card in self.cards:
                card.size = size
                card.pos = euclid.Vector3(x,y,z)
                x += x_incr
                y += y_incr
                z += 0.001
            self.width = x + card.width*size/2
            self.height = y - card.height*size/2
        else:
            self.visible = 0
    def focused_layout(self):
        min_size = 0.2
        if len(self) > 0:
            self.visible = 1.0
            self.header.visible = 0
            self.header.dt = 0.01
            w, h = self.cards[0].width, self.cards[0].height
            x_incr = w*0.025
            y_incr = h*0.025
            startx, starty = 20, -20
            x = startx-self.focus_idx*x_incr
            y = starty+(self.focus_idx-1)*y_incr
            z = 0.001
            for i, card in enumerate(self.cards[:self.focus_idx]):
                card.size = min_size
                card.pos = euclid.Vector3(x,y,z)
                x += x_incr
                y -= y_incr
                z += 0.001
            card = self.cards[self.focus_idx]
            card.size = self.focus_size #anim.animate(card.size, self.focus_size, dt=0.2, method="sine")
            card.pos = euclid.Vector3(startx+w*0.45, y-h*0.4, z)
            self.text.visible = 1.0
            if card.triggered: self.text.visible = 1.0
            else: self.text.visible = 0.0
            self.text.pos = euclid.Vector3(startx, y-h*0.7, z)
            self.text.set_text(str(card.ability), width=0.9*w)
            x -= x_incr*4
            y -= h*0.8
            z += 0.001
            for i, card in enumerate(self.cards[self.focus_idx+1:]):
                card.size = min_size
                card.pos = euclid.Vector3(x,y,z)
                x -= x_incr
                y -= y_incr
                z += 0.001
        else:
            self.visible = 0
    def handle_click(self, x, y):
        x -= self.pos.x
        y -= self.pos.y
        if -10 < x < self.width+10 and self.height-10 < y < 5:
            for idx, card in enumerate(self.cards[::-1]):
                sx, sy, sw, sh = card.pos.x, card.pos.y, card.width*card.size/2, card.height*card.size/2
                if x > sx-sw and x < sx+sw and y >= sy-sh and y <= sy+sh:
                    return len(self.cards)-1-idx, card
        return -1, None
    def render_after_transform(self):
        if self.header.visible == 1.0:
            glColor4f(0.7,0.7,0.7, 0.5)
            glDisable(GL_TEXTURE_2D)
            glBegin(GL_QUADS)
            glVertex3f(-10, 5, 0)
            glVertex3f(self.width+10, 5, 0)
            glVertex3f(self.width+10, self.height-10, 0)
            glVertex3f(-10, self.height-10, 0)
            glEnd()
            glColor3f(0,0,0)
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            glVertex3f(-10, 5, 0)
            glVertex3f(self.width+12, 5, 0)
            glVertex3f(self.width+12, self.height-12, 0)
            glVertex3f(-10, self.height-12, 0)
            glEnd()
            self.header.render()
        super(StackView,self).render_after_transform()
        self.text.render()

class ZoneView(CardView):
    def __init__(self, pos=euclid.Vector3(0,0,0)):
        super(ZoneView,self).__init__(pos,reverse_draw=True)
        self._pos.set_transition(dt=0.001)
        self.sorted = False
        points = [(0.0, 0.0), (26.0, 244.0), (184.0, 368.0), (400.0, 226.0)]
        self.path = BezierPath(*[euclid.Point2(v[0], v[1]) for v in points])
        self.visible = anim.animate(0,0,dt=0.3)
        self.layout = self.layout_straight
    def build(self, zone, is_opponent):
        self.cards = []
        self.selected = []
        self.shift_factor = 0.1
        if is_opponent:
            self.dir = -1
            align = ["left", "right"]
        else:
            self.dir = 1
            align = ["right", "left"]
        self.selected_text = [Label("Top", halign=align[0], background=True), Label("Bottom", halign=align[1], background=True)]
        self.selected_text[0].visible = self.selected_text[1].visible = 0.0
        for card in zone: self.add_card(card)
        self.orig_order = dict([(c.gamecard.key, i) for i, c in enumerate(self.cards)])
        self.focus_idx = 0
        self.layout()
        self.scroll = ((self.scroll_shift*self.focus_idx)*self.dir, -17*self.dir, (self.scroll_shift*(self.focus_idx+1))*self.dir, -10*self.dir)
    def focus_next(self):
        if self.dir == 1: cond = (self.focus_idx < len(self)-1)
        else: cond = self.focus_idx > 0
        if cond: #self.focus_idx < len(self)-1:
            dispatcher.send(GUIEvent.FocusCard())
            self.focus_dir = self.dir
            self.focus_idx += self.focus_dir
            self.layout()
            return True
        else: return False
    def focus_previous(self):
        if self.dir == 1: cond = self.focus_idx > 0
        else: cond = self.focus_idx < len(self)-1
        if cond: #self.focus_idx > 0:
            dispatcher.send(GUIEvent.FocusCard())
            self.focus_dir = -self.dir
            self.focus_idx += self.focus_dir
            self.layout()
            return True
        else: return False
    def toggle_sort(self):
        if self.sorted:
            self.sorted = False
            self.cards.sort(key=lambda c: self.orig_order[c.gamecard.key])
            self.layout()
        else:
            self.sorted = True
            self.cards.sort(key=lambda c: str(c))
            self.layout()
    def add_card(self, card):
        newcard = CardLibrary.CardLibrary.getCardCopy(card)
        newcard._pos.set_transition(dt=0.5, method=self.pos_transition)
        newcard._orientation.set(euclid.Quaternion())
        newcard._orientation.set_transition(dt=0.2, method=self.orientation_transition)
        newcard.size = anim.animate(0.1, 0.1, dt=0.2, method="sine")
        newcard.alpha = anim.animate(0, 1, dt=1.0, method="ease_out_circ")
        self.cards.append(newcard)
    def select_card(self, card):
        self.cards.remove(card)
        self.selected.append(card)
        if self.focus_dir < 0: self.focus_idx += self.focus_dir
        if self.focus_idx > len(self)-1: self.focus_idx = len(self)-1
        elif self.focus_idx < 0: self.focus_idx = 0
        self.layout()
        self.layout_selected()
    def deselect_card(self, card):
        self.selected.remove(card)
        self.cards.insert(self.focus_idx, card) # Find the right position to reinsert
        self.layout()
        self.layout_selected()
    def handle_click(self, x, y):
        size = self.focus_size / 4.
        card = self.focused
        if card:
            sx, sy, sw, sh = card.pos.x, card.pos.y, card.width/2, card.height/2
            if x > sx-sw and x < sx+sw and y >= sy-sh and y <= sy+sh:
                return 0, card
        for card in self.selected:
            sx, sy, sw, sh = card.pos.x, card.pos.y, card.width*size, card.height*size
            if x > sx-sw and x < sx+sw and y >= sy-sh and y <= sy+sh:
                return 1, card
        return -1, None
    def show(self):
        super(ZoneView,self).show()
    def hide(self):
        self.visible = 0.0
        for card in self.cards:
            card.alpha = 0.5
            #card._pos.set_transition(dt=0.25, method="ease_out_circ")
            card.pos = euclid.Vector3(0,0,0)
            card.size = anim.animate(card.size, 0.1, dt=0.25, method="ease_out_circ")
        for card in self.selected:
            card.alpha = 0.5
            #card._pos.set_transition(dt=0.25, method="ease_out_circ")
            card.pos = euclid.Vector3(0,0,0)
            card.size = anim.animate(card.size, 0.1, dt=0.25, method="ease_out_circ")
    def layout_selected(self):
        dir = self.dir
        x = 0
        size = self.focus_size / 2
        if self.selected:
            for card in self.selected:
                card.size = size
                y = card.height*(1.1+size/2)*dir
                card.pos = euclid.Vector3(x,y,0)
                x += card.width*size*1.1*dir
            self.selected_text[0].visible = self.selected_text[1].visible = 1.0
            self.selected_text[0].pos = euclid.Vector3(-card.width*size*0.65*dir, y, 0)
            self.selected_text[1].pos = euclid.Vector3(x-card.width*size*0.45*dir, y, 0)
        else:
            self.selected_text[0].visible = self.selected_text[1].visible = 0.0
    def layout_straight(self):
        numcards = len(self)
        if numcards > 0:
            cards = self.cards
            dir = self.dir
            size = 0.25
            i = 0.001
            x = y = 0
            xincr = self.shift_factor
            #x -= cards[0].width*self.focus_size*0.6*dir
            for card in cards[:self.focus_idx]:
                card.size = size
                x += card.width*size*xincr*dir
                card.pos = euclid.Vector3(x, y+card.height*size/2*dir,i)
                i += 0.001
            card = cards[self.focus_idx]
            card.size = self.focus_size
            x += card.width*self.focus_size*0.5*dir
            card.pos = euclid.Vector3(x, y+card.height*self.focus_size/2*dir,i)
            self.height = card.height*self.focus_size
            x += card.width*self.focus_size*0.5*dir
            i += 0.001
            for card in cards[self.focus_idx+1:]:
                card.size = size
                x += card.width*size*xincr*dir
                card.pos = euclid.Vector3(x, y+card.height*size/2*dir,i)
                i += 0.001
            self.width = x #+card.width*0.25
            self.scroll_bar = (0, -5*dir, self.width, -20*dir)
            self.scroll_shift = self.width/len(self.cards)
    def layout_up(self):
        numcards = len(self)
        if numcards > 0:
            cards = self.cards
            dir = self.dir
            i = 0.001
            x = 0
            size = 0.8
            y = cards[0].height*size*0.5*dir
            for card in cards[::dir]:
                card.size = size
                y += card.height*size*0.08*dir
                card.pos = euclid.Vector3(x,y,i)
                i += 0.001
    def layout_bezier(self):
        numcards = len(self)
        if numcards > 0:
            cards = self.cards
            path_param = 1./numcards
            cardcounter = 0
            i = 0.001
            for card in cards[:self.focus_idx]:
                point = self.path.get(cardcounter*path_param)
                card.pos = euclid.Vector3(point.x, point.y,i)
                card.size = 0.25
                i += 0.001
                cardcounter += 1
            card = cards[self.focus_idx]
            point = self.path.get(cardcounter*path_param)
            card.pos = euclid.Vector3(point.x, point.y,i)
            card.size = 0.25
            cardcounter += 1
            i += 0.001
            for card in cards[self.focus_idx+1:]:
                point = self.path.get(cardcounter*path_param)
                card.pos = euclid.Vector3(point.x, point.y,i)
                card.size = 0.25
                i += 0.001
                cardcounter += 1
    def render_after_transform(self):
        #if not self.reverse_draw:
        #    for card in self.cards: card.draw()
        #else:
        #    for card in self.cards[::-1]: card.draw()
        if len(self.cards) > 1:
            glDisable(GL_TEXTURE_2D)
            glBegin(GL_QUADS)
            glColor4f(0.1,0.1,0.1,0.95)
            l, b, r, t = self.scroll_bar
            glVertex2f(l, b)
            glVertex2f(r, b)
            glVertex2f(r, t)
            glVertex2f(l, t)
            glColor4f(0.5,0.5,0.5,0.8)
            l, b, r, t = self.scroll
            glVertex2f(l, b)
            glVertex2f(r, b)
            glVertex2f(r, t)
            glVertex2f(l, t)
            glEnd()
        #glColor4f(0.1,0.1,0.1,0.9)
        #l, b, r, t = -20, -20, self.width+20, self.height+20
        #glVertex2f(l, b)
        #glVertex2f(r, b)
        #glVertex2f(r, t)
        #glVertex2f(l, t)
        #glEnd()
        #glColor3f(0,0,0)
        #glLineWidth(2.0)
        #glBegin(GL_LINE_LOOP)
        #glEnd()
        if self.cards:
            for card in self.cards[:self.focus_idx]: card.draw()
            for card in self.cards[-1:self.focus_idx:-1]: card.draw()
            self.focused.draw()
        for card in self.selected: card.draw()
        for label in self.selected_text: label.render()
