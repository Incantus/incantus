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
from resources import render_9_part
from engine.pydispatch import dispatcher

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
        #if is_opponent: 
        #    self.dir = -1
        #    align="left"
        #else:
        #    self.dir = 1
        #    align = "right"
        self.dir = 1
        self.vdir = -1 if is_opponent else 1
        align = "left"
        #self.hand_size = Label("0", size=30, halign=align, valign="center")
        self.is_opponent = is_opponent
        self.small_size = 0.6
        self.focus_idx = 0
        self.visible = 0.0
        self.zooming = 0
        self.avail_width = 0
        self.height = 0
        self.layout = self.unfocused_layout
        self.render_after_transform = self.render_unfocused
        self.unfocused_size = (0.05, 0.40)
        self.unfocused_spacing = 1.025
        self.hidden = True
        self._card_map = {}
    def set_hidden(self, value=True):
        self.hidden = value
        for card in self.cards: card.hidden = value
    def resize(self, width, height, avail_width):
        self.screen_width = width
        offset = 5
        self.avail_width = avail_width-10-2*offset
        self.height = 136 #90 #85.5
        if not self.is_opponent: self.pos = euclid.Vector3(width-offset-self.avail_width, offset+self.height/2, 0)
        else: self.pos = euclid.Vector3(width-self.avail_width-offset, height - self.height/2 - offset, 0)
        #if not self.is_opponent: self.pos = euclid.Vector3(width-self.avail_width, 1.1*self.height/2, 0)
        #else: self.pos = euclid.Vector3(0, height - 1.1*self.height/2, 0)
        self.layout()
    def setup_player(self, color):
        self.color = color
    #def show(self):
    #    #self.focus_idx = len(self)/2
    #    self.layout = self.layout_staggered
    #    self.render_after_transform = self.render_focused
    #    self.pos = euclid.Vector3(self.screen_width/2, 150, 0)
    #    for card in self.cards:
    #        card.alpha = 1.0
    #        card._pos.set_transition(dt=0.4, method=self.pos_transition)
    #    self.layout()
    #    #super(HandView,self).show()
    #def hide(self):
    #    self.layout = self.unfocused_layout
    #    self.render_after_transform = self.render_unfocused
    #    for card in self.cards:
    #        #card.alpha = 0.85
    #        card._pos.set_transition(dt=0.4, method="sine")
    #    self.layout()
    #    #super(HandView,self).hide()
    def add_card(self, card):
        newcard = CardLibrary.CardLibrary.getHandCard(card)
        self._card_map[card.key] = newcard
        newcard.hidden = self.hidden
        newcard._pos.set_transition(dt=0.8, method="sine") #self.pos_transition)
        newcard._orientation.set_transition(dt=0.2, method=self.orientation_transition)
        newcard.size = anim.animate(newcard.size, newcard.size, dt=0.2, method="sine")
        newcard.alpha = anim.animate(0, 1.0, dt=1.0, method="ease_out_circ")
        self.cards.append(newcard)
        self.layout()
    def remove_card(self, card):
        card = self._card_map.pop(card.key)
        self.cards.remove(card)
        if self.focus_dir < 0: self.focus_idx += self.focus_dir
        if self.focus_idx > len(self)-1: self.focus_idx = len(self)-1
        elif self.focus_idx < 0: self.focus_idx = 0
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
            if self.is_opponent and card.pos.x-card.width/2 < 0: pos_shift = card.width/1.5
            elif card.pos.x+card.width/2 > self.avail_width: pos_shift = self.avail_width - card.width/1.5
            else: pos_shift = card.pos.x
            card._pos.set_transition(dt=0.2, method="sine") #self.pos_transition)
            card.pos = euclid.Vector3(pos_shift, (self.height+card.height/2)*self.vdir, 0)
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
        #self.hand_size.set_text(numhand)
        #if not self.is_opponent: self.hand_size.pos = euclid.Vector3(self.avail_width-10, 0, 0)
        #else: self.hand_size.pos = euclid.Vector3(10, 0, 0)
        #avail_width = self.avail_width - self.hand_size.width - 20
        avail_width = self.avail_width - 20
        size = self.unfocused_size[1]
        if numhand > 0:
            self.visible = 1.0
            cardwidth = self.cards[0].width
            # First lay out, then overlap, and then scale
            spacing = self.unfocused_spacing
            numhand += .5
            while (numhand*cardwidth*size*spacing) - avail_width > 0.005:
                # Figure out the spacing that will fit
                spacing = avail_width / (numhand*cardwidth*size)
                if spacing < 0.7:
                    spacing = self.unfocused_spacing
                    size -= 0.005
            x_incr = cardwidth*size*spacing*self.dir
            x, y = avail_width-cardwidth*size/2, 0
            #if not self.is_opponent: x, y = avail_width-cardwidth*size/2, 0
            #else: x, y = self.hand_size.width + cardwidth*size/2 + 20, 0
            z = 0
            for card in self.cards:
                card.size = size
                card.orientation = euclid.Quaternion()
                card._pos.set_transition(dt=0.8, method="sine")
                card.pos = euclid.Vector3(x,y,z)
                x -= x_incr
        else:
            self.visible = 0.0
        self.box = (0, -self.height/2, self.avail_width, self.height/2)
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
            Q = euclid.Quaternion.new_rotate_axis(-extra_arc, euclid.Vector3(0,0,-1))
            y_incr += h*0.1*self.small_size
            for card in cards[self.focus_idx+1:]:
                card.orientation = Q
                card.pos = Q*euclid.Vector3(0,radius,0) - euclid.Vector3(0,radius+y_incr,i)
                card.size = self.small_size
                Q.rotate_axis(incr_arc, euclid.Vector3(0,0,1))
                y_incr += h*0.1*self.small_size
                i += 0.001
    def render_unfocused(self):
        #glColor4f(0.2,0.2,0.3,0.5)
        #glDisable(GL_TEXTURE_2D)
        #glBegin(GL_QUADS)
        c = self.color
        glColor4f(c[0], c[1], c[2], 1.0)
        l, b, r, t = self.box
        render_9_part("box4",
                      r-l, t-b,
                      x=l, y=b)
        for card in self.cards: card.draw()
    def render_focused(self):
        for card in self.cards[self.focus_idx::-1]: card.draw()
        for card in self.cards[self.focus_idx+1:]: card.draw()

