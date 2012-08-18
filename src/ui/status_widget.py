__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import pyglet
from pyglet.gl import *
import anim, math
import euclid
import mtg_decoder
from widget import Widget, Image, Label
from engine import Mana
from resources import ImageCache, render_9_part
from card_view import ZoneView

zero = euclid.Vector3(0,0,0)

class Button(Widget):
    def __init__(self, text='', pos=zero):
        super(Button, self).__init__(pos)
        self._padding = 12
        self.toggled = False
        self.visible = anim.constant(1)
        self.label = pyglet.text.Label('', font_size=12, color=(0,0,0,255),
        #self.label = pyglet.text.Label(text, font_size=12, color=(255,255,255,255),
                                    anchor_x = "center", anchor_y = "center",
                                    x = 0, y = 0)
        self.set_text(text)
    def set_text(self, text):
        self.label.text = text
        self.width = self.label.content_width+self._padding*2
        self.height = 32 #self.label.content_height+self._padding*2
    def render_after_transform(self):
        w, h = self.width, self.height
        glColor4f(1.0, 1.0, 1.0, 1.0)
        #render_9_part("box3" if not self.toggled else "box5",
        render_9_part("button2" if not self.toggled else "button3",
                      w, h,
                      x = -w/2, y = -h/2)
        self.label.draw()

class MessageDialog(Widget):
    def __init__(self, pos=zero):
        super(MessageDialog,self).__init__(pos)
        self.visible = 0
        self._size = 11
        self._padding = 10
        self._button1 = Button()
        self._button2 = Button()
        self.width, self.height = 250, 100
        self.prompt = pyglet.text.Label('', multiline=True,
                           anchor_x = "left", anchor_y="center",
                           x = -self.width/2+self._padding, 
                           y = self.height/6, width= self.width-self._padding)
    def handle_click(self, x, y):
        for item, val in [(self._button1, True), (self._button2, False)]:
            sw, sh = item.width, item.height
            sx, sy = item.pos.x-sw/2, item.pos.y-sh/2
            if x > sx and x < sx+sw and y >= sy and y <= sy+sh: return (item, val)
        else: return None, -1
    def construct(self, text, options=None, msg_type="ask"):
        self.prompt.document = mtg_decoder.decode_text(text)
        self.prompt.set_style("color", (0,0,0,255))
        self.prompt.set_style("font_name", "Arial")
        self.prompt.set_style("font_size", self._size)
        #Now layout
        b1, b2 = self._button1, self._button2
        if msg_type == "prompt":
            b1.visible, b2.visible = 0, 0
        elif msg_type == "notify":
            b1.set_text(options)
            b1.visible, b2.visible = 1, 0
            y = 2.5*self._padding + (-self.height)/2
            b1.pos = euclid.Vector3((self.width-b1.width)/2-self._padding, y, 0)
        elif msg_type == "ask":
            b1.set_text(options[0])
            b2.set_text(options[1])
            b1.visible, b2.visible = 1, 1
            y = 2.5*self._padding + (-self.height)/2
            b1.pos = euclid.Vector3((self.width-b1.width)/2-b2.width-2*self._padding, y, 0)
            b2.pos = euclid.Vector3((self.width-b2.width)/2-self._padding, y, 0)
        
    def render_after_transform(self):
        w, h = self.width, self.height
        glColor4f(0.9, 0.9, 0.9, 1.0)
        render_9_part("box1",
                      w, h,
                      x = -w/2, y = -h/2)
        self.prompt.draw()
        self._button1.render()
        self._button2.render()

