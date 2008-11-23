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
    def setup_attack_zone(self):
        self.orig_card_pos = {}
        if self.attack_zone.is_opponent_view:
            self.orient = -1
            self.compare = min
        else:
            self.orient = 1
            self.compare = max
        guicard = list(self.attack_zone.cards)[0]
        self.zone_shift_vec = euclid.Vector3(0,0,2.5*self.orient)
        self.attack_zone.pos += self.zone_shift_vec
        self.orig_attacker_pos = {}
        self.orig_blocker_pos = {}
        self.attackers = []
        self.attacker_map = {}
    def setup_block_zone(self):
        self.block_zone.pos -= self.zone_shift_vec
    def restore_orig_pos(self):
        self.hide_combat_zones()
        self.reset_attackers()
        self.reset_blockers()
    def hide_combat_zones(self):
        self.attack_zone.pos = self.orig_attack_pos
        self.block_zone.pos = self.orig_block_pos
    def reset_attackers(self):
        self.attackers = []
        for guicard, orig_pos in self.orig_attacker_pos.values():
            guicard.pos = orig_pos
            guicard.can_layout = True
        self.attack_zone.layout()
    def reset_blockers(self):
        for guicard, orig_pos in self.orig_blocker_pos.values():
            guicard.pos = orig_pos
            guicard.can_layout = True
        self.block_zone.layout()
    def add_attacker(self, attacker):
        guicard = self.attack_zone.get_card(attacker)
        self.orig_attacker_pos[guicard.gamecard] = (guicard,guicard.pos)
        self.attackers.append(guicard)
        self.attacker_map[attacker] = guicard
        guicard.can_layout = False
        self.layout_attackers()
    def layout_attackers(self):
        shift_vec = -self.zone_shift_vec * 1.5
        size = 0.01*1.1*self.orient
        self.attack_zone.layout_subset(self.attackers, size, 0.1, 0.001, shift_vec.z, self.compare, combat=True)
    def declare_attackers(self):
        self.blocking_list = dict([(attacker, []) for attacker in self.attackers])
        self.layout_attackers()
    def set_blocker_for_attacker(self, attacker, blocker):
        guicard = self.block_zone.get_card(blocker)
        guicard.can_layout = False
        self.orig_blocker_pos[guicard.gamecard] = (guicard,guicard.pos)

        attacker_gui = self.attacker_map[attacker]
        self.blocking_list[attacker_gui].append(guicard)
        self.layout_all()
    def layout_card(self, zone, card, size, startx, y, row):
        positions = []
        cards = []
        big_halfx = size*card.spacing*0.5
        x = z = 0
        if not len(card.gamecard.attachments): halfx = big_halfx
        else:
            x += big_halfx
            halfx = 0.1*size*card.spacing*0.5
        for attachment in card.gamecard.attachments[::-1]:
            attachment = zone.get_card(attachment)
            if not attachment: continue
            x += halfx
            positions.append(euclid.Vector3(x, y, row+z))
            cards.append(attachment)
            x += halfx
            z += 0.1*size*card.height
            y += 0.01
        x += halfx
        positions.append(euclid.Vector3(x, y, row+z))
        avgx = startx-sum([pos.x for pos in positions])/len(positions)
        cards.append(card)
        for pos in positions: pos += euclid.Vector3(avgx, 0, 0)
        width = x
        return (width, cards, positions)
    def layout_all(self):
        shift_vec = self.zone_shift_vec * 1.5
        x = 0
        size = 0.01*1.05*self.orient
        cards = []
        total_positions = []
        for attacker in self.attackers:
            blocker_set = self.blocking_list[attacker]
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
                    #positions.append(euclid.Vector3(x+width, blocker.pos.y, shift_vec.z))
                    #cards.append(blocker)
                    #width += size*blocker.spacing*0.5
                    half_b, blocker_cards, blocker_positions = self.layout_card(self.block_zone, blocker, size, x+width, blocker.pos.y, shift_vec.z)
                    cards.extend(blocker_cards)
                    positions.extend(blocker_positions)
                    width += half_b
                avgx = sum([pos.x for pos in positions])/len(positions)
                total_positions.extend(positions)
            half_a, attacker_cards, positions = self.layout_card(self.attack_zone, attacker, size, avgx, attacker.pos.y, -shift_vec.z)
            total_positions.extend(positions)
            cards.extend(attacker_cards)
            if len(blocker_set) < 2: x += half_a
            else: x += width+attacker.width*size*0.1

        halfx = x/2
        for card, position in zip(cards, total_positions):
            card.pos = position - euclid.Vector3(halfx, 0, 0)
    def layout_all2(self):
        shift_vec = self.zone_shift_vec * 1.5
        x = 0
        size = 0.01*1.05*self.orient
        combat_sets = []
        for attacker in self.attackers:
            blocker_set = self.blocking_list[attacker]
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
            if len(blocker_set) < 2: x += half_a
            else: x += width+attacker.width*size*0.1
            combat_sets.append((attacker, attacker_pos, blocker_set, positions))

        halfx = x/2
        for attacker, attacker_pos, blockers, positions in combat_sets:
            attacker.pos = attacker_pos - euclid.Vector3(halfx, 0, 0)
            for blocker, pos in positions:
                blocker.pos = pos - euclid.Vector3(halfx, 0, 0)


