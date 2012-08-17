
import pyglet
from pyglet.window import key
from cocos.director import director
from cocos.menu import *
from cocos.layer import Layer, MultiplexLayer
from cocos.text import Label
from cocos.actions import FadeIn, FadeOut, Repeat
import soundfx
import Incantus
from resources import fontname, config

class HierarchicalMenu(Layer):
    current_menu = property(fget=lambda self: self.menu_trail[-1])
    def __init__(self, main):
        super(HierarchicalMenu, self).__init__()
        self.add(main)
        self.menu_trail = [main]
    def on_exit(self):
        # Reset to first menu
        self.reset()
        super(HierarchicalMenu, self).on_exit()
    def move_up(self):
        self.remove(self.current_menu)
        self.menu_trail.pop()
        self.add(self.current_menu)
    def move_down(self, menu):
        self.remove(self.current_menu)
        self.menu_trail.append(menu)
        self.add(menu)
    def reset(self):
        self.remove(self.current_menu)
        self.menu_trail[:] = self.menu_trail[:1]
        self.add(self.current_menu)

class SubMenuItem(MenuItem):
    def __init__(self, label, submenu):
        super(SubMenuItem, self).__init__(label, self.switch_to_submenu)
        submenu.top_level = False
        self.submenu = submenu
    def switch_to_submenu(self):
        self.parent.parent.move_down(self.submenu)

class IncantusMenu(Menu):
    top_level = True
    def __init__(self, title=''):
        if title: title = "Incantus - %s"%title
        else: title = "Incantus"
        super(IncantusMenu, self).__init__(title)

        #self.select_sound = soundfx.load('move.mp3')
        # you can override the font that will be used for the title and the items
        # you can also override the font size and the colors. see menu.py for
        # more info
        self.font_title['font_name'] = fontname
        self.font_title['font_size'] = 32
        self.font_title['color'] = (204,164,164,255)

        self.font_item['font_name'] = fontname
        self.font_item['color'] = (200, 200, 200 ,255)
        self.font_item['font_size'] = 24
        self.font_item_selected['font_name'] = fontname
        self.font_item_selected['color'] = (200,200,200,255)
        self.font_item_selected['font_size'] = 32

        # example: menus can be vertical aligned and horizontal aligned
        self.menu_anchor_y = CENTER
        self.menu_anchor_x = CENTER
    def create_menu(self, items, selected_effect=shake(), unselected_effect=shake_back()):
        super(IncantusMenu, self).create_menu(items) #, selected_effect, unselected_effect)
    def on_quit(self):
        self.parent.move_up()

class MainMenu(IncantusMenu):
    def __init__(self):
        super(MainMenu, self).__init__()
        items = []
        items.append(SubMenuItem('Start Solitaire Game', SolitaireGameMenu()))
        items.append(SubMenuItem('Reload Solitaire Game', ReloadSolitaireGameMenu()))
        items.append(SubMenuItem('Start Network Game', StartGameMenu()))
        items.append(SubMenuItem('Join Network Game', JoinGameMenu()))
        items.append(SubMenuItem('Observe Network Game', ObserveGameMenu()))
        items.append(SubMenuItem('Options', OptionsMenu()))
        items.append(MenuItem('Quit', self.on_quit) )
        self.create_menu(items)
    def on_quit(self):
        pyglet.app.exit()

class InGameMenu(IncantusMenu):
    def __init__(self, layer):
        super(InGameMenu, self).__init__()
        items = []
        items.append(MenuItem('Resume Game', self.on_quit))
        items.append(SubMenuItem('Options', OptionsMenu(layer)))
        items.append(MenuItem('Exit Game', self.on_quit_game))
        self.create_menu(items)
    def on_quit(self):
        # Quitting the menu
        director.pop()
    def on_quit_game(self):
        director.pop()
        Incantus.quit()