class SelectionList(Widget):
    alpha = anim.Animatable()
    def __init__(self, pos=zero):
        super(SelectionList,self).__init__(pos)
        #self.options = []
        #self.alpha = anim.animate(0, 0.9, dt=1.0, method="sine")
        self.border = 20
        self.visible = anim.constant(0)
        #self.focus_idx = 0
        self.large_size = 17
        self.max_width = 700
        #self.small_scale = 0.35
        #self.intermediate_scale = 0.55
        #self.layout = self.layout_normal
        self.prompt = Label("", size=self.large_size, halign="center", shadow=False)
    #def move_up(self):
    #    if self.visible == 1 and self.focus_idx > 0:
    #        self.focus_dir = -1
    #        self.options[self.focus_idx], self.options[self.focus_idx+self.focus_dir] = self.options[self.focus_idx+self.focus_dir], self.options[self.focus_idx]
    #        self.focus_idx += self.focus_dir
    #        self.layout()
    #def move_down(self):
    #   if self.visible == 1 and self.focus_idx < len(self.options)-1:
    #        self.focus_dir = 1
    #        self.options[self.focus_idx], self.options[self.focus_idx+self.focus_dir] = self.options[self.focus_idx+self.focus_dir], self.options[self.focus_idx]
    #        self.focus_idx += self.focus_dir
    #        self.layout()
    #def focus_previous(self):
    #    if self.visible == 1 and self.focus_idx > 0:
    #        self.focus_dir = -1
    #        self.focus_idx += self.focus_dir
    #        self.layout()
    #def focus_next(self):
    #   if self.visible == 1 and self.focus_idx < len(self.options)-1:
    #        self.focus_dir = 1
    #        self.focus_idx += self.focus_dir
    #        self.layout()
    #def hide(self):
    #    for item, val in self.options:
    #        item.pos = zero
    #    self.visible = anim.animate(1., 0.0, dt=0.1)
    def construct(self, prompt, sellist):
        self.prompt.set_text(prompt)
        max_width = self.max_width
        document = mtg_decoder.decode_text(u'\u2028'.join([str(val[0]) for val in sellist]))
        choice_list = pyglet.text.DocumentLabel(document, multiline=True, width=max_width,
                           anchor_x = "center", anchor_y="center")
        choice_list.set_style("color", (255,255,255,255))
        choice_list.set_style("font_name", "Arial")
        choice_list.set_style("font_size", 13.5)
        choice_list.set_style("halign", "center")
        self.choice_list = choice_list
        self.choices = [val[1] for val in sellist]
        #self.options = [(Label(str(val[0]), size=13.5, halign="center", shadow=False), val[1]) for val in sellist]
        #y = 0
        #for item, val in self.options:
        #    item._scale = anim.animate(1.0, 1.0, dt=dt, method=method)
        #self.focus_idx = len(self.options)/2
        #self.layout()
        #self.width = max([item[0].width for item in self.options]+[self.prompt.width])
        #self.height = sum([item[0].height for item in self.options]+[self.prompt.height])
        #self.scroll = self.height/len(self.options)
        self.width = max(self.prompt.width, choice_list.content_width)
        self.height = choice_list.content_height+self.prompt.height
        self.prompt._pos.set(euclid.Vector3(0,(self.height-self.prompt.height)/2, 0))
        choice_list.x = (max_width-self.width)/2
    #def layout_normal(self):
    #    x = y = 0
    #    self.prompt.scale = 0.7
    #    y -= self.prompt.height
    #    self.prompt.pos = euclid.Vector3(0, y, 0)
    #    for option, val in self.options:
    #        #option.scale = 0.45
    #        y -= option.height
    #        option.pos = euclid.Vector3(0, y, 0)
    #def layout_resize(self):
    #    x = y = 0
    #    idx = self.focus_idx
    #    self.prompt.scale = 0.7
    #    y -= self.prompt.height
    #    self.prompt.pos = euclid.Vector3(0, y, 0)
    #    count = 0
    #    for option, val in self.options[:idx]:
    #        if count == idx - 1: option.scale = self.intermediate_scale
    #        else: option.scale = self.small_scale
    #        y -= option.height
    #        option.pos = euclid.Vector3(0,y,0)
    #        count += 1
    #    option, val = self.options[idx]
    #    option.scale = 1.0
    #    y -= option.height
    #    option.pos = euclid.Vector3(0,y,0)
    #    count += 1
    #    for option, val in self.options[idx+1:]:
    #        if count == idx + 1: option.scale = self.intermediate_scale
    #        else: option.scale = self.small_scale
    #        y -= option.height
    #        option.pos = euclid.Vector3(0,y,0)
    #        count += 1
    def selection(self, indices, all):
        if not all:
            sel = [self.choices[i] for i in indices]
            if len(sel) == 1: sel = sel[0]
            return sel
        else:
            return [self.choices[i] for i in range(len(self.choices)-1,-1,-1)]
    def handle_click(self, x, y):
        choice_list = self.choice_list
        xpos, ypos, cwidth, cheight = choice_list.x, choice_list.y, choice_list.content_width, choice_list.content_height
        y += ypos + cheight/2
        if 0 < y <= cheight:
            num_choices = len(self.choices)
            return num_choices - int(y // (cheight/num_choices)) - 1
        else: return -1
    def render_after_transform(self):
        w, h = self.border*2+self.width, self.border*2+self.height
        render_9_part("box4",
                      w, h,
                      x = -w/2, y = -h/2)
        self.prompt.render()
        self.choice_list.draw()
        #for item, val in self.options:
        #    item.render()

class LoggingOutput(object):
    def __init__(self):
        import sys
        self._data = ''
        self.log = []
        #self.old_stdout = sys.stdout
        #sys.stdout = self
    def write(self,data):
        #self.old_stdout.write(data)
        self._data = self._data+data
        _lines = self._data.split("\n")
        for line in _lines[:-1]: self.log.append(str(line))
        self._data = _lines[-1:][0]
    def __len__(self): return len(self.log)
    def __iter__(self):
        return iter(self.log)
    def __getitem__(self, idx):
        return self.log[idx]

class GameStatus(Widget):
    def __init__(self, pos=zero):
        super(GameStatus,self).__init__(pos)
        self.screen_width = self.screen_height = 0
        self._pos.set_transition(dt=0.5, method="ease_out_back")
        self.prompt = Label("", size=20, shadow=False, halign="center", valign="top", background=True)
        self.prompt.border = 3
        self.prompt._pos.set_transition(dt=0.5, method="sine")
        self.show_log = False
        self.width = 400
        self.gamelog = [Label('', size=14, halign="left", width=self.width) for i in range(15)]
        self.logger = []
    def clear(self):
        self.prompt.set_text("")
    def resize(self, width, height, avail_width):
        self.screen_width = width
        self.screen_height = height
        self.pos = euclid.Vector3(width/2, height/2, 0)
        self.prompt.pos = euclid.Vector3(avail_width/2, 125-height/2, 0)
    def log(self, prompt):
        self.prompt.set_text(prompt)
        self.layout()
    def log_event(self, sender, msg):
        self.logger.append((len(self.logger)+1, sender, msg))
        if self.show_log: self.construct_gamelog()
    def layout(self): pass
    def toggle_gamelog(self):
        self.show_log = not self.show_log
        self.construct_gamelog()
    def construct_gamelog(self):
        height = 0
        for text, (i, sender, line) in zip(self.gamelog, self.logger[-len(self.gamelog):]):
            text.set_text("%d. %s"%(i, line))
            height += text.height
            text.pos = euclid.Vector3(0, -height, 0)
        self.height = height
    def render_after_transform(self):
        self.prompt.render()
        if self.show_log:
            border = 10
            w = border+self.width/2; h=border+self.height/2
            glDisable(GL_TEXTURE_2D)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-w, -h)
            glVertex2f(w, -h)
            glVertex2f(w,h)
            glVertex2f(-w, h)
            glEnd()
            glColor4f(0.1, 0.1, 0.1, 0.9)
            glBegin(GL_QUADS)
            glVertex2f(-w, -h)
            glVertex2f(w, -h)
            glVertex2f(w,h)
            glVertex2f(-w, h)
            glEnd()
            glEnable(GL_TEXTURE_2D)
            glTranslatef(-self.width/2,self.height/2,0)
            for item in self.gamelog: item.render()

