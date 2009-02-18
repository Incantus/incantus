import pygame
from pgu import gui
from card_widgets import CardInfo
from color_dialog import ColorDialog
from card_widgets import CardInfo
import CardLibrary

class CardNameLabel(gui.area._List_Item):
    def __init__(self,label,key,cardinfo,image=None,value=None,**params):
        super(CardNameLabel,self).__init__(label,image=image,value=value,**params)
        self.cardinfo = cardinfo
        self.key = key
    def event(self,e):
        super(CardNameLabel,self).event(e)
        if e.type == gui.MOUSEMOTION: self.show()
    def show(self):
        self.cardinfo.showCard(self.key)

class OutOfPlay(gui.Dialog):
    from card_widgets import CardsHand
    def __init__(self, title, cardlist, cinfo, **params):
        title = gui.Label(title)
        tt = gui.Table()
        spacing = 15
        width = len(cardlist)*(65+spacing)
        height = 133
        show = OutOfPlay.CardsHand(width=width, height=height)
        show.init(cinfo)
        #cardlist = list(cardlist)[::-1]
        show.set_zone(cardlist)
        self.show = show
        card_area = gui.ScrollArea(show, 300, height, vscrollbar = False)
        tt.td(card_area)
        tt.tr()
        b = gui.Button("Okay")
        b.connect(gui.CLICK,self.send,"OK")
        self.ok = b
        #tt.td(b)
        super(OutOfPlay,self).__init__(title,tt)
    def event(self, event):
        if event.type == gui.KEYDOWN:
            if event.key == gui.K_RETURN:
                self.close()
                #self.ok.send(gui.CLICK)
            return True
        elif event.type == gui.CLICK:
            res = super(OutOfPlay, self).event(event)
            if self.show.selectedCard:
                #self.show.update_cards()
                self.close()
                #self.ok.send(gui.CLICK)
            return res
        else: return super(OutOfPlay, self).event(event)

class RevealCardDialog(gui.Dialog):
    def __init__(self, keys, msgs=[], titlemsg = "Reveal card", **params):
        tt = gui.Table()
        title = gui.Label(titlemsg)
        numcards = len(keys)
        if msgs:
            for i in range(numcards):
                tt.td(gui.Label(msgs[i]))
                if numcards > 1:
                    tt.td(gui.Spacer(width=2,height=0))

        tt.tr()
        for i in range(numcards):
            cardinfo = CardInfo(width=234,height=333)
            tt.td(cardinfo)
            cardinfo.cardlib = CardLibrary.CardLibrary
            cardinfo.showCard(keys[i])
            if numcards > 1:
                tt.td(gui.Spacer(width=2,height=0))
        tt.tr()
        tt.td(gui.Spacer(width=0,height=8))
        tt.tr()
        b = gui.Button("Okay")
        b.connect(gui.CLICK,self.send,"OK")
        self.ok = b
        tt.td(b, colspan=numcards*2)
        super(RevealCardDialog,self).__init__(title,tt)
    def event(self, event):
        if event.type == gui.KEYDOWN:
            if event.key == gui.K_RETURN:
                self.ok.send(gui.CLICK)
            return True
        else: return super(RevealCardDialog, self).event(event)

class MessageDialog(gui.Dialog):
    def __init__(self,msg,**params):
        tt = gui.Table()
        title = gui.Label("Would you like to")
        message = gui.Label(msg)
        tt.td(message, colspan=3)
        tt.tr()
        b = gui.Button("Okay")
        b.connect(gui.CLICK,self.send,"OK")
        self.ok = b
        tt.td(b)
        tt.td(gui.Spacer(width=40,height=8))
        b = gui.Button("Cancel")
        b.connect(gui.CLICK,self.send,"CANCEL")
        self.cancel = b
        tt.td(b)
        super(MessageDialog,self).__init__(title,tt)
    def event(self, event):
        if event.type == gui.KEYDOWN:
            if event.key == gui.K_RETURN:
                self.ok.send(gui.CLICK)
            elif event.key == gui.K_ESCAPE:
                self.cancel.send(gui.CLICK)
            return True
        else: return super(MessageDialog, self).event(event)

class CardList(gui.area.List):
    def _add(self, label, image=None, value=None, iscard=False):
        if not iscard: super(CardList, self)._add(label,image=image,value=value)
        else:
            item = label
            self.table.tr()
            self.table.add(item)
            self.items.append(item)
            item.group = self.group
            item.group.add(item)

