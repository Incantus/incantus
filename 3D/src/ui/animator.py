import random
from pyglet import image
from pyglet import clock
from pyglet.gl import *
import euclid
import anim
from widget import Image, Label
from resources import ColorDict
import CardLibrary
from game import GameEvent
from game.pydispatch import dispatcher
from game.Match import isPlayer, isPermanent, isAbility

from play_view import CombatZone

class SparkFXManager(object):
    COLORS = ColorDict()
    def __init__(self):
        self.active_sparks = []
        self.active_sparks_3d = []
        clock.schedule_interval(self.purge, 10)
        self.randomizer = random.Random()
    def purge(self, dt):
        alive = []
        for spark in self.active_sparks:
            if not spark.visible == 0: alive.append(spark)
        self.active_sparks[:] = alive
        alive = []
        for spark in self.active_sparks_3d:
            if not spark.visible == 0: alive.append(spark)
        self.active_sparks_3d[:] = alive
    def render3d(self):
        for spark in self.active_sparks_3d: spark.render()
    def render2d(self):
        glEnable(GL_TEXTURE_2D)
        for spark in self.active_sparks: spark.render()
        glDisable(GL_TEXTURE_2D)
    def add_number_spark(self, number, start_pos, end_pos, dt=1.0, color=None, dim=2):
        random_offset = euclid.Vector3(self.randomizer.random()*50-25,self.randomizer.random()*30,0)
        start_pos += random_offset
        end_pos += random_offset
        if color == None: color=(1.,1.,1.,1)
        elif type(color) == str: color = self.COLORS.get(color)
        else: color = color
        spark = Label(str(number), size=40, color=color, shadow=False, halign="center", valign="center", pos=start_pos)
        spark._pos.set_transition(dt=dt, method="ease_out_circ") #ease_out_back")
        spark.pos = end_pos
        spark.visible = anim.animate(1., 0., dt=dt)
        spark.scale = anim.animate(1.0, 1.3, dt=dt, method="sine")
        if dim == 2: self.active_sparks.append(spark)
        else: self.active_sparks_3d.append(spark)
    def add_spark(self, start_pos, end_pos, dt=1.0, color=None, grow=False, dim=2):
        spark = Image("glow", pos=start_pos)
        spark._pos.set_transition(dt=dt, method="ease_out_back") #ease_out_circ") #ease_out_back")
        spark.pos = end_pos
        if color == None: spark.color=(1.,1.,1.)
        elif type(color) == str:
            spark.color = self.COLORS.get(color)
        else: spark.color = color
        spark.visible = anim.animate(1., 0., dt=dt)
        if grow: spark.scale = anim.animate(0.5, 2.0, dt=dt, method="sine")
        else: spark.scale = anim.animate(2.0, 0.2, dt=dt, method="sine")
        if dim == 2: self.active_sparks.append(spark)
        else: self.active_sparks_3d.append(spark)
    def add_star_spark(self, start_pos, end_pos, dt=1.0, color=None, start_size=0.2, end_size=2.0, dim=2):
        spark = Image('targeting', pos=start_pos)
        if color == None: spark.color = (1.0, 1.0, 1.0)
        elif type(color) == str:
            spark.color = self.COLORS.get(color)
        else: spark.color = color
        spark.visible = anim.animate(1., 0., dt=dt)
        spark.rotatez = anim.animate(-15, 45, dt=dt, method="sine")
        spark.scale = anim.animate(start_size, end_size, dt=dt, method="sine")
        spark.alpha = anim.animate(1.0, 0., dt=dt)
        if dim == 2: self.active_sparks.append(spark)
        else: self.active_sparks_3d.append(spark)
    def add_sparkle_star(self, start_pos, end_pos, dt=1.0, color=None, dim=2):
        if color == None: color = (1., 0.9, 0)
        elif type(color) == str: color = self.COLORS.get(color)
        else: color = color
        spark = Image('targeting', pos=start_pos)
        spark.visible = anim.animate(1., 0., dt=dt)
        spark.rotatez = anim.animate(-15, 45, dt=dt, method="sine")
        spark.scale = anim.animate(0.2, 1.5, dt=dt, method="sine")
        spark.color = color
        spark.alpha = anim.animate(1.0, 0., dt=dt)
        if dim == 2: self.active_sparks.append(spark)
        else: self.active_sparks_3d.append(spark)
        dt = 0.75*dt
        spark = Image('glow', pos=start_pos)
        spark._pos.set_transition(dt=dt, method="ease_out_back")
        spark.pos = end_pos
        spark.color = color
        spark.visible = anim.animate(1., 0., dt=dt)
        spark.alpha = anim.animate(1.0, 0., dt=dt)
        spark.scale = anim.animate(0.5, 1.5, dt=dt, method="sine")
        if dim == 2: self.active_sparks.append(spark)
        else: self.active_sparks_3d.append(spark)


