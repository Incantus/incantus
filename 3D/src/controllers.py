import euclid
from pyglet.window import key, mouse
from game import Action
from game import Mana

class MessageController(object):
    def __init__(self, dialog, window):
        self.dialog = dialog
        self.window = window
        self.do_action = True
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
        return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return True
    def on_mouse_release(self, x, y, button, modifiers):
        x -= self.dialog.pos.x
        y -= self.dialog.pos.y
        result = self.dialog.handle_click(x, y)
        if not result == -1:
            if self.do_action:
                if result == True: self.window.user_action = Action.OKAction()
                else: self.window.user_action = Action.CancelAction()
            self.deactivate()
        return True

class SelectController(object):
    def __init__(self, listview, window):
        self.listview = listview
        self.window = window
        self.required = False
        self.tmp_dy = 0
        #self.index = None
    def activate(self):
        self.listview._pos.set(euclid.Vector3(self.window.width/2, self.window.height/2, 0))
        self.listview.show()
        #self.window.set_mouse_visible(False)
        self.window.push_handlers(self)
        self.dragging = False
    def deactivate(self):
        self.listview.hide()
        #self.window.set_mouse_visible(True)
        self.window.pop_handlers()
    def build(self,sellist,required,numselections,prompt=''):
        self.required = required
        self.numselections = numselections
        self.listview.construct(prompt,sellist)
        self.activate()
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER:
            self.return_selections()
            return True
        elif symbol == key.ESCAPE:
            if not self.required:
                self.window.user_action = Action.CancelAction()
                self.deactivate()
            return True
        elif symbol == key.SPACE:
            self.return_selections()
            return True
        elif symbol == key.UP:
            self.listview.focus_previous()
        elif symbol == key.DOWN:
            self.listview.focus_next()
    def return_selections(self):
        if self.numselections == 1: SelAction = Action.SingleSelected
        else: SelAction = Action.MultipleSelected
        self.window.user_action = SelAction(self.listview.selection(self.numselections))
        self.deactivate()
    def on_mouse_press(self, x, y, button, modifiers):
        return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.dragging = True
        self.tmp_dy += dy
        if self.tmp_dy > 2:
            self.tmp_dy = 0
            self.listview.move_up()
        elif self.tmp_dy < -2:
            self.tmp_dy = 0
            self.listview.move_down()
        return True
    def on_mouse_release(self, x, y, button, modifiers):
        if self.dragging:
            self.dragging = False
            return True
        else:
            #x -= self.listview.pos.x
            #y -= self.listview.pos.y
            self.return_selections()
    def on_mouse_motion(self, x, y, dx, dy):
        self.tmp_dy += dy
        if self.tmp_dy > 2:
            self.tmp_dy = 0
            self.listview.focus_previous()
        elif self.tmp_dy < -2:
            self.tmp_dy = 0
            self.listview.focus_next()
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
        #self.window.set_mouse_visible(False)
        self.window.push_handlers(self)
        # Figure out where to pop up
        if from_zone == '': self.zone_view.pos = euclid.Vector3(self.window.width/2, self.window.height/2, 0)
        else:
            if not is_opponent: status = self.mainstatus
            else: status = self.otherstatus
            self.zone_view.pos = status.pos + status.symbols[from_zone].pos
        self.zone_view.build(sellist, is_opponent)
        self.zone_view.show()
    def deactivate(self):
        self.zone_view.hide()
        #self.window.set_mouse_visible(True)
        self.window.pop_handlers()
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER:
            selection = [card.gamecard for card in self.zone_view.selected]
            if (len(selection) == self.number) or (len(self.zone_view.cards) == 0 and len(selection) < self.number):
                self.window.user_action = Action.MultipleSelected(selection)
                self.deactivate()
            return True
        elif symbol == key.ESCAPE:
            if not self.required: self.window.user_action = Action.CancelAction()
            self.deactivate()
            return True
        elif symbol == key.LEFT:
            self.zone_view.focus_previous()
            return True
        elif symbol == key.RIGHT:
            self.zone_view.focus_next()
            return True
        elif symbol == key.UP:
            self.zone_view.toggle_sort()
            return True
    def on_mouse_press(self, x, y, button, modifiers):
        x -= self.zone_view.pos.x
        y -= self.zone_view.pos.y
        result = self.zone_view.handle_click(x, y)
        if result:
            self.zone_view.deselect_card(result)
        else:
            if len(self.zone_view.cards):
                if self.number == 1: 
                    self.window.user_action = Action.MultipleSelected([self.zone_view.focused.gamecard])
                    self.deactivate()
                else:
                    if len(self.zone_view.selected) < self.number:
                        self.zone_view.select_card()
        return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return True
    def on_mouse_motion(self, x, y, dx, dy):
        self.tmp_dx += dx
        if self.tmp_dx > 15:
            self.tmp_dx = 0
            self.zone_view.focus_next()
        elif self.tmp_dx < -15:
            self.tmp_dx = 0
            self.zone_view.focus_previous()
        return True
    def on_mouse_release(self, x, y, button, modifiers):
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
        self.observable_zones = set(["graveyard", "removed", "hand", "library"])
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
            #self.window.set_mouse_visible(True)
            self.tmp_dx = 0
            self.clicked = False
    def on_mouse_press(self, x, y, button, modifiers):
        for status in [self.mainstatus, self.otherstatus]:
            value = status.handle_click(x, y)
            if value:
                if value == "life": self.window.user_action = Action.PlayerSelected(status.player)
                if value == "hand" and status == self.otherstatus and not self.solitaire: return True
                if value == "library": return False # and self.window.start_new_game: return True
                elif value in self.observable_zones:
                    zone = getattr(status.player, value)
                    if len(zone):
                        self.clicked = True
                        #self.window.set_mouse_visible(False)
                        self.zone_view.pos = euclid.Vector3(x, y, 0)
                        self.zone_view.pos = status.pos + status.symbols[value].pos
                        self.zone_view.build(zone, status.is_opponent)
                        self.zone_view.show()
                return True