class ChooseSelectionDialog(gui.Dialog):
    def __init__(self,items,numselection=1,cardinfo=None,required=True,title_msg='',**params):
        if numselection < 0: numselection = 0
        if not numselection == 0: msg = "Choose %d from the list"%numselection
        else: msg = ''
        if not title_msg: title_msg = msg
        title = gui.Label(title_msg)
        tt = gui.Table()
        numcol = 0
        self.form = gui.Form()
        mainlist = CardList(width=300,height=333,name="selection",value=0)
        self.mainlist = mainlist
        numcol += 2
        tt.td(mainlist,colspan=numcol)
        for i, item in enumerate(items):
            if not cardinfo: mainlist.add("%s"%(item[0]), value=item[1])
            else: 
                #if item.facedown: name = "*** Facedown *** "
                #else: name = item.name
                #mainlist.add("%d. %s"%(i+1,name), value=item)
                if item.facedown: name = "%d. *** Facedown *** "%i+1
                else: name = CardNameLabel("%d. %s"%(i+1, item.name), item.key, cardinfo, value=item)
                mainlist.add(name,value=item,iscard=True)
        if numselection > 1:
            numcol += 2
            newt = gui.Table()
            choose = CardList(width=300,height=333,value=0)
            self.choose = choose
            def move_item(dir, mainlist=mainlist, choose=choose):
                self.error.set_value(msg)
                self.error.repaint()
                if dir:
                    item = mainlist.value
                    if not item == None:
                        # make sure it's not already added
                        notfound = True
                        for val in choose.items:
                            if item == val.value: notfound = False
                        if notfound:
                            if not cardinfo: choose.add("%s"%(items[item][0]), value=item)
                            else: choose.add("%s"%(item.name), value=item)
                            choose.resize()
                            choose.repaint()
                        else:
                            self.error.set_value("This card is already added")
                            self.error.repaint()
                else:
                    item = choose.value
                    if item:
                        choose.remove(item)
                        choose.resize()
                        choose.repaint()
            e = gui.Button("Add -->")
            e.connect(gui.CLICK,move_item,True)
            newt.td(e)
            newt.tr()
            e = gui.Button("<-- Remove")
            e.connect(gui.CLICK,move_item,False)
            newt.td(e)

            tt.td(newt)
            tt.td(choose)
            msg = "Choose %d - add them to the list on the right"%numselection

        tt.tr()
        tt.td(gui.Spacer(width=8,height=8),colspan=numcol)
        tt.tr()
        self.error = gui.Label(msg)
        if numselection != 0: tt.td(self.error, colspan=numcol)
        tt.tr()
        self.b = gui.Button("Okay")
        self.b.connect(gui.CLICK,self.send,gui.CHANGE)
        self.cancel = gui.Button("Cancel")
        if required: tt.td(self.b, colspan=numcol)
        else: 
            if numselection == 1:
                tt.td(self.b, colspan=numcol-1)
                tt.td(self.cancel, 1)
            else:
                tt.td(self.b, colspan=numcol-2)
                tt.td(self.cancel,2)
        gui.Dialog.__init__(self,title,tt)
    def event(self, event):
        if event.type == gui.KEYDOWN:
            if event.key == gui.K_RETURN:
                self.b.send(gui.CLICK)
            elif event.key == gui.K_ESCAPE:
                self.cancel.send(gui.CLICK)
            return True
        else: return super(ChooseSelectionDialog, self).event(event)