class OptionsMenu(IncantusMenu):
    def __init__(self, layer=None):
        super(OptionsMenu, self).__init__('Options')
        items = []
        items.append( ToggleMenuItem('Music: ', self.on_music, soundfx.toggle_music) )
        items.append( ToggleMenuItem('Sound Effects: ', self.on_soundfx, soundfx.toggle_fx) )
        items.append( MultipleMenuItem(
                        'Music volume: ',
                        self.on_music_volume,
                        ['Mute','10','20','30','40','50','60','70','80','90','100'],
                        int(soundfx.music_volume * 10) )
                    )
        items.append( MultipleMenuItem(
                        'Sound volume: ',
                        self.on_sound_volume,
                        ['Mute','10','20','30','40','50','60','70','80','90','100'],
                        int(soundfx.sound_volume * 10) )
                    )
        items.append( ToggleMenuItem('Show FPS: ', self.on_show_fps, director.show_FPS) )
        items.append( ToggleMenuItem('Fullscreen: ', self.on_fullscreen, director.window.fullscreen) )
        items.append( MenuItem('Back', self.on_quit) )
        self.layer = layer
        self.create_menu(items)
    def on_fullscreen( self, value ):
        director.window.set_fullscreen( value )
    def on_show_fps( self, value ):
        director.show_FPS = value
    def on_music_volume( self, idx ):
        vol = idx / 10.0
        soundfx.music_volume = vol
        if self.layer:
            self.layer.soundfx.update_music_volume()
    def on_sound_volume( self, idx ):
        vol = idx / 10.0
        soundfx.sound_volume = vol
    def on_music( self, value ):
        soundfx.toggle_music = value
    def on_soundfx( self, value ):
        soundfx.toggle_fx = value

class NetworkGameMenu(IncantusMenu):
    def __init__(self, title):
        super(NetworkGameMenu, self).__init__(title)
        self.player_name = config.get("main", "playername")
        self.host = config.get("network", "server")
        self.port = int(config.get("network", "port"))
        self.deckfile = config.get("main", "deckfile")
        self.avatar = config.get("main", "avatar")
        self.flashing = False
        #self.flash_action = Repeat(FadeOut(1)+FadeIn(1))
    def on_name(self, name):
        self.player_name = name
    def on_port(self, port):
        if port: self.port = int(port)
    def on_host(self, host):
        self.host = host
    def on_deckfile(self, deckfile):
        self.deckfile = deckfile
    def on_join(self):
        decklist = Incantus.load_deckfile(self.deckfile)
        avatar_data = Incantus.load_avatar(self.avatar)
        defrd = Incantus.join_game(self.player_name, decklist, avatar_data, self.host, self.port)
        #defrd.addCallback(lambda x: self.parent.parent.switch_to(1))
        #defrd.addErrback(lambda x: self.stop_flashing())
        #self.flash()
    def on_key_press(self, symbol, modifiers):
        if not self.flashing: return super(NetworkGameMenu, self).on_key_press(symbol, modifiers)
        elif symbol == key.ESCAPE:
            # XXX Cancel the network join
            self.on_quit()
            return True
    def on_mouse_release(self, x, y, buttons, modifiers):
        if not self.flashing: return super(NetworkGameMenu, self).on_mouse_release(x, y, buttons, modifiers)
    def on_mouse_motion( self, x, y, dx, dy ):
        if not self.flashing: return super(NetworkGameMenu, self).on_mouse_motion(x, y, dx, dy)
    def on_exit(self):
        super(NetworkGameMenu, self).on_exit()
        #self.stop_flashing()
    def stop_flashing(self):
        if self.flashing:
            self.flash_item.remove_action(self.flash_action)
            self.flashing = False
    def flash(self):
        self.flashing = True
        self.flash_item.do(self.flash_action)

class StartGameMenu(NetworkGameMenu):
    def __init__(self):
        super(StartGameMenu, self).__init__('New Game')
        self.flash_item = MenuItem('Create', self.on_create)
        self.num_players = 2
        items = []
        items.append(self.flash_item)
        items.append(EntryMenuItem('Name:', self.on_name, self.player_name))
        items.append(EntryMenuItem('Deck file:', self.on_deckfile, self.deckfile))
        items.append(EntryMenuItem('Port:', self.on_port, str(self.port)))
        #items.append(MultipleMenuItem(
        #    'Number of Players:',
        #    self.on_num_players,
        #    ['2', '3', '4'],
        #    0)
        #)
        items.append(MenuItem('Back', self.on_quit))
        self.create_menu(items)
    def on_num_players(self, val): self.num_players = int(val)
    def on_create(self):
        Incantus.start_server(self.port, self.num_players)
        self.on_join()