class ManaPool(Widget):
    def __init__(self, is_opponent, pos=zero):
        super(ManaPool, self).__init__(pos)
        document = mtg_decoder.decode_text(u'')
        self.padding = 6
        self.is_opponent = is_opponent
        mana_label = pyglet.text.layout.IncrementalTextLayout(document, multiline=True, width=50, height=0)
        mana_label.anchor_y = "top"
        #mana_label = pyglet.text.DocumentLabel(document, multiline=True,
        #                          width=100, anchor_x="left", anchor_y=anchor_y)
        #mana_label.set_style("color", (255,255,255,255))
        #mana_label.set_style("font_name", "Arial Bold")
        #mana_label.set_style("font_size", 12)
        self.mana_label = mana_label
 
        pay_label = pyglet.text.layout.IncrementalTextLayout(document, multiline=True, width=50, height=0)
        pay_label.anchor_y = "top"
        self.pay_label = pay_label

        self._render = False
        self._render_pay = False

        self.colors = "WUBRGC" 
        self.mana = dict(zip(self.colors, [0]*len(self.colors)))
        self.pay = dict(zip(self.colors, [0]*len(self.colors)))
    def remove_pay(self, col):
        self.pay[col] -= 1
        self.mana[col] += 1
        self.gen_labels()
    def add_pay(self, col):
        self.pay[col] += 1
        self.mana[col] -= 1
        self.gen_labels()
    def gen_labels(self):
        mana_text, pay_text = [], []
        self._render = False
        self._render_pay = False
        for c in self.colors:
            pay_amt, mana_amt = self.pay[c], self.mana[c]
            if pay_amt:
                if c == "C": pay_text.append(u"{%d}"%pay_amt)
                else: pay_text.append((u"{%s}"%c)*pay_amt)
                self._render_pay = True
            if mana_amt:
                if c == "C": mana_text.append(u"{%d}"%mana_amt)
                else: mana_text.append((u"{%s}"%c)*mana_amt)
                self._render = True
        if self._render:
            self.mana_label.content_width = 0
            self.mana_label.document = mtg_decoder.decode_text(u'\u2028'.join(mana_text))
            self.mana_label.height = self.mana_label.content_height
            self.mana_label.width = self.mana_label.content_width
        #self.mana_label.set_style("color", (255,255,255,255))
        #self.mana_label.set_style("font_name", "Arial Bold")
        #self.mana_label.set_style("font_size", 12)
        if self._render_pay:
            self.pay_label.content_width = 0
            self.pay_label.document = mtg_decoder.decode_text(u'\u2028'.join(pay_text))
            self.pay_label.height = self.pay_label.content_height
            self.pay_label.width = self.pay_label.content_width
    def _get_position_from_point(self, label, x, y):
        line = label.lines[label.get_line_from_point(x, y)]
        x -= label.top_group.translate_x
        position = line.start
        last_glyph_x = line.x
        for box in line.boxes:
            if 0 <= x - last_glyph_x < box.advance: break
            last_glyph_x += box.advance
            position += box.length
        return position

    def handle_click(self, x, y):
        arrow_width, padding = 8.0, self.padding 
        x -= arrow_width+padding
        height = self.mana_label.content_height+padding
        if self._render_pay:
            height = max(height, self.pay_label.content_height + padding)
        if self.is_opponent: y -= height
        else: y += padding
        if (0 <= x < self.mana_label.content_width and 
            0 <= -y < self.mana_label.content_height):
            pos = self._get_position_from_point(self.mana_label, x, y)
            try:
                color = self.mana_label.document.get_element(pos).symbol
                self.add_pay(color)
                return True
            except: pass
        else:
            x -= self.mana_label.content_width + 2*padding
            if (0 <= x < self.pay_label.content_width and
                0 <= -y < self.pay_label.content_height):
                pos = self._get_position_from_point(self.pay_label, x, y)
                try:
                    color = self.pay_label.document.get_element(pos).symbol
                    self.remove_pay(color)
                    return True
                except: pass
        return False
        #for color, symbol in zip(self.colors, self.symbols):
        #    if not symbol.visible: continue
        #    sx, sy = symbol.pos.x, symbol.pos.y
        #    rad = symbol.width/2
        #    if (x-sx)**2+(y-sy)**2 <= rad*rad:
        #        return symbol, self.values[color], self.spend_values[color]
        #else: return None
    def select(self, x=False):
        pass
        #self.select_mana = not self.select_mana
        #self.select_x = x
        #self.layout()
    def update_mana(self, sender, amount):
        for idx, c in enumerate(self.colors):
            self.mana[c] = self.mana[c] + amount[idx]
        self.gen_labels()
    def clear_pay(self):
        for key in self.pay: self.pay[key] = 0
        #self.pay_label.text = ''
        self._render_pay = False
    def clear_mana(self, sender):
        for key in self.mana:
            self.mana[key] = 0
            self.pay[key] = 0
        self._render = False
    def render_after_transform(self):
        if self._render:
            padding = self.padding
            arrow_width = 8
            width = self.mana_label.content_width + 2*padding
            height = self.mana_label.content_height + 2*padding
            if self._render_pay:
                width += self.pay_label.content_width + 2*padding
                height = max(height, self.pay_label.content_height + 2*padding)
            if self.is_opponent: y, shift, yshift = 0, 1, height-padding
            else: y, shift, yshift = -height, -1, -padding
            #y, shift = -height, -1
            glColor4f(1., 1., 1., 1.)
            render_9_part("box2",
                          width, height,
                          x=arrow_width, y=y)

            glColor4f(0,0,0,1)
            glBegin(GL_TRIANGLES)
            glVertex2f(0, 2*shift*arrow_width)
            glVertex2f(arrow_width+1, shift*arrow_width)
            glVertex2f(arrow_width+1, 3*shift*arrow_width)
            glEnd()
            glTranslatef(arrow_width+padding, yshift, 0)
            self.mana_label.draw()
            if self._render_pay:
                glTranslatef(self.mana_label.content_width+2*padding, 0, 0)
                glColor4f(0.5, .5, .5, 1.)
                glLineWidth(2.0)
                glBegin(GL_LINES)
                glVertex2f(-padding, -padding)
                glVertex2f(-padding, -height+2*padding)
                glEnd()
                self.pay_label.draw()