class XDialog(gui.Dialog):
    def __init__(self,**params):
        tt = gui.Table()
        title = gui.Label("Select amount of X")
        self.error = gui.Label(" "*30, color=(255,0,0))
        tt.tr()
        tt.td(self.error,colspan=2)
        self.form = gui.Form()
        b = gui.Button("Okay")

        def validate_input(input_field):
            # This just checks to see if that you put in at least the required
            # amount, and no more than what you have
            if not input_field.value == None:
                try:
                    value = int(input_field.value)
                    if value < 0:
                        input_field.value = "0"
                        input_field.repaint()
                        self.error.set_value("Invalid amount")
                        self.error.repaint()
                    else:
                        self.error.set_value("")
                        self.error.repaint()
                except TypeError:
                    input_field.value = "0"
                    input_field.repaint()
                    self.error.set_value("Invalid value")
                    self.error.repaint()
        tt.tr()
        tt.td(gui.Label("X"))
        input_field = gui.Input("0", size=2,name="X")
        input_field.connect(gui.K_TAB,validate_input,input_field)
        tt.td(input_field)
        tt.tr()

        b.connect(gui.CLICK,self.send,"OK")
        self.b = b
        tt.td(b,colspan=2)
        #b = gui.Button("Cancel")
        #b.connect(gui.CLICK,self.send,"CANCEL")
        #tt.td(b)
        super(XDialog,self).__init__(title,tt)
    def event(self, event):
        if event.type == gui.KEYDOWN and event.key == gui.K_RETURN:
            try:
                value = int(self.form['X'].value)
                if value < 0:
                    self.error.set_value("Invalid amount")
                    self.error.repaint()
                    return
                self.send("OK")
            except TypeError:
                self.error.set_value("Invalid value")
                self.error.repaint()
            return True
        else: return super(XDialog, self).event(event)

class ManaDialog(gui.Dialog):
    def __init__(self,manapool,required,**params):
        import game.Mana
        tt = gui.Table()
        title = gui.Label("Select Mana payment")
        if required == '': required = 'X'
        tt.td(gui.Label("%s required"%required),colspan=3)
        self.error = gui.Label(" "*30, color=(255,0,0))
        tt.tr()
        tt.td(self.error,colspan=3)
        mana = [("white", 'W'), ("red", 'R'), ("green", 'G'), ("blue", 'U'), ("black", 'B') ,("colorless", 'C')]
        self.form = gui.Form()
        required = game.Mana.convert_mana_string(required)

        b = gui.Button("Okay")

        def validate_input(input):
            # This just checks to see if that you put in at least the required
            # amount, and no more than what you have
            input_field, nummana, numrequired = input
            if not input_field.value == None:
                try:
                    value = int(input_field.value)
                    if value > nummana or value < numrequired:
                        input_field.value = str(numrequired)
                        input_field.repaint()
                        return
                except ValueError:
                    input_field.value = str(numrequired)
                    input_field.repaint()
            self.error.set_value("")
            self.error.repaint()

        for mana_color, mana_name in mana:
            tt.tr()
            nummana = getattr(manapool, mana_color)
            if mana_color == "colorless" and nummana == 0: continue
            tt.td(gui.Label(str(nummana)))
            tt.td(gui.Image("./data/images/colors/%s.png"%mana_color))
            req_mana = manapool.getMana(required,mana_color)
            if nummana > 0 and mana_color != "colorless":
                input_field = gui.Input(str(req_mana), size=2,name=mana_name)
                input_field.connect(gui.K_TAB,validate_input,(input_field,nummana,req_mana))
                tt.td(input_field)
            else: tt.td(gui.Label(str(min(req_mana,nummana)),name=mana_name))
        tt.tr()
        tt.td(gui.Spacer(width=40,height=8))
        tt.tr()
        b.connect(gui.CLICK,self.send,"OK")
        self.ok = b
        tt.td(b,colspan=2)
        b = gui.Button("Cancel")
        b.connect(gui.CLICK,self.send,"CANCEL")
        self.cancel = b
        tt.td(b)
        super(ManaDialog,self).__init__(title,tt)
    def event(self, event):
        if event.type == gui.KEYDOWN:
            if event.key == gui.K_RETURN:
                try:
                    for color, value in self.form.items():
                        value = int(value)
                    else: self.ok.send(gui.CLICK)
                except ValueError:
                    self.error.set_value("Invalid value")
                    self.error.repaint()
            elif event.key == gui.K_ESCAPE:
                self.cancel.send(gui.CLICK)
            else: return super(ManaDialog, self).event(event)
        else: return super(ManaDialog, self).event(event)

