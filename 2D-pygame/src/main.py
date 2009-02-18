#!/usr/local/bin/python2.4

import pygame
from MtG import App

if __name__ == "__main__":
    # Can only use default theme for the ChooseSelectionDialog (until the slider images are created)
    #theme = gui.Theme("gray")
    #app = App(theme=theme)
    pygame.display.set_icon(pygame.image.load("./data/MtG.png"))
    app = App()
    #pygame.display.set_caption("Magic the Gathering v0.1", "MtG")
    app.run()