class StackView(CardView):
    width = anim.Animatable()
    height = anim.Animatable()
    def __init__(self, pos=euclid.Vector3(0,0,0)):
        super(StackView,self).__init__(pos)
        self.is_focused = False
        self._is_spaced = True
        self.visible = anim.constant(0)
        #self.header = Label("Stack", halign="left", valign="top")
        #self.header.pos = euclid.Vector3(0,0,0)
        #self.text = Label("", halign="left", valign="center", shadow=False, background=True)
        #self.text.visible = anim.animate(0, 0, dt=0.4, method="linear")
        self.width = anim.animate(0, 0, dt=0.2, method="ease_out")
        self.height = anim.animate(0, 0, dt=0.2, method="ease_out")
        #self.layout()
    def toggle(self):
        self._is_spaced = not self._is_spaced
        self.layout()
    def announce(self, ability, startt=0):
        from engine.Ability.CastingAbility import CastSpell
        from engine.Ability.ActivatedAbility import ActivatedAbility
        if isinstance(ability, CastSpell): func = CardLibrary.CardLibrary.getStackCard
        elif isinstance(ability, ActivatedAbility): func = CardLibrary.CardLibrary.getActivatedCard
        else: func = CardLibrary.CardLibrary.getTriggeredCard
        newcard = func(ability.source, str(ability))
        newcard.ability = ability
        return self.add_ability(newcard, startt)
    def add_ability(self, newcard, startt):
        self.cards.append(newcard)
        self.focus_idx = len(self)-1
        newcard.size = anim.animate(0.2, 0.2, startt=startt, dt=0.5, method="ease_out_circ")
        if startt != 0:
            newcard.visible = anim.animate(0,1,dt=startt, method="step")
            #self.header.dt = startt
        else: pass #self.header.dt = 0.01
        self.layout()
        newcard.alpha = anim.animate(0, 0.5, startt=startt, dt=0.3, method="ease_out_circ")
        newcard._pos.set_transition(dt=0.2, method="ease_out") #self.pos_transition)
        newcard.announced = False
        return newcard
    def finalize_announcement(self, ability):
        if ability.source == "Assign Damage":
            newcard = CardLibrary.CardLibrary.getCombatCard(ability)
            newcard.bordered = True
            newcard.ability = ability
            self.add_ability(newcard, 0)
        else:
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
        if self._is_spaced: 
            spacing = 0.4
            alpha = 1.0
        else: 
            spacing = 0.1
            alpha = 0.1
        size = 0.5
        #self.text.visible = anim.animate(0.0, 0.0, dt=0.1)
        if len(self.cards):
            self.visible = 1.0
            #self.header.visible = anim.animate(self.header.visible, 1.0, dt=self.header.dt, method="linear")
            #width, height = self.cards[0].width*size, self.cards[0].height*size
            width, height = self.cards[0].renderwidth*size, self.cards[0].renderheight*size

            self.cardwidth = width
            x_incr, y_incr = width*spacing, 0 #-height*size*0.20
            #x, y = width*size/2, -self.header.height-height*size/2
            #x, y = width*size/2+spacing, -height*size/2+y_incr
            x, y, z = spacing,0,0
            for card in self.cards:
                card.size = size
                card.pos = euclid.Vector3(x,y,z)
                card.alpha = alpha
                x += x_incr
                y += y_incr
                z += 0.001
            #card.alpha = alpha
            self.width = width + x_incr*(len(self.cards)-1)
            self.height = height 
        else:
            self.visible = 0
    def focused_layout(self):
        min_size = 0.2
        if len(self) > 0:
            self.visible = 1.0
            #self.header.visible = 0
            #self.header.dt = 0.01
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
            #self.text.visible = 1.0
            #if card.bordered: self.text.visible = 1.0
            #else: self.text.visible = 0.0
            #self.text.pos = euclid.Vector3(startx, y-h*0.7, z)
            #self.text.set_text(str(card.ability), width=0.9*w)
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
        w, h = self.width/2, self.height/2
        if -w < x < w and -h < y < h:
        #if -10 < x < self.width+10 and self.height-10 < y < 5:
            for idx, card in enumerate(self.cards[::-1]):
                sx, sy, sw, sh = card.pos.x, card.pos.y, card.width*card.size/2, card.height*card.size/2
                if x > sx-sw and x < sx+sw and y >= sy-sh and y <= sy+sh:
                    return len(self.cards)-1-idx, card
        return -1, None
    def render_after_transform(self):
        #if self.header.visible == 1.0:
        #w, h = self.width, self.height
        #render_9_part("box2",
        #              self.width*1.2, self.height,
        #              x=-self.cardwidth/2, y=-h/2)
        super(StackView,self).render_after_transform()
        #self.text.render()

