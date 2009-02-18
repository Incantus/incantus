
import pygame
from pgu import gui
from pgu.gui import basic, table, app, group, button, surface
from pgu.gui.const import *

from game import Action

class StatusImage(basic.Image):
    def __init__(self,value,number=0,tcolor=(0,0,0),font=None,ismana=False,**params):
        params.setdefault('cls','label')
        basic.Image.__init__(self,value,**params)
        if not font: self.font = self.style.font
        else: self.font = font
        self.tcolor = tcolor
        self.showlist = None
        if ismana: self.tcolor = (255,255,255)
        self.ismana = False #ismana
        self.set_number(number)
    def set_number(self, n):
        self.number = str(n)
        self.twidth, self.theight = self.font.size(self.number)
    def paint(self,s):
        s.blit(self.value,(0,0))
        if not self.ismana:
            tx, ty = self.style.width/2-self.twidth/2, self.style.height/2-self.theight/2
        else:
            tx, ty = self.rect.bottomright
            tx, ty = tx-self.twidth-2, ty-self.theight-2
            numrect = pygame.rect.Rect(tx-1, ty-1,self.twidth+1,self.theight+1)
            s.fill((210,210,210,255),numrect)
            inner = (220,220,220); outer = (150,150,150)
            outer = (220,220,220); inner = (150,150,150)
            pygame.draw.line(s, inner, numrect.topleft, numrect.topright)
            pygame.draw.line(s, inner, numrect.topleft, numrect.bottomleft)
            pygame.draw.line(s, outer, numrect.topright, numrect.bottomright)
            pygame.draw.line(s, outer, numrect.bottomleft, numrect.bottomright)
        s.blit(self.font.render(self.number, 1, self.tcolor),(tx,ty))
    def event(self, event):
        if event.type == gui.CLICK and self.showlist:
            self.showlist()
            return True
        else: return super(StatusImage, self).event(event)

class PlayerStatus(table.Table):
    def __init__(self, **params):
        table.Table.__init__(self,background=(255,255,255),**params)
        self.status = {}
        self.player = None
        status_names = [["status/life", "colors/white"],["status/poison", "colors/red"], ["status/hand", "colors/green"], ["status/library", "colors/blue"],["status/graveyard", "colors/black"], ["status/removed", "colors/colorless"]]
        #self.font = pygame.font.Font("./data/themes/default/Inconsolata.otf", 16)
        self.font = pygame.font.Font("data/themes/default/Vera.ttf", 20) #16)
        #status_colors = zip([(0,0,0)]*6, [(255,255,255), (255,0,0), (0,255,0), (0,0,255), (0,0,0), (128,128,128)])
        status_colors = [((0,0,0), (0,0,0))]*6
        self.tr()
        self.player_name = basic.Label(" "*15, color=(0,0,0))
        self.td(self.player_name, colspan=2)
        self.player_color = (255,255,255)
        def setup_double(sname, color):
            self.tr()
            if not sname[0] == None:
                si = StatusImage("./data/images/%s.png"%sname[0], tcolor=color[0],font=self.font)
                self.status[sname[0].split("/")[1]] = si
                self.td(si,align=0)
            else:
                si = basic.Spacer(2,2)
                self.td(si,align=0)
            si = StatusImage("./data/images/%s.png"%sname[1], tcolor=color[1], font=self.font, ismana=True)
            self.status[sname[1].split("/")[1]] = si
            self.td(si,align=1)

        for sname, color in zip(status_names, status_colors):
            setup_double(sname,color)
        self.border_size = 4
    def resize(self, width, height):
        w, h = super(PlayerStatus, self).resize(width,height)
        self.style.w, self.style.h = w+8, h+2
        return (self.style.w, self.style.h)
    def setup_player(self, player, showlist, color):
        self.player = player
        self.player_color = color
        self.player_name.set_value(player.name)
        self.status['library'].showlist = lambda: showlist(self.player.library,msg="%s: %s"%(self.player.name,str(self.player.library)))
        self.status['graveyard'].showlist = lambda: showlist(self.player.graveyard,msg="%s: %s"%(self.player.name,str(self.player.graveyard)))
        self.status['removed'].showlist = lambda: showlist(self.player.removed,msg="%s: %s"%(self.player.name,str(self.player.removed)))
        #self.status['library'].showlist = lambda: showlist(self.player.library,0,msg="%s: %s"%(self.player.name,str(self.player.library)))
        #self.status['graveyard'].showlist = lambda: showlist(self.player.graveyard,0,msg="%s: %s"%(self.player.name,str(self.player.graveyard)))
        #self.status['removed'].showlist = lambda: showlist(self.player.removed,0,msg="%s: %s"%(self.player.name,str(self.player.removed)))
        self.update_status()
        self.update_cards()
        self.update_mana()
    def update_status(self):
        status = self.status
        player = self.player
        counters = ["life", "poison"]
        for c in counters: status[c].set_number(getattr(player, c))
        self.repaint()
    def update_cards(self):
        status = self.status
        player = self.player
        counters = ["hand", "library", "graveyard", "removed"]
        for c in counters: status[c].set_number(len(getattr(player, c)))
        self.repaint()
    def update_mana(self):
        status = self.status
        player = self.player
        counters = ["red", "blue", "black", "white", "green", "colorless"]
        for c in counters: status[c].set_number(getattr(player.manapool, c))
        self.repaint()
    def paint(self, s):
        #s.fill(self.player_color)
        super(PlayerStatus,self).paint(s)
        rect = pygame.rect.Rect(0,0,self.rect.w-self.border_size, self.rect.h-self.border_size)
        pygame.draw.rect(s,self.player_color,rect, self.border_size)
    def event(self, event):
        if not super(PlayerStatus, self).event(event):
            if event.type == gui.CLICK and self.player:
                pygame.event.post(pygame.event.Event(USEREVENT, {"action": Action.PlayerSelected(self.player)}))