class ManaView(Widget):
    def __init__(self, pos=zero):
        super(ManaView,self).__init__(pos)
        self._pos.set_transition(dt=1.0, method="ease_out_circ")
        self.colors = ["white", "blue", "black", "red", "green", "colorless"]
        self.colormap = dict(zip(self.colors, "WUBRG"))
        self.nummana = len(self.colors)
        self.symbols = [ManaImage(color) for color in self.colors]
        self.pool = [Label("", size=20) for i in range(self.nummana)]
        self.values = dict([(c,v) for c, v in zip(self.colors, self.pool)])
        self.spend = [Label("0", size=30) for i in range(self.nummana)]
        self.spend_values = dict([(c,v) for c, v in zip(self.colors, self.spend)])
        for p, s in zip(self.pool, self.spend):
            p.visible = anim.constant(1)
            s.visible = anim.constant(1)
        self.cost = Label("0", size=40, halign="center", background=True)
        self.select_mana = self.select_x = False
        self.layout()
    def resize(self, width, height, flip=False):
        if flip: flip=-1
        else: flip=1
        self.select_pos = euclid.Vector3(flip*width/2, flip*height/2, 0)
        if self.select_mana or self.select_x:
            self.pos = self.select_pos+euclid.Vector3(-self.width/2, 0, 0)
    def clear_mana(self, sender):
        status = self.values
        for idx, c in enumerate(self.colors):
            if not status[c].value == '':
                status[c].set_text('')
                self.symbols[idx].animate(pain=True)
                self.symbols[idx].alpha = 0.4
        self.layout()
    def update_mana(self, sender, amount):
        status = self.values
        for idx, c in enumerate(self.colors):
            amt = amount[idx]
            if amt > 0: self.symbols[idx].animate()
            if status[c].value == '': new_value = amt
            else: new_value = int(status[c].value)+amt
            if new_value > 0:
                status[c].set_text(new_value)
                self.symbols[idx].alpha = 0.8
            else:
                status[c].set_text('')
                self.symbols[idx].alpha = 0.4
        self.layout()
    def handle_click(self, x, y):
        for color, symbol in zip(self.colors, self.symbols):
            if not symbol.visible: continue
            sx, sy = symbol.pos.x, symbol.pos.y
            rad = symbol.width/2
            if (x-sx)**2+(y-sy)**2 <= rad*rad:
                return symbol, self.values[color], self.spend_values[color]
        else: return None
    def select(self, x=False):
        self.select_mana = not self.select_mana
        self.select_x = x
        self.layout()
    def layout(self):
        x = 0
        if not self.select_mana:
            self.pos = self.orig_pos
            for symbol, current in zip(self.symbols, self.pool):
                symbol.visible = current.visible = 1
                symbol.scale = 0.25 #0.4
                hw = symbol.width/2
                spacer = 0.1*hw
                x += hw
                symbol.pos = euclid.Vector3(x, 0, 0)
                current.pos = euclid.Vector3(x-current.width/2, -current.height/2, 0)
                x += hw+spacer
            self.width = len(self.symbols)*(symbol.width*1.1)
        else:
            if not self.select_x:
                for symbol, current, pay in zip(self.symbols, self.pool, self.spend):
                    symbol.visible = current.visible = pay.visible = 1
                    symbol.pos = euclid.Vector3(x,0,0)
                    symbol.scale = 1.0
                    spacer = 10 #symbol.width*0.1
                    pay.pos = euclid.Vector3(x-pay.width/2, symbol.height/2, 0)
                    current.pos = euclid.Vector3(x-current.width/2, -current.height-symbol.height/2, 0)
                    if current.value == 0: symbol.alpha = 0.75
                    else: symbol.alpha = 1.0
                    x += symbol.width + spacer
                self.cost.pos = euclid.Vector3((x-symbol.width)/2, symbol.height*1.1, 0)
            else:
                y = self.symbols[0].height
                cost_y = y+self.cost.height
                symbol = self.symbols[-1]
                symbol.scale = 1.0
                symbol.alpha = 1.0
                symbol.pos = euclid.Vector3(-symbol.width/2, 0, 0)
                spacer = symbol.width*0.1
                amount = self.spend[-1]
                amount.pos = euclid.Vector3(x+spacer, -amount.height/2, 0)
                self.spend[-1].visible = 1.0
                self.pool[-1].visible = 0
                for symb, current, pay in zip(self.symbols, self.pool, self.spend)[:-1]:
                    symb.visible = 0
                    pay.visible = 0
                    current.visible = 0
                self.cost.pos = euclid.Vector3((x-symbol.width)/2, symbol.height*0.7, 0)
            self.width = x - symbol.width - spacer
            self.pos = self.select_pos-euclid.Vector3(self.width/2, 0, 0)
        self.height = symbol.height
    def render_after_transform(self):
        for symbol, text in zip(self.symbols, self.pool):
                symbol.render()
                text.render()
        if self.select_mana:
            for pay in self.spend: pay.render()
            self.cost.render()