class ZoneView(CardView):
    selected_width = anim.Animatable()
    def __init__(self, pos=euclid.Vector3(0,0,0)):
        super(ZoneView,self).__init__(pos,reverse_draw=True)
        self._pos.set_transition(dt=0.001)
        self.selected_width = anim.animate(0, 0, dt=0.3, method="sine")
        self.sorted = False
        self.padding = 15
        points = [(0.0, 0.0), (26.0, 244.0), (184.0, 368.0), (400.0, 226.0)]
        self.path = BezierPath(*[euclid.Point2(v[0], v[1]) for v in points])
        self.visible = anim.animate(0,0,dt=0.3)
        self.layout = self.layout_straight
        self.is_library = False
    def build(self, zone, is_opponent):
        self.cards = []
        self.selected = []
        self.shift_factor = 0.05 #0.1
        if is_opponent:
            self.dir = -1
        #    align = ["left", "right"]
        else:
            self.dir = 1
        #    align = ["right", "left"]
        #self.selected_text = [Label("Top", halign=align[0], background=True), Label("Bottom", halign=align[1], background=True)]
        #self.selected_text[0].visible = self.selected_text[1].visible = 0.0
        for card in zone: self.add_card(card)
        if str(card.zone) == "library": self.is_library = True
        self.cards.reverse()
        self.focus_idx = len(self.cards)-1 #0
        self.orig_order = dict([(c.gamecard.key, i) for i, c in enumerate(self.cards)])
        self.layout()
        self.selected_width = 0
    def focus_next(self):
        dir = 1
        if dir == 1: cond = (self.focus_idx < len(self)-1)
        else: cond = self.focus_idx > 0
        if cond: #self.focus_idx < len(self)-1:
            dispatcher.send(GUIEvent.FocusCard())
            self.focus_dir = dir
            self.focus_idx += self.focus_dir
            self.layout()
            return True
        else: return False
    def focus_previous(self):
        dir = 1
        if dir == 1: cond = self.focus_idx > 0
        else: cond = self.focus_idx < len(self)-1
        if cond: #self.focus_idx > 0:
            dispatcher.send(GUIEvent.FocusCard())
            self.focus_dir = -dir
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
        newcard = CardLibrary.CardLibrary.getCard(card)
        newcard._pos.set_transition(dt=0.3, method="sine") #ease_out_back") #self.pos_transition)
        #newcard._orientation.set(euclid.Quaternion())
        #newcard._orientation.set_transition(dt=0.2, method=self.orientation_transition)
        newcard.size = anim.animate(0.1, 0.1, dt=0.3, method="sine")
        newcard.alpha = anim.animate(0, 1, dt=0.1, method="linear")
        self.cards.append(newcard)
    def move_to_end(self, card):
        self.cards.remove(card)
        self.cards.append(card)
        self.layout()
    def select_card(self, card):
        self.cards.remove(card)
        self.selected.append(card)
        #if self.focus_dir < 0: self.focus_idx += self.focus_dir
        #self.focus_idx += 1
        if self.focus_idx > len(self)-1: self.focus_idx = len(self)-1
        elif self.focus_idx < 0 and self.cards: self.focus_idx = 0
        self.layout()
        self.layout_selected()
    def deselect_card(self, card):
        self.selected.remove(card)
        #self.cards.insert(self.focus_idx, card) # Find the right position to reinsert
        #if self.focus_idx < 0: self.focus_idx = 0
        if self.focus_idx == len(self)-1: 
            self.cards.append(card)
        else: self.cards.insert(self.focus_idx+1, card) # Find the right position to reinsert
        self.focus_idx += 1
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
        self.visible = 1.0
    def hide(self):
        self.visible = 0.0
        for card in self.cards:
            card.alpha = 0.5
            #card._pos.set_transition(dt=0.25, method="ease_out_circ")
            card.pos = euclid.Vector3(-self.padding,0,0)
            card.size = anim.animate(card.size, 0.1, dt=0.25, method="ease_out_circ")
        for card in self.selected:
            card.alpha = 0.5
            #card._pos.set_transition(dt=0.25, method="ease_out_circ")
            card.pos = euclid.Vector3(-self.padding,0,0)
            card.size = anim.animate(card.size, 0.1, dt=0.25, method="ease_out_circ")
    def layout_selected(self):
        if self.selected:
            size = self.focus_size / 2
            swidth, sheight = self.selected[0].width*size, self.selected[0].height*size
            self.selected_width = swidth+2*self.padding
            x = self.width+swidth/2+2*self.padding
 
            yincr = (self.height-sheight) / (len(self.selected)+1)
            y = yincr+sheight/2
            if self.dir == -1: y += -self.height
            for card in self.selected:
                card.size = size
                card.pos = euclid.Vector3(x,y,0)
                y += yincr
        else:
            self.selected_width = 0
    def layout_straight(self):
        numcards = len(self)
        if numcards > 0:
            cards = self.cards
            dir = 1 #self.dir
            size = self.focus_size*0.95 #0.25
            i = 0.001
            x_bump =  ((4-self.focus_idx)*self.shift_factor) if self.focus_idx < 4 else 0
            x, y = self.cards[0].width*size*(x_bump+1/2.), 0
            self.height = self.cards[0].height*self.focus_size
            if self.dir == -1: y = -self.height
            xincr = 0 #self.shift_factor
            j = 0
            for card in cards[:self.focus_idx]:
                j+= 1
                if j > self.focus_idx-4: xincr = self.shift_factor
                card.size = size
                card.alpha = 0.8
                x += card.width*size*xincr #*dir
                card.pos = euclid.Vector3(x, y+card.height*self.focus_size/2*dir,i)
                #if self.is_library: card.hidden = True
                #i += 0.001
            xincr = self.shift_factor*5
            card = cards[self.focus_idx]
            card.size = self.focus_size
            card.alpha = 1.0
            #x += card.width*self.focus_size*0.5*dir
            x += card.width*self.focus_size*2*xincr #*dir
            card.pos = euclid.Vector3(x, y+card.height*self.focus_size/2*dir,i)
            if self.is_library: card.hidden = False
            x += card.width*self.focus_size*2*xincr #*dir
            #x += card.width*self.focus_size*(1+xincr) #*dir
            #x += card.width*self.focus_size*0.5*dir
            xincr = 0 #self.shift_factor
            #i += 0.001
            xincr = self.shift_factor
            j = 0
            for card in cards[self.focus_idx+1:]:
                j += 1
                if j > 4 : xincr = 0
                card.size = size
                card.alpha = 0.8
                x += card.width*size*xincr#*dir
                card.pos = euclid.Vector3(x, y+card.height*self.focus_size/2*dir,i)
                if self.is_library: card.hidden = False
                #i += 0.001
            x_bump = ((4-j)*self.shift_factor) if j < 4 else 0
            self.width = x+card.width*size*(x_bump+1/2.)
            self.scroll_bar = (0, y-28*dir, self.width, y-11*dir)
            self.scroll_shift = 6
            self.scroll = (self.scroll_shift*self.focus_idx, self.scroll_bar[1], self.scroll_shift*(self.focus_idx+1-numcards)+self.width, self.scroll_bar[3])
        else: self.width = 0
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
        dir = self.dir
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
            self.width = int(point.x) #+card.width*0.25
            self.scroll_bar = (0, -5*dir, self.width, -20*dir)
            #self.scroll_shift = self.width/len(self.cards)
    def render_after_transform(self):
        if self.dir == -1: y = -self.height
        else: y = 0
        if self.visible == 1:
            alpha = 1.0
            glColor4f(1., 1., 1., alpha)
            w, h = self.width+self.selected_width+self.padding*2, self.height+self.padding*4
            x = -self.padding
            render_9_part("box2",
                           w, h, x=x, y=y-self.padding*3)
                           #w, h, x=0, y=-20)
            if len(self.cards) > 1:
                glColor4f(1., 1., 1., 1.)
                l, b, r, t = self.scroll_bar
                glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
                render_9_part("track",
                    width=r-l, height=20, x=l, y=b)
                l, b, r, t = self.scroll
                render_9_part("thumb",
                        width=r-l, height=20, x=l, y=b)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            arrow_width = 10
            glColor4f(0,0,0,alpha)
            glBegin(GL_TRIANGLES)
            glVertex2f(x+1, arrow_width)
            glVertex2f(x+1, -arrow_width)
            glVertex2f(x-arrow_width, 0)
            glEnd()
        if self.cards:
            for card in self.cards[-1:self.focus_idx:-1]: card.draw()
            for card in self.cards[:self.focus_idx]: card.draw()
            self.focused.draw()
        for card in self.selected[::-1]: card.draw()
        #for label in self.selected_text: label.render()
