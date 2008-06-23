__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet.gl import *
import pyglet.clock
from pyglet import event
from pyglet import window
from pyglet.window import key
import ConfigParser

import math, random
import anim
import euclid
from anim_euclid import AnimatedVector3, AnimatedQuaternion

import widget
from card_view import HandView, StackView, ZoneView
from play_view import PlayView, Table
from status_widget import StatusView, GameStatus, SelectionList, MessageDialog, ManaView, PhaseStatus
from animator import ZoneAnimator
from controllers import *
from soundfx import MediaEffects
import networkcomm, replaydump
import GUIEvent

fourfv = GLfloat*4
sixteenfv = GLfloat*16

import CardLibrary
import game
from game.pydispatch import dispatcher

class GameOverException(Exception): pass

class Camera:
    def pos():
        def fget(self): return euclid.Vector3(self._pos.x, self._pos.y, self._pos.z)
        def fset(self, val):
            self._pos.x = val.x
            self._pos.y = val.y
            self._pos.z = val.z
        return locals()
    pos = property(**pos())
    def orientation():
        def fget(self): return self._orientation.copy()
        def fset(self, val):
            self._orientation.x = val.x
            self._orientation.y = val.y
            self._orientation.z = val.z
            self._orientation.w = val.w
        return locals()
    orientation = property(**orientation())
    def __init__(self, pos):
        self._pos = AnimatedVector3(pos)
        self._orientation = AnimatedQuaternion()
        #self._pos.set_transition(dt=0.5, method="sine")
        self._orientation.set_transition(dt=0.5, method="sine")
        self.viewangle = -7*math.pi/16
        #self.viewangle = -15*math.pi/32
        #self.viewangle = -127*math.pi/256
        self._orientation.rotate_axis(self.viewangle, euclid.Vector3(1,0,0))
        self.view_switched = False
        self.vis_distance = 6.5
        self.x_limit = (-20, 20)
        self.y_limit = (8, 30)
        self.z_limit = (-20, 20)
    def setup(self):
        glLoadIdentity()
        glMultMatrixf(sixteenfv(*tuple(self.orientation.conjugated().get_matrix())))
        glTranslatef(*tuple(-1*self.pos))
    def move_by(self, delta):
        self._pos -= delta*0.1
        if self.pos.x < self.x_limit[0]: self._pos.x = self.x_limit[0]
        elif self.pos.x > self.x_limit[1]: self._pos.x = self.x_limit[1]
        if self.pos.y <= self.y_limit[0]: self._pos.y = self.y_limit[0]
        elif self.pos.y >= self.y_limit[1]: self._pos.y = self.y_limit[1]
        if self.pos.z < self.z_limit[0]: self._pos.z = self.z_limit[0]
        elif self.pos.z > self.z_limit[1]: self._pos.z = self.z_limit[1]
    def switch_viewpoint(self):
        axis = math.pi/2.+self.viewangle
        angle = math.pi
        if self.view_switched: angle = -1*math.pi
        self._orientation.rotate_axis(angle, euclid.Vector3(0,math.sin(axis),math.cos(axis)))
        self.view_switched = not self.view_switched

