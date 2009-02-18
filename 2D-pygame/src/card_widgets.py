"""<title>Menus, Toolboxes, a full Application</title>
Most all widgets are used in this example.  A full custom widget
is included.  A number of connections are used to make the application
function.
"""
import math
import pygame
from pygame.locals import *

from pgu import gui
from Card import Card, FakeCard

from game import Action, GameEvent
from game.Match import isPermanent, isCreature, isLand, isPlayer

class CardArea(gui.Widget):
    NOTHING = 0
    CARD_SELECTED = 1
    def __init__(self,**params):
        params.setdefault('focusable',False)
        super(CardArea, self).__init__(**params)
        self.mode = self.NOTHING
        self.color = '0xb0b0b0'
    def init(self, cinfo):
        self.bgcolor = pygame.Color(self.color)
        self.cinfo = cinfo
        self.cardhover = None
        self.samecard = False
        self.cards = []
        self.selectedCard = None
    def set_zone(self, zone, active=True):
        self.zone = zone
        self.active = active
        self.update_cards()
    def update_cards(self): pass
    def find_card_rect(self, card):
        for c in self.cards:
            if card == c.gamecard: 
                return c.rect
                break
        else: False
    def paint(self,s):
        s.fill(self.bgcolor)
        for c in self.cards:
            c.draw(s)
        #if self.mode == self.CARD_SELECTED:
        #    pygame.draw.rect(s,(0xff,0xff,0x00),self.selectedCard.rect.inflate(2,2),1)
    def get_card(self, x, y):
        for i in range(len(self.cards)-1,-1,-1):
            if self.cards[i].rect.collidepoint(x,y):
                return self.cards[i]
    def event(self,event):
        if event.type == gui.MOUSEBUTTONDOWN:
            self.mouse_down(event)
        elif event.type == gui.MOUSEMOTION:
            self.mouse_motion(event)
        elif event.type is gui.MOUSEBUTTONUP:
            self.mouse_up(event)
        elif event.type is gui.ENTER:
            self.enter(event)
        elif event.type is gui.EXIT:
            self.exit(event)
        else:
            return super(CardArea,self).event(event)
    def enter(self, event): pass
    def exit(self, event): pass
    def mouse_motion(self,event):
        card = self.get_card(event.pos[0],event.pos[1])
        if card:
            if not card == self.cardhover:
                self.cinfo.showCard(card.key)
                self.cardhover = card
                self.samecard = False
            else: self.samecard = True
        else: self.cardhover = None
        #elif self.cardhover == None:
        #    self.cinfo.clear()
        #    self.cardhover = None
    def mouse_down(self,event):
        self.selectedCard = self.get_card(event.pos[0],event.pos[1])
        if self.selectedCard and self.active:
            self.mode = self.CARD_SELECTED
            #self.cinfo.showCard(self.selectedCard.key)
        else: self.mode = self.NOTHING
        #self.repaint()
    def mouse_up(self,event):
        card = self.get_card(event.pos[0],event.pos[1])
        if self.mode == self.CARD_SELECTED and self.selectedCard == card:
            pygame.event.post(pygame.event.Event(USEREVENT, {"action": Action.CardSelected(self.selectedCard.gamecard, self.zone)}))
            self.mode = self.NOTHING
        self.repaint()

