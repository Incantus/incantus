import euclid
from pyglet.window import key, mouse
from game import Action
from game import Mana

class MessageController(object):
    def __init__(self, dialog, window):
        self.dialog = dialog
        self.window = window
        self.do_action = True
        self.click = None
    def activate(self):
        self.dialog._pos.set(euclid.Vector3(self.window.width/2, self.window.height/2, 0))
        self.dialog.show()
        self.window.push_handlers(self)
    def deactivate(self):
        self.dialog.hide()
        self.window.pop_handlers()
    def ask(self, prompt, action=True):
        self.dialog.construct(prompt, msg_type='ask')
        self.do_action = action
        self.activate()
    def notify(self,prompt,action=True):
        self.dialog.construct(prompt, msg_type='notify')
        self.do_action = action
        self.activate()
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER:
            if self.do_action: self.window.user_action = Action.OKAction()
            self.deactivate()
            return True
        elif symbol == key.ESCAPE:
            if self.do_action: self.window.user_action = Action.CancelAction()
            self.deactivate()
            return True
        elif symbol in [key.F2, key.F3]:
            return True
    def on_mouse_press(self, x, y, button, modifiers):
        if (button == mouse.RIGHT or modifiers & key.MOD_OPTION): return False
        x -= self.dialog.pos.x
        y -= self.dialog.pos.y
        item, result = self.dialog.handle_click(x, y)
        if not result == -1:
            self.click = item
            item.main_text.color = (0.5, 0.5, 0.5, 1.0)
        return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if (buttons == mouse.RIGHT or modifiers & key.MOD_OPTION): return False
        if self.click:
            x -= self.dialog.pos.x
            y -= self.dialog.pos.y
            item, result = self.dialog.handle_click(x, y)
            if not item == self.click: self.click.main_text.color = self.click.color
            else: item.main_text.color = (0.5, 0.5, 0.5, 1.0)
        return True
    def on_mouse_release(self, x, y, button, modifiers):
        if (button == mouse.RIGHT or modifiers & key.MOD_OPTION): return False
        if self.click:
            x -= self.dialog.pos.x
            y -= self.dialog.pos.y
            item, result = self.dialog.handle_click(x, y)
            if item == self.click:
                if self.do_action:
                    if result == True: self.window.user_action = Action.OKAction()
                    else: self.window.user_action = Action.CancelAction()
                self.deactivate()
            self.click.main_text.color = self.click.color
            self.click = None
        return True

class SelectController(object):
    def __init__(self, listview, window):
        self.listview = listview
        self.window = window
        self.required = False
    def activate(self):
        self.listview._pos.set(euclid.Vector3(self.window.width/2, self.window.height/2, 0))
        self.listview.show()
        self.window.push_handlers(self)
        self.dragging = False
        self.tmp_dy = 0
    def deactivate(self):
        self.listview.hide()
        self.window.pop_handlers()
    def build(self,sellist,required,numselections,prompt=''):
        self.required = required
        self.numselections = numselections
        self.listview.construct(prompt,sellist)
        self.index = -1
        self.activate()
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER:
            if self.numselections != 1:
                self.return_selections()
            return True
        elif symbol == key.ESCAPE:
            if not self.required:
                self.window.user_action = Action.CancelAction()
                self.deactivate()
            return True
        elif symbol == key.UP:
            self.listview.focus_previous()
        elif symbol == key.DOWN:
            self.listview.focus_next()
    def return_selections(self):
        if self.numselections == 1: SelAction = Action.SingleSelected
        else: SelAction = Action.MultipleSelected
        self.window.user_action = SelAction(self.listview.selection(self.index, self.numselections))
        self.deactivate()
    def on_mouse_press(self, x, y, button, modifiers):
        x -= self.listview.pos.x
        y -= self.listview.pos.y
        self.listview.focus_idx = self.index
        return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self.index == -1:
            self.dragging = True
            self.tmp_dy += dy
            if self.tmp_dy > self.listview.scroll:
                self.tmp_dy = 0
                self.listview.move_up()
            elif self.tmp_dy < -self.listview.scroll:
                self.tmp_dy = 0
                self.listview.move_down()
        return True
    def on_mouse_release(self, x, y, button, modifiers):
        if not self.index == -1:
            x -= self.listview.pos.x
            y -= self.listview.pos.y
            idx = self.listview.handle_click(x, y)
            if self.dragging:
                self.dragging = False
                if not idx == self.index:
                    self.listview.options[self.index][0].main_text.color = (1., 1., 1., 1.)
                    self.listview.options[idx][0].main_text.color = (0.5, 0.5, 0.5, 1.0)
            else:
                if idx == self.index:
                    self.return_selections()
        return True
    def on_mouse_motion(self, x, y, dx, dy):
        x -= self.listview.pos.x
        y -= self.listview.pos.y
        idx = self.listview.handle_click(x, y)
        options = self.listview.options
        if not idx == -1:
            if not idx == self.index:
                options[self.index][0].main_text.color = (1., 1., 1., 1.)
                options[idx][0].main_text.color = (0.5, 0.5, 0.5, 1.0)
                self.index = idx
        elif self.index != -1:
            options[self.index][0].main_text.color = (1., 1., 1., 1.)
            self.index = -1
        return True

