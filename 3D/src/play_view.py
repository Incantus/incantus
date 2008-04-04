#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import pyglet
from pyglet.gl import *
import anim
import euclid
from anim_euclid import AnimatedVector3, AnimatedQuaternion

import math
import CardLibrary
from game import Match

from widget import Widget

class CombatZone(object):
    def __init__(self, attack_zone, block_zone):
        self.attack_zone = attack_zone
        self.block_zone = block_zone
        self.orig_attack_pos = self.attack_zone.pos
        self.orig_block_pos = self.block_zone.pos
    def layout_attackers(self, attackers):
        self.move_blocking_zone = False
        self.orig_card_pos = {}
        if self.attack_zone.is_opponent_view: self.orient = -1
        else: self.orient = 1
        guicard = list(self.attack_zone.cards)[0]
        self.zone_shift_vec = euclid.Vector3(0,0,guicard.size*guicard.height*self.orient)
        self.attack_zone.pos += self.zone_shift_vec

        self.block_zone.pos -= self.zone_shift_vec
        self.move_blocking_zone = True

        shift_vec = -self.zone_shift_vec * 1.5
        x = y = 0
        size = 0.01*1.1*self.orient
        cards = []
        positions = []
        for attacker in attackers:
            guicard = self.attack_zone.get_card(attacker)
            self.orig_card_pos[guicard.gamecard] = (guicard,guicard.pos)
            # XXX For some reason I need to keep the same y pos, or everything gets screwed up (selection wise)
            positions.append(euclid.Vector3(x, guicard.pos.y, 0))
            cards.append((guicard,attacker))
            x += size*guicard.spacing
        if positions: avgx = sum([p.x for p in positions])/len(positions)
        cards.sort(key=lambda a: a[0].pos.x)
        self.attackers = {}
        self.blocking_list = [None]*len(attackers)
        for i, ((guicard, attacker), pos) in enumerate(zip(cards, positions)):
            self.attackers[attacker] = (guicard,i)
            self.blocking_list[i] = (guicard, [])
            guicard.pos = pos + shift_vec - euclid.Vector3(avgx, 0, 0)
            guicard.can_layout = False
        self.total_blockers = 0
    def set_blockers_for_attacker(self, attacker, blockers):
        blocker_cards = []
        for b in blockers:
            guicard = self.block_zone.get_card(b)
            guicard.can_layout = False
            self.orig_card_pos[guicard.gamecard] = (guicard,guicard.pos)
            blocker_cards.append(guicard)
        blocker_cards.sort(key=lambda b: b.pos.x)
        self.total_blockers += len(blocker_cards)
        attacker_card, idx = self.attackers[attacker]
        self.blocking_list[idx] = (attacker_card, blocker_cards)
        self.layout_all()
        if not self.move_blocking_zone:
            self.block_zone.pos -= self.zone_shift_vec
            self.move_blocking_zone = True
    def layout_all(self):
        shift_vec = self.zone_shift_vec * 1.5
        x = y = 0
        size = 0.01*1.05*self.orient
        combat_sets = []
        for attacker, blocker_set in self.blocking_list:
            half_a = size*attacker.spacing / 2.
            positions = []
            if not blocker_set:
                x += half_a # size*attacker.spacing
                avgx = x
            else:
                if len(blocker_set) == 1:
                    width = -blocker_set[0].spacing*size*0.5
                    x += half_a
                else: width = 0
                for blocker in blocker_set:
                    width += size*blocker.spacing*0.5
                    positions.append((blocker, shift_vec+euclid.Vector3(x+width, blocker.pos.y, 0)))
                    width += size*blocker.spacing*0.5
                avgx = sum([p.x for c,p in positions])/len(positions)
            attacker_pos = euclid.Vector3(avgx, attacker.pos.y, attacker.pos.z)
            if len(blocker_set) < 2: x += half_a #attacker.spacing*self.orient*0.001
            else: x += width+attacker.width*size*0.1
            combat_sets.append((attacker, attacker_pos, blocker_set, positions))

        halfx = x/2
        for attacker, attacker_pos, blockers, positions in combat_sets:
            attacker.pos = attacker_pos - euclid.Vector3(halfx, 0, 0)
            for blocker, pos in positions:
                blocker.pos = pos - euclid.Vector3(halfx, 0, 0)
    def restore_orig_pos(self):
        self.attack_zone.pos = self.orig_attack_pos
        self.block_zone.pos = self.orig_block_pos
        for guicard, orig_pos in self.orig_card_pos.values():
            guicard.pos = orig_pos
            guicard.can_layout = True
        self.attack_zone.layout()
        self.block_zone.layout()