landtypes = ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest', 'Other']

class PlayView(Widget):
    def cards():
        def fget(self):
            for c in self.creatures: yield c
            for c in self.other_perms: yield c
            for c in self.attached: yield c
            for l in self.lands.values():
                for c in l: yield c
        return locals()
    cards = property(**cards())
    def __init__(self, z, is_opponent_view=False):
        super(PlayView,self).__init__(pos = euclid.Vector3(0,0,z))
        self.visible = True
        #self._pos.set_transition(dt=0.5, method="ease_out_circ")
        self.is_opponent_view = is_opponent_view

        self.clear()
    def clear(self):
        self._card_map = {}
        self.creatures = []
        self.other_perms = []
        self.attached = []
        self.lands = dict([(land,[]) for land in landtypes])
    def add_card(self, card, startt):
        guicard = CardLibrary.CardLibrary.getPlayCard(card)
        self._card_map[card.key] = guicard
        guicard.entering_play()
        guicard._pos.set(euclid.Vector3(0,0,0))
        if Match.isCreature(card):
            self.creatures.insert(0, guicard)
            guicard._row = self.creatures
        elif Match.isLand(card):
            for key in self.lands.keys():
                if card.subtypes == key:
                    self.lands[key].append(guicard)
                    guicard._row = self.lands[key]
                    break
            else:
                self.lands['Other'].append(guicard)
                guicard._row = self.lands['Other']
        elif Match.isAura(card) and Match.isPermanent(card.attached_to):
            # it should be attached at this point
            self.attached.append(guicard)
            guicard._row = self.attached
            self.card_attached(card, card.attached_to)
        else:
            self.other_perms.insert(0, guicard)
            guicard._row = self.other_perms
        guicard._orientation.set(euclid.Quaternion.new_rotate_axis(-math.pi/2, euclid.Vector3(1,0,0)))
        if self.is_opponent_view: guicard.orientation *= euclid.Quaternion.new_rotate_axis(math.pi, euclid.Vector3(0,0,1))
        if card.tapped: guicard.tap()
        self.layout()

        if startt != 0: guicard.visible = anim.animate(0,1,dt=startt, method="step")
        guicard.size = anim.animate(0.005, 0.010, dt=0.2, method="sine")
        guicard.alpha = anim.animate(0.5, 1,startt=startt, dt=1.0, method="ease_out_circ")
        guicard._orientation.set_transition(dt=0.2, method="sine")
        guicard._pos.set_transition(dt=0.2, method="ease_out_circ") #"ease_out_back")
        #guicard._pos.y = anim.animate(guicard._pos.y, guicard._pos.y, dt=0.4, method="sine") #"ease_out")
        return guicard
    def remove_card(self, card, clock):
        guicard = self._card_map.pop(card.key)
        guicard.leaving_play()
        for cardlist in [self.creatures,self.other_perms,self.attached]+self.lands.values():
            if guicard in cardlist: break
        guicard.alpha = anim.animate(1, 0.25, dt=1.5, method="ease_in_circ")
        clock.schedule_once(lambda t: cardlist.remove(guicard), 1.4)
        clock.schedule_once(lambda t: self.layout(), 1.5)
    def card_attached(self, sender, attached):
        attachment = self.get_card(sender)
        attached = self.get_card(attached)
        if attachment and attached:
            self.attached.append(attachment)
            attachment._row.remove(attachment)
            if Match.isBasicLand(attached.gamecard):
                attached._row.remove(attached)
                self.lands["Other"].append(attached)
            self.layout()
    def card_unattached(self, sender, unattached):
        attachment = self.get_card(sender)
        unattached = self.get_card(unattached)
        if attachment and unattached and attachment in self.attached:
            self.attached.remove(attachment)
            attachment._row.append(attachment)
            if Match.isBasicLand(unattached.gamecard):
                self.lands["Other"].remove(unattached)
                unattached._row.append(unattached)
            self.layout()
    def card_tapped(self, sender):
        card = self.get_card(sender)
        if card in self.cards:
            card.tap()
            self.layout()
    def card_untapped(self, sender):
        card = self.get_card(sender)
        if card in self.cards:
            card.untap()
            self.layout()
    def layout_subset(self, cardlist, size, y, y_incr, row, compare, combat=False):
        x = 0
        max_row_height = 0
        positions = []
        cards = []
        max_per_row = 25
        num_per_row = 0
        for card in cardlist:
            if not combat and not card.can_layout: continue
            z = 0
            big_halfx = size*card.spacing*0.5
            if not len(card.gamecard.attachments): halfx = big_halfx
            else:
                x += big_halfx
                halfx = 0.1*size*card.spacing*0.5
            for attachment in card.gamecard.attachments[::-1]:
                attachment = self.get_card(attachment)
                if not attachment: continue
                x += halfx
                positions.append(euclid.Vector3(x, y, row+z))
                cards.append(attachment)
                x += halfx
                z += 0.1*size*card.height
                y += y_incr
                max_row_height = compare(max_row_height, z+size*card.height)
            x += halfx
            positions.append(euclid.Vector3(x, y, row+z))
            cards.append(card)
            y += y_incr
            max_row_height = compare(max_row_height, z+size*card.height)
            x += big_halfx
            num_per_row += 1
            if num_per_row%max_per_row==0:
                row += max_row_height
                x = 0

        if positions: avgx = sum([p.x for p in positions])/len(positions)
        for pos, card in zip(positions, cards):
            if not combat and not card.can_layout: continue
            card.pos = pos - euclid.Vector3(avgx, 0, 0)
        row += max_row_height
        return (y,row)
    def layout(self):
        if self.is_opponent_view:
            orient = -1
            compare = min
        else:
            orient = 1
            compare = max
        size = 0.01*1.1 * orient
        y_incr = 0.005
        row = 0

        y, row = self.layout_subset(self.creatures, size, 0.1, y_incr, row, compare)
        y, row = self.layout_subset(self.other_perms+self.lands["Other"], size, y, y_incr, row, compare)

        x = 0.
        max_row_height = 0
        positions = []
        for landtype in landtypes[:-1]:
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
        for landtype in landtypes[:-1]:
            lands = self.lands[landtype]
            for card in lands:
                if not card.can_layout: continue
                card.pos = positions[i] - euclid.Vector3(avgx, 0, 0)
                i += 1
        #lands = self.lands["Other"]
        #row += max_row_height
        #y, max_row_height = self.layout_subset(lands, size, y, y_incr, row, compare)
    def get_card(self, card): return self._card_map.get(card.key, None)
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
                    glColor3f(0.2, 0.2, 0.2)
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
            ymin = -3.2
            ymax = 3.2
            z += 0.001
            glColor4f(1.0, 0.0, 0.0, 0.8)
            glBegin(GL_QUADS)
            glVertex3f(-x, z, ymin)
            glVertex3f(x, z, ymin)
            glVertex3f(x, z, ymax)
            glVertex3f(-x, z, ymax)
            glEnd()
