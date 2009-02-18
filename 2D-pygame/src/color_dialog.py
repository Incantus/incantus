"""<title>Custom Actions</title>"""
import pygame
from pgu import gui

class ColorDialog(gui.Dialog):
    def __init__(self,value,**params):
        self.value = list(pygame.Color(value))
        title = gui.Label("Color Picker")
        main = gui.Table()
        main.tr()
        
        self.color = gui.Color(self.value,width=64,height=64)
        main.td(self.color,rowspan=3,colspan=1)
        
        ##The sliders CHANGE events are connected to the adjust method.  The 
        ##adjust method updates the proper color component based on the value
        ##passed to the method.
        ##::
        main.td(gui.Label(' Red: '),1,0)
        e = gui.HSlider(value=self.value[0],min=0,max=255,size=32,width=128,height=16)
        e.connect(gui.CHANGE,self.adjust,(0,e))
        main.td(e,2,0)
        ##

        main.td(gui.Label(' Green: '),1,1)
        e = gui.HSlider(value=self.value[1],min=0,max=255,size=32,width=128,height=16)
        e.connect(gui.CHANGE,self.adjust,(1,e))
        main.td(e,2,1)

        main.td(gui.Label(' Blue: '),1,2)
        e = gui.HSlider(value=self.value[2],min=0,max=255,size=32,width=128,height=16)
        e.connect(gui.CHANGE,self.adjust,(2,e))
        main.td(e,2,2)

        ok = gui.Button("OK")
        ok.connect(gui.CLICK, self.close,None)
        main.td(gui.Spacer(width=5,height=5),1,4,colspan=3)
        main.td(ok,1,5,colspan=3)
                        
        gui.Dialog.__init__(self,title,main)
        
    ##The custom adjust handler.
    ##::
    def adjust(self,value):
        n,e = value
        self.value[n] = e.value
        #self.repaint() 
        self.color.repaint()
        self.send(gui.CHANGE)
    ##