class CardSelector(object):
    def __init__(self, mainstatus, otherstatus, zone_view, window):
        self.mainstatus = mainstatus
        self.otherstatus = otherstatus
        self.zone_view = zone_view
        self.window = window
    def activate(self, sellist, from_zone, number=1, required=False, is_opponent=False):
        self.required = required
        self.number = number
        self.tmp_dx = 0
        self.window.push_handlers(self)
        # Figure out where to pop up
        if from_zone == '': self.zone_view.pos = euclid.Vector3(self.window.width/2, self.window.height/2, 0)
        else:
            if not is_opponent: status = self.mainstatus
            else: status = self.otherstatus
            if from_zone == "hand" or from_zone == "play": 
               #self.zone_view.pos = status.pos + status.symbols["life"].pos
               self.zone_view.pos = euclid.Vector3(self.window.width/2, self.window.height/2, 0)
            else: self.zone_view.pos = status.pos + status.symbols[from_zone].pos
        self.zone_view.build(sellist, is_opponent)
        self.zone_view.show()
        self.dragging = False
        self.resizing = False
    def deactivate(self):
        self.zone_view.hide()
        self.window.pop_handlers()
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER:
            selection = [card.gamecard for card in self.zone_view.selected]
            if len(selection) == 0 and len(self.zone_view.cards) == self.number:
                self.window.user_action = Action.MultipleSelected([card.gamecard for card in self.zone_view.cards])
                self.deactivate()
            else:
                if (len(selection) == self.number) or (len(self.zone_view.cards) == 0 and len(selection) < self.number):
                    self.window.user_action = Action.MultipleSelected(selection)
                    self.deactivate()
            return True
        elif symbol == key.ESCAPE:
            if not self.required: 
                self.window.user_action = Action.CancelAction()
                self.deactivate()
            return True
        elif symbol == key.LEFT:
            if self.zone_view.focus_previous():
                sc, dx, dir = self.zone_view.scroll, self.zone_view.scroll_shift, self.zone_view.dir
                self.zone_view.scroll = (sc[0]-dx*dir, sc[1], sc[2]-dx*dir, sc[3])
            return True
        elif symbol == key.RIGHT:
            if self.zone_view.focus_next():
                sc, dx, dir = self.zone_view.scroll, self.zone_view.scroll_shift, self.zone_view.dir
                self.zone_view.scroll = (sc[0]+dx*dir, sc[1], sc[2]+dx*dir, sc[3])
            return True
        elif symbol == key.UP:
            self.zone_view.toggle_sort()
            return True
    def on_mouse_press(self, x, y, button, modifiers):
        x -= self.zone_view.pos.x
        y -= self.zone_view.pos.y
        # Check scroll bar
        l, b, r, t = self.zone_view.scroll
        if self.zone_view.dir == -1: b, t = t, b
        if button == mouse.RIGHT or modifiers & key.MOD_SHIFT:
            pass #self.resizing = True
        elif x >= l and x <= r and y >= b and y <= t:
            self.dragging = True
        else:
            flag, result = self.zone_view.handle_click(x, y)
            if flag == 0:
                if len(self.zone_view.cards):
                    if len(self.zone_view.selected) < self.number:
                        self.zone_view.select_card(result)
            elif flag == 1:
                self.zone_view.deselect_card(result)
        return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        zv = self.zone_view
        if self.dragging:
            x -= zv.pos.x
            scroll_width = (zv.scroll[2]-zv.scroll[0])/2
            if zv.scroll_bar[0]+scroll_width < x < zv.scroll_bar[2]-scroll_width:
                self.tmp_dx += dx
                sc = zv.scroll
                zv.scroll = (sc[0]+dx, sc[1], sc[2]+dx, sc[3])
                idx_change = int(self.tmp_dx / zv.scroll_shift)
                if idx_change != 0:
                    self.tmp_dx = self.tmp_dx % zv.scroll_shift
                    if idx_change < 0: self.tmp_dx -= zv.scroll_shift
                    zv.focus_idx += idx_change
                    zv.layout()
        elif self.resizing:
            self.tmp_dx += dx
            zv.shift_factor += self.tmp_dx/400
            if zv.shift_factor < 0.1:
                self.tmp_dx = 0
                zv.shift_factor = 0.1
            elif zv.shift_factor > 1.1:
                self.tmp_dx = 0
                zv.shift_factor = 1.1
            zv.layout()
        return True
    def on_mouse_motion(self, x, y, dx, dy):
        return True
    def on_mouse_release(self, x, y, button, modifiers):
        if self.dragging: self.dragging = False
        elif self.resizing: self.resizing = False
        return True

