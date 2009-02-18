import pygame
import CardLibrary
from game.Match import isCreature

class FakeCard:
    def __init__(self):
        self.rect = CardLibrary.CardLibrary.getCardSize()
        self.key = None
        self.gamecard = None
    def draw(self,surface):
        pygame.draw.rect(surface,(0xff,0xff,0xff),self.rect,2)

class Card:
    def __init__(self,key,gamecard=None,x=0,y=0, inplay=False):
        self.key = key
        self.bimg = CardLibrary.CardLibrary.getCardBack()
        self.fimg = CardLibrary.CardLibrary.getCard(key)
        self.img = self.fimg
        self.side = 1
        self.rect = self.img.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.old_rect = self.rect
        self.gamecard = gamecard
        self.selected = 0
        self.inplay = inplay
        self.tapped = False

        self.overlay = CardLibrary.CardLibrary.overlay
        self.popup = CardLibrary.CardLibrary.popup
        self.smallfont = CardLibrary.CardLibrary.smallfont

        if self.inplay:
            self.status_ico = CardLibrary.CardLibrary.status_ico
            self.counter_ico = CardLibrary.CardLibrary.counter_ico
            self.card_status = CardLibrary.CardLibrary.card_status
            self.combat_status = CardLibrary.CardLibrary.combat_status
            self.creature_status = CardLibrary.CardLibrary.creature_status

    def flip(self):
        if self.side==1:
            self.side = 0
            self.img = self.bimg
        else:
            self.side = 1
            self.img = self.fimg

    def backSide(self):
        self.side = 0
        self.img = self.bimg

    def frontSide(self):
        self.side = 1
        self.img = self.fimg

    def switchSide(self,side):
        if side == 0: self.frontSide()
        else: self.backSide()

    def change_tap(self):
        if self.tapped: self.untap()
        else: self.tap()
    def tap(self):
        self.tapped = True
        self.img = CardLibrary.CardLibrary.getCardTapped(self.key)
        self.rect = self.img.get_rect()
        self.rect.x, self.rect.y = self.old_rect.x, self.old_rect.y
    def untap(self):
        self.tapped = False
        self.img = self.fimg
        self.rect = self.old_rect

    #def move(self,dx,dy):
    #    self.rect.x += dx
    #    self.rect.y += dy
    #    if self.child:
    #        self.child.move(dx,dy)

    def draw(self,surface):
        surface.blit(self.img,self.rect.topleft)
        # Clear overlay
        self.overlay.fill((0,0,0,0))
        self.draw_card_info(self.popup)
        if self.inplay: self.draw_card_stuff(self.overlay, self.popup)
        if not self.tapped:
            surface.blit(self.overlay, self.rect.topleft)
        else:
            surface.blit(pygame.transform.rotate(self.overlay, -90), self.rect.topleft)

    def draw_card_info(self, surf):
        rect = surf.get_rect()
        surf.fill((220,220,220))
        name = self.gamecard.name.split()
        x, y = rect.topleft
        box_width = rect.w
        y+=1
        for n in name:
            twidth, theight = self.smallfont.size(n)
            tx, ty = x+box_width/2-twidth/2, y - 1
            y += theight - 2
            surf.blit(self.smallfont.render(n, True, (0,0,0)), (tx,ty))

    def draw_card_stuff(self, overlay, popup):
        popup_rect = popup.get_rect()
        overlay_rect = overlay.get_rect()
        pos = [2,2]
        gamecard = self.gamecard

        def draw_ico(key, pos=pos):
            status_ico = self.status_ico[key]
            status_rect = status_ico.get_rect()
            overlay.blit(status_ico, pos)
            pos[0] = pos[0]+status_rect.w+2
            if pos[0] + status_rect.w > overlay_rect.w:
                pos[0] = 2
                pos[1] += status_rect.h
        [draw_ico(key) for key, check in self.card_status if check(gamecard)]
        if isCreature(gamecard):
            [draw_ico(key) for key, check in self.creature_status if check(gamecard)]
            if gamecard.in_combat:
                [draw_ico(key) for key, check in self.combat_status if check(gamecard)]
            # Now draw the current power/toughness
            popup_pos = popup_rect.bottomright
            power, toughness = gamecard.power, gamecard.toughness
            PT = "%d/%d"%(power,toughness)
            twidth, theight = self.smallfont.size(PT)
            tx, ty = popup_pos[0] - twidth-1, popup_pos[1] - theight
            popup.blit(self.smallfont.render(PT, True, (0,0,0)),(tx,ty))
            
            power -= gamecard.base_power
            toughness -= gamecard.base_toughness
            if not (power == 0 and toughness == 0):
                PT = "%+d/%+d"%(power,toughness)
                twidth, theight = self.smallfont.size(PT)
                tx, ty = popup_rect.w/2 - twidth/2, popup_pos[1] - theight
                popup.blit(self.smallfont.render(PT, True, (0,0,255)),(tx,ty))

            # Now the damage
            popup_pos = popup_rect.bottomleft
            damage = "(%s)"%str(gamecard.currentDamage())
            twidth, theight = self.smallfont.size(damage)
            tx, ty = popup_pos[0], popup_pos[1] - theight
            popup.blit(self.smallfont.render(damage, True, (255,0,0)),(tx,ty))
        
        for c in gamecard.counters:
            counter_ico = self.counter_ico[c.ctype]
            counter_rect = counter_ico.get_rect()
            overlay.blit(counter_ico, pos)
            pos[0] = pos[0]+counter_rect.w+2
            if pos[0] + counter_rect.w > overlay_rect.w:
                pos[0] = 2
                pos[1] += counter_rect.h