class CardStack(CardArea):
    def __init__(self,**params):
        super(CardStack, self).__init__(**params)
        #self.font = pygame.font.Font("./data/themes/default/Inconsolata.otf", 12)
        self.font = pygame.font.Font("data/themes/default/Vera.ttf", 12)
    def setup_player_colors(self, player1, self_color, other_color):
        self.player1 = player1
        self.self_color = self_color
        self.other_color = other_color
    def update_cards(self):
        cards = []
        for ability in self.zone:
            # The stack stores a representation of the card
            if hasattr(ability, "card"):
                card = Card(ability.card.key, gamecard=ability.card)
                if ability.card.controller == self.player1: card.border_color = self.self_color
                else: card.border_color = self.other_color
            else:
                # No real card - for example combat damage
                card = FakeCard()
                card.border_color = (255,255,255)
            card.ability = ability  # This is so we return the ability if it is selected for a counterspell
            cards.append(card)

        self.cards = cards
        # layout cards
        numcards = len(cards)
        xpos = 5
        ypos = 5
        for card in cards:
            card.rect.x, card.rect.y = xpos, ypos
            ypos += 20
            xpos += 5
        self.overlay.clear_overlay()
        self.repaint()
    def mouse_up(self,event):
        if self.mode == self.CARD_SELECTED: #and event.button == 2:
            pygame.event.post(pygame.event.Event(USEREVENT, {"action": Action.CardSelected(self.selectedCard.ability, self.zone)}))
            self.mode = self.NOTHING
        self.repaint()
    def exit(self, event):
        self.overlay.clear_overlay()
        if self.cardhover:
            self.cardhover = None
            self.repaint()
    def mouse_motion(self,event):
        super(CardStack, self).mouse_motion(event)
        if self.cardhover:
            if not self.samecard:
                self.overlay.clear_overlay()
                if self.cardhover.gamecard:
                    self.overlay.show_targets(self.cardhover.gamecard, self.cardhover.rect, self.cardhover.ability.targets)
                else: self.overlay.show_damage(self.cardhover.ability.damages)
        else: self.overlay.clear_overlay()
    def paint(self,s):
        s.fill(self.bgcolor)
        # Draw text of ability on stack
        for c in self.cards:
            c.draw(s)
            if c == self.cardhover: border_color = (0,255,0)
            else: border_color = c.border_color
            pygame.draw.rect(s,border_color,c.rect.inflate(3,3), 3)
            ability_text = str(c.ability)
            #twidth, theight = self.font.size(ability_text)
            tx, ty = c.rect.topright
            s.blit(self.font.render(ability_text, 1, (0,0,0)),(tx+4, ty))

class CardsHand(CardArea):
    def __init__(self,**params):
        super(CardsHand, self).__init__(**params)
        self.color = "0x707070"
    def update_cards(self):
        cards = []
        for card in self.zone:
            guiCard = Card(card.key, gamecard=card)
            cards.append(guiCard)
        # layout cards
        numcards = len(cards)
        width = self.rect.w
        spacing = 15
        if cards:
            cardwidth = cards[0].rect.w
            total_width = numcards*cardwidth + (numcards-1)*spacing
            xpos = (width - total_width)/2
        # We iterate backwards to avoid putting the card at the beginning of the images
        # since order doesn't matter
        for card in cards[::-1]:
            card.rect.x, card.rect.y = xpos, 5
            xpos += cardwidth + spacing
        self.cards = cards
        self.repaint()
    def paint(self,s):
        s.fill(self.bgcolor)
        for card in self.cards:
            card.draw(s)
            if hasattr(card.gamecard, "onstack") and card.gamecard.onstack:
                rect = card.rect.inflate(0,0)
                pygame.draw.line(s,(255,255,255),rect.topleft,rect.bottomright,10)
                pygame.draw.line(s,(255,255,255),rect.topright,rect.bottomleft,10)
    def mouse_down(self,event):
        self.selectedCard = self.get_card(event.pos[0],event.pos[1])
        if self.selectedCard:
            if hasattr(self.selectedCard.gamecard, "onstack"):
                if not self.selectedCard.gamecard.onstack: self.mode = self.CARD_SELECTED
            else: self.mode = self.CARD_SELECTED
        else: self.mode = self.NOTHING