class AssignDamageDialog(gui.Dialog):
    def __init__(self,blocking_list,**params):
        tt = gui.Table()
        title = gui.Label("Assign Damage")
        
        self.error = gui.Label(" "*40, color=(255,0,0))
        
        self.form = gui.Form()

        b = gui.Button("Okay")
        def validate_input(input):
            input_field, total = input
            if not input_field.value == None:
                try:
                    value = int(input_field.value)
                    if value > total or value < 0:
                        input_field.value = str(0)
                        self.error.set_value("Incorrect assignment")
                        self.error.repaint()
                        return
                except ValueError:
                    input_field.value = str(0)
            self.error.set_value("")
            self.error.repaint()

        tt.tr()
        tt.td(gui.Label("Attackers (P)", color=(0,0,255)))
        tt.td(gui.Label("Blockers (T)", color=(0,0,255)))
        tt.td(gui.Label("Assigned (Current)", color=(255,0,0)))
        for attacker, blockers in blocking_list:
            tt.tr()
            tt.td(gui.Label("%s (%d)"%(attacker.name,attacker.power)))
            subtt = gui.Table()
            for blocker in blockers:
                subtt.td(gui.Label("%s (%d)"%(blocker.name, blocker.toughness)))
                subtt.tr()
            tt.td(subtt)
            subtt = gui.Table()
            for blocker in blockers:
                if len(blockers) == 1: v = attacker.power
                else: v = 0
                input_field = gui.Input(v, size=2,name=blocker)
                input_field.connect("RETURN",validate_input,(input_field,attacker.power))
                subtt.td(input_field)
                subtt.td(gui.Label("(%s)"%blocker.currentDamage()))
                subtt.tr()
            tt.td(subtt)
            tt.tr()
            tt.td(gui.Spacer(width=1,height=20), colspan=3)
            
        tt.tr()
        tt.td(gui.Spacer(width=40,height=8))
        tt.tr()
        tt.td(self.error,colspan=3)
        tt.tr()
        b.connect(gui.CLICK,self.send,"OK")
        self.b = b
        tt.td(b, colspan=3)
        super(AssignDamageDialog,self).__init__(title,tt)
    def event(self, event):
        if event.type == gui.KEYDOWN and event.key == gui.K_RETURN:
            self.b.send(gui.CLICK)
            return True
        else: return super(AssignDamageDialog, self).event(event)

class QuitDialog(gui.Dialog):
    def __init__(self,**params):
        title = gui.Label("Quit")
        t = gui.Table()
        t.tr()
        t.add(gui.Label("Are you sure you want to quit?"),colspan=2)
        t.tr()
        e = gui.Button("Okay")
        e.connect(gui.CLICK,self.send,gui.QUIT)
        t.td(e)
        e = gui.Button("Cancel")
        e.connect(gui.CLICK,self.close,None)
        t.td(e)
        gui.Dialog.__init__(self,title,t)

class NetworkGameDialog(gui.Dialog):
    def __init__(self,**params):
        title = gui.Label("Setup network game")
        # New network game
        ##Once a form is created, all the widgets that are added with a name
        ##are added to that form.
        ##::
        self.setup = gui.Form()
        t = gui.Table()
        t.tr()
        t.td(gui.Label("Name: "),align=0)
        t.td(gui.Input(value="",name="name",size=10))
        t.tr()
        
        t.td(gui.Label("Self color"))
        t.td(gui.Label("Other color"))
        t.tr()
        self_color = gui.Color("#0000FF",width=20,height=20,name="self_color")
        other_color = gui.Color("#FFFF00",width=20,height=20,name="other_color")
        picker = ColorDialog("#0000FF")

        def picker_open(color):
            picker.value[:] = list(color.value)
            picker.connect(gui.CHANGE,gui.action_setvalue,(picker,color))
            t.open(picker,None,None)

        self_color.connect(gui.CLICK,picker_open, self_color)
        other_color.connect(gui.CLICK,picker_open, other_color)

        t.td(self_color)
        t.td(other_color)
        t.tr()
        t.td(gui.Spacer(width=8,height=8))
        t.tr()

        t.td(gui.Label("IP address: "),align=0)
        t.td(gui.Input(value="127.0.0.1",name="address",size=10))
        t.tr()
        t.td(gui.Label("Port: "),align=0)
        t.td(gui.Input(value="5000",name="port",size=5))
        t.tr()
        
        g = gui.Group(name="server", value=True)
        t.td(gui.Label("Server"))
        t.td(gui.Radio(g,value=True))
        t.tr()
        t.td(gui.Label("Client"))
        t.td(gui.Radio(g,value=False))
        
        t.tr()
        t.td(gui.Spacer(width=8,height=8))
        t.tr()
        
        t.tr()
        e = gui.Button("Connect")
        e.connect(gui.CLICK,self.send,"OK")
        t.td(e)
        
        e = gui.Button("Cancel")
        e.connect(gui.CLICK,self.close,None)
        t.td(e)
        super(NetworkGameDialog,self).__init__(title,t)
