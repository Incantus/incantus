#!/usr/local/bin/python2.4
"""<title>Menus, Toolboxes, a full Application</title>
Most all widgets are used in this example.  A full custom widget
is included.  A number of connections are used to make the application
function.
"""
import sys,random,time
import pygame
from pgu import gui

import CardLibrary
import status_widgets
import card_widgets
import dialogs
import networkcomm, replaydump

import game
from game.pydispatch import dispatcher
from game import Action

def pdb(val):
    import pdb
    #import getobjects
    #obj = getobjects.get_all_objects()
    pdb.set_trace()

class App(gui.Desktop):
    def __init__(self,**params):
        super(App, self).__init__(**params)
        
        width = 1024
        height = 768
        container = gui.Container(width=width,height=height)
        
        #self.help_d = dialogs.HelpDialog()
        self.quit_d = dialogs.QuitDialog()
        self.quit_d.connect(gui.QUIT,self.quit,None)
        self.connect(gui.QUIT,self.quit_d.open,None)
        self.decklist = None
        self.connection = None
        self.replay = False
        self.dump_to_replay = lambda x: None

        self.showing_dialog = False  # Hack since dialogs don't seem to be modal with respect to the keyboard

        
        ##Initializing the Menus, we connect to a number of Dialog.open methods for each of the dialogs.
        menus = gui.Menus([
            ('Game/New',self.action_new_game,None),
            ('Game/New Network',self.action_new_network_game,None),
            ('Game/Quit',self.quit_d.open,None),
            ('Test/Crash',pdb, False),
            ('Test/Replay',self.action_new_game,False),
            ('Test/Replay fast',self.action_new_game,True),
            #('Help/Help',self.help_d.open,None),
            ])
        ##
        spacer = 8
        spacer = 3
        container.add(menus,spacer,0)
        menus.rect.w,menus.rect.h = menus.resize()

        otherplayer_status = status_widgets.PlayerStatus(style={"border":1})
        container.add(otherplayer_status,spacer, menus.rect.bottom+spacer)
        otherplayer_status.rect.x,otherplayer_status.rect.y = otherplayer_status.style.x,otherplayer_status.style.y
        otherplayer_status.rect.w,otherplayer_status.rect.h = otherplayer_status.resize()

        ##We utilize a Toolbox.  The value of this widget determins how drawing is done in the Painter class.
        ##::
        self.game_step = game_step = status_widgets.GameStatus([
            ('Untap','Untap'),
            ('Upkeep','Upkeep'),
            ('Draw','Draw'),
            ('Main 1','Main1'),
            ('PreCombat','PreCombat'),
            ('Attack','Attack'),
            ('Block','Block'),
            ('Damage','Damage'),
            ('End Combat','EndCombat'),
            ('Main 2','Main2'),
            ('End Phase','EndPhase'),
            ],cols=1,value='Untap')
        #
        container.add(game_step,spacer,otherplayer_status.rect.bottom+spacer)
        game_step.rect.x,game_step.rect.y = game_step.style.x,game_step.style.y
        game_step.rect.w,game_step.rect.h = game_step.resize()

        mainplayer_status = status_widgets.PlayerStatus(style={"border":1})
        container.add(mainplayer_status,spacer,game_step.rect.bottom+spacer)
        mainplayer_status.rect.w,mainplayer_status.rect.h = mainplayer_status.resize()

        card_info = card_widgets.CardInfo(width=234,height=333)
        container.add(card_info,container.rect.right-spacer, menus.rect.bottom+spacer)
        card_info.rect.w,card_info.rect.h = card_info.resize()

        pass_b = gui.Button("Pass")
        pass_b.connect(gui.CLICK, self.Pass_pressed, None)
        pass_b.rect.w,pass_b.rect.h=pass_b.resize()
        container.add(pass_b,container.rect.w-spacer,container.rect.h-pass_b.rect.h)
        b = gui.Button("Cancel")
        b.connect(gui.CLICK, self.Cancel,None)
        b.rect.w,b.rect.h=b.resize()
        container.add(b,container.rect.w-spacer+pass_b.rect.w,container.rect.h-b.rect.h)

        width = card_info.rect.w-spacer
        height = container.rect.h-(menus.rect.h+card_info.rect.h+b.rect.h+3*spacer)
        stack = card_widgets.CardStack(width=width,height=4*height/6,style={'border':1})
        container.add(stack,container.rect.w-spacer,menus.rect.h+card_info.rect.h+2*spacer)
        stack.init(card_info)
        stack.rect.w,stack.rect.h=stack.resize()

        logger = status_widgets.LogStatus(width=width,height=2*height/6-2*spacer,style={'border':1})
        container.add(logger,container.rect.w-spacer, menus.rect.h+card_info.rect.h+3*spacer+stack.rect.h)
        logger.rect.w,logger.rect.h=logger.resize()

        width = container.rect.w-game_step.rect.w-spacer*4
        height = 100
        player_hand = card_widgets.CardsHand(width=width,height=height,style={'border':1})
        container.add(player_hand,game_step.rect.right+spacer,container.rect.h-player_hand.rect.h-spacer)
        player_hand.init(card_info)
        player_hand.rect.w,player_hand.rect.h = player_hand.resize()
        
        other_hand = card_widgets.CardsHand(width=width,height=height,style={'border':1})
        container.add(other_hand,game_step.rect.right+spacer,menus.rect.bottom+spacer)
        other_hand.init(card_info)
        other_hand.rect.w,other_hand.rect.h = other_hand.resize()

        width = container.rect.w-game_step.rect.w-spacer*4
        height = (container.rect.h-player_hand.rect.h-other_hand.rect.h-menus.rect.h-spacer*3)/2
        #height = (container.rect.h-player_hand.rect.h-menus.rect.h-spacer*2)/2

        log_message = gui.Label("Welcome to Magic the Gathering"+' '*120, width=width)
        container.add(log_message,game_step.rect.right+spacer*10,menus.rect.top+2*spacer)

        other_play = card_widgets.CardsPlay(isother=True,width=width, height=height,style={'border':1})
        container.add(other_play,game_step.rect.right+spacer,menus.rect.h+other_hand.rect.h+spacer)
        #container.add(other_play,game_step.rect.right+spacer,menus.rect.h+spacer)
        other_play.init(card_info)
        other_play.rect.w,other_play.rect.h = other_play.resize()

        play = card_widgets.CardsPlay(width=width, height=height,style={'border':1})
        container.add(play,game_step.rect.right+spacer,menus.rect.h+other_hand.rect.h+other_play.rect.h+spacer)
        #container.add(play,game_step.rect.right+spacer,menus.rect.h+other_play.rect.h+spacer)
        play.init(card_info)
        play.rect.w,play.rect.h = play.resize()

        self.widget = container
        self.log_message = log_message
        self.mainplayer_status = mainplayer_status
        self.otherplayer_status = otherplayer_status
        self.play = play
        self.other_play = other_play
        self.player_hand = player_hand
        self.other_hand = other_hand
        self.logger = logger
        self.stack = stack
        self.card_info = card_info
        
        overlay = card_widgets.OverlayInfo(width=1255, height=768)
        overlay.setup_overlay(self.mainplayer_status, self.otherplayer_status, self.play, self.other_play, self.player_hand, self.stack)
        container.add(overlay, 0,0)
        self.overlay = overlay
        stack.overlay = overlay

    def init(self, widget = None, screen = None):
        super(App, self).init(widget, screen)
        # Load up all the graphics data
        CardLibrary.CardLibrary = CardLibrary._CardLibrary()
        self.card_info.cardlib = CardLibrary.CardLibrary
        self.overlay.init()

    def action_assign_damage(self, blocking_list):
        damageAssn = dialogs.AssignDamageDialog(blocking_list)
        def damage_assigned(dialog):
            dmg = dialog.form.results()
            for c in dmg.keys(): dmg[c] = int(dmg[c])
            correct = True
            for attacker, blockers in blocking_list:
                total_damage = sum([dmg[b] for b in blockers])
                if total_damage != attacker.power: correct = False
            if not correct:
                dialog.error.set_value("Incorrect assignment")
                dialog.error.repaint()
            else:
                dialog.close()
                #self.showing_dialog = False
                pygame.event.post(pygame.event.Event(gui.USEREVENT, {"action": Action.DamageAssignment(dmg)}))
        damageAssn.connect("OK",damage_assigned, damageAssn)
        self.showing_dialog = True
        damageAssn.open()

    def action_select_x(self):
        choice = dialogs.XDialog()
        def select_X(dialog):
            amount = int(dialog.form.results()["X"])
            dialog.close()
            #self.showing_dialog = False
            pygame.event.post(pygame.event.Event(gui.USEREVENT, {"action":  Action.XSelected(amount)}))
        choice.connect("OK",select_X,choice)
        #choice.connect("CANCEL",make_choice,Action.CancelAction())
        self.showing_dialog = True
        choice.open()

    def action_select_mana(self, manapool, required):
        choice = dialogs.ManaDialog(manapool, required)
        def mana_selected(dialog):
            import game.Mana
            # Assume that I have enough total mana
            # convert back into a mana string
            mana = dialog.form.results()
            manastr = ''.join([color*int(mana[color]) for color in "RGBUW" if mana[color] != ''])
            if mana.get("C", 0) > 0: manastr += str(mana.get('C'))
            if manastr == '': manastr = '0'

            if game.Mana.compareMana(required, manastr) and manapool.checkMana(manastr):
                dialog.close()
                #self.showing_dialog = False
                pygame.event.post(pygame.event.Event(gui.USEREVENT, {"action": Action.ManaSelected(manastr)}))
            else:
                req = game.Mana.convert_mana_string(required)
                m = game.Mana.convert_mana_string(manastr)
                if not manapool.checkMana(m): dialog.error.set_value("Not enough mana in pool")
                elif sum(req) > sum(m): dialog.error.set_value("Not enough mana")
                else: dialog.error.set_value("Too much mana")
                dialog.error.repaint()
        choice.connect("OK",mana_selected,choice)
        def close_no_selection(dialog):
            self.showing_dialog = False
            dialog.close()
            pygame.event.post(pygame.event.Event(gui.USEREVENT, {"action": Action.CancelAction()}))
        choice.connect("CANCEL",close_no_selection,choice)
        self.showing_dialog = True
        choice.open()

    def action_reveal_card(self, keys, msgs, title):
        reveal = dialogs.RevealCardDialog(keys, msgs, title)
        def close_dialog(dialog):
            dialog.close()
            pygame.event.post(pygame.event.Event(gui.USEREVENT, {"action": Action.CancelAction()}))
        reveal.connect("OK",close_dialog,reveal)
        self.showing_dialog = True
        reveal.open()

    def action_make_choice(self, msg):
        choice = dialogs.MessageDialog(msg)
        def make_choice(action):
            choice.close()
            #self.showing_dialog = False
            pygame.event.post(pygame.event.Event(gui.USEREVENT, {"action": action}))
        choice.connect("OK",make_choice,Action.OKAction())
        choice.connect("CANCEL",make_choice,Action.CancelAction())
        self.showing_dialog = True
        choice.open()
    
    def action_show_cardlist(self, cardlist, msg):
        cardlist = dialogs.OutOfPlay(msg, cardlist, self.card_info)
        def make_choice(action):
            cardlist.close()
            pygame.event.post(pygame.event.Event(gui.USEREVENT, {"action": Action.CancelAction()}))
        cardlist.connect("OK",make_choice,None)
        self.showing_dialog = True
        cardlist.open()

    def action_make_selection(self,sellist,numselection,isCardlist=True,required=True,msg=''):

        if isCardlist: cardinfo = self.card_info
        else: cardinfo = None
        choose_dialog = dialogs.ChooseSelectionDialog(sellist,numselection,cardinfo,required,msg)

        def onchange(dialog):
            if numselection == 1:
                index = dialog.form['selection'].value
                if index is not None:
                    dialog.close()
                    #self.showing_dialog = False
                    pygame.event.post(pygame.event.Event(gui.USEREVENT, {"action": Action.SingleSelected(index)}))
                else: 
                    dialog.error.set_value("Error: None selected")
                    dialog.error.repaint()
            else:
                sel = [i.value for i in dialog.choose.items]
                if (len(sel) == numselection) or (len(sellist) < numselection and len(sel) == len(sellist)):
                    dialog.close()
                    #self.showing_dialog = False
                    pygame.event.post(pygame.event.Event(gui.USEREVENT, {"action": Action.MultipleSelected(sel)}))
                elif len(sel) > numselection:
                    dialog.error.set_value("Error: Too many selected")
                    dialog.error.repaint()
                else:
                    dialog.error.set_value("Error: Select %d more"%(numselection-len(sel)))
                    dialog.error.repaint()

        def close_no_selection(dialog):
            dialog.close()
            #self.showing_dialog = False
            pygame.event.post(pygame.event.Event(gui.USEREVENT, {"action": Action.CancelAction()}))

        if not numselection == 0: choose_dialog.connect(gui.CHANGE,onchange,choose_dialog)
        else: choose_dialog.connect(gui.CHANGE,close_no_selection,choose_dialog)
        if not required: choose_dialog.cancel.connect(gui.CLICK,close_no_selection,choose_dialog)
        self.showing_dialog = True
        choose_dialog.open()


    def load_deck(self):
        import os
        self.log("Please load deck file")
        
        def read_deck_file(dlg):
            if os.path.isdir(dlg.value):
                self.decklist = None
                self.log("No deck file selected")
            else:
                deckfile = dlg.value
                self.decklist = [l.strip().split("\t") for l in file(deckfile).readlines() if l[0] != "#"]
                self.log("Deck (%s) has been loaded"%deckfile)

        filedialog = gui.FileDialog(path=os.path.expanduser("~"))
        filedialog.connect(gui.CHANGE,read_deck_file, filedialog)
        filedialog.open()

    def action_new_game(self,replay):
        dispatcher.reset()

        self.decklist = [l.strip().split("\t") for l in file("small_deck.txt").readlines() if l[0] != "#"]
        if not self.decklist: return self.load_deck()

        if replay == None: self.replay = self.replay_fast = False
        else:
            self.replay = True
            self.replay_fast = replay
        self.dump_to_replay = replaydump.ReplayDump(self, not self.replay)

        if not self.replay:
            seed = time.time()
            self.dump_to_replay(seed)
            self.dump_to_replay(self.decklist)
        else:
            seed = self.dump_to_replay.read()
            self.decklist = self.dump_to_replay.read()

        random.seed(seed)
        player1 = game.Player("Andrew")
        player2 = game.Player("Brian")

        self.player1 = player1
        self.player2 = player2

        # These need to be set here so that abilities can target the opponent
        player1.setOpponent(player2)
        player2.setOpponent(player1)

        player1.setDeck(self.decklist)
        player2.setDeck(self.decklist)

        self.make_connections((0,0,255), (255,255,0))
        
        game.Keeper.init(player1, player2)

        # This is hacky - need to change it
        player1.input = self.dirty_loop
        player2.input = self.dirty_loop

        try:
            game.Keeper.run()
        except:
            # Save the log
            #del self.dump_to_replay
            #del self.connection
            raise
        # XXX Game over - quit for now
        self.send(gui.QUIT)

    def action_new_network_game(self, value):
        self.decklist = [l.strip().split("\t") for l in file("small_deck.txt").readlines() if l[0] != "#"]
        if not self.decklist: return self.load_deck()
        new_game = dialogs.NetworkGameDialog()
        def start(dialog):
            setup = dialog.setup.results()
            playername = setup["name"]
            ipaddr = setup["address"]
            port = int(setup["port"])
            isserver = setup["server"]
            self_color = setup["self_color"]
            other_color = setup["other_color"]
            ready = True

            if ready:
                #self.showing_dialog = False
                new_game.close()
                self.start_network_game(playername, ipaddr, port, isserver, (self_color, other_color))
        new_game.connect("OK",start,new_game)
        self.showing_dialog = True
        new_game.open()

    def start_network_game(self, playername, ipaddr, port, isserver, colors):
        dispatcher.reset()
        player1 = game.Player(playername)
        self_color, other_color = colors
        if isserver:
            self.connection = networkcomm.Server(ipaddr, port)
            # exchange random seeds to synchronize RNG
            seed = time.time()
            random.seed(seed)
            self.connection.send(seed)
            self.connection.send(playername)
            # Get the name of the other player
            otherplayername = self.connection.receive()
        else:
            self.connection = networkcomm.Client(ipaddr, port)
            seed = self.connection.receive()
            random.seed(seed)
            # Get the name of the other player
            otherplayername = self.connection.receive()
            self.connection.send(playername)

        player2 = game.Player(otherplayername)
        self.player1 = player1
        self.player2 = player2

        # These need to be set here so that abilities can target the opponent
        player1.setOpponent(player2)
        player2.setOpponent(player1)

        self.make_connections(self_color, other_color)

        # Load decks - Make sure these are loaded in the same order for client and server
        if isserver:
            decklist1 = self.decklist
            self.connection.send(decklist1)
            decklist2 = self.connection.receive()
            player1.setDeck(decklist1)
            player2.setDeck(decklist2)
            game.Keeper.init(player1, player2)
        else:
            decklist2 = self.decklist
            decklist1 = self.connection.receive()
            self.connection.send(decklist2)
            player1.setDeck(decklist1)
            player2.setDeck(decklist2)
            # If we are the client, then the other player is the first player
            game.Keeper.init(player2, player1)

        # This is hacky - need to change it
        player1.input = self.dirty_loop
        player2.input = self.dirty_network_loop_other
        networkcomm.players = dict([(player.name,player) for player in [player1, player2]])
        
        game.Keeper.run()
        # XXX Game over - quit for now
        self.send(gui.QUIT)
        
    def make_connections(self, self_color, other_color):
        self.mainplayer_status.setup_player(self.player1, self.action_show_cardlist, self_color)
        self.otherplayer_status.setup_player(self.player2, self.action_show_cardlist, other_color)
        #self.mainplayer_status.setup_player(self.player1, self.action_make_selection, self_color)
        #self.otherplayer_status.setup_player(self.player2, self.action_make_selection, other_color)
        self.player_hand.set_zone(self.player1.hand)
        self.other_hand.set_zone(self.player2.hand)
        self.play.set_zone(self.player1.play)
        self.other_play.set_zone(self.player2.play)
        self.stack.set_zone(game.Keeper.stack)
        self.stack.setup_player_colors(self.player1, self_color, other_color)
        self.game_step.setup_player_colors(self.player1, self_color, other_color)
        self.logger.setup_player_colors(self.player1, self_color, other_color)

        dispatcher.connect(self.player_hand.update_cards, signal=game.GameEvent.CardEnteredZone(), sender=self.player1.hand)
        dispatcher.connect(self.player_hand.update_cards, signal=game.GameEvent.AbilityPlacedOnStack())
        dispatcher.connect(self.play.update_cards, signal=game.GameEvent.CardEnteredZone(), sender=self.player1.play)
        dispatcher.connect(self.play.update_cards, signal=game.GameEvent.CardControllerChanged())
        dispatcher.connect(self.other_play.update_cards, signal=game.GameEvent.CardEnteredZone(), sender=self.player2.play)
        dispatcher.connect(self.other_play.update_cards, signal=game.GameEvent.CardControllerChanged())
        dispatcher.connect(self.stack.update_cards, signal=game.GameEvent.AbilityPlacedOnStack())

        # XXX Disconnect these three for an actual game
        dispatcher.connect(self.other_hand.update_cards, signal=game.GameEvent.CardEnteredZone(), sender=self.player2.hand)
        dispatcher.connect(self.other_hand.update_cards, signal=game.GameEvent.CardLeftZone(), sender=self.player2.hand)
        dispatcher.connect(self.other_hand.update_cards, signal=game.GameEvent.AbilityPlacedOnStack())

        # XXX Overlay connections
        #dispatcher.connect(self.overlay.update_overlay, signal=game.GameEvent.CardEnteredZone(), sender=self.player1.play)
        #dispatcher.connect(self.overlay.update_overlay, signal=game.GameEvent.CardEnteredZone(), sender=self.player2.play)
        #dispatcher.connect(self.overlay.update_overlay, signal=game.GameEvent.CardLeftZone(), sender=self.player1.play)
        #dispatcher.connect(self.overlay.update_overlay, signal=game.GameEvent.CardLeftZone(), sender=self.player2.play)
        #dispatcher.connect(self.overlay.update_overlay, signal=game.GameEvent.CardEnteredZone(), sender=self.player1.hand)
        #dispatcher.connect(self.overlay.update_overlay, signal=game.GameEvent.CardEnteredZone(), sender=self.player2.hand)
        #dispatcher.connect(self.overlay.update_overlay, signal=game.GameEvent.CardLeftZone(), sender=self.player1.hand)
        #dispatcher.connect(self.overlay.update_overlay, signal=game.GameEvent.CardLeftZone(), sender=self.player2.hand)
        #dispatcher.connect(self.overlay.update_overlay, signal=game.GameEvent.CardLeftZone())
        #dispatcher.connect(self.overlay.update_overlay, signal=game.GameEvent.AbilityPlacedOnStack())
        #dispatcher.connect(self.overlay.update_overlay, signal=game.GameEvent.AbilityRemovedFromStack())

        dispatcher.connect(self.play.update_cards, signal=game.GameEvent.CardLeftZone(), sender=self.player1.play)
        dispatcher.connect(self.player_hand.update_cards, signal=game.GameEvent.CardLeftZone(), sender=self.player1.hand)
        dispatcher.connect(self.other_play.update_cards, signal=game.GameEvent.CardLeftZone(), sender=self.player2.play)
        dispatcher.connect(self.stack.update_cards, signal=game.GameEvent.AbilityRemovedFromStack())
        dispatcher.connect(self.stack.update_cards, signal=game.GameEvent.AbilityCountered())
        
        
        dispatcher.connect(self.play.update_cards, signal=game.GameEvent.EndCombatEvent())
        dispatcher.connect(self.other_play.update_cards, signal=game.GameEvent.EndCombatEvent())
        dispatcher.connect(self.mainplayer_status.update_status, signal=game.GameEvent.PlayerStatusChanged(),sender=self.player1)
        dispatcher.connect(self.otherplayer_status.update_status, signal=game.GameEvent.PlayerStatusChanged(),sender=self.player2)
        dispatcher.connect(self.mainplayer_status.update_cards, signal=game.GameEvent.CardEnteredZone(), sender=self.player1.hand)
        dispatcher.connect(self.mainplayer_status.update_cards, signal=game.GameEvent.CardLeftZone(), sender=self.player1.hand)
        dispatcher.connect(self.otherplayer_status.update_cards, signal=game.GameEvent.CardEnteredZone(), sender=self.player2.hand)
        dispatcher.connect(self.otherplayer_status.update_cards, signal=game.GameEvent.CardLeftZone(), sender=self.player2.hand)
        dispatcher.connect(self.mainplayer_status.update_cards, signal=game.GameEvent.CardEnteredZone(), sender=self.player1.library)
        dispatcher.connect(self.mainplayer_status.update_cards, signal=game.GameEvent.CardLeftZone(), sender=self.player1.library)
        dispatcher.connect(self.otherplayer_status.update_cards, signal=game.GameEvent.CardEnteredZone(), sender=self.player2.library)
        dispatcher.connect(self.otherplayer_status.update_cards, signal=game.GameEvent.CardLeftZone(), sender=self.player2.library)
        dispatcher.connect(self.mainplayer_status.update_cards, signal=game.GameEvent.CardEnteredZone(), sender=self.player1.graveyard)
        dispatcher.connect(self.mainplayer_status.update_cards, signal=game.GameEvent.CardLeftZone(), sender=self.player1.graveyard)
        dispatcher.connect(self.otherplayer_status.update_cards, signal=game.GameEvent.CardEnteredZone(), sender=self.player2.graveyard)
        dispatcher.connect(self.otherplayer_status.update_cards, signal=game.GameEvent.CardLeftZone(), sender=self.player2.graveyard)
        dispatcher.connect(self.mainplayer_status.update_cards, signal=game.GameEvent.CardEnteredZone(), sender=self.player1.removed)
        dispatcher.connect(self.mainplayer_status.update_cards, signal=game.GameEvent.CardLeftZone(), sender=self.player1.removed)
        dispatcher.connect(self.otherplayer_status.update_cards, signal=game.GameEvent.CardEnteredZone(), sender=self.player2.removed)
        dispatcher.connect(self.otherplayer_status.update_cards, signal=game.GameEvent.CardLeftZone(), sender=self.player2.removed)
        dispatcher.connect(self.mainplayer_status.update_mana, signal=game.GameEvent.ManaAdded(), sender=self.player1.manapool)
        dispatcher.connect(self.mainplayer_status.update_mana, signal=game.GameEvent.ManaSpent(), sender=self.player1.manapool)
        dispatcher.connect(self.mainplayer_status.update_mana, signal=game.GameEvent.ManaRemoved(), sender=self.player1.manapool)
        dispatcher.connect(self.otherplayer_status.update_mana, signal=game.GameEvent.ManaAdded(), sender=self.player2.manapool)
        dispatcher.connect(self.otherplayer_status.update_mana, signal=game.GameEvent.ManaSpent(), sender=self.player2.manapool)
        dispatcher.connect(self.otherplayer_status.update_mana, signal=game.GameEvent.ManaRemoved(), sender=self.player2.manapool)

        dispatcher.connect(self.game_step.set_phase, signal=game.GameEvent.GameStepEvent())
        dispatcher.connect(self.game_step.pass_priority, signal=game.GameEvent.HasPriorityEvent())
        dispatcher.connect(self.game_step.new_turn, signal=game.GameEvent.NewTurnEvent())

        # This might lead to a lot of repaints
        #dispatcher.connect(self.play.repaint, signal=game.GameEvent.HasPriorityEvent())
        #dispatcher.connect(self.other_play.repaint, signal=game.GameEvent.HasPriorityEvent())

        dispatcher.connect(self.play.update_cards, signal=game.GameEvent.CardTapped())
        dispatcher.connect(self.other_play.update_cards, signal=game.GameEvent.CardTapped())
        dispatcher.connect(self.play.update_cards, signal=game.GameEvent.CardUntapped())
        dispatcher.connect(self.other_play.update_cards, signal=game.GameEvent.CardUntapped())


    def log(self, txt):
        self.logtxt = txt  # XXX This is a hack so the replay functionality can access it when asking to continue recording
        self.log_message.set_value(txt)
        self.log_message.repaint()

    def dirty_loop(self, context, prompt=''):
        s = self.screen
        userevent = False
        self.log(prompt)

        if self.replay and self.replay_fast:
            result = self.dump_to_replay.read()
            if not result == False: return result

        process = context['process']
        if self.replay: pass
        elif context.get("get_ability", False): pass
        elif context.get("get_target", False): pass
        elif context.get("get_selection", False):
            sellist = context['list']
            numselections = context['numselections']
            isCardlist = context['cardlist']
            required = context['required']
            self.action_make_selection(sellist,numselections,isCardlist,required,prompt)
        elif context.get("get_choice", False):
            msg = context['msg']
            self.action_make_choice(msg)
        elif context.get("get_mana_choice", False):
            required = context['required']
            manapool = context['manapool']
            self.action_select_mana(manapool,required)
        elif context.get("get_X", False):
            self.action_select_x()
        elif context.get("get_damage_assign", False):
            blocking_list = context['blocking_list']
            self.action_assign_damage(blocking_list)
        elif context.get("reveal_card", False):
            keys = context['cardkeys']
            msgs = context['msgs']
            title = context['title']
            self.action_reveal_card(keys, msgs, title)

        # The game has probably changed state - reflect this in an update
        us = self.update(s)
        pygame.display.update(us)

        while not userevent:
            e = pygame.event.poll()
            if not self.event(e):
                if e.type == gui.USEREVENT:
                    if self.replay: result = self.dump_to_replay.read()
                    else: result = process(e.action)
                    if result is not False: userevent = True
                    self.showing_dialog = False
                elif e.type == gui.KEYDOWN and not self.showing_dialog:   # This is a hack because dialogs don't seem to be modal with regards the keyboard
                    if e.key == gui.K_RETURN: self.Pass_pressed()
                    elif e.key == gui.K_ESCAPE: self.Cancel()
            us = self.update(s)
            pygame.display.update(us)
            pygame.time.wait(10)

        if self.connection: self.connection.send(result)
        if not self.replay: self.dump_to_replay(result)
        return result

    def dirty_network_loop_other(self, context, prompt=''):
        s = self.screen
        networkevent = False
        self.log(prompt)

        # The game has probably changed state - reflect this in an update
        us = self.update(s)
        pygame.display.update(us)

        while not networkevent:
            e = pygame.event.poll()
            #e = pygame.event.wait()
            self.event(e)
            us = self.update(s)
            pygame.display.update(us)
            pygame.time.wait(10)

            # Poll other network player for action
            if self.connection.poll_other():
                result = self.connection.receive()
                networkevent = True

        return result

    def event(self, event):
        if event.type == gui.QUIT:
            del self.dump_to_replay
            del self.connection
            sys.exit(0)
        else: return super(App,self).event(event)

    def Pass_pressed(self, value=None):
        pygame.event.post(pygame.event.Event(gui.USEREVENT, {"action": Action.PassPriority()}))
    def Cancel(self, value=None):
        pygame.event.post(pygame.event.Event(gui.USEREVENT, {"action": Action.CancelAction()}))


if __name__ == "__main__":
    # Can only use default theme for the ChooseSelectionDialog (until the slider images are created)
    #theme = gui.Theme("gray")
    #app = App(theme=theme)
    pygame.display.set_icon(pygame.image.load("./data/MtG.png"))
    app = App()
    pygame.display.set_caption("Magic the Gathering v0.1", "MtG")
    app.run()