class PlayView(Widget):
    def cards():
        def fget(self):
            for c in self.creatures: yield c
            for c in self.other_perms: yield c
            for l in self.lands.values():
                for c in l: yield c
        return locals()
    cards = property(**cards())
    def __init__(self, z, is_opponent_view=False):
        super(PlayView,self).__init__(pos = euclid.Vector3(0,0,z))
        self.visible = True
        #self._pos.set_transition(dt=0.5, method="ease_out_circ")
        self.is_opponent_view = is_opponent_view

        self.lands = dict([(land,[]) for land in ['Forest', 'Mountain', 'Swamp', 'Plains', 'Island', 'Other']])
        self.creatures = []
        self.other_perms = []
    def clear(self):
        self.creatures = []
        self.other_perms = []
        self.lands = dict([(land,[]) for land in ['Forest', 'Mountain', 'Swamp', 'Plains', 'Island', 'Other']])
    def add_card(self, card, startt):
        guicard = CardLibrary.CardLibrary.getPlayCard(card)
        guicard.entering_play()
        guicard._pos.set(euclid.Vector3(0,0,0))
        if Match.isCreature(card): self.creatures.insert(0, guicard)
        elif Match.isLand(card):
            for key in self.lands.keys():
                if card.subtypes == key:
                    self.lands[key].append(guicard)
                    break
            else: self.lands['Other'].append(guicard)
        else: self.other_perms.insert(0, guicard)
        self.layout()
        guicard._orientation.set(euclid.Quaternion.new_rotate_axis(-math.pi/2, euclid.Vector3(1,0,0)))
        if self.is_opponent_view: guicard.orientation *= euclid.Quaternion.new_rotate_axis(math.pi, euclid.Vector3(0,0,1))
        if card.tapped: guicard.tap()
        if startt != 0: guicard.visible = anim.animate(0,1,dt=startt, method="step")
        guicard.size = anim.animate(0.005, 0.010, dt=0.2, method="sine")
        guicard.alpha = anim.animate(0.5, 1,startt=startt, dt=1.0, method="ease_out_circ")
        # XXX Now set by the card itself
        guicard._orientation.set_transition(dt=0.3, method="sine")
        #guicard._pos.set_transition(dt=0.4, method="ease_out_circ") #"ease_out_back")
        #guicard._pos.y = anim.animate(guicard._pos.y, guicard._pos.y, dt=0.4, method="ease_out")
        return guicard
    def remove_card(self, card, clock):
        guicard = CardLibrary.CardLibrary.getPlayCard(card)
        guicard.leaving_play()
        #if Match.isCreature(card): cardlist = self.creatures
        #elif Match.isLand(card):
        #    for key in self.lands.keys():
        #        if card.subtypes == key:
        #            cardlist = self.lands[key]
        #            break
        #    else: cardlist = self.lands['Other']
        #else: cardlist = self.other_perms
        for cardlist in [self.creatures]+self.lands.values()+[self.other_perms]:
            if guicard in cardlist: break
        guicard.alpha = anim.animate(1, 0.25, dt=1.5, method="ease_in_circ")
        # XXX This breaks if a card from one list (like an artifact) gains the creature role, and is removed from play before losing the role
        clock.schedule_once(lambda t: cardlist.remove(guicard) or self.layout(), 1.5)
    def card_tapped(self, sender):
        card = CardLibrary.CardLibrary.getPlayCard(sender)
        if card in self.cards:
            card.tap()
            self.layout()
    def card_untapped(self, sender):
        card = CardLibrary.CardLibrary.getPlayCard(sender)
        if card in self.cards:
            card.untap()
            self.layout()
    def layout(self):
        if self.is_opponent_view:
            orient = -1
            compare = min
        else: 
            orient = 1
            compare = max
        size = 0.01*1.1 * orient
        y_incr = 0.001
        row = 0
        def layout_subset(cardlist, y, row):
            x = 0
            max_row_height = 0
            positions = []
            for card in cardlist:
                if not card.can_layout: continue
                halfx = size*card.spacing*0.5
                x += halfx
                positions.append(euclid.Vector3(x, y, row))
                x += halfx
                y += y_incr
                max_row_height = compare(max_row_height, size*card.height)
            if positions: avgx = sum([p.x for p in positions])/len(positions)
            for pos, card in zip(positions, cardlist):
                if not card.can_layout: continue
                card.pos = pos - euclid.Vector3(avgx, 0, 0)
            return (y,max_row_height)

        y, max_row_height = layout_subset(self.creatures, 0.1, row)
        row += max_row_height
        y, max_row_height = layout_subset(self.other_perms, y, row)
        row += max_row_height
        x = 0.
        max_row_height = 0
        positions = []
        for landtype in ['Forest', 'Mountain', 'Swamp', 'Plains', 'Island']:
            lands = self.lands[landtype]
            z = 0
            i = 0
            for card in lands:
                if i == 5:
                    i = z = 0
                    x += size*card.spacing
                if not card.can_layout: continue
                halfx = 0.1*size*card.spacing*0.5
                x += halfx
                positions.append(euclid.Vector3(x, y, row+z))
                x += halfx
                z += 0.1*size*card.height
                y += y_incr
                max_row_height = compare(max_row_height, z+size*card.height)
                i += 1
            if len(lands): x += size*card.spacing
        i = 0
        if positions: avgx = sum([p.x for p in positions])/len(positions)
        for landtype in ['Forest', 'Mountain', 'Swamp', 'Plains', 'Island']:
            lands = self.lands[landtype]
            for card in lands:
                if not card.can_layout: continue
                card.pos = positions[i] - euclid.Vector3(avgx, 0, 0)
                i += 1
        lands = self.lands["Other"]
        row += max_row_height
        positions = []
        for card in lands:
            if not card.can_layout: continue
            halfx = size*card.spacing*0.5
            x += halfx
            positions.append(euclid.Vector3(x, y, row))
            x += halfx
            y += y_incr
        if positions: avgx = sum([p.x for p in positions])/len(positions)
        for pos,card in zip(positions, lands):
            if not card.can_layout: continue
            card.pos = pos - euclid.Vector3(avgx,0,0)
    def get_card(self, gamecard):
        for card in self.cards:
            if card.gamecard == gamecard: return card
        else: return None
    def get_card_from_hit(self, select_ray):
        hits = []
        m = euclid.Matrix4()
        m.translate(*tuple(-self.pos)) # 0, 0, -self.z)
        select_ray = m*select_ray
        for card in self.cards:
            result = card.intersects(select_ray)
            if result:
                hits.append((card, result))

        if not hits: return
        hits.sort(cmp=lambda x, y: cmp(abs(x[1] - select_ray.p), abs(y[1] - select_ray.p)))
        selected = hits[0][0]
        spot=hits[0][1]
        return selected
    def render_after_transform(self):
        for card in self.cards: card.draw()