class DamageSelector(object):
    def __init__(self, playzone1, playzone2, window):
        self.play1 = playzone1
        self.play2 = playzone2
        self.window = window
    def activate(self, sellist, trample=False):
        self.trample = trample
        self.layout(sellist)
        self.window.push_handlers(self)
    def deactivate(self):
        for card in [self.attacker]+self.blockers:
            #card.damage_text.scale = 0.4
            #card.damage_text.pos = card.damage_text.zoom_pos
            card.damage_text.color = (1., 0., 0., 1.)
            card.damage_text.set_text("%d"%card.damage)
            card.restore_pos()
        self.window.pop_handlers()
    def layout(self, sellist):
        self.blockers = []
        size = 0.01 #075
        x = z = 0
        camera = self.window.camera
        currplay, otherplay = self.play1, self.play2
        for attacker, blockers in sellist:
            card = currplay.get_card(attacker)
            if card == None:
                #XXX This is a hack, since it will never occur for network play
                currplay, otherplay = self.play2, self.play1
                card = currplay.get_card(attacker)
            z = card.height*size*1.1*0.5
            card.zoom_to_camera(camera, currplay.pos.z, size=size,offset=euclid.Vector3(x,0,z))
            card.damage_text.visible = 1.0
            card.damage_text.scale = 2.0
            card.damage_text.color = (1., 1., 1., 1.)
            card.damage_text.pos = euclid.Vector3(0, -card.height/4, 0.01)
            card.damage_text.set_text("%d"%attacker.combatDamage())
            self.attacker = card
            z = -z
            width = card.width*size*(len(blockers)+0.1*(len(blockers)-1))
            x = (-width+card.width*size)*0.5*1.1
            for blocker in blockers:
                card = otherplay.get_card(blocker)
                card.zoom_to_camera(camera, otherplay.pos.z, size=size,offset=euclid.Vector3(x,0,z))
                card.text.scale = 2.0
                card.text.pos = card.text.orig_pos
                card.damage_text.visible = 1.0
                card.damage_text.scale = 2.0
                card.damage_text.pos = euclid.Vector3(0, card.height/2.5, 0.01)
                card.damage_text.set_text("0")
                self.blockers.append(card)
                x += card.width*size*1.1
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER:
            # Check damage assignment
            dmg = {}
            total_dmg = 0
            for blocker in self.blockers:
                damage = int(blocker.damage_text.value)
                dmg[blocker.gamecard] = damage
                total_dmg += damage
            if int(self.attacker.damage_text.value) == 0 or (self.trample and all([int(blocker.damage_text.value)>=blocker.gamecard.toughness for b in self.blockers])):
                self.window.user_action = Action.DamageAssignment(dmg)
                self.deactivate()
            return True
    def on_mouse_press(self, x, y, button, modifiers):
        select_ray = self.window.selection_ray(x, y)
        selected, play = self.play1.get_card_from_hit(select_ray), self.play1
        if not selected: selected, play = self.play2.get_card_from_hit(select_ray), self.play2
        if selected in self.blockers:
            power = self.attacker.damage_text
            dmg = selected.damage_text
            if (button == mouse.RIGHT or modifiers & key.MOD_OPTION): power, dmg = dmg, power
            if not int(power.value) == 0:
                power.set_text(int(power.value)-1)
                dmg.set_text(int(dmg.value)+1)
                selected.flash()
            #else:
            #    selected.shake()
        return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return True
    def on_mouse_release(self, x, y, button, modifiers):
        return True
    def on_mouse_motion(self, x, y, dx, dy):
        return True

