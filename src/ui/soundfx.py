
from pyglet import media, resource
import GUIEvent
from engine import GameEvent
from engine.pydispatch import dispatcher
from resources import config

resource.path.append("./data/soundfx")
resource.reindex()

music_volume = config.getfloat("music", "volume")
sound_volume = config.getfloat("sound", "volume")
toggle_fx = config.getboolean("sound", "enabled")
toggle_music = config.getboolean("music", "enabled")
background_file = config.get("music", "bgm")

class SoundEffects(object):
    def __init__(self):
        self.sound_on = False
        self.music_on = False

        def make_sound(filename):
            sound = resource.media(filename, streaming=False)
            def vplay():
                player = sound.play()
                player.volume = sound_volume
                return player
            sound.vplay = vplay
            return sound

        self.click = make_sound("click.wav")
        self.your_focus = make_sound("your_focus.wav")
        self.opponent_focus = make_sound("opponent_focus.wav")
        self.end_turn = make_sound("end_turn.wav")
        self.start_combat = make_sound("combat.wav")
        self.gamestart = make_sound("gamestart.wav")
        self.gameover = make_sound("gameover.wav")
        self.mana = make_sound("mana.wav")
        self.manaspent = make_sound("manaspent.wav")
        self.tap = make_sound("tap.wav")
        #self.clink = make_sound("ding.wav")
        #self.enter_sound = make_sound("card_entering_play.wav")
        #self.leave_sound = make_sound("card_leaving_play.wav")
        #self.play_ability = make_sound("play_ability.wav")
        #self.untap = make_sound("untap.wav")
        #self.lifeloss = make_sound("lifeloss.wav")

        if toggle_music:
            self.player = media.Player()
            self.player.queue(resource.media(background_file, streaming=True))
            self.player.eos_action = self.player.EOS_LOOP
        else:
            self.player = None

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
    def update_music_volume(self):
        if self.player: self.player.volume = music_volume
    def update_sound_volume(self):
        for sound, _ in self.connections:
            sound.volume = sound_volume
    def enable_music(self):
        self.update_music_volume()
        if self.player and not self.music_on:
            self.music_on = True
            self.player.play()
    def enable_sound(self):
        self.update_sound_volume()
        if not self.sound_on:
            self.sound_on = True
            for sound, event in self.connections:
                dispatcher.connect(sound.vplay, signal=event, priority=dispatcher.UI_PRIORITY)
    def disable_music(self):
        if self.music_on:
            self.music_on = False
            self.player.pause()
    def disable_sound(self):
        if self.sound_on:
            self.sound_on = False
            for sound, event in self.connections:
                dispatcher.disconnect(sound.vplay, signal=event)
    def disconnect(self):
        self.disable_sound()
        self.disable_music()
    def connect(self):
        if toggle_music:
            self.enable_music()
        else:
            self.disable_music()
        if toggle_fx:
            self.enable_sound()
        else:
            self.disable_sound()
