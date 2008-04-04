import glob, os
import urllib
import bsddb
from cStringIO import StringIO
from lrucache import LRUCache
import pyglet.image

from card import Card, PlayCard, StackCard

token_img_info = [("10e", ["Soldier","Zombie","Dragon","Goblin","Saproling","Wasp"]),
("lorwyn",["Avatar","Elemental","Kithkin Soldier","Merfolk Wizard","Goblin Rogue","Elemental Shaman","Beast","Elemental","Elf Warrior","Wolf","Shapeshifter"]),
("morningtide",["Giant Warrior","Faerie Rogue","Treefolk Shaman"]),]
token_cards = {}
for ed, names in token_img_info:
    for i,n in enumerate(names):
        token_cards[n] = (ed,i+1)

class _CardLibrary:
    img_cache = LRUCache(size=50)
    card_cache = {}
    play_card_cache = {}
    #datapath = "./data/cards/"
    #cardlists = {}

    def __init__(self):
        self.cardfile = bsddb.hashopen("./data/card_images.db", "c")
        self.back = pyglet.image.load("./data/images/back.jpg").texture
        self.trigger = pyglet.image.load("./data/images/fx/triggered.png").texture
        #tokens = [("white", "W"), ("red", "R"), ("blue", "U"), ("black","B"), ("green","G"), ("white", "C")]
        #self.token_image = dict([(color,pygame.image.load("./data/images/tokens/%s_token.png"%t).convert_alpha()) for t, color in tokens])
        #total = 0
        #for cs in cardsets:
        #    total += self.load_set(cs)

        #self.numberCards = total
        #self.load_card_properties()
        #self.load_card_counters()
        #cardsize = self.getCardSize()
        #self.card_width, self.card_height = cardsize.w, cardsize.h
        #self.overlay = pygame.Surface((cardsize.w, cardsize.h), pygame.SRCALPHA, 32)
        #popup_rect = pygame.rect.Rect((2,52), (cardsize.w-4,39))
        #self.popup = self.overlay.subsurface(popup_rect)

    #def load_set(self, cardset):
    #    import string, operator
    #    cardlist = self.cardfile.read("cards/"+cardset+"/checklist.txt").splitlines()
    #    cardlist = [map(string.strip, c.split("\t")) for c in cardlist if c[0] != "#"]
    #    numCards = len(cardlist)
    #    cardlist = [(int(c[0]), c[1]) for c in cardlist]
    #    cardlist.sort(key=operator.itemgetter(0))
    #    self.cardlists[cardset] = dict(cardlist)
    #    return len(cardlist)

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
        imagename = name.replace(" ", "_").replace("-", "_").replace("'","").replace(",","")
        if name in self.cardfile: data = self.cardfile[name]
        else:
            if name.endswith("Token"):
                token_type = name[:-6] #.split(" ")[:-1]
                if token_type in token_cards:
                    ed, number = token_cards[token_type]
                    img_file = urllib.urlopen("http://magiccards.info/tokens/thumb/%s-%03d.jpg"%(ed,number))
                    data = img_file.read()
                    img_file.close()
                else: return self.back
            else:
                #img_file = urllib.urlopen("http://magiccards.info/scans/en/%s/%d.jpg"%(cardset,number))
                img_file = urllib.urlopen("http://www.wizards.com/global/images/magic/general/%s.jpg"%imagename)
                data = img_file.read()
                img_file.close()
            self.cardfile[name] = data 
        return pyglet.image.load(imagename, file=StringIO(data)).texture

    def getCard(self, gamecard, card_cls=Card, cache=None):
        key = gamecard.key
        if cache == None: cache = self.card_cache
        if key in cache: card = cache[key]
        else:
            name = img_key = key[1]
            if img_key in self.img_cache: cardImage = self.img_cache[img_key]
            else:
                cardImage = self.loadImage(name)
                self.img_cache[img_key] = cardImage
            card = card_cls(gamecard, cardImage, self.back)
            cache[key] = card
        return card

    def getStackCard(self, gamecard, triggered=False):
        card = self.getCard(gamecard)
        stack_card = StackCard(card.gamecard, card.front, card.back, self.trigger, triggered)
        return stack_card

    def getPlayCard(self, gamecard):
        card = self.getCard(gamecard,PlayCard,self.play_card_cache)
        return card

    def getFakeCard(self, ability):
        return Card(ability.card, self.back, self.back)

    def getCardCopy(self, gamecard):
        return self.getCard(gamecard).copy()

    def getCardBack(self, size="default"):
        return self.back

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