class StatusController(object):
    def __init__(self, mainstatus, otherstatus, zone_view, window):
        self.mainstatus = mainstatus
        self.otherstatus = otherstatus
        self.zone_view = zone_view
        self.window = window
        self.value = None
        self.clicked = False
        self.observable_zones = set(["graveyard", "removed", "library"])
        self.tmp_dx = 0
        self.solitaire = False
    def set_solitaire(self):
        self.solitaire = True
    def activate(self):
        self.window.push_handlers(self)
    def deactivate(self):
        self.window.pop_handlers()
    def on_key_press(self, symbol, modifiers):
        if self.clicked:
            if symbol == key.LEFT: self.zone_view.focus_previous()
            elif symbol == key.RIGHT: self.zone_view.focus_next()
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.tmp_dx += dx
        if self.clicked:
            if self.tmp_dx > 15:
                self.tmp_dx = 0
                self.zone_view.focus_next()
            elif self.tmp_dx < -15:
                self.tmp_dx = 0
                self.zone_view.focus_previous()
        return self.clicked
    def on_mouse_release(self, x, y, button, modifiers):
        if self.clicked:
            zone_view = self.zone_view
            if len(zone_view.cards):
                self.window.user_action = Action.CardSelected(zone_view.focused.gamecard, zone_view.focused.gamecard.zone)
                if modifiers & key.MOD_CTRL: self.window.keep_priority()
            zone_view.hide()
            self.tmp_dx = 0
            self.clicked = False
    def on_mouse_press(self, x, y, button, modifiers):
        for status in [self.mainstatus, self.otherstatus]:
            value = status.handle_click(x, y)
            if value:
                if value == "life": self.window.user_action = Action.PlayerSelected(status.player)
                if value == "library" and not self.solitaire: return True # and self.window.start_new_game: return True
                elif value in self.observable_zones:
                    zone = getattr(status.player, value)
                    if len(zone):
                        self.clicked = True
                        self.zone_view.pos = euclid.Vector3(x, y, 0)
                        self.zone_view.pos = status.pos + status.symbols[value].pos
                        self.zone_view.build(zone, status.is_opponent)
                        self.zone_view.show()
                return True