class JoinGameMenu(NetworkGameMenu):
    def __init__(self):
        super(JoinGameMenu, self).__init__('Join Game')
        self.flash_item = MenuItem('Join', self.on_join)
        items = []
        items.append(self.flash_item)
        items.append(EntryMenuItem('Name:', self.on_name, self.player_name))
        items.append(EntryMenuItem('Deck file:', self.on_deckfile, self.deckfile))
        items.append(EntryMenuItem('Host:', self.on_host, self.host))
        items.append(EntryMenuItem('Port:', self.on_port, str(self.port)))
        items.append(MenuItem('Back', self.on_quit))
        self.create_menu(items)

class ObserveGameMenu(NetworkGameMenu):
    def __init__(self):
        super(ObserveGameMenu, self).__init__('Observe Game')
        self.flash_item = MenuItem('Observe', self.on_join)
        items = []
        items.append(self.flash_item)
        items.append(EntryMenuItem('Name:', self.on_name, self.player_name))
        items.append(EntryMenuItem('Host:', self.on_host, self.host))
        items.append(EntryMenuItem('Port:', self.on_port, str(self.port)))
        items.append(MenuItem('Back', self.on_quit))
        self.create_menu(items)
    def on_join(self):
        defrd = Incantus.observe_game(self.player_name, self.host, self.port)
        defrd.addCallback(lambda x: self.parent.parent.switch_to(1))
        defrd.addErrback(lambda x: self.stop_flashing())
        self.flash()

class SolitaireGameMenu(IncantusMenu):
    def __init__(self):
        super(SolitaireGameMenu, self).__init__('Solitaire Game')
        self.p1_name = config.get("main", "playername")
        self.p2_name = config.get("solitaire", "playername")
        self.p1_deckfile = config.get("main", "deckfile")
        self.p2_deckfile = config.get("solitaire", "deckfile")
        self.p1_avatar = config.get("main", "avatar")
        self.p2_avatar = config.get("solitaire", "avatar")
        items = []
        items.append(MenuItem('Start', self.on_start))
        items.append(EntryMenuItem('Player 1 Name:', lambda v: self.on_name(1, v), self.p1_name))
        items.append(EntryMenuItem('Player 1 Deck file:', lambda v: self.on_deckfile(1, v), self.p1_deckfile))
        items.append(EntryMenuItem('Player 1 Avatar:', lambda v: self.on_avatar(1, v), self.p1_avatar))
        items.append(EntryMenuItem('Player 2 Name:', lambda v: self.on_name(2, v), self.p2_name))
        items.append(EntryMenuItem('Player 2 Deck file:', lambda v: self.on_deckfile(2, v), self.p2_deckfile))
        items.append(EntryMenuItem('Player 2 Avatar:', lambda v: self.on_avatar(2, v), self.p2_avatar))
        items.append(MenuItem('Back', self.on_quit))
        self.create_menu(items)
    def on_name(self, num, val):
        varname = "p%d_name"%num
        setattr(self, varname, val)
    def on_deckfile(self, num, val):
        varname = "p%d_deckfile"%num
        setattr(self, varname, val)
    def on_avatar(self, num, val):
        varname = "p%d_avatar"%num
        setattr(self, varname, val)
    def on_start(self):
        players = [(self.p1_name, Incantus.load_deckfile(self.p1_deckfile), Incantus.load_avatar(self.p1_avatar)), 
                   (self.p2_name, Incantus.load_deckfile(self.p2_deckfile), Incantus.load_avatar(self.p2_avatar))]
        Incantus.start_solitaire(self.p1_name, players)

class ReloadSolitaireGameMenu(IncantusMenu):
    def __init__(self):
        super(ReloadSolitaireGameMenu, self).__init__('Reload Solitaire Game')
        self.replay_file = config.get("general", "replay")
        items = []
        items.append(MenuItem('Reload', self.on_reload))
        items.append(EntryMenuItem('Replay File:', self.on_replayfile, self.replay_file))
        items.append(MenuItem('Back', self.on_quit))
        self.create_menu(items)
    def on_replayfile(self, replay):
        self.replay_file = replay
    def on_reload(self):
        Incantus.reload_solitaire(self.replay_file)
