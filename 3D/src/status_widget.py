__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet.gl import glColor4f, glVertex2f, glDisable, glEnable, glBegin, glEnd, glTranslatef, GL_TEXTURE_2D, GL_QUADS, glLineWidth, GL_LINE_LOOP
import anim
import euclid
from widget import Widget, Image, Label

class MessageDialog(Widget):
    alpha = anim.Animatable()
    def __init__(self, pos=euclid.Vector3(0,0,0)):
        super(MessageDialog,self).__init__(pos)
        self.alpha = anim.animate(0, 0.9, dt=0.5, method="sine")
        self.border = 20
        self.visible = 0
        self.focus_idx = 0
        self.size = 20
        self.ok = Label("OK", self.size-4, shadow=True, border=True)
        self.cancel = Label("Cancel", self.size-4, shadow=True, border=True)
    def hide(self):
        self.visible = anim.animate(1., 0.0, dt=0.1)
    def handle_click(self, x, y):
        for item, val in [(self.ok, True), (self.cancel, False)]:
            b = item.border
            sx, sy, sw, sh = item.pos.x-b, item.pos.y-b, item.width+2*b, item.height+2*b
            if x > sx and x < sx+sw and y >= sy and y <= sy+sh: return (item, val)
        else: return None, -1
    def construct(self, prompt, msg_type="ask"):
        self.prompt = Label(prompt, self.size, halign="center", shadow=True)
        self.width = max(1.1*(self.ok.width + self.cancel.width), self.prompt.width)
        self.height = self.prompt.height+self.ok.height
        #Now layout
        y = -self.prompt.height*1.1
        if msg_type == "notify":
            self.ok.set_text("OK")
            self.ok.pos = euclid.Vector3(-self.ok.width/2, y, 0)
            self.cancel.visible = 0
        elif msg_type == "ask":
            self.ok.set_text("Yes")
            self.cancel.set_text("No")
            self.cancel.visible = 1
            self.ok.pos = euclid.Vector3(-self.width/4-self.ok.width/2, y, 0)
            self.cancel.pos = euclid.Vector3(self.width/4-self.cancel.width/2, y, 0)
    def render_after_transform(self):
        glColor4f(0.2, 0.2, 0.2, self.alpha)
        w = self.border+self.width/2; h=self.border+self.height/2
        glDisable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glVertex2f(-w, -h)
        glVertex2f(w, -h)
        glVertex2f(w,h)
        glVertex2f(-w, h)
        glEnd()
        glColor4f(0.0, 0.0,0.0,1.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(-w, -h)
        glVertex2f(w, -h)
        glVertex2f(w,h)
        glVertex2f(-w, h)
        glEnd()
        glEnable(GL_TEXTURE_2D)
        self.prompt.render()
        self.ok.render()
        self.cancel.render()

class SelectionList(Widget):
    alpha = anim.Animatable()
    def __init__(self, pos=euclid.Vector3(0,0,0)):
        super(SelectionList,self).__init__(pos)
        self.options = []
        self.alpha = anim.animate(0, 0.9, dt=1.0, method="sine")
        self.border = 20
        self.visible = 0
        self.focus_idx = 0
        self.large_size = 30
        self.small_scale = 0.35
        self.intermediate_scale = 0.55
        self.layout = self.layout_normal
        self.prompt = Label("", size=self.large_size, halign="center", shadow=False)
    def move_up(self):
        if self.visible == 1 and self.focus_idx > 0:
            self.focus_dir = -1
            self.options[self.focus_idx], self.options[self.focus_idx+self.focus_dir] = self.options[self.focus_idx+self.focus_dir], self.options[self.focus_idx]
            self.focus_idx += self.focus_dir
            self.layout()
    def move_down(self):
       if self.visible == 1 and self.focus_idx < len(self.options)-1:
            self.focus_dir = 1
            self.options[self.focus_idx], self.options[self.focus_idx+self.focus_dir] = self.options[self.focus_idx+self.focus_dir], self.options[self.focus_idx]
            self.focus_idx += self.focus_dir
            self.layout()
    def focus_previous(self):
        if self.visible == 1 and self.focus_idx > 0:
            self.focus_dir = -1
            self.focus_idx += self.focus_dir
            self.layout()
    def focus_next(self):
       if self.visible == 1 and self.focus_idx < len(self.options)-1:
            self.focus_dir = 1
            self.focus_idx += self.focus_dir
            self.layout()
    def hide(self):
        for item, val in self.options:
            item.pos = euclid.Vector3(0,0,0)
        self.visible = anim.animate(1., 0.0, dt=0.1)
    def construct(self, prompt, sellist):
        self.prompt.set_text(prompt)
        self.options = [(Label(str(val[0]), size=self.large_size, halign="center", shadow=False), val[1]) for val in sellist]
        y = 0
        method = "linear" #sine"
        dt = 0.3
        for item, val in self.options:
            item._scale = anim.animate(1.0, 1.0, dt=dt, method=method)
            item._pos.set_transition(dt=dt, method=method)
        self.focus_idx = len(self.options)/2
        self.layout()
        self.width = max([item[0].width for item in self.options]+[self.prompt.width])
        self.height = sum([item[0].height for item in self.options]+[self.prompt.height])
        self.scroll = self.height/len(self.options)
    def layout_normal(self):
        x = y = 0
        self.prompt.scale = 0.7
        y -= self.prompt.height
        self.prompt.pos = euclid.Vector3(0, y, 0)
        for option, val in self.options:
            option.scale = 0.45
            y -= option.height
            option.pos = euclid.Vector3(0, y, 0)
    def layout_resize(self):
        x = y = 0
        idx = self.focus_idx
        self.prompt.scale = 0.7
        y -= self.prompt.height
        self.prompt.pos = euclid.Vector3(0, y, 0)
        count = 0
        for option, val in self.options[:idx]:
            if count == idx - 1: option.scale = self.intermediate_scale
            else: option.scale = self.small_scale
            y -= option.height
            option.pos = euclid.Vector3(0,y,0)
            count += 1
        option, val = self.options[idx]
        option.scale = 1.0
        y -= option.height
        option.pos = euclid.Vector3(0,y,0)
        count += 1
        for option, val in self.options[idx+1:]:
            if count == idx + 1: option.scale = self.intermediate_scale
            else: option.scale = self.small_scale
            y -= option.height
            option.pos = euclid.Vector3(0,y,0)
            count += 1
    def selection(self, index=0, number=1):
        if number == 1:
            return self.options[index][1]
        else:
            return [self.options[i][1] for i in range(number-1,-1,-1)]
    def handle_click(self, x, y):
        y -= self.height/2
        for idx, (item, val) in enumerate(self.options):
            sx, sy, sw, sh = item.pos.x, item.pos.y, item.width/2., item.height
            if x > sx-sw and x < sx+sw and y >= sy and y <= sy+sh: return idx
        else: return -1
    def render_after_transform(self):
        glColor4f(0.1, 0.1, 0.1, self.alpha)
        glDisable(GL_TEXTURE_2D)
        w = self.border+self.width/2; h=self.border+self.height/2
        glBegin(GL_QUADS)
        glVertex2f(-w, -h)
        glVertex2f(w, -h)
        glVertex2f(w,h)
        glVertex2f(-w, h)
        glEnd()
        glColor4f(0.0, 0.0,0.0,1.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(-w, -h)
        glVertex2f(w, -h)
        glVertex2f(w,h)
        glVertex2f(-w, h)
        glEnd()
        glEnable(GL_TEXTURE_2D)
        glTranslatef(0,self.height/2,0)
        self.prompt.render()
        for item, val in self.options:
            item.render()

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
    def __init__(self, pos=euclid.Vector3(0,0,0)):
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

class ManaImage(Image):
    def pos():
        def fget(self): return euclid.Vector3(self._pos.x, self._pos.y, self._pos.z)
        def fset(self, val):
            self._pos.x = val.x
            self._pos.y = val.y
            self._pos.z = val.z
            self.glow.pos = val
        return locals()
    pos = property(**pos())
    def __init__(self, fname):
        super(ManaImage,self).__init__(fname)
        self.glow = Image("glow")
        self.glow.color = (1.0, 0.9, 0.0, 0.5)
        self.glow.visible = 0
        self.alpha = 0.4
        self.visible = anim.constant(1)
    def animate(self, sparkle=True, pain=False):
        if sparkle:
            if not pain: self.glow.color = (1.0, 0.9, 0.0, 0.5)
            else: self.glow.color = (1.0, 0.0, 0.0, 0.5)
            self.glow.visible = anim.animate(1.0,0.0, dt=0.5)
            self.glow.scale = anim.animate(0.5, 2.0, dt=0.5)
            self.glow.alpha = anim.animate(0.5,0.0,dt=0.5, method="ease_in_circ")
        self.rotatey = anim.animate(0,360,dt=1.5, method="sine")
    def render(self):
        super(ManaImage,self).render()
        self.glow.render()

class ManaView(Widget):
    def __init__(self, pos=euclid.Vector3(0, 0, 0), reverse=False):
        from game import Mana
        super(ManaView,self).__init__(pos)
        self.reverse = reverse
        self._pos.set_transition(dt=0.5, method="ease_out_back")
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
    def resize(self, width, height):
        self.select_pos = euclid.Vector3((width-self.width)/2, height/2, 0)
        if self.select_mana or self.select_x:
            self.pos = self.select_pos
    def clear_mana(self, sender):
        status = self.values
        manapool = sender
        for idx, c in enumerate(self.colors):
            if status[c].value == '': oldamt = 0
            else: oldamt = int(status[c].value)
            val = getattr(manapool, c)
            if val > 0:
                status[c].set_text(val)
                self.symbols[idx].alpha = 0.8
            else:
                status[c].set_text('')
                self.symbols[idx].alpha = 0.4
            if oldamt > 0: self.symbols[idx].animate(pain=True)
        self.layout()
    def update_mana(self, sender, amount):
        status = self.values
        manapool = sender
        for idx, c in enumerate(self.colors):
            val = getattr(manapool, c)
            if val > 0:
                status[c].set_text(val)
                self.symbols[idx].alpha = 0.8
            else:
                status[c].set_text('')
                self.symbols[idx].alpha = 0.4
        self.layout()
        for idx, amt in enumerate(amount):
            if amt > 0: self.symbols[idx].animate()
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
            self.pos = self.select_pos
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
                self.pool[-1].visible = 0
                for symbol, current, pay in zip(self.symbols, self.pool, self.spend)[:-1]:
                    symbol.visible = 0
                    pay.visible = 0
                    current.visible = 0
                self.cost.pos = euclid.Vector3((x-symbol.width)/2, symbol.height+spacer, 0)
            self.width = x - symbol.width - spacer
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
    def __init__(self, zone):
        super(LibraryImage, self).__init__(zone)
        self.zone = zone
        self.library = None
        self.reveal = False
    def setup_player(self, player):
        self.library = getattr(player, self.zone)
        self.back = CardLibrary.CardLibrary.getCardBack()
        self.img = self.back
    def update(self):
        if self.reveal:
            libtop = self.library.top()
            if libtop: self.img = CardLibrary.CardLibrary.getCard(libtop).front
        else:
            self.img = self.back
    def toggle_reveal(self):
        self.reveal = not self.reveal
        self.update()

class StatusView(Widget):
    def __init__(self, pos=euclid.Vector3(0, 0, 0), is_opponent=False):
        super(StatusView,self).__init__(pos)
        self.is_opponent = is_opponent
        self._pos.set_transition(dt=0.5, method="ease_out_circ")
        symbols = ["life", "library", "graveyard", "removed"]
        img_classes = [Image, LibraryImage, Image, Image]
        sizes = [30, 20, 20, 20]
        self.symbols = dict([(symbol, cls(symbol)) for symbol, cls in zip(symbols, img_classes)])
        self.symbols["life"].shaking = 0
        for symbol in self.symbols.values():
            symbol.alpha = 0.5
        self.player_name = Label(" ", 20, halign="center", shadow=True)
        self.values = dict([(symbol, Label('', size, halign="center", valign="center")) for symbol, size in zip(self.symbols, sizes)])
        self.values["life"].halign = "center"
        self.values["life"].valign = "center"
        self.manapool = ManaView(reverse=is_opponent)
        self.active = Image("ring")
        self.active.scale = anim.animate(0.1, 0.1, dt=0.2, method="ease_out_back")
        self.active.visible = 1.
        self.visible = 0
        self.layout()
    def resize(self, width, height):
        if self.is_opponent: pos = euclid.Vector3(width, height, 0)
        else: pos = euclid.Vector3(0, 0, 0)
        self.manapool.resize(width, height)
        self.pos = self.orig_pos = pos + euclid.Vector3(self._transx, self._transy, 0)
    def clear(self):
        self.symbols['life'].rotatey = anim.constant(0)
        status = self.values
        counters = ["life", "library", "graveyard", "removed"]
        #for c in counters: status[c].set_text(0)
    def show(self):
        self.pos = self.orig_pos
        super(StatusView,self).show()
    def hide(self):
        if self.visible == 1.0:
            self.orig_pos = self.pos
            if self.is_opponent: self.pos += euclid.Vector3(self.width, 0, 0)
            else: self.pos -= euclid.Vector3(self.width, 0, 0)
            super(StatusView,self).hide()
    def animate(self, status):
        symbol = self.symbols[status]
        #symbol._pos.set_transition(dt=0.5, method=lambda t: anim.oscillate_n(t, 3))
        #symbol.pos += euclid.Vector3(15, 0, 0)
        symbol.scale = anim.animate(symbol.scale, 1.15*symbol.scale, dt=1.0, method=lambda t: anim.oscillate_n(t, 3))
    def handle_click(self, x, y):
        x -= self.pos.x
        y -= self.pos.y
        for status, item in self.symbols.items():
            sx, sy, sw, sh = item.pos.x, item.pos.y, item.width/2., item.height/2.
            if x > sx-sw and x < sx+sw and y >= sy-sh and y <= sy+sh:
                return status
        else: return None
    def setup_player(self, player, color):
        self.player = player
        self.active.color = color
        self.player_name.set_text(player.name)
        self.update_life()
        self.symbols["library"].setup_player(player)
        for zone in ["library", "graveyard", "removed"]:
            self.update_zone(getattr(player, zone))
        #self.update_cards()
        self.active.scale = anim.animate(0.1, 0.75, dt=0.2, method="ease_out_back")
        self.layout()
    def new_turn(self, player):
        return
        life = self.symbols["life"]
        if self.player == player: life.rotatey = anim.animate(0,360,dt=5,method='linear',extend='repeat')
        else: life.rotatey = anim.constant(0)
    def pass_priority(self, player):
        active = self.active
        life = self.symbols["life"]
        if self.player == player:
            life.rotatey = anim.animate(0,360,dt=5,method='linear',extend='repeat')
            #active.scale = anim.animate(active.scale, 1.2, dt=0.2, method="ease_out_back")
            #active.visible = 1.0
        else:
            life.rotatey = anim.constant(0)
            #active.scale = anim.animate(active.scale, 0.1, dt=0.2, method="sine")
            #active.visible = 0.0
    def animate_life(self, amount):
        symbol = self.symbols["life"]
        curr_scale = 0.5 #symbol.scale
        if amount > 0: final_scale = curr_scale*1.5
        else: final_scale = curr_scale*0.5
        symbol._scale = anim.animate(curr_scale, final_scale,dt=0.75, method="oscillate")
        self.update_life()
    def update_life(self):
        status = self.values
        player = self.player
        counters = ["life"] #, "poison"]
        for c in counters: status[c].set_text(getattr(player, c))
    def update_cards(self):
        status = self.values
        player = self.player
        counters = ["library", "graveyard", "removed"]
        for c in counters:
            val = len(getattr(player, c))
            if val > 0:
                self.symbols[c].alpha = 0.8
                status[c].set_text(val)
            else:
                self.symbols[c].alpha = 0.4
                status[c].set_text('')
    def update_zone(self, zone):
        val = len(zone)
        status = self.values[str(zone)]
        if val > 0:
            self.symbols[str(zone)].alpha = 0.8
            status.set_text(val)
        else:
            self.symbols[str(zone)].alpha = 0.4
            status.set_text('')
        if str(zone) == "library": self.symbols[str(zone)].update()
    def layout(self):
        status = "life"
        life, lifevalue = self.symbols[status], self.values[status]
        life.alpha = 1.0
        life.scale = 0.5
        if not self.is_opponent: dir = 1
        else: dir = -1
        startx = x = life.width*1.5*dir
        starty = y = life.height*dir
        for status in ["graveyard", "removed"][::dir]:
            symbol, value = self.symbols[status], self.values[status]
            symbol.scale = 0.35
            if self.is_opponent: y -= symbol.height/4*dir
            symbol.pos = euclid.Vector3(x+symbol.width/2*dir, y, 0)
            value.pos = euclid.Vector3(x+symbol.width/2*dir, y, 0)
            y -= symbol.height*dir*.75
        y = starty-symbol.height*0.5*dir
        x += symbol.width*1.3*dir
        status = "library"
        symbol, value = self.symbols[status], self.values[status]
        symbol.scale = 0.275
        x += symbol.width/2*dir
        #y += symbol.height/2*dir
        symbol.pos = euclid.Vector3(x, y, 0)
        value.pos = euclid.Vector3(x, y, 0)
        width = x + symbol.width/2*dir
        if not self.is_opponent:
            x, y = life.width/2, life.height/2
            life.pos = euclid.Vector3(x, y, 0)
            self.active.pos = euclid.Vector3(x, y, 0)
            lifevalue.pos = euclid.Vector3(x, y, 0)
            self.player_name.pos = euclid.Vector3(x, -self.player_name.height, 0)
            self.manapool.pos = self.manapool.orig_pos = euclid.Vector3((width-self.manapool.width)/2, starty+self.manapool.height, 0)
            self._transx = -(width-self.manapool.width)/2
            self._transy = self.player_name.height
        else:
            x, y = -life.width/2, -life.height/2
            life.pos = euclid.Vector3(x, y, 0)
            self.active.pos = euclid.Vector3(x,y,0)
            lifevalue.pos = euclid.Vector3(x,y,0)
            self.player_name.pos = euclid.Vector3(x, 0, 0)
            self.manapool.pos = self.manapool.orig_pos = euclid.Vector3(-(self.manapool.width-width)/2, starty-self.manapool.height, 0)
            self._transx = -10 #-self.manapool.width/2 #0.2*width
            self._transy = -self.player_name.height
        self.width = self.manapool.width
        if self.is_opponent: self.box = (-self.width+10, starty-self.manapool.height*1.5-5, -self._transx, -self._transy)
        else: self.box = (-self.pos.x, -self.pos.y, -self.pos.x+self.width-5, starty+self.manapool.height*1.5+5)
    def render_after_transform(self):
        ac = self.active.color
        glColor4f(0.2, 0.2, 0.3, 0.5) #glColor4f(ac[0]*0.5, ac[1]*0.5, ac[2]*0.5, 0.3)
        l, b, r, t = self.box
        glDisable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glVertex2f(l, b)
        glVertex2f(r, b)
        glVertex2f(r, t)
        glVertex2f(l, t)
        glEnd()
        glColor4f(0,0,0,1)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(l, b)
        glVertex2f(r, b)
        glVertex2f(r, t)
        glVertex2f(l, t)
        glEnd()
        self.active.render()
        for status in ["life", "library", "graveyard", "removed"]:
            symbol, value = self.symbols[status], self.values[status]
            symbol.render()
            value.render()
        self.player_name.render()
        self.manapool.render()


# This is where I should handle priority stops and such (or at least the controller, since I can use this class
# to set priorities)
class PhaseStatus(Widget):
    def __init__(self, pos=euclid.Vector3(0, 0, 0)):
        super(PhaseStatus,self).__init__(pos)
        self._pos.set(euclid.Vector3(0,0,0))
        states = [('Untap','Untap'),
            ('Upkeep','Upkeep'),
            ('Draw','Draw'),
            ('Main1','Main'),
            ('PreCombat','Beginning of combat'),
            ('Attack','Declare attackers'),
            ('Block','Declare blockers'),
            ('Damage','Combat damage'),
            ('EndCombat','End of combat'),
            ('Main2','Main'),
            ('EndPhase','End of turn'),
            ('Cleanup','Cleanup')]
        self.group = [0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0]
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
        self.render_after_transform = self.render_game
    def toggle_select(self, other=False):
        self.select = not self.select
        if self.select:
            self.old_dir = self.dir
            self.old_align = self.state_labels[0].main_text.halign
            self.turn_label = Label("", size=24, halign="center", valign="top", shadow=False)
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
            if self.group[i] == 1: y -= hh*.5
            y -= hh
            x = self.dir*symbol.width
            symbol.pos = euclid.Vector3(0, y, 0)
            label.pos = euclid.Vector3(1.1*x/2, y, 0)
            label.scale = 0.8
            y -= hh
            i += 1
        self.height = -y
        self.turn_label.pos = euclid.Vector3(0, 0, 0) # This is because the untap symbol is hidden
    def layout_small(self):
        y = 0
        i = 0
        for symbol in self.states:
            symbol.alpha = 0.75
            symbol.scale = 0.75
            hh = symbol.height / 2
            if self.group[i] == 1: y -= hh*.5
            y -= hh
            symbol.pos = euclid.Vector3(-symbol.width/2, y, 0)
            y -= hh
            i += 1
        self.height = -y
    def layout(self):
        y = 0
        dir = self.dir
        i = 0
        for symbol in self.states[:self.current]:
            symbol.alpha = 0.75
            symbol.scale = 0.75
            symbol.color = (1, 1, 1)
            hh = symbol.height / 2
            if self.group[i] == 1: y -= hh*.75
            y -= hh
            symbol.pos = euclid.Vector3(dir*symbol.width/2, y, 0)
            y -= hh
            i += 1
        curr_state = self.states[self.current]
        curr_state.alpha = 1.0
        curr_state.scale = 1.25
        curr_state.color = self.marker_color
        nhh = curr_state.height/2
        if self.group[i] == 1: y -= nhh*.75
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
            if self.group[i] == 1: y -= hh*.75
            y -= hh
            symbol.pos = euclid.Vector3(dir*symbol.width/2, y, 0)
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
        self.show()
    def change_focus(self, sender):
        if sender == self.player:
            self.marker_color = self.self_color
            if not self.select: self.states[self.current].color = self.marker_color
        else:
            self.marker_color = self.other_color
            if not self.select: self.states[self.current].color = self.marker_color
    def pass_priority(self, player=None):
        if player == None: raise Exception("player not specified")
        if player == self.player:
            self.marker_color = self.self_color
            if not self.select: self.states[self.current].color = self.marker_color
        else:
            self.marker_color = self.other_color
            if not self.select: self.states[self.current].color = self.marker_color
    def new_turn(self, player=None):
        if player == None: raise Exception("player not specified")
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
    def set_phase(self, state=None):
        if state == None: raise Exception("State change not specified")
        if state in self.state_map:
            self.current, txt = self.state_map[state]
            self.state_text = self.state_labels[self.current]
            if not self.select:
                self.state_text._pos.x = anim.animate(0, 0, dt=0.5, method="ease_out_circ") #sine")
                self.layout()
