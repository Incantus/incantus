__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from greenlet import greenlet
from cStringIO import StringIO

import pyglet
from pyglet.gl import *
from pyglet import event
from pyglet.window import key
import colors

from cocos.director import director
from cocos.layer import Layer
from cocos.scene import Scene
from cocos.scenes.transitions import *

import random
import euclid
import soundfx

from Camera import Camera
from card_view import HandView, StackView
from play_view import PlayView, Table
from status_widget import StatusView, GameStatus, SelectionList, MessageDialog, ManaView, PhaseStatus, PhaseBar
from animator import ZoneAnimator
from controllers import *
import GUIEvent

fourfv = GLfloat*4

from engine.Player import Player as GamePlayer
from engine.GameKeeper import Keeper
from engine.pydispatch import dispatcher
import engine.Action
import engine.GameEvent

from network import replaydump
#from chatbox import ChatBox


class IncantusLayer(Layer):
    is_event_handler = True
    def __init__(self):
        super(IncantusLayer, self).__init__()
        self.width, self.height = director.window.width, director.window.height
        self.network = False
        self.pending_actions = []
        self.init()
        self.clear_game()
        self.soundfx = soundfx.SoundEffects()

    def init(self):
        self.camera = Camera(euclid.Point3(0,15, 0))
        self.mainplayer_status = StatusView()
        self.otherplayer_status = StatusView(is_opponent=True)
        self.mana_controller = ManaController(self.mainplayer_status.manapool, self.otherplayer_status.manapool, self)
        self.x_controller = XSelector(self.mainplayer_status.manapool, self.otherplayer_status.manapool, self)
        self.card_selector = CardSelector(self.mainplayer_status, self.otherplayer_status, self)
        #self.game_status = GameStatus()
        self.phase_status = PhaseStatus()
        self.phase_bar = PhaseBar()
        self.phase_controller = PhaseController(self.phase_status, self)
        self.status_controller = StatusController(self.mainplayer_status, self.otherplayer_status, self.phase_status, self)
        self.selection = SelectionList()
        self.list_selector = SelectController(self.selection, self)
        self.msg_dialog = MessageDialog()
        self.msg_controller = MessageController(self.msg_dialog, self)
        self.table = Table()
        self.mainplay = PlayView(z=3)
        self.otherplay = PlayView(z=-3, is_opponent_view=True)
        self.play_controller = PlayController(self.mainplay, self.otherplay, self)
        self.damage_assignment = DamageSelector(self.mainplay, self.otherplay, self)
        self.distribution_assignment = DistributionSelector(self.mainplay, self.otherplay, self)
        self.player_hand = HandView()
        self.hand_controller = HandController(self.player_hand, self)
        self.otherplayer_hand = HandView(is_opponent=True)
        self.otherhand_controller = HandController(self.otherplayer_hand, self)
        self.stack = StackView()
        self.stack_controller = StackController(self.stack, self)
        self.zone_animator = ZoneAnimator(self)
        self._keep_priority = False
        self.finish_turn = False
        self.p1_stop_next = False
        self.p2_stop_next = False

    def setup_lighting(self):
        glEnable(GL_LIGHTING)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, fourfv(0.5,0.5,0.5,1.0))
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, fourfv(0.5, 0.5, 0.5, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, fourfv(0.8, 0.8, 0.8, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, fourfv(0.8, 0.8, 0.8, 1.0))

        # ColorMaterial use inspired by: http://www.sjbaker.org/steve/omniv/opengl_lighting.html
        glEnable ( GL_COLOR_MATERIAL )
        glColorMaterial ( GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    def on_enter(self):
        super(IncantusLayer, self).on_enter()
        self.on_resize(self.width, self.height)
        self.setup_lighting()
        self.play_controller.activate()
        self.status_controller.activate()
        self.hand_controller.activate()
        self.otherhand_controller.activate()
        self.stack_controller.activate()
        self.mainplayer_status.show()
        self.otherplayer_status.show()

    def on_exit(self):
        super(IncantusLayer, self).on_exit()
        glDisable(GL_LIGHTING)
        self.play_controller.deactivate()
        self.status_controller.deactivate()
        self.hand_controller.deactivate()
        self.otherhand_controller.deactivate()
        self.stack_controller.deactivate()
        self.mainplayer_status.hide()
        self.otherplayer_status.hide()

    def on_resize(self, width, height):
        self.width, self.height = width, height
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(80., width/float(height), 0.1, 3000.)
        glMatrixMode(GL_MODELVIEW)
        
        offset = 5
        self.phase_bar.pos = euclid.Vector3(offset+self.phase_bar.width/2,offset+self.phase_bar.height/2, 0)
        self.msg_dialog.pos = euclid.Vector3(offset+self.msg_dialog.width/2, 2*offset+self.phase_bar.height+self.msg_dialog.height/2,0)
        self.mainplayer_status.pos = euclid.Vector3(offset, 3*offset+self.phase_bar.height+self.msg_dialog.height, 0)
        self.mainplayer_status.resize(width, height)
        self.otherplayer_status.pos = euclid.Vector3(offset, height-self.otherplayer_status.height-offset, 0)
        self.otherplayer_status.resize(width, height)
        self.stack.pos = euclid.Vector3(150,height/2,0)
        self.player_hand.resize(width, height, width-self.msg_dialog.width)
        self.otherplayer_hand.resize(width, height, width-self.otherplayer_status.width)
        #self.game_status.resize(width, height, self.mainplayer_status.width)
        self.phase_status.resize(width, height)
        self.selection.pos = euclid.Vector3(width/2., height/2., 0)

    def draw(self):
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_FALSE)
        self.camera.setup()
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        self.table.draw()
        glClear(GL_DEPTH_BUFFER_BIT)
        self.mainplay.render()
        self.otherplay.render()
        self.zone_animator.render3d()
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        self.draw_overlay()
        self.camera.reset()
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

    def draw_overlay(self):
        # draw left mask
        self.set_2d(-50, 50)
        self.phase_status.render()
        self.phase_bar.render()
        self.otherplayer_hand.render()
        self.player_hand.render()
        self.stack.render()
        self.otherplayer_status.render()
        self.mainplayer_status.render()
        #self.game_status.render()
        self.zone_animator.render2d()
        self.msg_dialog.render()
        self.selection.render()
        #glDisable(GL_TEXTURE_2D)
        self.unset_2d()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER:
            self.process_action(engine.Action.PassPriority())
        elif symbol == key.ESCAPE:
            self.process_action(engine.Action.CancelAction())
        #elif symbol == key.L and modifiers & key.MOD_SHIFT:
        #    self.game_status.toggle_gamelog()
        elif symbol == key.D and modifiers & key.MOD_SHIFT:
            import pdb
            pdb.set_trace()
        elif symbol == key.V and modifiers & key.MOD_SHIFT:
            self.camera.switch_viewpoint()
        elif symbol == key.F:
            self.finish_turn = True
            self.process_action(engine.Action.PassPriority())
        elif symbol == key.F1:
            show_ingame_menu(self)
        elif symbol == key.F2:
            self.phase_controller.activate(other=False)
        elif symbol == key.F3:
            self.phase_controller.activate(other=True)
        elif symbol == key.Q:
            self.soundfx.disconnect()
            quit()
        elif symbol == key.F7:
            pyglet.image.get_buffer_manager().get_color_buffer().save('screenshot.png')
        else:
            return event.EVENT_UNHANDLED
        return True

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

    def clear_game(self):
        dispatcher.reset()
        self.phase_status.clear()
        #self.game_status.clear()
        self.stack.clear()
        self.mainplay.clear()
        self.otherplay.clear()
        self.player_hand.clear()
        self.otherplayer_hand.clear()
        self.mainplayer_status.clear()
        self.otherplayer_status.clear()
    def make_connections(self, player1_info, player2_info):
        player1, self_color, self_avatar_data = player1_info
        player2, other_color, other_avatar_data = player2_info
        self_avatar = pyglet.image.load('avatar.png', StringIO(self_avatar_data))
        other_avatar = pyglet.image.load('avatar.png', StringIO(other_avatar_data))
        if not self_color: self_color = colors.compute_color_from_image(self_avatar)
        if not other_color: other_color = colors.compute_color_from_image(other_avatar)
        self.player1 = player1
        self.player2 = player2
        self.mainplayer_status.setup_player(player1, self_color, self_avatar)
        self.otherplayer_status.setup_player(player2, other_color, other_avatar)
        self.phase_status.setup_player_colors(player1, self_color, other_color)
        self.player_hand.setup_player(self_color)
        self.otherplayer_hand.setup_player(other_color)
        self.zone_animator.setup(self.mainplayer_status, self.otherplayer_status, self.stack, self.mainplay,self.otherplay,self.table)

        dispatcher.connect(self.stack.finalize_announcement, signal=engine.GameEvent.AbilityPlacedOnStack())
        dispatcher.connect(self.stack.remove_ability, signal=engine.GameEvent.AbilityCanceled())

        dispatcher.connect(self.player_hand.add_card, signal=engine.GameEvent.CardEnteredZone(), sender=player1.hand, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.player_hand.remove_card, signal=engine.GameEvent.CardLeftZone(), sender=player1.hand, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.player_hand.remove_card, signal=engine.GameEvent.CardCeasesToExist(), sender=player1.hand, priority=dispatcher.UI_PRIORITY)

        dispatcher.connect(self.otherplayer_hand.add_card, signal=engine.GameEvent.CardEnteredZone(), sender=player2.hand, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_hand.remove_card, signal=engine.GameEvent.CardLeftZone(), sender=player2.hand, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_hand.remove_card, signal=engine.GameEvent.CardCeasesToExist(), sender=player2.hand, priority=dispatcher.UI_PRIORITY)

        dispatcher.connect(self.mainplayer_status.animate_life, signal=engine.GameEvent.LifeGainedEvent(),sender=player1, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.animate_life, signal=engine.GameEvent.LifeGainedEvent(),sender=player2, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplayer_status.animate_life, signal=engine.GameEvent.LifeLostEvent(),sender=player1, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.animate_life, signal=engine.GameEvent.LifeLostEvent(),sender=player2, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplayer_status.manapool.update_mana, signal=engine.GameEvent.ManaAdded(), sender=player1.manapool, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplayer_status.manapool.update_mana, signal=engine.GameEvent.ManaSpent(), sender=player1.manapool, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplayer_status.manapool.clear_mana, signal=engine.GameEvent.ManaCleared(), sender=player1.manapool, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.manapool.update_mana, signal=engine.GameEvent.ManaAdded(), sender=player2.manapool, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.manapool.update_mana, signal=engine.GameEvent.ManaSpent(), sender=player2.manapool, priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.manapool.clear_mana, signal=engine.GameEvent.ManaCleared(), sender=player2.manapool, priority=dispatcher.UI_PRIORITY)

        dispatcher.connect(self.phase_bar.new_turn, signal=engine.GameEvent.NewTurnEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.phase_bar.set_phase, signal=engine.GameEvent.GameStepEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.phase_status.new_turn, signal=engine.GameEvent.NewTurnEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.phase_status.set_phase, signal=engine.GameEvent.GameStepEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.phase_status.change_focus, signal=engine.GameEvent.GameFocusEvent(), priority=dispatcher.UI_PRIORITY)
        #dispatcher.connect(self.game_status.log_event, signal=engine.GameEvent.LogEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplayer_status.new_turn, signal=engine.GameEvent.NewTurnEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.new_turn, signal=engine.GameEvent.NewTurnEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplayer_status.pass_priority, signal=engine.GameEvent.HasPriorityEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplayer_status.pass_priority, signal=engine.GameEvent.HasPriorityEvent(), priority=dispatcher.UI_PRIORITY)

        dispatcher.connect(self.mainplay.card_tapped, signal=engine.GameEvent.CardTapped(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplay.card_tapped, signal=engine.GameEvent.CardTapped(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplay.card_untapped, signal=engine.GameEvent.CardUntapped(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplay.card_untapped, signal=engine.GameEvent.CardUntapped(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplay.card_attached, signal=engine.GameEvent.AttachedEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplay.card_attached, signal=engine.GameEvent.AttachedEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.mainplay.card_unattached, signal=engine.GameEvent.UnAttachedEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.otherplay.card_unattached, signal=engine.GameEvent.UnAttachedEvent(), priority=dispatcher.UI_PRIORITY)


        dispatcher.connect(self.priority_stop, signal=engine.GameEvent.HasPriorityEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.play_ability, signal=engine.GameEvent.AbilityPlayedEvent(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.new_turn, signal=engine.GameEvent.NewTurnEvent(), priority=dispatcher.UI_PRIORITY)
        self.soundfx.connect()

    def new_turn(self, player): self.finish_turn = False
    def keep_priority(self): self._keep_priority = True
    def priority_stop(self, player):
        # XXX This and the play_ability function won't work until i can properly put events
        # onto the event queue
        if Keeper.stack.empty():
            if (not self.p1_stop_next and
               ((player != Keeper.active_player and self.phase_status.check_opponent_stop()) or
                (player == Keeper.active_player and self.phase_status.check_my_stop()))):
                self.pending_actions.append(engine.Action.PassPriority())
            elif self.finish_turn:
                self.pending_actions.append(engine.Action.PassPriority())
                return
        if (player == self.player1):
            #self.player_hand.set_hidden(False)
            #self.otherplayer_hand.set_hidden(True)
            dispatcher.send(GUIEvent.MyPriority())
        else:
            #self.player_hand.set_hidden(True)
            #self.otherplayer_hand.set_hidden(False)
            dispatcher.send(GUIEvent.OpponentPriority())
    def play_ability(self, ability):
        if not self._keep_priority and not hasattr(ability, "mana_ability"): self.pending_actions.append(engine.Action.PassPriority())
        # Keep priority after playing card
        else: self._keep_priority = False

    def network_input(self, context, prompt=''):
        #self.game_status.log("Waiting for %s"%prompt.split(":")[0])
        self.msg_controller.prompt("Waiting for %s"%prompt.split(":")[0])
        self.pending_actions = []   # this is necessary to clear any extra actions
        self.network = True
        result = False
        if context.get("reveal_card", False) and context["all"]:
            self.card_selector.activate(context['cards'], context['from_zone'], 0, required=False, is_opponent=(context['from_player'] != self.player1), actionable=False)
        g_self = greenlet.getcurrent()
        result = g_self.parent.switch()
        self.network = False
        return result

    def replay_input(self, context, prompt=''):
        #self.game_status.log(prompt)
        self.msg_controller.prompt(prompt)
        process = context['process']
        try:
            result = self.dump_to_replay.read()
        except replaydump.ReplayFinishedException:
            # Switch the input to the greenlet_input
	    self.soundfx.connect()
            self.player1.dirty_input = self.greenlet_input
            self.player2.dirty_input = self.greenlet_input
            result = self.greenlet_input(context, prompt)
        return result

    def greenlet_input(self, context, prompt=''):
        #self.game_status.log(prompt)
        self.msg_controller.prompt(prompt)
        process = context['process']
        result = False
        if self.pending_actions:
            result = process(self.pending_actions.pop())
            self.pending_actions = []
        while result is False:
            self.do_action(context)
            g_self = greenlet.getcurrent()
            result = process(g_self.parent.switch())
        self.dump_to_replay.write(result)
        if self.client: self.client.send_action(result)
        return result

    def switch_to_rules_engine(self, action=None):
        try:
            self.rules_engine.switch(action)
        except engine.GameEvent.GameOverException:
            self.soundfx.disconnect()
            # Game over
            quit()

    def process_action(self, action):
        if not self.network:
            #this is like pushing an event onto the pyglet loop
            pyglet.clock.schedule_once(lambda dt: self.switch_to_rules_engine(action), 0.0001)

    def start_rules_engine(self):
        self.rules_engine = greenlet(Keeper.start)
        pyglet.clock.schedule_once(lambda dt: self.rules_engine.switch(), 0.001)

    def do_action(self, context):
        #if context.get("get_ability", False): pass
        #elif context.get("get_target", False): pass
        if context.get("get_cards", False):
            sellist = context['list']
            numselections = context['numselections']
            required = context['required']
            from_zone = context['from_zone']
            from_player = context['from_player']
            check_card = context['check_card']
            self.card_selector.activate(sellist, from_zone, numselections, required=required, is_opponent=(from_player != self.player1), filter=check_card)
        elif context.get("reveal_card", False):
            sellist = context['cards']
            from_zone = context['from_zone']
            from_player = context['from_player']
            self.card_selector.activate(sellist, from_zone, 0, required=False, is_opponent=(from_player != self.player1))
        elif context.get("get_selection", False):
            sellist = context['list']
            numselections = context['numselections']
            required = context['required']
            msg = context['msg']
            self.list_selector.build(sellist,required,numselections,msg)
        elif context.get("get_choice", False):
            msg = context['msg']
            notify = context['notify']
            options = context['options']
            if notify: self.msg_controller.notify(msg, options)
            else: self.msg_controller.ask(msg, options)
        elif context.get("get_mana_choice", False):
            required = context['required']
            manapool = context['manapool']
            from_player = context['from_player']
            self.mana_controller.request_mana(required, manapool, is_opponent=(from_player != self.player1))
        elif context.get("get_X", False):
            from_player = context['from_player']
            self.x_controller.request_x(is_opponent=(from_player != self.player1))
        elif context.get("get_distribution", False):
            amount = context['amount']
            targets = context['targets']
            self.distribution_assignment.activate(amount, targets)
        elif context.get("get_damage_assign", False):
            blocking_list = context['blocking_list']
            trample = context['trample']
            deathtouch = context['deathtouch']
            self.damage_assignment.activate(blocking_list, trample, deathtouch)
        elif context.get("get_game_over", False):
            director.pop()

    def game_reload(self, replay_file):
        #self.game_status.log("Reloading game")
        self.msg_controller.prompt("Reloading game")

        self.dump_to_replay = replaydump.ReplayDump(filename=replay_file, save=False)
        isserver = self.dump_to_replay.read()
        seed = self.dump_to_replay.read()
        player1_name = self.dump_to_replay.read()
        my_deck = self.dump_to_replay.read()
        my_avatar = self.dump_to_replay.read_raw()
        player2_name = self.dump_to_replay.read()
        other_deck = self.dump_to_replay.read()
        other_avatar = self.dump_to_replay.read_raw()
        player_data = [(player1_name,my_deck,my_avatar), (player2_name,other_deck,other_avatar)]

        random.seed(seed)
        players = []
        for name, deck, avatar in player_data: players.append(GamePlayer(name, deck))

        player1, player2 = players[:2]

        for player in players:
            player.dirty_input = self.replay_input
        self.player_hand.set_hidden(False)
        self.otherplayer_hand.set_hidden(False)

        Keeper.init(players)
        self.make_connections((player1, None, my_avatar), (player2, None, other_avatar))
	self.soundfx.disconnect() # When replaying, don't blare sound at us.

        # XXX This is hacky - need to change it
        replaydump.players = dict([(player.name,player) for player in players])
        replaydump.stack = Keeper.stack

        self.client = None
        self.start_rules_engine()

    def game_start(self, player_name, seed, player_data, client=None):
        #self.game_status.log("Starting game")
        self.msg_controller.prompt("Starting game")

        self.dump_to_replay = replaydump.ReplayDump(save=True)
        self.dump_to_replay.write(True)
        self.dump_to_replay.write(seed)
        for name, deck, avatar in player_data:
            self.dump_to_replay.write(name)
            self.dump_to_replay.write(deck)
            self.dump_to_replay.write_raw(avatar)

        random.seed(seed)
        players = []
        for name, deck, avatar in player_data: players.append(GamePlayer(name, deck))

        player1, player2 = players[:2]
        if player1.name != player_name: 
            player1, player2 = player2, player1
            player_data.reverse()

        for player in players:
            if not client or player.name == player_name:
                player.dirty_input = self.greenlet_input
                self.player_hand.set_hidden(False)
                if not client: self.otherplayer_hand.set_hidden(False)
            else: player.dirty_input = self.network_input

        Keeper.init(players)
        self.make_connections((player1, None, player_data[0][2]), (player2, None, player_data[1][2]))

        # XXX This is hacky - need to change it
        replaydump.players = dict([(player.name,player) for player in players])
        replaydump.stack = Keeper.stack

        self.client = client
        if client:
            client.call_action = lambda result, self=self: self.switch_to_rules_engine(result)
            client.ready_to_play()
        self.start_rules_engine()

from network import realm

# XXX Note, because of the way scene transitions work (the on_enter and on_exit handler of the transitioning scenes is called twice - see http://groups.google.com/group/cocos2d-iphone-discuss/browse_frm/thread/41dc2e67a16a1136/f77139350307a45f?lnk=gst) we can't use them to play the game layer (since those handlers set up the controller event handlers)

def start_server(port, num_players):
    gamerealm = realm.Realm(port, realm.GameServer(num_players, pyglet.clock.time.time()))
    gamerealm.start()

def start_solitaire(player_name, players):
    gamescene = Scene()
    gamelayer = IncantusLayer()
    gamescene.add(gamelayer, z=0, name="table")
    director.push(gamescene)
    #director.push(ZoomTransition(gamescene, 1.5))
    gamelayer.game_start(player_name, pyglet.clock.time.time(), players)

def reload_solitaire(replay_file):
    gamescene = Scene()
    gamelayer = IncantusLayer()
    gamescene.add(gamelayer, z=0, name="table")
    director.push(gamescene)
    #director.push(ZoomTransition(gamescene, 1.5))
    gamelayer.game_reload(replay_file)

def join_game(player_name, decklist, avatar_data, host, port):
    #chatbox = ChatBox(0, 40, 400, 40, 'bottom')
    def setup_board(client):
        gamelayer = IncantusLayer()
        gamescene = Scene()
        gamescene.add(gamelayer, z=0, name="table")
        #gamescene.add(chatbox, z=1, name="chat")
        director.push(gamescene)
        #director.push(ZoomTransition(gamescene, 1.5))
        gamelayer.msg_controller.prompt("Waiting for other players")
        #gamelayer.game_status.log("Waiting for other players")
        defrd = client.ready_to_start()
        defrd.addCallback(lambda (seed, players): gamelayer.game_start(player_name, seed, players, client))
    def connected(client, avatar):
        client.avatar = avatar
        #client.msg_callback = chatbox.add_text
        #chatbox.set_callback(client.send_message)
        defrd = client.send_info((decklist, avatar_data))
        defrd.addCallback(lambda result: setup_board(client))

    client = realm.Client(player_name, host, port)
    defrd = client.connect()
    defrd.addCallback(lambda avatar: connected(client, avatar))
    return defrd

def observe_game(player_name, host, port):
    def connected(client, avatar):
        client.avatar = avatar
        #client.msg_callback = chatbox.add_text
        #chatbox.set_callback(client.send_message)
        gamelayer = IncantusLayer()
        gamescene = Scene()
        gamescene.add(gamelayer, z=0, name="table")
        #gamescene.add(chatbox, z=1, name="chat")
        director.push(gamescene)
        #director.push(ZoomTransition(gamescene, 1.5))
        #gamelayer.game_status.log("Waiting for other players")
        gamelayer.msg_controller.prompt("Waiting for other players")
        defrd = client.ready_to_start()
        defrd.addCallback(lambda (seed, players): gamelayer.game_start(player_name, seed, players, client))

    client = realm.Client(player_name, host, port)
    defrd = client.connect()
    defrd.addCallback(lambda avatar: connected(client, avatar))
    return defrd

def show_ingame_menu(layer):
    from menu import HierarchicalMenu, InGameMenu
    director.push(Scene(HierarchicalMenu(InGameMenu(layer))))

def quit():
    director.pop()

def load_deckfile(filename):
    deckfile = [l.strip().split() for l in file(filename, "rU").readlines() if not (l[0] == "#" or l[:2] == "//")]
    decklist = [(l[0], " ".join(l[1:])) for l in deckfile if l and l[0] != "SB:"]
    return decklist

def load_avatar(filename):
    return file(filename, "rb").read()