class XSelector(object):
    def __init__(self, mana_gui, window):
        self.mana = mana_gui
        self.colorless_symbol = mana_gui.symbols[-1]
        self.colorless = mana_gui.values["colorless"]
        self.window = window
    def request_x(self):
        self.activate(x=True)
        self.mana.cost.set_text("Choose X")
        self.orig_alpha = self.colorless_symbol.alpha
        self.orig_colorless = self.colorless.value
        self.colorless.set_text(0)
    def activate(self, x=False):
        self.mana.select(x)
        self.window.push_handlers(self)
    def deactivate(self):
        self.colorless.set_text(self.orig_colorless)
        self.colorless_symbol.alpha = self.orig_alpha
        self.mana.select()
        self.window.pop_handlers()
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER:
            amount = int(self.mana.spend_values["colorless"].value)
            self.window.user_action = Action.XSelected(amount)
            self.deactivate()
            return True
        elif symbol == key.ESCAPE:
            self.window.user_action = Action.CancelAction()
            self.colorless.set_text(self.orig_colorless)
            self.deactivate()
            return True
    def on_mouse_press(self, x, y, button, modifiers):
        # Find out which mana we selected
        x -= self.window.mainplayer_status.pos.x + self.mana.pos.x
        y -= self.window.mainplayer_status.pos.y + self.mana.pos.y
        values = self.mana.handle_click(x, y)
        if values:
            symbol, current, pay = values
            if (button == mouse.RIGHT or modifiers & key.MOD_OPTION):
                if not int(pay.value) == 0:
                    pay.set_text(int(pay.value)-1)
                    symbol.animate(sparkle=False)
            else:
                pay.set_text(int(pay.value)+1)
                symbol.animate(sparkle=False)
        return True
    def on_mouse_release(self, x, y, button, modifiers):
        return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return True
    def on_mouse_motion(self, x, y, dx, dy):
        return True

class ManaController(object):
    def __init__(self, mainmana_gui, othermana_gui, window):
        self.mainmana = mainmana_gui
        self.othermana = othermana_gui
        self.window = window
    def request_mana(self, required, manapool):
        self.mana = self.mainmana
        self.activate()
        self.manapool = manapool
        self.required_str = required
        required = Mana.convert_mana_string(required)
        for i, color in enumerate(self.mana.colors):
            nummana = getattr(manapool, color)
            req_mana = manapool.getMana(required,color)
            spend = min(nummana,req_mana)
            self.mana.spend_values[color].set_text(spend)
            self.mana.values[color].set_text(nummana-spend)
            if nummana == 0:
                self.mana.spend_values[color].visible = 0
                self.mana.values[color].visible = 0
                self.mana.symbols[i].alpha = 0.5
        self.set_cost()
    def reset_mana(self):
        for color in self.mana.colors:
            self.mana.values[color].set_text(getattr(self.manapool, color))
    def activate(self, x=False):
        self.mana.select(x)
        self.mana.pos = euclid.Vector3((self.window.width-self.mana.width)/2, self.window.height/2, 0)
        self.window.push_handlers(self)
    def deactivate(self):
        self.reset_mana()
        self.mana.select()
        self.window.pop_handlers()
    def set_cost(self):
        def convert(val):
            if val == '': return 0
            else: return int(val)
        mana = [convert(self.mana.spend_values[c].value) for c in self.mana.colors]
        self.required = Mana.convert_mana_string(self.required_str)
        for i, val in enumerate(mana):
            for j in range(val):
                if self.required[i] == 0: self.required[-1] -= 1
                else: self.required[i] -= 1
        manastr = Mana.convert_to_mana_string(self.required)
        if manastr == "0": manastr = 'Fulfilled'
        else: manastr = 'Required (%s): %s'%(self.required_str, manastr)
        self.mana.cost.set_text(manastr)
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER:
            # Check if we have enough mana
            mana = [self.mana.spend_values[c].value for c in self.mana.colors]
            manastr = ''.join([color*int(mana[i]) for i, color in enumerate("WUBRG") if mana[i] != ''])
            if mana[-1] > 0: manastr += str(mana[-1])
            if manastr == '': manastr = '0'
            if Mana.compareMana(self.required_str, manastr) and self.manapool.checkMana(manastr):
                self.window.user_action = Action.ManaSelected(manastr)
                self.deactivate()
            return True
        elif symbol == key.ESCAPE:
            self.window.user_action = Action.CancelAction()
            self.deactivate()
            return True
    def on_mouse_release(self, x, y, button, modifiers):
        return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return True
    def on_mouse_press(self, x, y, button, modifiers):
        # Find out which mana we selected
        x -= self.window.mainplayer_status.pos.x + self.mana.pos.x
        y -= self.window.mainplayer_status.pos.y + self.mana.pos.y
        values = self.mana.handle_click(x, y)
        if values:
            symbol, current, pay = values
            if (button == mouse.RIGHT or modifiers & key.MOD_OPTION): current, pay = pay, current
            if not int(current.value) == 0: # or Mana.convert_to_mana_string(self.required) == "0"):
                current.set_text(int(current.value)-1)
                pay.set_text(int(pay.value)+1)
                symbol.animate(sparkle=False)
                self.set_cost()
        return True
    def on_mouse_motion(self, x, y, dx, dy):
        return True

