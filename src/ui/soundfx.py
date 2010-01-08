
from pyglet import media, resource
import GUIEvent
from engine import GameEvent
from engine.pydispatch import dispatcher

resource.path.append("./data/soundfx")
resource.reindex()

volume = 0
toggle_fx = False
toggle_music = False

class SoundEffects(object):
    def __init__(self):
        return
        self.click = resource.media("click.wav", streaming=False)
        self.your_focus = resource.media("your_focus.wav", streaming=False)
        self.opponent_focus = resource.media("opponent_focus.wav", streaming=False)
        self.end_turn = resource.media("end_turn.wav", streaming=False)
        self.start_combat = resource.media("combat.wav", streaming=False)
        self.gamestart = resource.media("gamestart.wav", streaming=False)
        self.gameover = resource.media("gameover.wav", streaming=False)
        self.mana = resource.media("mana.wav", streaming=False)
        self.manaspent = resource.media("manaspent.wav", streaming=False)
        self.tap = resource.media("tap.wav", streaming=False)
        #self.clink = resource.media("ding.wav", streaming=False)
        #self.enter_sound = resource.media("card_entering_play.wav", streaming=False)
        #self.leave_sound = resource.media("card_leaving_play.wav", streaming=False)
        #self.play_ability = resource.media("play_ability.wav", streaming=False)
        #self.untap = resource.media("untap.wav", streaming=False)
        #self.lifeloss = resource.media("lifeloss.wav", streaming=False)

        self.player = media.Player()
        self.player.queue(resource.media("background.ogg", streaming=True))
        self.player.eos_action = self.player.EOS_LOOP
        self.connections = [(self.gamestart, GameEvent.GameStartEvent()),
                            (self.gameover, GameEvent.GameOverEvent()),
                            (self.your_focus, GUIEvent.MyPriority()),
                            (self.opponent_focus, GUIEvent.OpponentPriority()),
                            (self.end_turn, GameEvent.NewTurnEvent()),
                            (self.start_combat, GameEvent.DeclareAttackersEvent()),
                            (self.tap, GameEvent.CardTapped()),
                            #(self.tap, GameEvent.CardUntapped()),
                            #(self.lifeloss, GameEvent.LifeLostEvent()),
                            #(self.mana, GameEvent.ManaAdded()),
                            (self.manaspent,GameEvent.ManaSpent()),
                            #(self.clink, GUIEvent.FocusCard(), sender=dispatcher.Anonymous, priority=dispatcher.UI_PRIORITY)),
                            #(self_ability, GameEvent.AbilityAnnounced()),
                            #(self.enter_sound, GameEvent.CardEnteredZone()),
                            #(self.leave_sound, GameEvent.CardLeftZone()),
                            ]
    def disconnect(self):
        return
        for sound, event in self.connections:
            dispatcher.disconnect(sound.play, signal=event)
    def connect(self):
        return
        if toggle_music:
            self.player.play()
        if toggle_fx:
            for sound, event in self.connections:
                dispatcher.connect(sound.play, signal=event, priority=dispatcher.UI_PRIORITY)