class XSelector(object):
    def __init__(self, mana_gui, window):
        self.mana = mana_gui
        self.colorless = mana_gui.values["colorless"]
        self.window = window
    def request_x(self):
        self.activate(x=True)
        self.mana.cost.set_text("Choose X")
        self.orig_colorless = self.colorless.value
        self.colorless.set_text(0)
    def activate(self, x=False):
        self.mana.select(x)
        self.mana.pos = euclid.Vector3(self.window.width/2, self.window.height/2, 0)
        self.window.push_handlers(self)
    def deactivate(self):
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
    def __init__(self, mana_gui, window):
        self.mana = mana_gui
        self.window = window
    def request_mana(self, required, manapool):
        self.activate()
        self.manapool = manapool
        self.mana.cost.set_text("Required: "+required)
        self.required_str = required
        required = Mana.convert_mana_string(required)
        for color in self.mana.colors:
            nummana = getattr(manapool, color)
            req_mana = manapool.getMana(required,color)
            spend = min(nummana,req_mana)
            self.mana.spend_values[color].set_text(spend)
            self.mana.values[color].set_text(nummana-spend)
    def reset_mana(self):
        for color in self.mana.colors:
            self.mana.values[color].set_text(getattr(self.manapool, color))
    def activate(self, x=False):
        self.mana.select(x)
        self.mana.pos = euclid.Vector3(0, self.window.height/2, 0)
        self.window.push_handlers(self)
    def deactivate(self):
        self.mana.select()
        self.window.pop_handlers()
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER:
            # Check if we have enough mana
            mana = [self.mana.spend_values[c].value for c in self.mana.colors]
            manastr = ''.join([color*int(mana[i]) for i, color in enumerate("WRGUB") if mana[i] != ''])
            if mana[-1] > 0: manastr += str(mana[-1])
            if manastr == '': manastr = '0'
            if Mana.compareMana(self.required_str, manastr) and self.manapool.checkMana(manastr):
                self.window.user_action = Action.ManaSelected(manastr)
                self.deactivate()
            return True
        elif symbol == key.ESCAPE:
            self.window.user_action = Action.CancelAction()
            self.reset_mana()
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
            if not int(current.value) == 0:
                current.set_text(int(current.value)-1)
                pay.set_text(int(pay.value)+1)
                symbol.animate(sparkle=False)
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
        #elif symbol == key.T:
        #    self.deactivate()
        #    self.activate(not self.other)
        #    return True
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
        if not self.zooming:
            if buttons == mouse.RIGHT or modifiers & key.MOD_SHIFT:
                self.camera.move_by(euclid.Vector3(0,-dy,0))
                if self.camera.pos.y <= 10: self.camera._pos.y = 10
                elif self.camera.pos.y >= 25: self.camera._pos.y = 25
            elif buttons == mouse.LEFT: self.camera.move_by(euclid.Vector3(dx, 0, -dy))
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
        self.tmp_dx = 0
        self.activated = False
    def set_zone(self, zone):
        self.zone = zone
    def activate(self):
        self.player_hand.show()
        if not self.activated:
            self.activated = True
            self.window.mainplayer_status.hide()
            #self.window.set_mouse_visible(False)
            self.window.push_handlers(self)
    def deactivate(self):
        #self.window.set_mouse_visible(True)
        if self.activated:
            self.activated = False
            self.player_hand.hide()
            self.window.mainplayer_status.show()
            self.window.pop_handlers()
            self.tmp_dx = 0
    def on_key_press(self, symbol, modifiers):
        hand = self.player_hand
        if symbol == key.LEFT:
            hand.focus_previous()
        elif symbol == key.RIGHT:
            hand.focus_next()
        elif symbol == key.SPACE:
            if len(hand) > 0: self.window.user_action = Action.CardSelected(hand.focused.gamecard, self.zone)
            if modifiers & key.MOD_CTRL: self.window.keep_priority()
            return True
        #elif symbol == key.ESCAPE:
        #    self.deactivate()
        #    return True
        elif symbol == key.ENTER:
            self.deactivate()
            return True
    def on_mouse_press(self, x, y, button, modifiers):
        return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if modifiers & key.MOD_SHIFT:
            min_size = 0.2
            max_size = 1.0
            self.tmp_dx += dx
            if self.tmp_dx >= 400: self.tmp_dx = 400
            elif self.tmp_dx <= -400: self.tmp_dx = -400
            self.player_hand.small_size = 0.6 + (max_size-min_size)*self.tmp_dx/(2*400.)
            self.player_hand.layout()
        return True
    def on_mouse_release(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            hand = self.player_hand
            if len(hand) > 0:
                self.window.user_action = Action.CardSelected(hand.focused.gamecard, self.zone)
            if modifiers & key.MOD_CTRL: self.window.keep_priority()
        elif button == mouse.RIGHT:
            self.deactivate()
        return True
    def on_mouse_motion(self, x, y, dx, dy):
        self.tmp_dx += dx
        if self.tmp_dx > 10:
            self.tmp_dx = 0
            self.player_hand.focus_next()
        elif self.tmp_dx < -10:
            self.tmp_dx = 0
            self.player_hand.focus_previous()
        return True

from game.Ability import MultipleTargets, AllPermanentTargets, AllPlayerTargets
from game.Match import isPlayer, isPermanent, isAbility
class StackController(object):
    def __init__(self, stack_gui, window):
        self.stack_gui = stack_gui
        self.window = window
        self.tmp_dy = 0
        self.activated = False
        self.highlighted = []
    def set_zone(self, zone):
        self.zone = zone
    def activate(self):
        self.activated = True
        self.stack_gui.focus()
        self.highlight_targets()
        #self.window.set_mouse_visible(False)
        #self.window.otherplayer_status.hide()
        self.window.push_handlers(self)
    def deactivate(self):
        self.stack_gui.unfocus()
        for obj in self.highlighted: obj.unhighlight()
        self.highlighted = []
        #self.window.set_mouse_visible(True)
        #self.window.otherplayer_status.show()
        self.window.pop_handlers()
        self.activated = False
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
                elif isPlayer(tt): # and t.targeting == None:
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
        stack = self.stack_gui
        if symbol == key.UP:
            self.focus_previous()
        elif symbol == key.DOWN:
            self.focus_next()
        elif symbol == key.SPACE:
            self.window.user_action = Action.CardSelected(stack.focused.ability, self.zone)
            return True
        elif symbol == key.ESCAPE:
            self.deactivate()
            return True
    def on_mouse_press(self, x, y, button, modifiers):
        self.window.user_action = Action.CardSelected(self.stack_gui.focused.ability, self.zone)
        return True
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return True
    def on_mouse_release(self, x, y, button, modifiers):
        #stack = self.stack_gui
        #self.window.user_action = Action.CardSelected(hand.focused.gamecard, self.zone)
        #self.deactivate()
        return True
    def on_mouse_motion(self, x, y, dx, dy):
        if y < self.window.height-200: self.deactivate()
        return True
    def on_mouse_motion2(self, x, y, dx, dy):
        self.tmp_dy += dy
        if self.tmp_dy > 15:
            self.tmp_dy = 0
            self.focus_next()
        elif self.tmp_dy < -15:
            self.tmp_dy = 0
            self.focus_previous()
        if y < self.window.height-200: self.deactivate()
        return True