class ZoneAnimator(object):
    def __init__(self, window):
        self.status_zones = {}
        self.play_zones = {}
        self.tracker = {}
        self.window = window
        self.sparks = SparkFXManager()
        self.player_status = {}

        self.red_zone = None
    def setup(self, main_status, other_status, stack, main_play, other_play, board):
        for playerstatus, playzone in zip([main_status, other_status], [main_play, other_play]):
            for status in ["library", "graveyard", "removed"]:
                self.status_zones[getattr(playerstatus.player, status)] = (playerstatus, playerstatus.symbols[status])
            self.play_zones[playerstatus.player.play] = playzone
            self.player_status[playerstatus.player] = (playerstatus, playerstatus.symbols["life"])
        self.player = main_status.player
        self.stack = stack
        self.board = board
        self.register()
    def register(self):
        dispatcher.connect(self.enter_zone, signal=GameEvent.CardEnteredZone(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.leave_zone, signal=GameEvent.CardLeftZone(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.enter_stack, signal=GameEvent.AbilityAnnounced(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.leave_stack, signal=GameEvent.AbilityRemovedFromStack(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.controller_changed, signal=GameEvent.CardControllerChanged(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.select_attacker, signal=GameEvent.AttackerSelectedEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.reset_attackers, signal=GameEvent.AttackersResetEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.declare_attackers, signal=GameEvent.DeclareAttackersEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.select_blocker, signal=GameEvent.BlockerSelectedEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.reset_blockers, signal=GameEvent.BlockersResetEvent(), priority=dispatcher.UI_PRIORITY)

        dispatcher.connect(self.end_combat, signal=GameEvent.EndCombatEvent())
        dispatcher.connect(self.card_damage, signal=GameEvent.ReceivesDamageEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.player_life, signal=GameEvent.LifeChangedEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.invalid_target, signal=GameEvent.InvalidTargetEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.targeted_by, signal=GameEvent.TargetedByEvent(), priority=dispatcher.UI_PRIORITY)
    def invalid_target(self, sender, target):
        if isAbility(target):
            guicard = self.stack.get_card(target)
            guicard.shake()
            clock.schedule_once(lambda t: guicard.unshake(), 0.25)
        elif isPlayer(target):
            pstatus, life = self.player_status[target]
            if life.shaking == 0:
                life.shaking = 1
                life._pos.set_transition(dt=0.25, method=lambda t: anim.oscillate_n(t, 4))
                life.pos += euclid.Vector3(10, 0, 0)
                clock.schedule_once(lambda t: setattr(life, "shaking", 0), 0.5)
        elif isPermanent(target):
            zone = self.play_zones[target.zone]
            guicard = zone.get_card(target)
            guicard.shake()
            clock.schedule_once(lambda t: guicard.unshake(), 0.25)
    def targeted_by(self, sender, targeter):
        color =  (0.5,0.71,0.94, 1.0)
        dt = 2.0
        if isPlayer(sender):
            pstatus, life = self.player_status[sender]
            pos = pstatus.pos + life.pos
            self.sparks.add_star_spark(pos, pos, dt=dt, color=color, dim=2)
        if isPermanent(sender):
            zone = self.play_zones[sender.zone]
            guicard = zone.get_card(sender)
            start_pos = self.window.project_to_window(*tuple(zone.pos+guicard.pos))
            self.sparks.add_star_spark(start_pos, start_pos, dt=dt, color=color, dim=2)
    def card_damage(self, sender, source, amount):
        zone = self.play_zones[sender.controller.play]
        guicard = zone.get_card(sender)
        start_pos = self.window.project_to_window(*tuple(zone.pos+guicard.pos))+euclid.Vector3(0,10,0)
        end_pos = start_pos + euclid.Vector3(0,40,0)
        self.sparks.add_number_spark(amount, start_pos, end_pos, color=(1,0,0,1), dt=1.0, dim=2)
    def player_life(self, sender, amount):
        pstatus, life = self.player_status[sender]
        start_pos = pstatus.pos + life.pos + euclid.Vector3(0,10,0)
        end_pos = start_pos + euclid.Vector3(0,30,0)
        if amount < 0: color = (1, 0, 0, 1)
        else: color = (1, 1, 1, 1)
        self.sparks.add_number_spark(amount, start_pos, end_pos, dt=1.0, color=color, dim=2)
    def select_attacker(self, sender, attacker):
        if not self.red_zone:
            play_zones = self.play_zones.values()
            attack_zone = self.play_zones[sender.play]
            play_zones.remove(attack_zone)
            block_zone = play_zones[0]
            self.red_zone = CombatZone(attack_zone, block_zone)
            self.board.render_redzone = True
            self.red_zone.setup_attack_zone()
            self.red_zone.setup_block_zone()
        self.red_zone.add_attacker(attacker)
    def reset_attackers(self):
        if self.red_zone: self.red_zone.reset_attackers()
    def declare_attackers(self):
        if self.red_zone: self.red_zone.declare_attackers()
    def select_blocker(self, sender, attacker, blocker):
        self.red_zone.set_blocker_for_attacker(attacker, blocker)
    def reset_blockers(self):
        self.red_zone.reset_blockers()
        self.red_zone.declare_attackers()  # To reset the blocking list and re layout the attackers
    def end_combat(self):
        if self.red_zone:
            self.red_zone.restore_orig_pos()
            self.board.render_redzone = False
            self.red_zone = None
    def enter_stack(self, sender, ability):
        card = ability.card
        if card == "Assign Damage":
            self.stack.add_ability(ability)
            return
        # XXX this is a hack right now because the card isn't actually placed on the stack (or it never leaves it's zone)
        zone = card.zone
        start_pos = None
        if zone in self.status_zones and not ability.card.controller ==self.player:
            pstatus, symbol = self.status_zones[zone]
            start_pos = pstatus.pos + symbol.pos
        elif zone in self.play_zones:
            zone = self.play_zones[zone]
            guicard = zone.get_card(card)
            start_pos = self.window.project_to_window(*tuple(zone.pos+guicard.pos))
        if start_pos:
            guicard = self.stack.add_ability(ability, 0.85) #1.0) #0.75)
            end_pos = self.stack.pos + guicard.pos
            self.sparks.add_spark(start_pos, end_pos, grow=True, dt=1.0, color=str(card.color))
        else: self.stack.add_ability(ability)
    def leave_stack(self, sender, ability):
        from game.Ability import CastSpell
        guicard = self.stack.get_card(ability)
        pos = self.stack.pos + guicard.pos
        if isinstance(ability, CastSpell): self.tracker[ability.card] = pos, self.stack
        elif not ability.card == "Assign Damage": self.sparks.add_sparkle_star(pos, pos, dt=1.0, color=str(ability.card.color))
        self.stack.remove_ability(ability)
    def controller_changed(self, card, original):
        start_zone = self.play_zones[original.play]
        end_zone = self.play_zones[card.controller.play]
        guicard = start_zone.get_card(card)
        start_pos = self.window.project_to_window(*tuple(start_zone.pos+guicard.pos))
        start_zone.remove_card(card, clock)
        guicard = end_zone.add_card(card,startt=2.)
        end_pos = self.window.project_to_window(*tuple(end_zone.pos+guicard.pos))
        clock.schedule_once(lambda t: self.sparks.add_spark(start_pos, end_pos, dt=1.25, color=str(card.color)), 0.75)
    def enter_zone(self, sender, card):
        if sender in self.status_zones:
            pstatus, symbol = self.status_zones[sender]
            if card in self.tracker:
                start_pos, from_zone = self.tracker[card]
                end_pos = pstatus.pos + symbol.pos
                if from_zone in self.play_zones.values():
                    self.sparks.add_spark(start_pos, start_pos, dt=1.5, color=str(card.color), grow=True)
                    clock.schedule_once(lambda t: self.sparks.add_spark(start_pos, end_pos, dt=1.25, color=str(card.color)), 1.55)
                    clock.schedule_once(lambda t: pstatus.update_zone(sender), 2.80)
                    #clock.schedule_once(lambda t: pstatus.update_cards(), 2.80)
                    clock.schedule_once(lambda t: self.sparks.add_star_spark(end_pos, end_pos, dt=.5, color=str(card.color)) , 2.70)
                else:
                    self.sparks.add_spark(start_pos, end_pos, dt=1.25, color="")
                    clock.schedule_once(lambda t: pstatus.update_zone(sender), 1.25)
                    #clock.schedule_once(lambda t: pstatus.update_cards(), 1.25)
                del self.tracker[card]
            else: pstatus.update_zone(sender)
            #else: pstatus.update_cards()
        elif sender in self.play_zones:
            if card in self.tracker:
                guicard = self.play_zones[sender].add_card(card,startt=1.0)
                zone = self.play_zones[sender]
                start_pos, from_zone = self.tracker[card]
                end_pos = self.window.project_to_window(*tuple(zone.pos+guicard.pos))
                self.sparks.add_spark(start_pos, end_pos, grow=True, dt=1.0, color=str(card.color))
                del self.tracker[card]
            else: self.play_zones[sender].add_card(card,startt=0)
    def leave_zone(self, sender, card):
        if sender in self.status_zones:
            pstatus, symbol = self.status_zones[sender]
            if pstatus.visible == 1 and not card in self.tracker: # already here because it was in the stack
                self.tracker[card] = (pstatus.pos + symbol.pos, pstatus)
            pstatus.update_zone(sender)
            #pstatus.update_cards()
        elif sender in self.play_zones:
            zone = self.play_zones[sender]
            guicard = zone.get_card(card)
            self.tracker[card] = (self.window.project_to_window(*tuple(zone.pos+guicard.pos)), zone)
            zone.remove_card(card, clock)
    def render2d(self):
        self.sparks.render2d()
    def render3d(self):
        self.sparks.render3d()
