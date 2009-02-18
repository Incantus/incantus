"""<title>Menus, Toolboxes, a full Application</title>
Most all widgets are used in this example.  A full custom widget
is included.  A number of connections are used to make the application
function.
"""
import pygame
from pygame.locals import *

from pgu import gui
from Card import Card
from CardGroup import CardGroup

import game

class Cardspace(gui.Widget):
    NOTHING = 0
    DRAW_SELECTION = 1
    CARD_SELECTED = 2
    SELECTION_SELECTED = 3
    SELECTION_SPREAD_INIT = 4
    SELECTION_SPREAD = 5
    
    def __init__(self,**params):
        gui.Widget.__init__(self,**params)
        self.surface = None
    def init(self,cards,cinfo,v):
        self.surface = pygame.Surface((int(v['width']),int(v['height'])))
        color = '0xb0b0b0'
        self.bgcolor = pygame.Color(color)
        self.surface.fill(self.bgcolor)
        #self.overlay = pygame.Surface((int(v['width']),int(v['height'])),pygame.SRCALPHA,32)

        self.selectCard = None
        self.selectionRect = pygame.Rect((0,0,0,0))
        self.selectionCards = []
        self.cinfo = cinfo

        self.cardGroup = CardGroup(cards)
        self.cardGroup.shuffle()
        self.mode = self.NOTHING
        
    def event(self,e):
        if not self.surface: return
        if e.type == gui.MOUSEBUTTONDOWN:
            self.mouse_down(e)
        if e.type == gui.MOUSEMOTION:
            self.mouse_motion(e)
        if e.type is gui.MOUSEBUTTONUP:
            self.mouse_up(e)
    def paint(self,s):
        self.surface.fill(self.bgcolor)
        self.cardGroup.draw(self.surface)
        if self.selectionRect.width > 0 and self.selectionRect.height>0:
            pygame.draw.rect(self.surface,(0xff,0xff,0x00),self.selectionRect,1)
        s.blit(self.surface,(0,0))
        #s.blit(self.overlay,(0,0))
    def mouse_down(self,event):
        if self.mode == self.NOTHING:
            if self.selectionRect.width > 0 and self.selectionRect.height > 0:
                if self.selectionRect.collidepoint(event.pos[0],event.pos[1]):
                    # see if we are within the selection rectangle to drag it
                    self.mode = self.SELECTION_SELECTED
                    self.cardGroup.popCards(self.selectionCards)
        if self.mode == self.NOTHING:
            if len(self.selectionCards):
                self.cardGroup.popCards(self.selectionCards)
                self.cardGroup.dropCards(self.selectionCards)
                self.selectionCards = []
                self.selectionRect.size=(0,0)
            self.selectedCard = self.cardGroup.getCard(event.pos[0],event.pos[1], 0)
            if self.selectedCard:
                self.mode = self.CARD_SELECTED
                self.cinfo.showCard(self.selectedCard.key)
        # initiate selection rectangle
        if self.mode == self.NOTHING:
            self.selectionStart = (event.pos[0],event.pos[1])
            self.mode = self.DRAW_SELECTION
        self.repaint()

    def mouse_motion(self,event):
        if self.mode == self.SELECTION_SELECTED:
            #Handle the drag of a selection rectangle.
            if len(self.selectionCards):
                self.selectionRect.topleft = (self.selectionRect.x+event.rel[0],self.selectionRect.y+event.rel[1])
                for c in self.selectionCards:
                    c.move(event.rel[0],event.rel[1]);

        elif self.mode == self.CARD_SELECTED:
            #Handle the drag of a selected card.
            self.selectedCard.move(event.rel[0],event.rel[1]);

        elif self.mode == self.DRAW_SELECTION:
            #Handle the selection rectangle
            if event.pos[0] <= self.selectionStart[0]:
                self.selectionRect.x = self.selectionStart[0]-(self.selectionStart[0]-event.pos[0])
                self.selectionRect.width = self.selectionStart[0]-event.pos[0]
            else:
                self.selectionRect.x=self.selectionStart[0]
                self.selectionRect.width=event.pos[0]-self.selectionStart[0]

            if event.pos[1] <= self.selectionStart[1]:
                self.selectionRect.y = self.selectionStart[1]-(self.selectionStart[1]-event.pos[1])
                self.selectionRect.height = self.selectionStart[1]-event.pos[1]
            else:
                self.selectionRect.y=self.selectionStart[1]
                self.selectionRect.height=event.pos[1]-self.selectionStart[1]
        self.repaint()

    def mouse_up(self,event):
        if self.mode == self.SELECTION_SELECTED:
            self.mode = self.NOTHING
        elif self.mode == self.SELECTION_SPREAD or self.mode == self.SELECTION_SPREAD_INIT:
            self.mode = self.NOTHING
        elif self.mode == self.CARD_SELECTED:
            if event.button == 2:
                self.selectedCard.change_tap()
            self.cardGroup.dropCard(self.selectedCard)
            self.selectedCard = None
            self.mode = self.NOTHING
        elif self.mode == self.DRAW_SELECTION:
            if self.selectionRect.width>0 and self.selectionRect.height>0:
                self.selectionRect,self.selectionCards = self.cardGroup.getCards(self.selectionRect)
            self.mode = self.NOTHING
        self.repaint()
