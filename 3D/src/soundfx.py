
from pyglet import media
import GUIEvent
from game import GameEvent
from game.pydispatch import dispatcher

class SoundEffects(object):
    def __init__(self):
        self.click = media.load("./data/soundfx/click.wav", streaming=False)
        self.your_focus = media.load("./data/soundfx/your_focus.wav", streaming=False)
        self.opponent_focus = media.load("./data/soundfx/opponent_focus.wav", streaming=False)
        self.end_turn = media.load("./data/soundfx/end_turn.wav", streaming=False)
        self.start_combat = media.load("./data/soundfx/combat.wav", streaming=False)
        self.gamestart = media.load("./data/soundfx/gamestart.wav", streaming=False)
        self.gameover = media.load("./data/soundfx/gameover.wav", streaming=False)
        self.mana = media.load("./data/soundfx/mana.wav", streaming=False)
        self.manaspent = media.load("./data/soundfx/manaspent.wav", streaming=False)
        self.tap = media.load("./data/soundfx/tap.wav", streaming=False)
        #self.clink = media.load("./data/soundfx/ding.wav", streaming=False)
        #self.enter_sound = media.load("./data/soundfx/card_entering_play.wav", streaming=False)
        #self.leave_sound = media.load("./data/soundfx/card_leaving_play.wav", streaming=False)
        #self.play_ability = media.load("./data/soundfx/play_ability.wav", streaming=False)
        #self.untap = media.load("./data/soundfx/untap.wav", streaming=False)
        #self.lifeloss = media.load("./data/soundfx/lifeloss.wav", streaming=False)

        #self.player = media.Player()
        #self.player.queue(media.load("./data/soundfx/background.ogg", streaming=True))
        #self.player.eos_action = self.player.EOS_LOOP
        self.connections = [(self.gamestart, GameEvent.GameStartEvent()),
                            (self.gameover, GameEvent.GameOverEvent()),
                            (self.your_focus, GUIEvent.MyPriority()),
                            (self.opponent_focus, GUIEvent.OpponentPriority()),
                            (self.end_turn, GameEvent.NewTurnEvent()),
                            (self.start_combat, GameEvent.DeclareAttackersEvent()),
                            (self.tap, GameEvent.CardTapped()),
                            #(self.tap, GameEvent.CardUntapped()),
                            #(self.lifeloss, GameEvent.LifeChangedEvent()),
                            #(self.mana, GameEvent.ManaAdded()),
                            (self.manaspent,GameEvent.ManaSpent()),
                            #(self.clink, GUIEvent.FocusCard(), sender=dispatcher.Anonymous, priority=dispatcher.UI_PRIORITY)),
                            #(self_ability, GameEvent.AbilityAnnounced()),
                            #(self.enter_sound, GameEvent.CardEnteredZone()),
                            #(self.leave_sound, GameEvent.CardLeftZone()),
                            ]
    def disconnect(self):
        for sound, event in self.connections:
            dispatcher.connect(sound.play, signal=event)
    def connect(self):
        #self.player.play()
        for sound, event in self.connections:
            dispatcher.connect(sound.play, signal=event, priority=dispatcher.UI_PRIORITY)
    def dispatch_events(self):
        media.dispatch_events()
        #self.player.dispatch_events()

MediaEffects = SoundEffects