import CardLibrary
class LibraryImage(Image):
    def __init__(self, is_opponent):
        self.back = CardLibrary.CardLibrary.getCardBack()
        self.padding = 8
        self.is_opponent = is_opponent
        super(LibraryImage,self).__init__(self.back)
    def update(self, library):
        top_card = library.top()
        if top_card:
            self.img = CardLibrary.CardLibrary.getCard(top_card).front
        else:
            self.img = self.back
    def render(self):
        padding = 2*self.padding
        arrow_width = 8
        width = self.width + padding
        height = self.height + padding
        glColor4f(1., 1., 1., 1.)
        if self.is_opponent: y, shift = self.pos.y+padding-height, -1
        else: y, shift = self.pos.y-padding, 1
        x = self.pos.x
        render_9_part("box2",
                      width, height,
                      x=x+arrow_width, y=y)
        glColor4f(0,0,0,1)
        glBegin(GL_TRIANGLES)
        y = self.pos.y
        glVertex2f(x, y)
        glVertex2f(x+arrow_width+1, y+shift*arrow_width)
        glVertex2f(x+arrow_width+1, y-shift*arrow_width)
        glEnd()
        glTranslatef(arrow_width+width/2, shift*(height/2-padding), 0)
        super(LibraryImage, self).render()

class StatusView(Widget):
    alpha = anim.Animatable()
    def __init__(self, pos=zero, is_opponent=False):
        super(StatusView,self).__init__(pos)
        self._toggled = False
        self._spacing = 10
        self._reveal_library = False
        self.color = (0.5, 0.5, 0.5)
        self.is_opponent = is_opponent
        #self._pos.set_transition(dt=0.1, method="linear")
        #symbols = ["life", "library", "hand", "graveyard", "exile"]
        symbols = ["life", "hand", "library", "graveyard", "exile"]
        self.symbols = dict([(symbol, cls(symbol)) for symbol, cls in zip(symbols, [Image, Image, Image, Image, Image])])
        for symbol in self.symbols.values():
            symbol.alpha = 0.8
        self.player_name = Label("", 11, halign="left", fontname = "Arial Bold", valign="center", shadow=False)
        #sizes = [20, 16, 14, 14, 14]
        sizes = [20, 14, 14, 14, 14]
        self.values = dict([(symbol, Label('', size, fontname = "Arial Bold", halign="center", valign="center", shadow=False)) for symbol, size in zip(symbols, sizes)])
        #for val in self.values.values():
        self.avatar = Image(pyglet.image.Texture.create(80,80))
        self.avatar.shaking = 0
        self.avatar.alpha = anim.animate(1., 1., dt=0.25)
        self.alpha = anim.animate(1., 1., dt=0.25)

        self.manapool = ManaPool(is_opponent)
        self.zone_view = ZoneView()
        self._library = LibraryImage(is_opponent)
        self.width, self.height = 145,135
    #    self.layout()
    def resize(self, width, height):
        self.layout()
    #    offset = 5
    #    if self.is_opponent:
    #        pos = euclid.Vector3(offset, height-self.height-offset, 0)
    #    else:
    #        pos = euclid.Vector3(offset, offset, 0)
    #    self._pos.set(pos)
        self._orig_pos = self.pos
    def clear(self):
        self.symbols['life'].rotatey = anim.constant(0)
        status = self.values
        counters = ["life", "hand", "library", "graveyard", "exile"]
        for c in counters: status[c].set_text(0)
    def toggle(self):
        if not self._toggled: 
            x = self.width - self.values['life'].width-self._spacing*1.5
            self.pos += euclid.Vector3(-x, 0, 0)
        else: self.pos = self._orig_pos
        self._toggled = not self._toggled
    def toggle_library(self):
        self._reveal_library = not self._reveal_library
    def animate(self, status):
        symbol = self.symbols[status]
        symbol.scale = anim.animate(symbol.scale, 1.15*symbol.scale, dt=1.0, method=lambda t: anim.oscillate_n(t, 3))
    def handle_click(self, x, y):
        x -= self.pos.x
        y -= self.pos.y
        for status, item in self.symbols.items():
            sx, sy, sw, sh = item.pos.x, item.pos.y, item.width/2., item.height/2.
            if x > sx-sw and x < sx+sw and y >= sy-sh and y <= sy+sh:
                return status
        else:
            return (0 < x <= self.width and 0 < y <= self.height)
    def setup_player(self, player, color, avatar):
        self.player = player
        self.color = color
        self.avatar.img = avatar.get_texture()
        self.player_name.set_text(player.name)
        self.update_life()
        for zone in ["library", "hand", "graveyard", "exile"]:
            self.update_zone(getattr(player, zone))
    def new_turn(self, player):
        return
        life = self.symbols["life"]
        if self.player == player: life.rotatey = anim.animate(0,360,dt=5,method='linear',extend='repeat')
        else: life.rotatey = anim.constant(0)
    def pass_priority(self, player):
        alpha = 1.0 if self.player == player else 0.6
        self.alpha = self.avatar.alpha = alpha
    def animate_life(self, amount):
        symbol = self.symbols["life"]
        curr_scale = symbol._final_scale
        if amount > 0: final_scale = curr_scale*1.5
        else: final_scale = curr_scale*0.5
        symbol._scale = anim.animate(curr_scale, final_scale,dt=0.75, method="oscillate")
        symbol.alpha = anim.animate(symbol.alpha, 0.7,dt=0.75, method="oscillate")
        self.update_life()
    def update_life(self):
        status = self.values
        player = self.player
        counters = ["life"] #, "poison"]
        for c in counters: status[c].set_text(getattr(player, c))
    def update_zone(self, zone):
        val = len(zone)
        status = self.values[str(zone)]
        if val > 0:
        #    self.symbols[str(zone)].alpha = 0.8
            status.set_text(val)
        else:
        #    self.symbols[str(zone)].alpha = 0.4
            status.set_text('0')
        if str(zone) == "library": self._library.update(zone)
    def layout(self):
        life_img, life = self.symbols["life"], self.values["life"]
        life_img.alpha = anim.constant(0.3)
        life_img._final_scale = 0.25
        life_img._scale = anim.constant(life_img._final_scale)
        #life_img.visible = anim.constant(0)
        avatar = self.avatar
        spacing = self._spacing
        if self.is_opponent:
            x, y = spacing, life.height / 2.
        
            self.player_name.pos = euclid.Vector3(x, y, 0)
            self.manapool.pos = euclid.Vector3(self.width, 0, 0)
            x = self.width - life.width/2 - spacing
            life.pos = life_img.pos = euclid.Vector3(x, y, 0)
            
            for i, status in enumerate(["graveyard", "library", "hand"]):
                symbol, value = self.symbols[status], self.values[status]
                #symbol.scale = 0.3
                #symbol.pos = value.pos = euclid.Vector3(x, life.height+spacing+symbol.height/2+0.7*i*(symbol.height), 0)
                symbol.pos = value.pos = euclid.Vector3(x, life.height+spacing/2+symbol.height/2+i*(symbol.height), 0)
                
            library, lib = self._library, self.symbols["library"]
            library.scale = 0.5
            library.pos = euclid.Vector3(self.width, life.height+spacing/2+1.5*lib.height, 0)
            #status = "library"
            #library, value = self.symbols["library"], self.values["library"]
            #library.scale = 0.3
            #library.pos = value.pos = euclid.Vector3(spacing + library.width/2, life.height+library.height/2+spacing,0)
            avatar.pos = euclid.Vector3(spacing + avatar.width/2, life.height+avatar.height/2+spacing,0)
        else:
            x, y = spacing, self.height - life.height / 2.
        
            self.player_name.pos = euclid.Vector3(x, y, 0)
            self.manapool.pos = euclid.Vector3(self.width, self.height, 0)
            x = self.width - life.width/2 - spacing
            life.pos = life_img.pos = euclid.Vector3(x, y, 0)
            
            for i, status in enumerate(["graveyard", "library", "hand"][::-1]):
                symbol, value = self.symbols[status], self.values[status]
                #symbol.scale = 0.3
                #symbol.pos = value.pos = euclid.Vector3(x, self.height-life.height-symbol.height/2-0.7*i*(symbol.height), 0)
                symbol.pos = value.pos = euclid.Vector3(x, self.height-life.height-symbol.height/2-i*(symbol.height)-spacing/2, 0)
                
            library, lib = self._library, self.symbols["library"]
            library.scale = 0.5
            library.pos = euclid.Vector3(self.width, 1.5*lib.height, 0)
            #status = "library"
            #library, value = self.symbols["library"], self.values["library"]
            #library.scale = 0.3
            #library.pos = value.pos = euclid.Vector3(spacing + library.width/2, self.height-life.height-library.height/2-spacing,0)
            avatar.pos = euclid.Vector3(spacing + avatar.width/2, self.height-life.height-avatar.height/2-spacing,0)
            
    def render_after_transform(self):
        ac = self.color
        glColor4f(ac[0], ac[1], ac[2], self.alpha)
        life_height = self.values['life'].height
        h1, h2 = self.height - life_height, life_height
        if self.is_opponent: h1, h2 = h2, h1
        render_9_part("box4",
                      self.width, h1,
                      x=0, y=0)
        render_9_part("box4",
                      self.width, h2,
                      x=0, y=h1)
        
        self.avatar.render()
        self.player_name.render()
        for status in ["life", "library", "hand", "graveyard"]: #, "exile"]:
            symbol, value = self.symbols[status], self.values[status]
            symbol.render()
            value.render()
        self.manapool.render()
        self.zone_view.render()
        if self._reveal_library: self._library.render()


