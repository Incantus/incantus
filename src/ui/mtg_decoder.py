

import re

import pyglet
from pyglet.text.formats import structured

from resources import ImageCache

def decode_text(text):
    decoder = MtGDecoder()
    return decoder.decode(text)

_pattern = re.compile(r'''
       (?P<escape_symbol>\{(?P<symbol>[BCGQRTUWXYZ0123456789])\})
     | (?P<nl_hard>\n\s*)
     | (?P<text>[^\{\}\n]+)
       ''', re.VERBOSE | re.DOTALL)

# There is a bug with structured.ImageElement not passing in the correct
# flag for the vertices list to the batch (it uses v2i instead of v2f).
# Instead of fixing it just make a copy of that class with the fix
class ImageElement(pyglet.text.document.InlineElement):
    def __init__(self, image, width=None, height=None, text=None):
        self.image = image.get_texture()
        self.width = width is None and image.width or width
        self.height = height is None and image.height or height
        self.vertex_lists = {}
        self.labels = {}
        self.text = text

        anchor_y = self.height // image.height * image.anchor_y
        ascent = max(0, self.height - anchor_y)
        descent = min(-2, -anchor_y)
        super(ImageElement, self).__init__(ascent, descent, self.width)

    def place(self, layout, x, y):
        group = pyglet.graphics.TextureGroup(self.image.texture, 
                                             layout.top_group)
        x1 = x
        y1 = y + self.descent
        x2 = x + self.width
        y2 = y + self.height + self.descent
        vertex_list = layout.batch.add(4, pyglet.gl.GL_QUADS, group,
            ('v2f', (x1, y1, x2, y1, x2, y2, x1, y2)),
            ('c3B', (255, 255, 255) * 4),
            ('t3f', self.image.tex_coords))
        if self.text: self.labels[layout] = pyglet.text.Label(self.text,
                         font_name="MPlantin", font_size=14,
                         color=(0,0,0,255), anchor_x="center", anchor_y="center",
                         x=x1 + self.width/2, y=y1 + self.height/2,
                         batch=layout.batch, group=group)
        
        self.vertex_lists[layout] = vertex_list

    def remove(self, layout):
        self.vertex_lists[layout].delete()
        del self.vertex_lists[layout]
        if layout in self.labels:
            self.labels[layout].delete()
            del self.labels[layout]

class MtGDecoder(structured.StructuredTextDecoder):
    default_style = {
         'font_name': 'MPlantin',
         'margin_bottom': '6pt',
    }
         
    def decode_structured(self, text, location):
        self.location = location
        self.push_style('_default', self.default_style)

        # parse text for {} to replace with images
        for m in _pattern.finditer(text):
            group = m.lastgroup
            if group == 'text':
                t = m.group('text')
                self.add_text(t)
            elif group == 'nl_hard':
                self.add_text(u'\u2029')
            elif group == 'escape_symbol':
                symbol = 's'+m.group('symbol')
                image = ImageCache.get(symbol)
                if not image: 
                    image = ImageCache.get('sC')
                    self.add_element(ImageElement(image, width=16, height=16, text=symbol[1:]))
                else:
                    self.add_element(ImageElement(image, width=16, height=16))


