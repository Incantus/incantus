# This file should always be imported at module level scope

import pyglet
import sys, glob, os, string
import urllib
import bsddb
from cStringIO import StringIO
from lrucache import LRUCache

from card import Card, PlayCard, HandCard, StackCard

#token_img_info = [("10e", ["Soldier","Zombie","Dragon","Goblin","Saproling","Wasp"]),
#("lorwyn",["Avatar","Elemental","Kithkin Soldier","Merfolk Wizard","Goblin Rogue","Elemental Shaman","Beast","Elemental","Elf Warrior","Wolf","Shapeshifter"]),
#("morningtide",["Giant Warrior","Faerie Rogue","Treefolk Shaman"]),
#("dueldecks",["Elemental","Elf Warrior","Goblin"]),
#("shadowmoor",["Kithkin Soldier","Spirit","Rat","Elemental","Elf Warrior","Spider","Wolf","Faerie Rogue","Elemental","Giant Warrior","Goblin Warrior","Elf Warrior"]),]
#token_cards = {}
#for ed, names in token_img_info:
#    for i,n in enumerate(names):
#        token_cards[n] = (ed,i+1)

class _CardLibrary:
    img_cache = LRUCache(size=50)

    def __init__(self):
        self.cardfile = bsddb.hashopen("./data/card_images.db", "c")
        self.back = pyglet.resource.texture("back.jpg")
        self.notfound = pyglet.resource.texture("notfound.jpg")
        self.combat = pyglet.resource.texture("combat.png")
        self.triggered = pyglet.resource.texture("triggered.png")
        self.activated = pyglet.resource.texture("activated.png")

        # XXX This is a hack
        Card.build_fbo()

    def close(self):
        self.cardfile.close()

    def retrieveCardImages(self, cardlist):
        for name in cardlist:
            if not name in self.cardfile:
                imagename = name.replace(" ", "_").replace("-", "_").replace("'","").replace(",","")
                img_file = urllib.urlopen("http://www.wizards.com/global/images/magic/general/%s.jpg"%imagename)
                data = img_file.read()
                img_file.close()
                self.cardfile[name] = data

    def loadImage(self, name):
        name, cardtype = name.split(":")
        table = string.maketrans(" -", "__")
        imagename = name.translate(table, "',")
        altname = name.replace(" ", "_").replace("'","").replace(",","")
        if name in self.cardfile: data = self.cardfile[name]
        else:
            if cardtype == "Token":
                imgname = name.replace("/","-").replace(" ","_").replace("*","X")
                if os.path.exists("./data/tokenimg/%s.jpg"%imgname):
                    img_file = file("./data/tokenimg/%s.jpg"%imgname, 'rb')
                    data = img_file.read()
                    img_file.close()
                else: return self.back
            else:
                # Try local directory
                local_path = "./data/cardimg/%s.jpg"%imagename
                if os.path.exists(local_path):
                    img_file = file(local_path, 'rb')
                    data = img_file.read()
                    img_file.close()
                else: # Get it from wizards
                    try:
                        img_file = urllib.urlopen("http://www.wizards.com/global/images/magic/general/%s.jpg"%imagename)
                        data = img_file.read()
                        img_file.close()
                        if "<HTML>" in data or "<h1>Service Unavailable</h1>" in data:
                            img_file = urllib.urlopen("http://www.wizards.com/global/images/magic/general/%s.jpg"%altname)
                            data = img_file.read()
                            img_file.close()
                            if "<HTML>" in data or "<h1>Service Unavailable</h1>" in data: return self.notfound
                            else: self.cardfile[name] = data
                        else: self.cardfile[name] = data
                    except:
                        print sys.exc_info()
                        return self.notfound
        return pyglet.image.load(imagename, file=StringIO(data)).texture

    def getCard(self, gamecard, card_cls=Card):
        key = gamecard.key
        name = img_key = key[1]
        if img_key in self.img_cache: cardImage, orig = self.img_cache[img_key]
        else:
            orig = self.loadImage(name)

            cardImage = pyglet.image.Texture.create(orig.width, orig.height)
            card_cls._render(cardImage, orig, gamecard, tiny=True)

            self.img_cache[img_key] = (cardImage, orig)
        card = card_cls(gamecard, cardImage, self.back)
        card._art = orig
        return card

    def getStackCard(self, gamecard, text="", style="regular"):
        card = self.getCard(gamecard)
        return StackCard(card.gamecard, card.front, card.back, card._art, text, style)
    def getActivatedCard(self, gamecard, text):
        return self.getStackCard(gamecard, text, style="activated")
    def getTriggeredCard(self, gamecard, text):
        return self.getStackCard(gamecard, text, style="triggered")

    def getHandCard(self, gamecard):
        return self.getCard(gamecard,HandCard)

    def getPlayCard(self, gamecard):
        card = self.getCard(gamecard,PlayCard)
        return card

    def getCombatCard(self, ability):
        return Card(ability.source, self.combat, self.combat)

    def getCardBack(self, size="default"):
        return self.back

    # XXX These are old - notice they still call pygame
    def load_card_counters(self):
        counter_path = "./data/images/counters/"
        counters = glob.glob(counter_path+"*.gif")
        counters = [os.path.splitext(os.path.basename(c))[0] for c in counters]
        self.counter_ico = dict([(c, pygame.image.load("./data/images/counters/%s.gif"%c).convert()) for c in counters])

    def load_card_properties(self):
        #self.smallfont = pygame.font.Font("./data/themes/default/Vera.ttf", 9)
        self.smallfont = pygame.font.Font("./data/themes/default/Inconsolata.otf", 10)
        property_path = "./data/images/properties/"
        status_files = glob.glob(property_path+"*.gif")
        self.status_ico = dict([(os.path.splitext(os.path.basename(s))[0], pygame.image.load(s).convert()) for s in status_files])
        get_attribute = lambda attr, value: lambda card: getattr(card, attr) == value
        get_keyword = lambda keyword: lambda card: keyword in card.keywords
        self.card_status = [] #("targeted", get_attribute("targeted", True)),]
                       #("untargetable", get_attribute("untargetable", True))]
        self.combat_status = [("attacking", get_attribute("attacking", True)),
                         ("blocking", get_attribute("blocking", True)),
                         ("blocked", get_attribute("blocked", True)),
                         ("unblocked", lambda card: getattr(card, "blocked")==False and getattr(card,"attacking")==True)]
        self.creature_status = [("summon", get_attribute("continuously_in_play", False)),
                           ("double-strike", get_keyword("double-strike")),
                           ("protection-from-red", get_keyword("protection-from-red")),
                           ("protection-from-black", get_keyword("protection-from-black")),
                           ("flying", get_keyword("flying")),
                           ("protection-from-white", get_keyword("protection-from-white")),
                           ("trample", get_keyword("trample")),
                           ("haste", get_keyword("haste")),
                           ("protection-from-blue", get_keyword("protection-from-blue")),
                           ("first-strike", get_keyword("first-strike")),
                           ("protection-from-green", get_keyword("protection-from-green"))]

CardLibrary = _CardLibrary()