class PhaseBar(Widget):
    def __init__(self, pos=zero):
        super(PhaseBar, self).__init__(pos)
        self._padding = 10
        self._state = self._player = ''
        width = 250

        document = pyglet.text.decode_attributed('Starting Game')
        self.status = pyglet.text.DocumentLabel(document,
                           anchor_x = "left", anchor_y="center",
                           x = -width/2+self._padding, 
                           width = width-self._padding)
        self.status.set_style("font_name", "Arial Bold")
        self.status.set_style("font_size", 15)
        self.status.set_style("color", (255,255,255,255))
        
        self.width, self.height = width, self.status.content_height+self._padding
        states = [('Untap','Untap'),
            ('Upkeep','Upkeep'),
            ('Draw','Draw'),
            ('Main1','Main 1'),
            ('BeginCombat','Beginning of combat'),
            ('Attack','Declare attackers'),
            ('Block','Declare blockers'),
            ('Damage','Combat damage'),
            ('EndCombat','End of combat'),
            ('Main2','Main 2'),
            ('EndStep','End Step'),
            ('Cleanup','Cleanup')]
        self._state_map = dict(states)
        self._status_str = "{font_name 'Arial'}{font_size 14}{color (255,255,255,255)}{bold True}%s{bold False} {font_size 11}%s"
    def set_phase(self, state):
        if state in self._state_map: self._state = self._state_map[state]
        self.update()
    def new_turn(self, player):
        self._player = player
        self.update()
    def update(self):
        status = self._status_str%(self._state, self._player)
        self.status.document = pyglet.text.decode_attributed(status)
    def render_after_transform(self):
        w, h = self.width, self.height
        glColor4f(0.9, 0.9, 0.9, 1.0)
        render_9_part("box2",
                      w, h,
                      x = -w/2, y = -h/2)
        self.status.draw()