class CardsPlay(CardArea):
    def __init__(self,isother=False,**params):
        super(CardsPlay, self).__init__(**params)
        self.popup = False
        self.clear_popup = True
        self.isother = isother
    def update_cards(self):
        cards = []
        for card in self.zone:
            cards.append(Card(card.key, gamecard=card, inplay=True))
        self.cards = cards
        # Divide into two lines of cards (lands on the bottom)
        spacing = 15
        if cards:
            rows = [[], []]
            for card in cards[::-1]:
                if not isLand(card.gamecard): rows[0].append(card)
                else: rows[1].append(card)
            cardwidth, cardheight = cards[0].rect.w, cards[0].rect.h
            width, height = self.rect.w, self.rect.h
            total_width = [numcards*cardwidth+(numcards-1)*spacing for numcards in map(len,rows)]
            xpos = [(width - twidth)/2 for twidth in total_width]
            if not self.isother: ypos = [10, height - cardheight - 20]
            else: ypos = [height - cardheight - 20, 10]
            # layout cards
            for i, r in enumerate(rows):
                for card in r:
                    card.rect.x, card.rect.y = xpos[i], ypos[i]
                    #if hasattr(card.gamecard, "tapped") and card.gamecard.tapped:
                    if card.gamecard.tapped:
                        xpos[i] += cardheight+spacing
                        card.tap()
                    else: 
                        xpos[i] += cardwidth+spacing
                        card.untap()
        self.popup = None
        self.repaint()
    def paint(self,s):
        s.fill(self.bgcolor)
        for card in self.cards:
            card.draw(s)
        #if self.popup: self.draw_popup(s)
    def draw_popup(self, s):
        card = self.popup.gamecard
        if not isCreature(card): return
        popup_rect = pygame.rect.Rect((self.popup.rect.topleft), (57, 60))
        popup_rect.x += (self.popup.rect.w-popup_rect.w)/2
        popup_rect.y += (self.popup.rect.h-popup_rect.h)/2
        s.fill((255,255,255),popup_rect)
        pygame.draw.rect(s,(0,0,0), popup_rect, 1)
        PT = "%d/%d"%(card.base_power,card.base_toughness)
        twidth, theight = self.font.size(PT)
        tx, ty = popup_rect.bottomright
        tx, ty = tx - twidth - 2, ty - theight - 2
        s.blit(self.font.render(PT, 1, (0,0,0)),(tx,ty))
        
        power = card.power-card.base_power
        toughness = card.toughness-card.base_toughness
        PT = "%+d/%+d"%(power,toughness)
        twidth, theight = self.font.size(PT)
        tx, ty = popup_rect.right - twidth - 2, ty - theight - 2
        s.blit(self.font.render(PT, 1, (0,0,255)),(tx,ty))
        
        damage = str(card.currentDamage())
        dam = "(%s)"%damage
        twidth, theight = self.font.size(dam)
        tx, ty = popup_rect.bottomleft
        tx, ty = tx + 2, ty - theight - 2
        s.blit(self.font.render(dam, 1, (255,0,0)),(tx,ty))
    def mouse_motion(self,event):
        super(CardsPlay, self).mouse_motion(event)
        if self.cardhover:
            if not self.popup == self.cardhover:
                if isCreature(self.cardhover.gamecard):
                    self.popup = self.cardhover
                    self.clear_popup = False
                    self.repaint()
                else:
                    self.popup = None
                    if not self.clear_popup:
                        self.repaint()
                        self.clear_popup = True
        else:
            self.popup = None
            if not self.clear_popup:
                self.repaint()
                self.clear_popup = True

class CardInfo(gui.Widget):
    def __init__(self,**params):
        params.setdefault('focusable',False)
        gui.Widget.__init__(self,**params)
        self.size = (self.rect.w, self.rect.h)
        self.cardimage = None
        self.bgcolor = (0,0,0)
        self.old_focus = None
    def showCard(self, key):
        # XXX This focusing stuff is really hacky - I need to figure out if there is 
        # a better way to do it with PGU
        self.cardimage = self.cardlib.getCard(key,"large", self.size)
        if not self.container.container.mywindow == None:
            self.old_focus = self.container.container.mywindow
            self.focus()
        self.repaint()
    def clear(self):
        self.cardimage = None
        self.repaint()
    def paint(self,s):
        if self.cardimage: s.blit(self.cardimage,(0,0))
        else: s.fill(self.bgcolor)
        if self.old_focus:
            self.old_focus.focus()
            self.old_focus = None

