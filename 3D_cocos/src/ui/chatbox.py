from colors import *
import pyglet
from cocos.layer import Layer

# XXX Update this to work properly with cocos
class ChatBox(Layer):
    is_event_handler = True
    def __init__(self, x, y, width, height, ti_align='top'):
        super(ChatBox, self).__init__()
        #text_style = dict(font_name="Arial", color=white, font_size=14)
        text_style = dict(color=white, font_size=14)

        # Scrollable text display for chat messages.
        self.text_display = pyglet.text.document.UnformattedDocument()
        self.text_display.set_style(0, 0, text_style)
        self.td_layout = pyglet.text.layout.IncrementalTextLayout(self.text_display,
                                                                  width, height,
                                                                  multiline=True)
        # Text input with a caret for nice editing.
        self.text_input = pyglet.text.document.UnformattedDocument()
        self.text_input.set_style(0, 0, text_style)
        self.ti_layout = pyglet.text.layout.IncrementalTextLayout(self.text_input,
                                                                  width, 20)
        self.ti_layout.selection_color = black
        self.ti_layout.selection_background_color = grey
        self.ti_caret = pyglet.text.caret.Caret(self.ti_layout)
        self.ti_caret.color = grey[:-1]
        self.ti_align = ti_align

        self.width = width
        self.height = height
        self.td_layout.x = x
        self.ti_layout.x = x
        self.td_layout.y = y
        if self.ti_align != 'top':
            self.ti_layout.y = y - height
        else:
            self.ti_layout.y = y+25
        self.callback = self.add_text

    def add_text(self, text):
        self.text_display.insert_text(len(self.text_display.text), '\n' + text)
        self.td_layout.view_y -= 10000000 # Probably a little hackish.

    def on_text(self, text):
        if ord(text) != 13: # Hack. Do not want hard returns showing up.
            self.ti_caret.on_text(text)

    def on_text_motion(self, motion):
        self.ti_caret.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        self.ti_caret.on_text_motion_select(motion)

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ENTER:
            self.callback(self.text_input.text)
            self.text_input.text = ""
            self.ti_caret.position = 0

    def on_mouse_press(self, x, y, button, modifiers):
        self.ti_caret.on_mouse_press(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.ti_caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.td_layout.view_y += scroll_y * 2

    def on_activate(self):
        self.ti_caret.on_activate()

    def on_deactivate(self):
        self.ti_caret.on_deactivate()

    def draw(self):
        self.td_layout.draw()
        self.ti_layout.draw()

    def set_callback(self, callback):
        self.callback = callback