class Status(button._button):
    def __init__(self,group,widget=None,value=None,**params): #TODO widget= could conflict with module widget
        params.setdefault('cls','tool') #status')
        button._button.__init__(self,**params)
        self.group = group
        self.group.add(self)
        self.value = value
        if widget: self.setwidget(widget)
    def setwidget(self,w):
        self.widget = w
    def event(self,e):
        pass
    def resize(self,width=None,height=None):
        self.widget.rect.w,self.widget.rect.h = self.widget.resize()
        return self.widget.rect.w,self.widget.rect.h
    def paint(self,s):
        self.widget.paint(surface.subsurface(s,self.widget.rect))

class GameStatus(table.Table):
    def __init__(self,data,value=None,**params):
        #params.setdefault('cls','toolbox')
        table.Table.__init__(self,**params)
        rows = len(data)
        self.tools = {}
        self.group = group.Group()
        self.group.value = value

        x,y,p,s = 0,0,None,1
        for ico,value in data:
            #img = app.App.app.theme.get(tool_cls+"."+ico,"","image")
            #if img: i = basic.Image(img)
            #else: i = basic.Label(ico) #,cls=tool_cls+".label")
            i = basic.Label(ico)
            p = Status(self.group,i,value) #,cls=tool_cls)
            self.tools[value] = p
            self.add(p,x,y)
            s = 0
            if rows != 0: y += 1
            if rows != 0 and y == rows: x,y = x+1,0
        self.marker_color = None
    def setup_player_colors(self, player, self_color, other_color):
        self.player = player
        self.self_color = self_color
        self.other_color = other_color
        self.marker_color = self_color
        rect = self.tools["Untap"].rect
        self.status_size = rect.size
        self.p1_x = self.p_x = 10
        self.p2_x = self.status_size[0]-10
        self.p_y = self.status_size[1]/2
        self.repaint()
    def paint(self,s):
        super(GameStatus,self).paint(s)
        if self.marker_color:
            marker_pos = (self.p_x, self.p_y)
            pygame.draw.circle(s, self.marker_color, marker_pos, 8, 0)
    def pass_priority(self, player=None):
        if player == None: raise Exception("player not specified")
        if player == self.curr_player: self.p_x = self.p1_x
        else: self.p_x = self.p2_x
        if player == self.player: self.marker_color = self.self_color
        else: self.marker_color = self.other_color
        self.repaint()
    def new_turn(self, player=None):
        if player == None: raise Exception("player not specified")
        self.curr_player = player
        if player == self.player:
            self.marker_color = self.self_color
            self.curr_player_color = self.self_color
            self.other_player_color = self.other_color
        else:
            self.marker_color = self.other_color
            self.curr_player_color = self.other_color
            self.other_player_color = self.self_color
        self.p_x = self.p1_x
        self.repaint()
    def set_phase(self, state=None):
        if state == None: raise Exception("State change not specified")
        curr_w = self.tools[self.group.value]
        curr_w.pcls = ""
        if state in self.tools:
            self.group.value = state
            status = self.tools[state]
            status.pcls = "down"
            if not state=="Block":
                self.p_x = self.p1_x
                self.marker_color = self.curr_player_color
            else:
                self.p_x = self.p2_x
                self.marker_color = self.other_player_color
            self.p_y = status.rect.y+self.status_size[1]/2
            self.repaint()

class LoggingLabel(gui.Widget):
    def __init__(self, value, bkgd=(255,255,255),**params):
        params.setdefault("cls", "log")
        params.setdefault('focusable',False)
        super(LoggingLabel,self).__init__(**params)
        self.font = self.style.font
        self.value = value
        self.bkgd = bkgd
        self.style.width, self.style.height = self.font.size(self.value)
        self.style.width, self.style.height = self.style.width+4, self.style.height+2
        self.txt = self.font.render(self.value,1,(0,0,0)) #self.bkgd)
    def paint(self, s):
        s.fill(self.bkgd, self.rect) #(128,128,128), self.rect)
        pygame.draw.rect(s, self.bkgd, self.rect, 1)
        s.blit(self.txt,(2,1))

class LoggingOutput:
    def __init__(self, status):
        import sys
        self._data = ''
        self.status = status
        self.old_stdout = sys.stdout
        #sys.stdout = self
    def write(self,data):
        #self.old_stdout.write(data)
        self._data = self._data+data
        _lines = self._data.split("\n")
        #for line in _lines[:-1]:
        #    self.status.log(str(line))
        self._data = _lines[-1:][0]

class LogStatus(gui.ScrollArea):
    def __init__(self,**params):
        self.messages = gui.Table()
        self.logger = LoggingOutput(self)
        self.player1 = ""
        super(LogStatus,self).__init__(self.messages, **params)
        #super(LogStatus,self).__init__(self.messages, hscrollbar=False, **params)
    def setup_player_colors(self, player1, self_color, other_color):
        self.player1 = player1.name
        self.name_length = len(self.player1)
        self.self_color = self_color
        self.other_color = other_color
    def log(self, msg):
        self.messages.tr()
        msg = [m.strip() for m in msg.split(":")]
        name, msg = msg[0], ': '.join(msg[1:])
        if name == self.player1:
            color = self.self_color
        else: color = self.other_color
        self.messages.td(LoggingLabel(msg, bkgd=color),align=-1)
        self.set_vertical_scroll(100)
        self.repaint()