class GameWindow(window.Window):
    def __init__(self, *args, **kwargs):
        super(GameWindow, self).__init__(*args, **kwargs)
        self.conf = ConfigParser.ConfigParser()
        self.conf.read("incantus.ini")
        self.camera = Camera(euclid.Point3(0,15, 0)) #15,5))
        self.mainplayer_status = StatusView(pos=euclid.Vector3(0, 0, 0))
        self.otherplayer_status = StatusView(pos=euclid.Vector3(self.width, self.height, 0), is_opponent=True)
        self.mana_controller = ManaController(self.mainplayer_status.manapool, self.otherplayer_status.manapool, self)
        self.x_controller = XSelector(self.mainplayer_status.manapool, self)
        self.zone_view = ZoneView()
        self.card_selector = CardSelector(self.mainplayer_status, self.otherplayer_status, self.zone_view, self)
        self.game_status = GameStatus()
        self.phase_status = PhaseStatus()
        self.phase_controller = PhaseController(self.phase_status, self)
        self.status_controller = StatusController(self.mainplayer_status, self.otherplayer_status, self.zone_view, self.phase_status, self)
        self.selection = SelectionList()
        self.list_selector = SelectController(self.selection, self)
        self.msg_dialog = MessageDialog()
        self.msg_controller = MessageController(self.msg_dialog, self)
        self.table = Table()
        self.mainplay = PlayView(z=3)
        self.otherplay = PlayView(z=-3, is_opponent_view=True)
        self.play_controller = PlayController(self.mainplay, self.otherplay, self)
        self.damage_assignment = DamageSelector(self.mainplay, self.otherplay, self)
        self.player_hand = HandView()
        self.hand_controller = HandController(self.player_hand, self)
        self.otherplayer_hand = HandView(is_opponent=True)
        self.otherhand_controller = HandController(self.otherplayer_hand, self)
        self.stack = StackView()
        self.stack_controller = StackController(self.stack, self)
        self.fps = pyglet.clock.ClockDisplay(color=(1.0, 1.0, 1.0, 0.3))
        self.zone_animator = ZoneAnimator(self)
        self.start_new_game = False
        self._keep_priority = False
        self.finish_turn = False
        self.p1_stop_next = False
        self.p2_stop_next = False
        self.user_action = None
        self.connection = None
        self.replay = False
        self.dump_to_replay = lambda x: None
        self.soundfx = MediaEffects()

    def init(self):
        glEnable(GL_LIGHTING)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, fourfv(0.5,0.5,0.5,1.0))
        glEnable(GL_LIGHT0)
        #glLightfv(GL_LIGHT0, GL_POSITION, fourfv(20, 50, 20, 0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, fourfv(0.5, 0.5, 0.5, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, fourfv(0.8, 0.8, 0.8, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, fourfv(0.8, 0.8, 0.8, 1.0))

        #glEnable(GL_LIGHT1)
        #glLightfv(GL_LIGHT1, GL_POSITION, fourfv(0, -1, -3, 0))
        #glLightfv(GL_LIGHT1, GL_DIFFUSE, fourfv(.5, .5, .5, 1))
        #glLightfv(GL_LIGHT1, GL_SPECULAR, fourfv(1, 1, 1, 1))

        # ColorMaterial use inspired by: http://www.sjbaker.org/steve/omniv/opengl_lighting.html
        glEnable ( GL_COLOR_MATERIAL )
        glColorMaterial ( GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        glEnable(GL_BLEND)
        glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0,0,0,0)
        self.camera.setup()
        CardLibrary.CardLibrary = CardLibrary._CardLibrary()

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(80., self.width / float(self.height), 1, 100.)
        glMatrixMode(GL_MODELVIEW)
        self.mainplayer_status.resize(width, height)
        self.otherplayer_status.resize(width, height)
        self.stack.pos = euclid.Vector3(50,height-110,0)
        self.player_hand.resize(width, height, width-self.mainplayer_status.width)
        self.otherplayer_hand.resize(width, height, width-self.mainplayer_status.width)
        self.game_status.resize(width, height, self.mainplayer_status.width)
        self.phase_status.resize(width, height)

    def draw(self):
        self.clear()
        self.camera.setup()
        self.table.draw()
        glClear(GL_DEPTH_BUFFER_BIT)
        self.mainplay.render()
        self.otherplay.render()
        self.zone_animator.render3d()
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        self.draw_overlay()
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        self.flip()

    def draw_haze(self):
        fraction = 0.1
        glBegin(GL_QUADS)
        fAlpha = 1.0
        glColor4f(afBGColor[0], afBGColor[1], afBGColor[2], fAlpha)
        glVertex2f(0, 0)
        fAlpha = 0.0
        glColor4f(afBGColor[0], afBGColor[1], afBGColor[2], fAlpha)
        glVertex2f(width*fraction, 0)
        fAlpha = 0.0
        glColor4f(afBGColor[0], afBGColor[1], afBGColor[2], fAlpha)
        glVertex2f (width*fraction, height)
        fAlpha = 1.0
        glColor4f(afBGColor[0], afBGColor[1], afBGColor[2], fAlpha)
        glVertex2f(0, height)
        glEnd()
        # draw right mask
        glBegin(GL_QUADS)
        fAlpha = 0.0
        glColor4f(afBGColor[0], afBGColor[1], afBGColor[2], fAlpha)
        glVertex2f(width *(1-fraction), 0)
        fAlpha = 1.0
        glColor4f(afBGColor[0], afBGColor[1], afBGColor[2], fAlpha)
        glVertex2f(width,0)
        fAlpha = 1.0
        glColor4f(afBGColor[0], afBGColor[1], afBGColor[2], fAlpha)
        glVertex2f(width,height)
        fAlpha = 0.0
        glColor4f(afBGColor[0], afBGColor[1], afBGColor[2], fAlpha)
        glVertex2f(width *(1-fraction),height)
        glEnd()
    def draw_overlay(self):
        # draw left mask
        width, height = self.width, self.height
        afBGColor = [0.0, 0.0, 0.0, 1.0]
        self.set_2d(-50, 50)
        #glDisable(GL_TEXTURE_2D)
        #self.draw_haze()
        #glEnable(GL_TEXTURE_2D)
        self.phase_status.render()
        self.otherplayer_status.render()
        self.mainplayer_status.render()
        self.stack.render()
        self.zone_animator.render2d()
        self.game_status.render()
        self.msg_dialog.render()
        self.otherplayer_hand.render()
        self.player_hand.render()
        self.zone_view.render()
        self.selection.render()
        #self.fps.draw()
        glDisable(GL_TEXTURE_2D)
        self.unset_2d()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER:
            self.user_action = game.Action.PassPriority()
        elif symbol == key.ESCAPE:
            self.user_action = game.Action.CancelAction()
        elif symbol == key.TAB:
            self.game_status.toggle_gamelog()
        elif symbol == key.Q:
            self.has_exit=True
        elif symbol == key.D and modifiers & key.MOD_SHIFT:
            import pdb
            pdb.set_trace()
        elif symbol == key.F1:
            self.set_fullscreen(not self.fullscreen)
        elif symbol == key.F:
            self.finish_turn = True
            self.user_action = game.Action.PassPriority()
        #elif symbol == key.W:
        #    if game.Keeper.curr_player == self.player1: self.p1_stop_next = True
        #    else: self.p2_stop_next = True
        elif symbol == key.V and modifiers & key.MOD_SHIFT:
            self.camera.switch_viewpoint()
        elif not self.start_new_game:
            if symbol == key.N:
                self.status_controller.set_solitaire()
                self.otherplayer_hand.set_solitaire()
                self.action_new_game()
            elif symbol == key.F7:
                self.status_controller.set_solitaire()
                self.otherplayer_hand.set_solitaire()
                self.action_new_game(True)
            elif symbol == key.F8:
                self.status_controller.set_solitaire()
                self.otherplayer_hand.set_solitaire()
                self.action_new_game(False)
            elif symbol == key.C and modifiers & key.MOD_SHIFT: # client
                self.start_network_game(self.conf.get("network", "server"), int(self.conf.get("network", "port")), False)
            elif symbol == key.S and modifiers & key.MOD_SHIFT: #server
                self.start_network_game(self.conf.get("network", "server"), int(self.conf.get("network", "port")), True)
            elif symbol == key.F6:
                self.restart_network_game(self.conf.get("network", "server"), int(self.conf.get("network", "port")))
        elif self.start_new_game:
            if symbol == key.F2:
                #if self.hand_controller.activated: self.hand_controller.deactivate()
                self.phase_controller.activate(other=False)
            elif symbol == key.F3:
                #if self.hand_controller.activated: self.hand_controller.deactivate()
                self.phase_controller.activate(other=True)
        else:
            return event.EVENT_UNHANDLED

    def set_2d(self, near, far):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, near, far)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def unset_2d(self):
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def selection_ray(self, x, y):
        self.camera.setup()
        model_view = (GLdouble * 16)()
        glGetDoublev(GL_MODELVIEW_MATRIX, model_view)
        projection = (GLdouble * 16)()
        glGetDoublev(GL_PROJECTION_MATRIX, projection)
        viewport = (GLint * 4)()
        glGetIntegerv(GL_VIEWPORT, viewport)

        x1, y1, z1 = GLdouble(), GLdouble(), GLdouble()
        x2, y2, z2 = GLdouble(), GLdouble(), GLdouble()
        gluUnProject(x, y, 0, model_view, projection, viewport, x1, y1, z1)
        gluUnProject(x, y, 1, model_view, projection, viewport, x2, y2, z2)
        ray = euclid.Ray3(euclid.Point3(x1.value, y1.value, z1.value),
                          euclid.Point3(x2.value, y2.value, z2.value))
        ray.v.normalize()
        return ray

    def project_to_window(self, x,y,z):
        self.camera.setup()
        model_view = (GLdouble * 16)()
        glGetDoublev(GL_MODELVIEW_MATRIX, model_view)
        projection = (GLdouble * 16)()
        glGetDoublev(GL_PROJECTION_MATRIX, projection)
        viewport = (GLint * 4)()
        glGetIntegerv(GL_VIEWPORT, viewport)

        x1, y1, z1 = GLdouble(), GLdouble(), GLdouble()
        gluProject(x, y, z, model_view, projection, viewport, x1, y1, z1)
        return euclid.Vector3(x1.value, y1.value, z1.value)

    def clear_game(self):
        self.phase_status.clear()
        self.game_status.clear()
        self.stack.clear()
        self.mainplay.clear()
        self.otherplay.clear()
        self.player_hand.clear()
        self.otherplayer_hand.clear()
        self.mainplayer_status.clear()
        self.otherplayer_status.clear()
        self.game_status.log("Press 'n' to start a solitaire game")

    def start_network_game(self, ipaddr, port, isserver):
        self.game_status.log("Starting network game")
        
        playername = self.conf.get("main", "playername")
        player1 = game.Player(playername)
        if isserver:
            self.game_status.log("Waiting for client")
            self.connection = networkcomm.Server(ipaddr, port)
            # exchange random seeds to synchronize RNG
            self.game_status.log("Connection received")
            seed = pyglet.clock.time.time()
            self.connection.send(seed)
            self.connection.send(playername)
            # Get the name of the other player
            otherplayername = self.connection.receive()
        else:
            self.game_status.log("Connecting to server at %s, %d"%(ipaddr, port))
            self.connection = networkcomm.Client(ipaddr, port)
            self.game_status.log("Connected to server")
            seed = self.connection.receive()
            # Get the name of the other player
            otherplayername = self.connection.receive()
            self.connection.send(playername)

        self.game_status.log("Exchanging data with other player")
        player2 = game.Player(otherplayername)
        self.player1 = player1
        self.player2 = player2

        # These need to be set here so that abilities can target the opponent
        player1.setOpponent(player2)
        player2.setOpponent(player1)

        # Choose starting player
        random.seed(seed)
        coin = random.randint(0,1)
        #if coin == 0: msg = "%s won the coin toss"%player1.name
        #else: msg = "%s won the coin toss"%player2.name
        #self.game_status.log(msg)
        #self.msg_controller.notify(msg, action=False)

        # Load decks - Make sure these are loaded in the same order for client and server
        my_deck = self.read_deckfile(self.conf.get("main", "deckfile"))
        if isserver:
            self.connection.send(my_deck)
            other_deck = self.connection.receive()
            player1.setDeck(my_deck)
            player2.setDeck(other_deck)
            if coin == 0: first_player, second_player = player1, player2
            else: first_player, second_player = player2, player1
        else:
            other_deck = self.connection.receive()
            self.connection.send(my_deck)
            player1.setDeck(my_deck)
            player2.setDeck(other_deck)
            if coin == 0: first_player, second_player = player2, player1
            else: first_player, second_player = player1, player2

        self.make_connections((0,0,255), (255,255,0), soundfx=True)
        game.Keeper.init(first_player, second_player)

        # Save info for replay
        self.replay = False
        replay_file = self.conf.get("main", "replayfile")
        self.dump_to_replay = replaydump.ReplayDump(self, replay_file, True)
        self.dump_to_replay(isserver)
        self.dump_to_replay(seed)
        # From the perspective of the replay file, the first player is saved first
        #self.dump_to_replay(first_player.name)
        #if player1 == first_player: self.dump_to_replay(my_deck)
        #else: self.dump_to_replay(other_deck)
        #self.dump_to_replay(second_player.name)
        #if player1 == second_player: self.dump_to_replay(my_deck)
        #else: self.dump_to_replay(other_deck)
        self.dump_to_replay(player1.name)
        self.dump_to_replay(my_deck)
        self.dump_to_replay(player2.name)
        self.dump_to_replay(other_deck)
        self.dump_to_replay(first_player.name)

        # XXX This is hacky - need to change it
        replaydump.players = dict([(player.name,player) for player in [player1, player2]])
        replaydump.stack = game.Keeper.stack
        player1.dirty_input = self.userinput
        player2.dirty_input = self.userinput_network_other

        self.start_new_game = True

    def restart_network_game(self, ipaddr, port):
        self.game_status.log("Restarting network game")

        self.replay = self.replay_fast = True
        replay_file = self.conf.get("main", "replayfile")

        self.dump_to_replay = replaydump.ReplayDump(self, replay_file, False, prompt_continue=False)

        isserver = self.dump_to_replay.read()
        seed = self.dump_to_replay.read()
        playername = self.dump_to_replay.read()
        my_deck = self.dump_to_replay.read()
        otherplayername = self.dump_to_replay.read()
        other_deck = self.dump_to_replay.read()

        if isserver:
            self.game_status.log("Waiting for client")
            self.connection = networkcomm.Server(ipaddr, port)
            # exchange random seeds to synchronize RNG
            self.game_status.log("Connection received")
        else:
            self.game_status.log("Connecting to server at %s, %d"%(ipaddr, port))
            self.connection = networkcomm.Client(ipaddr, port)
            self.game_status.log("Connected to server")

        player1 = game.Player(playername)
        player2 = game.Player(otherplayername)
        self.player1 = player1
        self.player2 = player2
        player1.setDeck(my_deck)
        player2.setDeck(other_deck)

        # These need to be set here so that abilities can target the opponent
        player1.setOpponent(player2)
        player2.setOpponent(player1)

        # Choose starting player
        random.seed(seed)
        coin = random.randint(0,1)
        name = self.dump_to_replay.read()
        if name == player1.name: first_player, second_player = player1, player2
        else: first_player, second_player = player2, player1

        self.make_connections((0,0,255), (255,255,0), soundfx=False)
        game.Keeper.init(first_player, second_player)


        # XXX This is hacky - need to change it
        replaydump.players = dict([(player.name,player) for player in [player1, player2]])
        replaydump.stack = game.Keeper.stack
        player1.dirty_input = self.userinput
        player2.dirty_input = self.userinput_network_other

        self.start_new_game = True

    def action_new_game(self, replay=None):
        if replay == None:
            self.replay = self.replay_fast = False
            self.game_status.log("Starting new game")
        else:
            self.game_status.log("Reloading game")
            self.replay = True
            self.replay_fast = replay
        replay_file = self.conf.get("main", "replayfile")
        self.dump_to_replay = replaydump.ReplayDump(self, replay_file, not self.replay)

        if not self.replay:
            seed = pyglet.clock.time.time()
            player1_name = self.conf.get("main", "playername")
            player2_name = self.conf.get("solitaire", "playername")
            my_deck = self.read_deckfile(self.conf.get("main", "deckfile"))
            other_deck = self.read_deckfile(self.conf.get("solitaire", "deckfile"))
            self.dump_to_replay(True)
            self.dump_to_replay(seed)
            self.dump_to_replay(player1_name)
            self.dump_to_replay(my_deck)
            self.dump_to_replay(player2_name)
            self.dump_to_replay(other_deck)
        else:
            isserver = self.dump_to_replay.read()
            seed = self.dump_to_replay.read()
            player1_name = self.dump_to_replay.read()
            my_deck = self.dump_to_replay.read()
            player2_name = self.dump_to_replay.read()
            other_deck = self.dump_to_replay.read()

        player1 = game.Player(player1_name)
        player2 = game.Player(player2_name)

        self.player1 = player1
        self.player2 = player2

        # These need to be set here so that abilities can target the opponent
        player1.setOpponent(player2)
        player2.setOpponent(player1)

        player1.setDeck(my_deck)
        player2.setDeck(other_deck)

        # Choose starting player
        random.seed(seed)
        coin = random.randint(0,1)
        if not self.replay:
            if coin == 0: first_player, second_player = player1, player2
            else: first_player, second_player = player2, player1
            self.dump_to_replay(first_player.name)
        else:
            name = self.dump_to_replay.read()
            if name == player1.name: first_player, second_player = player1, player2
            else: first_player, second_player = player2, player1

        self.make_connections((0,0,255), (255,255,0), soundfx=not self.replay_fast)
        game.Keeper.init(first_player, second_player)

        if self.conf.get("solitaire", "manaburn") == "No":
            game.Keeper.manaBurn = lambda: None

        # This is hacky
        replaydump.players = dict([(player.name,player) for player in [player1, player2]])
        replaydump.stack = game.Keeper.stack
        player1.dirty_input = self.userinput
        player2.dirty_input = self.userinput
        self.start_new_game = True

    def make_connections(self, self_color, other_color, soundfx):
        dispatcher.reset()
        self.mainplayer_status.setup_player(self.player1, self_color)
        self.otherplayer_status.setup_player(self.player2, other_color)
        self.hand_controller.set_zone(self.player1.hand)
        self.otherhand_controller.set_zone(self.player2.hand)
        self.stack_controller.set_zone(game.Keeper.stack)
        self.play_controller.set_zones(self.player1.play, self.player2.play)
        #self.game_status.setup_player_colors(self.player1, self_color, other_color)
        self.phase_status.setup_player_colors(self.player1, self_color, other_color)
        self.zone_animator.setup(self.mainplayer_status, self.otherplayer_status, self.stack, self.mainplay,self.otherplay,self.table)

        dispatcher.connect(self.stack.finalize_announcement, signal=game.GameEvent.AbilityPlacedOnStack())
        dispatcher.connect(self.stack.remove_ability, signal=game.GameEvent.AbilityCanceled())
        dispatcher.connect(self.player_hand.card_off_stack, signal=game.GameEvent.AbilityCanceled())
        dispatcher.connect(self.otherplayer_hand.card_off_stack, signal=game.GameEvent.AbilityCanceled())

        dispatcher.connect(self.player_hand.add_card, signal=game.GameEvent.CardEnteredZone(), sender=self.player1.hand, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.player_hand.remove_card, signal=game.GameEvent.CardLeftZone(), sender=self.player1.hand, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.player_hand.remove_card, signal=game.GameEvent.CardCeasesToExist(), sender=self.player1.hand, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.player_hand.card_on_stack, signal=game.GameEvent.AbilityAnnounced())

        dispatcher.connect(self.otherplayer_hand.add_card, signal=game.GameEvent.CardEnteredZone(), sender=self.player2.hand, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_hand.remove_card, signal=game.GameEvent.CardLeftZone(), sender=self.player2.hand, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_hand.remove_card, signal=game.GameEvent.CardCeasesToExist(), sender=self.player2.hand, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_hand.card_on_stack, signal=game.GameEvent.AbilityAnnounced(), priority=dispatcher.UI_PRIORITY)

        dispatcher.connect(self.mainplayer_status.animate_life, signal=game.GameEvent.LifeChangedEvent(),sender=self.player1, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.animate_life, signal=game.GameEvent.LifeChangedEvent(),sender=self.player2, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplayer_status.manapool.update_mana, signal=game.GameEvent.ManaAdded(), sender=self.player1.manapool, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplayer_status.manapool.update_mana, signal=game.GameEvent.ManaSpent(), sender=self.player1.manapool, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplayer_status.manapool.clear_mana, signal=game.GameEvent.ManaCleared(), sender=self.player1.manapool, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.manapool.update_mana, signal=game.GameEvent.ManaAdded(), sender=self.player2.manapool, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.manapool.update_mana, signal=game.GameEvent.ManaSpent(), sender=self.player2.manapool, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.manapool.clear_mana, signal=game.GameEvent.ManaCleared(), sender=self.player2.manapool, priority=dispatcher.UI_PRIORITY)

        dispatcher.connect(self.phase_status.new_turn, signal=game.GameEvent.NewTurnEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.phase_status.set_phase, signal=game.GameEvent.GameStepEvent(), priority=dispatcher.UI_PRIORITY)
        #dispatcher.connect(self.phase_status.pass_priority, signal=game.GameEvent.HasPriorityEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.phase_status.change_focus, signal=game.GameEvent.GameFocusEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.game_status.log_event, signal=game.GameEvent.LogEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplayer_status.new_turn, signal=game.GameEvent.NewTurnEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.new_turn, signal=game.GameEvent.NewTurnEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplayer_status.pass_priority, signal=game.GameEvent.HasPriorityEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.pass_priority, signal=game.GameEvent.HasPriorityEvent(), priority=dispatcher.UI_PRIORITY)

        dispatcher.connect(self.mainplay.card_tapped, signal=game.GameEvent.CardTapped(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplay.card_tapped, signal=game.GameEvent.CardTapped(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplay.card_untapped, signal=game.GameEvent.CardUntapped(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplay.card_untapped, signal=game.GameEvent.CardUntapped(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplay.card_attached, signal=game.GameEvent.AttachedEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplay.card_attached, signal=game.GameEvent.AttachedEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplay.card_unattached, signal=game.GameEvent.UnAttachedEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplay.card_unattached, signal=game.GameEvent.UnAttachedEvent(), priority=dispatcher.UI_PRIORITY)

        dispatcher.connect(self.priority_stop, signal=game.GameEvent.HasPriorityEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.phase_stop, signal=game.GameEvent.GameStepEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.play_ability, signal=game.GameEvent.PlayAbilityEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.new_turn, signal=game.GameEvent.NewTurnEvent(), priority=dispatcher.UI_PRIORITY)
        self.set_stops()

        if soundfx: self.soundfx.connect()
        self.play_controller.activate()
        self.status_controller.activate()
        self.hand_controller.activate()
        self.otherhand_controller.activate()
        self.stack_controller.activate()
        self.mainplayer_status.show()
        self.otherplayer_status.show()

    def set_stops(self):
        self.my_turn_stops = set([state for state, val in self.conf.items("my stops") if val == "No"])
        self.opponent_turn_stops = set([state for state, val in self.conf.items("opponent stops") if val == "No"])
    def keep_priority(self): self._keep_priority = True
    def priority_stop(self, player):
        if game.Keeper.stack.empty():
            if (not self.p1_stop_next and
               ((player == game.Keeper.other_player and self.state in self.opponent_turn_stops) or 
               (player == game.Keeper.curr_player and self.state in self.my_turn_stops))):
                self.user_action = game.Action.PassPriority()
            elif self.finish_turn: #player == game.Keeper.curr_player and self.finish_turn:
                self.user_action = game.Action.PassPriority()
            elif (player == self.player1): dispatcher.send(GUIEvent.MyPriority())
        else:
            if (player == self.player1): dispatcher.send(GUIEvent.MyPriority())
            else: dispatcher.send(GUIEvent.OpponentPriority())
    def new_turn(self, player):
        self.finish_turn = False
    def phase_stop(self, state):
        self.state = state.lower()
    def play_ability(self, ability):
        if not self._keep_priority and ability.needs_stack():
            self.user_action = game.Action.PassPriority()
        else:
            # Keep priority after playing card
            self._keep_priority = False

    def read_deckfile(self, filename):
        deckfile = [l.strip().split() for l in file(filename, "rU").readlines() if not (l[0] == "#" or l[:2] == "//")]
        decklist = [(l[0], " ".join(l[1:])) for l in deckfile if l and l[0] != "SB:"]
        self.game_status.log("Retrieving card images from web")
        CardLibrary.CardLibrary.retrieveCardImages([c[1] for c in decklist])
        return decklist

    def on_close(self):
        del self.dump_to_replay
        del self.connection
        return super(GameWindow, self).on_close()

    def run(self):
        self.clock = pyglet.clock.get_default()
        self.clock.schedule(anim.add_time)
        self.clock.set_fps_limit(15)
        self.clear_game()
        while not self.has_exit:
            self.soundfx.dispatch_events()
            self.dispatch_events()
            self.clock.tick()
            self.draw()
            if self.start_new_game:
                msg = game.Keeper.run()
                self.msg_controller.notify(msg, action=False)
                self.start_new_game = False
                self.clear_game()

        CardLibrary.CardLibrary.close()

    def userinput_network_other(self, context, prompt=''):
        #self.game_status.log(prompt)
        self.game_status.log("Waiting for %s"%self.player2.name)
        networkevent = False

        if self.replay and self.replay_fast:
            result = self.dump_to_replay.read()
            if not result == False: return result
            else: self.soundfx.connect()

        while not (self.has_exit or networkevent):
            self.soundfx.dispatch_events()
            self.dispatch_events()
            self.clock.tick()
            self.draw()
            # Poll other network player for action
            if self.connection.poll_other():
                result = self.connection.receive()
                networkevent = True
            self.user_action = None

        if self.has_exit: raise GameOverException()
        if not self.replay: self.dump_to_replay(result)
        return result

    def userinput(self, context, prompt=''):
        self.game_status.log(prompt)
        userevent = False
        if self.replay and self.replay_fast:
            result = self.dump_to_replay.read()
            if result is not False: return result
            else: self.soundfx.connect()

        process = context['process']
        if self.replay: pass
        elif context.get("get_ability", False): pass
        elif context.get("get_target", False): pass
        elif context.get("get_cards", False):
            sellist = context['list']
            numselections = context['numselections']
            required = context['required']
            from_zone = context['from_zone']
            from_player = context['from_player']
            check_card = context['check_card']
            #if self.hand_controller.activated: self.hand_controller.deactivate()
            self.card_selector.activate(sellist, from_zone, numselections, required=required, is_opponent=(from_player != self.player1), filter=check_card)
        elif context.get("get_selection", False):
            sellist = context['list']
            numselections = context['numselections']
            required = context['required']
            msg = context['msg']
            #if self.hand_controller.activated: self.hand_controller.deactivate()
            self.list_selector.build(sellist,required,numselections,msg)
        elif context.get("get_choice", False):
            msg = context['msg']
            notify = context['notify']
            #if self.hand_controller.activated: self.hand_controller.deactivate()
            if notify: self.msg_controller.notify(msg)
            else: self.msg_controller.ask(msg)
        elif context.get("get_mana_choice", False):
            required = context['required']
            manapool = context['manapool']
            #if self.hand_controller.activated: self.hand_controller.deactivate()
            self.mana_controller.request_mana(required, manapool)
        elif context.get("get_X", False):
            #if self.hand_controller.activated: self.hand_controller.deactivate()
            self.x_controller.request_x()
        elif context.get("get_damage_assign", False):
            blocking_list = context['blocking_list']
            trample = context['trample']
            #if self.hand_controller.activated: self.hand_controller.deactivate()
            self.damage_assignment.activate(blocking_list, trample)
        elif context.get("reveal_card", False):
            #msgs = context['msgs']
            sellist = context['cards']
            #if self.hand_controller.activated: self.hand_controller.deactivate()
            self.card_selector.activate(sellist, '', 0, required=False)

        while not (self.has_exit or userevent):
            self.soundfx.dispatch_events()
            self.dispatch_events()
            self.clock.tick()
            self.draw()
            if self.user_action:
                if self.replay: result = self.dump_to_replay.read()
                else: result = process(self.user_action)
                self.user_action = None
                if result is not False: userevent = True

        if self.has_exit: raise GameOverException()

        if self.connection: self.connection.send(result)
        if not self.replay: self.dump_to_replay(result)
        return result

def main():
    width = 1024
    height = 768
    configs = [
        Config(double_buffer=True, depth_size=24,
               sample_buffers=1, samples=4),
        Config(double_buffer=True, depth_size=24,
               sample_buffers=1, samples=2),
        Config(double_buffer=True, depth_size=24),
        Config(double_buffer=True, depth_size=16),
    ]
    widget.ImageCache.load_images()
    for config in configs:
        try:
            win = GameWindow(width=width, height=height, config=config, resizable=True, caption='Incantus')
            break
        except window.NoSuchConfigException:
            pass
    #win.set_fullscreen()
    win.init()
    win.set_icon(pyglet.image.load("./data/Incantus.png"))
    try:
        win.run()
    except GameOverException:
        pass

if __name__ == '__main__':
    main()