class PhaseController(object):
    def __init__(self, phasegui, window):
        self.phases = phasegui
        self.window = window
        self.dim = 0.4
    def activate(self, other=False):
        self.other = other
        if not other: self.stops = self.window.my_turn_stops
        else: self.stops = self.window.opponent_turn_stops
        self.phases.toggle_select(other)
        for key, (i, val) in self.phases.state_map.items():
            state = self.phases.states[i]
            label = self.phases.state_labels[i]
            if other: label.main_text.halign = "right"
            else: label.main_text.halign = "left"
            if key == "Untap":
                state.visible = 0
                label.visible = 0
            elif key.lower() in self.stops:
                state.alpha = self.dim
                label.scale = 0.6
                col = label.main_text.color
                label.main_text.color = (col[0], col[1], col[2], self.dim)
        self.window.push_handlers(self)
    def deactivate(self):
        if not self.other: self.window.my_turn_stops = self.stops
        else: self.window.opponent_turn_stops = self.stops
        for state, label in zip(self.phases.states, self.phases.state_labels):
            state.visible = 1.0
            state.alpha = 1.0
            label.visible = 1.0
            label.scale = 0.8
            col = label.main_text.color
            label.main_text.color = (col[0], col[1], col[2], 1.0)
        self.phases.toggle_select()
        self.window.pop_handlers()
    def on_key_press(self, symbol, modifiers):
        if symbol in [key.ENTER, key.ESCAPE, key.F]:
            return True
        if symbol == key.F2:
            self.deactivate()
            if self.other: self.activate(not self.other)
            return True
        elif symbol == key.F3:
            self.deactivate()
            if not self.other: self.activate(not self.other)
            return True
    def on_mouse_release(self, x, y, button, modifiers):
        return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return True
    def on_mouse_motion(self, x, y, dx, dy):
        return True
    def on_mouse_press(self, x, y, button, modifiers):
        value = self.phases.handle_click(x, y)
        if value:
            key, state, label = value
            if key.lower() in self.stops:
                self.stops.remove(key.lower())
                state.alpha = 1.0
                label.scale = 0.8
                col = label.main_text.color
                label.main_text.color = (col[0], col[1], col[2], 1.0)
            else:
                self.stops.add(key.lower())
                state.alpha = self.dim
                label.scale = 0.6
                col = label.main_text.color
                label.main_text.color = (col[0], col[1], col[2], self.dim)
        return True

