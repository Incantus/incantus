
from pyglet import media
import GUIEvent
from game import GameEvent
from game.pydispatch import dispatcher

class MediaEffects(object):
    def __init__(self):
        return
        #self.click = media.load("./data/soundfx/click.wav", streaming=False)
        #self.clink = media.load("./data/soundfx/ding.wav", streaming=False)
        #self.enter_sound = media.load("./data/soundfx/card_entering_play.wav", streaming=False)
        #self.leave_sound = media.load("./data/soundfx/card_leaving_play.wav", streaming=False)
        #self.play_ability = media.load("./data/soundfx/play_ability.wav", streaming=False)
        #self.mana = media.load("./data/soundfx/mana.wav", streaming=False)
        self.start_combat = media.load("./data/soundfx/start_combat.ogg", streaming=False)
        self.tap = media.load("./data/soundfx/tap.wav", streaming=False)
        #self.untap = media.load("./data/soundfx/untap.wav", streaming=False)
        self.lifeloss = media.load("./data/soundfx/lifeloss.wav", streaming=False)
        self.player = media.Player()
        #self.player.queue(media.load("./data/soundfx/background.ogg", streaming=True))
        self.player.eos_action = self.player.EOS_LOOP
    def connect(self, game):
        return
        #self.player.play()
        dispatcher.connect(self.tap.play, signal=GameEvent.CardTapped(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.tap.play, signal=GameEvent.CardUntapped(), priority=dispatcher.UI_PRIORITY)
        dispatcher.connect(self.lifeloss.play, signal=GameEvent.LifeChangedEvent(), priority=dispatcher.UI_PRIORITY)
        #dispatcher.connect(self.clink.play, signal=GUIEvent.FocusCard(), sender=dispatcher.Anonymous, priority=dispatcher.UI_PRIORITY)
        #dispatcher.connect(self.play_ability.play, signal=GameEvent.AbilityPlacedOnStack(), priority=dispatcher.UI_PRIORITY)
        #dispatcher.connect(self.enter_sound.play, signal=GameEvent.CardEnteredZone(), sender=game.player1.play, priority=dispatcher.UI_PRIORITY)
        #dispatcher.connect(self.enter_sound.play, signal=GameEvent.CardEnteredZone(), sender=game.player2.play, priority=dispatcher.UI_PRIORITY)
        #dispatcher.connect(self.start_combat.play, signal=GameEvent.DeclareAttackersEvent(), priority=dispatcher.UI_PRIORITY)
        #dispatcher.connect(self.leave_sound.play, signal=GameEvent.CardLeftZone(), sender=game.player1.play, priority=dispatcher.UI_PRIORITY)
        #dispatcher.connect(self.leave_sound.play, signal=GameEvent.CardLeftZone(), sender=game.player2.play, priority=dispatcher.UI_PRIORITY)
        #dispatcher.connect(self.mana.play, signal=GameEvent.ManaAdded(), priority=dispatcher.UI_PRIORITY)
        #dispatcher.connect(self.mana.play, signal=GameEvent.ManaSpent(), priority=dispatcher.UI_PRIORITY)
        #dispatcher.connect(self.mana.play, signal=GameEvent.ManaCleared(), priority=dispatcher.UI_PRIORITY) # need a mana burn sound
    def dispatch_events(self):
        return
        media.dispatch_events()
        #self.player.dispatch_events()