class Table(object):
    def __init__(self):
        self.table_plane = euclid.Plane(euclid.Point3(0., 0, 0.), euclid.Vector3(0., 1., 0.))
        self.render_redzone = False
        self.background = pyglet.image.load("./data/images/hardwoodfloor.png").texture
    def draw(self):
        SIZE = 8
        z = 0 #5
        glNormal3f(.0, 1., .0)
        for x in range(-4*SIZE, 4*SIZE, SIZE):
            for y in range(-4*SIZE, 4*SIZE, SIZE):
                if ((x + y) / SIZE) % 2:
                    glColor3f(0.1, 0.1, 0.1)
                else:
                    glColor3f(0.3, 0.3, 0.3)
                glEnable(GL_TEXTURE_2D)
                tc = self.background.tex_coords
                glBindTexture(self.background.target, self.background.id)
                glBegin(GL_QUADS)
                glTexCoord2f(tc[0], tc[1])
                glVertex3f(x, z, y)
                glTexCoord2f(tc[3], tc[4])
                glVertex3f(x+SIZE, z, y)
                glTexCoord2f(tc[6], tc[7])
                glVertex3f(x+SIZE, z, y+SIZE)
                glTexCoord2f(tc[9], tc[10])
                glVertex3f(x, z, y+SIZE)
                glEnd()
        if self.render_redzone:
            x = 4*SIZE
            ymin = -3
            ymax = 3
            z += 0.001
            glColor4f(1.0, 0.0, 0.0, 0.8)
            glBegin(GL_QUADS)
            glVertex3f(-x, z, ymin)
            glVertex3f(x, z, ymin)
            glVertex3f(x, z, ymax)
            glVertex3f(-x, z, ymax)
            glEnd()