from resources import config
# This is where I should handle priority stops and such (or at least the controller, since I can use this class
# to set priorities)
class PhaseStatus(Widget):
    def __init__(self, pos=zero):
        super(PhaseStatus,self).__init__(pos)
        self.visible = anim.constant(0)
        states = [('Untap','Untap'),
            ('Upkeep','Upkeep'),
            ('Draw','Draw'),
            ('Main1','Main 1'),
            ('BeginCombat','Beginning of combat'),
            ('Attack','Declare attackers'),
            ('Block','Declare blockers'),
            ('Damage','Combat damage'),
            ('EndCombat','End of combat'),
            ('Main2','Main 2'),
            ('EndStep','End Step'),
            ('Cleanup','Cleanup')]
        self.state_list = [s.lower() for s, t in states]
        self.grouping = [0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0]
        self.state_map = dict([(key, (i, val)) for i,(key,val) in enumerate(states)])
        self.states = [Image(key) for key, val in states]
        self.state_labels = [Label(val, size=20, valign="center", shadow=False) for key, val in states]
        self.state_text = None
        for state in self.states:
            state.visible = anim.constant(1.0)
            state.alpha = anim.animate(1.0, 1.0, dt=0.5, method="ease_out_circ") ##sine")
            state.scale = anim.animate(1.0, 1.0, dt=0.5, method="sine")
            state._pos.set_transition(dt=0.5, method="sine")
        for label in self.state_labels:
            label.scale = 0.8
            label._pos.y = anim.constant(-100) # This is just a hack to hide it
        self.width = state.width
        self.current = 0
        self.select = False
        self.curr_player = None
        self.turn_label = Label("", size=24, halign="center", valign="top", shadow=False)
        self.render_after_transform = self.render_game
        self.set_stops()

    def set_stops(self):
        self.my_turn_stops = set([state for state, val in config.items("my stops") if val == "No"])
        self.opponent_turn_stops = set([state for state, val in config.items("opponent stops") if val == "No"])

    def toggle_select(self, other=False):
        self.select = not self.select
        if self.select:
            self.old_dir = self.dir
            self.old_align = self.state_labels[0].main_text.halign
            if other:
                self.turn_label.set_text("Opponent's turn")
                self.dir = -1
            else:
                self.turn_label.set_text("Your turn")
                self.dir = 1
            self.layout_big()
            self.old_pos = self.pos
            self.pos = euclid.Vector3(self.screen_width/2, (self.screen_height+self.height)/2, 0)
            self.render_after_transform = self.render_select
        else:
            self.dir = self.old_dir
            for label in self.state_labels: label.main_text.halign = self.old_align
            self.layout()
            self.pos = self.old_pos
            self.render_after_transform = self.render_game
    def resize(self, width, height):
        self.screen_width = width
        self.screen_height = height
        if self.select:
            self.pos = euclid.Vector3(self.screen_width/2, (self.screen_height+self.height)/2, 0)
            if self.curr_player == self.player:
                self.old_pos = euclid.Vector3(0, (self.screen_height+self.height)/2, 0)
            else:
                self.old_pos = euclid.Vector3(self.screen_width, (self.screen_height+self.height)/2, 0)
        elif self.curr_player:
            if self.curr_player == self.player:
                self.pos = euclid.Vector3(0, (self.screen_height+self.height)/2, 0)
            else:
                self.pos = euclid.Vector3(self.screen_width, (self.screen_height+self.height)/2, 0)
    def handle_click(self, x, y):
        x -= self.pos.x
        y -= self.pos.y
        for key, (i, val) in self.state_map.items(): #state in self.states:
            state = self.states[i]
            if state.visible == 0: continue
            sx, sy, sw, sh = state.pos.x, state.pos.y, state.width/2., state.height/2.
            if x > sx-sw and x < sx+sw and y >= sy-sh and y <= sy+sh:
                return key, state, self.state_labels[i]
        else: return None
    def layout_big(self):
        y = 0
        i = 0
        for symbol, label in zip(self.states, self.state_labels):
            symbol.alpha = 1.0
            symbol.scale = 1.0
            symbol.color = (1, 1, 1)
            hh = symbol.height / 2
            if self.grouping[i] == 1: y -= hh*.5
            y -= hh
            x = self.dir*symbol.width
            symbol.pos = euclid.Vector3(0, y, 0)
            label.pos = euclid.Vector3(1.1*x/2, y, 0)
            label.scale = 0.8
            y -= hh
            i += 1
        self.height = -y
        self.turn_label.pos = zero # This is because the untap symbol is hidden
    def layout_small(self):
        y = 0
        i = 0
        for symbol in self.states:
            symbol.alpha = 0.75
            symbol.scale = 0.75
            hh = symbol.height / 2
            if self.grouping[i] == 1: y -= hh*.5
            y -= hh
            symbol.pos = euclid.Vector3(-symbol.width/2, y, 0)
            y -= hh
            i += 1
        self.height = -y
    def layout(self):
        y = 0
        dir = self.dir
        i = 0
        def stop_incr(state):
            if dir == 1: stops = self.my_turn_stops
            else: stops = self.opponent_turn_stops
            if state in stops: return 0
            else: return dir*3
        incr = [stop_incr(state) for state in self.state_list[::-1]]
        for symbol in self.states[:self.current]:
            symbol.alpha = 0.75
            symbol.scale = 0.75
            symbol.color = (1, 1, 1)
            hh = symbol.height / 2
            if self.grouping[i] == 1: y -= hh*.75
            y -= hh
            symbol.pos = euclid.Vector3(dir*symbol.width/2+incr.pop(), y, 0)
            y -= hh
            i += 1
        incr.pop()
        curr_state = self.states[self.current]
        curr_state.alpha = 1.0
        curr_state.scale = 1.25
        curr_state.color = self.marker_color
        nhh = curr_state.height/2
        if self.grouping[i] == 1: y -= nhh*.75
        i += 1
        y -= nhh
        x = dir*curr_state.width
        curr_state.pos = euclid.Vector3(x/2, y, 0)
        self.state_text.pos = euclid.Vector3(1.1*x, y, 0)
        y -= nhh
        for symbol in self.states[self.current+1:]:
            symbol.alpha = 0.75
            symbol.scale = 0.75
            hh = symbol.height / 2
            if self.grouping[i] == 1: y -= hh*.75
            y -= hh
            symbol.pos = euclid.Vector3(dir*symbol.width/2+incr.pop(), y, 0)
            symbol.color = (1, 1, 1)
            y -= hh
            i += 1
        self.height = -y
    def render_game(self):
        for state in self.states: state.render()
        self.state_text.render()
    def render_select(self):
        glColor4f(0.1, 0.1, 0.1, .9)
        glDisable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        w = self.screen_width/2; h = (self.screen_height+self.height)/2
        glVertex2f(-w, -h)
        glVertex2f(w, -h)
        glVertex2f(w,h)
        glVertex2f(-w, h)
        glEnd()
        glEnable(GL_TEXTURE_2D)
        for state, label in zip(self.states, self.state_labels):
            state.render()
            label.render()
        self.turn_label.render()
    def clear(self):
        self.dir = 1
        self.current_state = self.states[0]
        self.state_text = self.state_labels[0]
        self.marker_color = (1.0, 1.0, 1.0)
        self.layout()
    def setup_player_colors(self, player, self_color, other_color):
        self.player = player
        self.self_color = self_color
        self.other_color = other_color
        self.marker_color = self_color
    def check_my_stop(self): return self.current_state in self.my_turn_stops
    def check_opponent_stop(self): return self.current_state in self.opponent_turn_stops
    def change_focus(self, sender):
        if sender == self.player:
            self.marker_color = self.self_color
            if not self.select: self.states[self.current].color = self.marker_color
        else:
            self.marker_color = self.other_color
            if not self.select: self.states[self.current].color = self.marker_color
    def pass_priority(self, player=None):
        if player == self.player:
            self.marker_color = self.self_color
            if not self.select: self.states[self.current].color = self.marker_color
        else:
            self.marker_color = self.other_color
            if not self.select: self.states[self.current].color = self.marker_color
    def new_turn(self, player=None):
        self.curr_player = player
        if player == self.player:
            if not self.select:
                self.dir = 1
                self.pos = euclid.Vector3(0, (self.screen_height+self.height)/2, 0)
                for label in self.state_labels: label.main_text.halign = "left"
            else:
                self.old_dir = 1
                self.old_align = "left"
                self.old_pos = euclid.Vector3(0, (self.screen_height+self.height)/2, 0)
        else:
            if not self.select:
                self.dir = -1
                self.pos = euclid.Vector3(self.screen_width, (self.screen_height+self.height)/2, 0)
                for label in self.state_labels: label.main_text.halign = "right"
            else:
                self.old_dir = -1
                self.old_align = "right"
                self.old_pos = euclid.Vector3(self.screen_width, (self.screen_height+self.height)/2, 0)
    def set_phase(self, state):
        self.current_state = state.lower()
        if state in self.state_map:
            self.current, txt = self.state_map[state]
            self.state_text = self.state_labels[self.current]
            if not self.select:
                self.state_text._pos.x = anim.animate(0, 0, dt=0.5, method="ease_out_circ") #sine")
                self.layout()