class PlayController(object):
    def __init__(self, play, other_play, window):
        self.play = play
        self.other_play = other_play
        self.window = window
        self.camera = window.camera
        self.selected = None
        self.zooming = False
    def set_zones(self, play, otherplay):
        self.mainzone = play
        self.otherzone = otherplay
    def activate(self):
        self.window.push_handlers(self)
    def deactivate(self):
        self.window.pop_handlers()
    def on_mouse_press(self, x, y, button, modifiers):
        # Iterate over all polys in all items, collect all intersections
        select_ray = self.window.selection_ray(x, y)
        self.selected, play = self.play.get_card_from_hit(select_ray), self.play
        if not self.selected: self.selected, play = self.other_play.get_card_from_hit(select_ray), self.other_play
        # Zoom the card
        if self.selected and (button == mouse.RIGHT or modifiers & key.MOD_OPTION):
            self.zooming = True
            self.selected.zoom_to_camera(self.camera, play.pos.z)
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        # Move the camera based on mouse movement
        if not self.selected:
            if buttons == mouse.RIGHT or modifiers & key.MOD_SHIFT:
                self.camera.move_by(euclid.Vector3(dx, 0, -dy))
            if buttons == mouse.MIDDLE or modifiers & key.MOD_OPTION:
                self.camera.move_by(euclid.Vector3(0,-dy,0))
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if not self.zooming: self.camera.move_by(euclid.Vector3(0,scroll_y,0))
    def on_mouse_release(self, x, y, button, modifiers):
        if self.selected is not None:
            if self.zooming:
                self.selected.restore_pos()
                self.zooming = False
            elif button == mouse.LEFT:
                #self.selected.flash()
                self.window.user_action = Action.CardSelected(self.selected.gamecard, self.selected.gamecard.zone)
                if modifiers & key.MOD_CTRL: self.window.keep_priority()
            self.selected = None

class HandController(object):
    def __init__(self, player_hand, window):
        self.player_hand = player_hand
        self.window = window
        self.card_clicked = None
        self.mouse_down = False
        self.dragged = False
        self.zooming = False
    def set_zone(self, zone):
        self.zone = zone
    def activate(self):
        self.window.push_handlers(self)
        self.drag_x = 0
    def deactivate(self):
        self.window.pop_handlers()
    def on_mouse_press(self, x, y, button, modifiers):
        if self.mouse_down: return True
        hand = self.player_hand
        x -= hand.pos.x
        y -= hand.pos.y
        if (hand.box[0] < x < hand.box[2] and hand.box[1] < y < hand.box[3]):
            self.mouse_down = True
            for card in hand.cards[::-1]:
                sx, sy, sw, sh = card.pos.x, card.pos.y, card.width*card.size/2, card.height*card.size/2
                if x > sx-sw and x < sx+sw and y >= sy-sh and y <= sy+sh:
                    self.card_clicked = card
                    if (button == mouse.RIGHT or modifiers & key.MOD_OPTION):
                        self.zooming = True
                        hand.zoom_card(self.card_clicked)
        else: self.mouse_down = False
        return self.mouse_down
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        hand = self.player_hand
        x -= hand.pos.x
        y -= hand.pos.y
        if self.mouse_down and self.card_clicked:
            if not self.zooming:
                return True
                self.drag_x += dx
                self.dragged = True
                w = self.card_clicked.width*self.card_clicked.size
                if self.drag_x > w or self.drag_x < -w:
                    if self.drag_x > w:
                        for i in range(int(self.drag_x/w)):
                            if hand.dir == 1: hand.shift_right(self.card_clicked)
                            else: hand.shift_left(self.card_clicked)
                    elif self.drag_x < -w:
                        for i in range(int(self.drag_x/-w)):
                            if hand.dir == 1: hand.shift_left(self.card_clicked)
                            else: hand.shift_right(self.card_clicked)
                    hand.layout()
                    self.drag_x = 0
                self.card_clicked._pos.set(self.card_clicked.pos)
                self.card_clicked._pos.x = self.card_clicked.pos.x + dx
            elif (buttons == mouse.RIGHT or modifiers & key.MOD_OPTION):
                for card in hand.cards[::-1]:
                    sx, sy, sw, sh = card.pos.x, card.pos.y, card.width*card.size/2, card.height*card.size/2
                    if x > sx-sw and x < sx+sw and y >= sy-sh and y <= sy+sh and not card == self.card_clicked:
                        hand.restore_card(self.card_clicked)
                        hand.zoom_card(card)
                        self.card_clicked = card
        return self.mouse_down
    def on_mouse_release(self, x, y, button, modifiers):
        if self.mouse_down:
            self.mouse_down = False
            if self.card_clicked:
                if self.zooming:
                    self.zooming = False
                    self.player_hand.restore_card(self.card_clicked)
                elif self.dragged:
                    # Move the card
                    self.dragged = False
                    self.player_hand.layout()
                else:
                    self.window.user_action = Action.CardSelected(self.card_clicked.gamecard, self.zone)
                    if modifiers & key.MOD_CTRL: self.window.keep_priority()
                self.card_clicked = None
            return True
        else: return False