class OverlayInfo(gui.Widget):
    def __init__(self,**params):
        params.setdefault('focusable', False)
        params.setdefault('glass', True)
        super(OverlayInfo, self).__init__(**params)
        self.font = pygame.font.Font("data/themes/default/Vera.ttf", 20)
        self.target_color = (0,255,0,200)
        self.damage_color = (255,0,0,200)
        self.alphacolor = (0,0,0,0) #(255,255,255)
    def init(self):
        w, h = self.rect.size
        self.overlay_plane = pygame.surface.Surface((w,h)).convert_alpha()
    def setup_overlay(self, main_status, other_status, main_play, other_play, main_hand, stack):
        get_pos = lambda area: (area.style.x,area.style.y)
        widget_names = ["main_status", "other_status", "main_play", "other_play", "main_hand", "stack"]
        widgets = [main_status, other_status, main_play, other_play, main_hand, stack]
        for n,w in zip(widget_names, widgets): setattr(self, n, (w, get_pos(w)))
        self.card_updates = {}
        self.arrows = []
    def update_overlay(self, sender, signal, card=None):
        if card:
            pos = None
            if signal == GameEvent.CardLeftZone() or signal == GameEvent.AbilityRemovedFromStack(): direction = "left"
            elif signal == GameEvent.CardEnteredZone() or signal == GameEvent.AbilityPlacedOnStack(): direction = "enter"
            # Find the card's zone
            for area, topleft in [self.main_play, self.other_play, self.main_hand, self.stack]:
                if sender == area.zone:
                    rect = area.find_card_rect(card)
                    pos = topleft[0]+rect.x+rect.w/2, topleft[1]+rect.y+rect.h/2
            info = self.card_updates.get(card)
            if info:
                if direction == "left":
                    start = pos
                    end = info["end"]
                else:
                    end = pos
                    start = info["start"]
                self.arrows.append((start,end))
                self.repaint()
            else:
                if direction == "left": self.card_updates[card] = {"start": pos}
                else: self.card_updates[card] = {"end": pos}
    def show_damage(self, damages):
        self.arrows[:] = []
        for damager, damage_assn in damages:
            for area, topleft in [self.main_play, self.other_play]:
                if damager.zone == area.zone:
                    rect = area.find_card_rect(damager)
                    start = topleft[0] + rect.x+rect.w/2, topleft[1]+rect.y+rect.h/2
            for damagee, amt in damage_assn.iteritems():
                if isPlayer(damagee):
                    for area, topleft in [self.main_status, self.other_status]:
                            if damagee == area.player:
                                end = topleft[0] + area.rect.w/2, topleft[1] +area.rect.h/2
                                break
                elif isPermanent(damagee):
                    for area, topleft in [self.main_play, self.other_play]:
                        if damagee.zone == area.zone:
                            rect = area.find_card_rect(damagee)
                            end = topleft[0] + rect.x+rect.w/2, topleft[1]+rect.y+rect.h/2
                            break
                self.arrows.append((start, end, amt, self.damage_color))
        self.repaint()
    def show_targets(self, card, rect, targets):
        from game.Ability import MultipleTargets
        self.arrows[:] = []
        topleft = self.stack[1]
        start = topleft[0] + rect.x+rect.w/2, topleft[1]+rect.y+rect.h/2
        for t in targets:
            if not isinstance(t, MultipleTargets): t = [t.target]
            else: t = t.target
            for i, tt in enumerate(t):
                if isPlayer(tt): # and t.targeting == None:
                    for area, topleft in [self.main_status, self.other_status]:
                        if tt == area.player:
                            end = topleft[0] + area.rect.w/2, topleft[1] +area.rect.h/2
                            break
                if isPermanent(tt):
                    for area, topleft in [self.main_play, self.other_play, self.stack]:
                        if tt.zone == area.zone:
                            rect = area.find_card_rect(tt)
                            end = topleft[0] + rect.x+rect.w/2, topleft[1]+rect.y+rect.h/2
                            break
                self.arrows.append((start, end, i+1, self.target_color))
        self.repaint()
    def clear_overlay(self):
        self.arrows[:] = []
        self.repaintall()
    def draw_arrow(self, s, color, p1, p2, change_length=0):
        p1x, p1y = p1
        p2x, p2y = p2
        width = 10
        length = math.sqrt(math.pow(p1x-p2x,2)+math.pow(p1y-p2y,2))-change_length
        cos, sin = (p2x-p1x)/length, (p2y-p1y)/length
        points = [(0, width),
                  (length-15, 0.5*width),
                  (length-20, 1.5*width),
                  (length, 0),
                  (length-20, -1.5*width),
                  (length-15, -0.5*width),
                  (0, -width)]
        points = [(x*cos-y*sin+p1x,x*sin+y*cos+p1y) for (x, y) in points]
        pygame.draw.polygon(s, color, points, 0)
        pygame.draw.polygon(s, (0,0,0, 200), points, 1)
    def paint(self,s):
        surf = self.overlay_plane
        if len(self.arrows) > 0:
            surf.fill(self.alphacolor)
            for start, end, num, color in self.arrows:
                txt = str(num)
                twidth, theight = self.font.size(txt)
                twidth /= 2; theight /= 2
                tx, ty = (end[0]-twidth), (end[1]-theight)
                radius = max(twidth, theight)
                self.draw_arrow(surf, color, start, end, change_length=radius)
                pygame.draw.circle(surf, (255,255,255,220), end, radius, 0)
                pygame.draw.circle(surf, (0,0,0), end, radius, 1)
                surf.blit(self.font.render(txt, 1, (0,0,0)),(tx,ty))

            s.blit(surf, (0,0))