from game.Ability import MultipleTargets, AllPermanentTargets, AllPlayerTargets
from game.Match import isPlayer, isPermanent, isAbility
class StackController(object):
    def __init__(self, stack_gui, window):
        self.stack_gui = stack_gui
        self.window = window
        self.tmp_dy = 0
        self.focused = False
        self.highlighted = []
    def set_zone(self, zone):
        self.zone = zone
    def activate(self):
        #self.activated = True
        #self.stack_gui.focus()
        #self.highlight_targets()
        self.window.push_handlers(self)
    def deactivate(self):
        #self.stack_gui.unfocus()
        #for obj in self.highlighted: obj.unhighlight()
        #self.highlighted = []
        self.window.pop_handlers()
        #self.activated = False
    def highlight_targets(self):
        old_highlighted = self.highlighted
        self.highlighted = []
        # Get targets
        targets = self.stack_gui.focused.ability.targets
        for t in targets:
            if not (isinstance(t, MultipleTargets) or isinstance(t, AllPermanentTargets) or isinstance(t, AllPlayerTargets)): t = [t.target]
            else: t = t.target
            for i, tt in enumerate(t):
                if tt == None: continue  # For delayed targeting abilities, like champion
                if isAbility(tt):
                    guicard = self.stack_gui.get_card(tt)
                    if guicard:
                        self.highlighted.append(guicard)
                        if guicard in old_highlighted: old_highlighted.remove(guicard)
                        guicard.highlight()
                elif isPlayer(tt):
                    for status in [self.window.mainplayer_status, self.window.otherplayer_status]:
                        if tt == status.player:
                            status.animate("life")
                elif isPermanent(tt):
                    for play in [self.window.mainplay, self.window.otherplay]:
                        guicard = play.get_card(tt)
                        if guicard:
                            self.highlighted.append(guicard)
                            if guicard in old_highlighted: old_highlighted.remove(guicard)
                            guicard.highlight()
        for obj in old_highlighted: obj.unhighlight()
    def focus_previous(self):
        if self.stack_gui.focus_previous():
            self.highlight_targets()
    def focus_next(self):
        if self.stack_gui.focus_next():
            self.highlight_targets()
    def on_key_press(self, symbol, modifiers):
        if self.focused:
            stack = self.stack_gui
            if symbol == key.UP:
                self.focus_previous()
            elif symbol == key.DOWN:
                self.focus_next()
            elif symbol == key.RIGHT:
                stack.text.visible = 1-stack.text.visible
            elif symbol == key.ENTER:
                if stack.focused.announced: self.window.user_action = Action.CardSelected(stack.focused.ability, self.zone)
                return True
            elif symbol == key.ESCAPE:
                self.deactivate()
                return True
    def on_mouse_press(self, x, y, button, modifiers):
        idx, card = self.stack_gui.handle_click(x, y)
        if idx != -1:
            if (button == mouse.RIGHT or modifiers & key.MOD_OPTION):
                self.focused = True
                self.stack_gui.focus(idx)
                self.highlight_targets()
            else:
                if card.announced: self.window.user_action = Action.CardSelected(card.ability, self.zone)
            return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return self.focused
    def on_mouse_release(self, x, y, button, modifiers):
        if self.focused:
            self.stack_gui.unfocus()
            for obj in self.highlighted: obj.unhighlight()
            self.highlighted = []
            self.focused = False
            return True
