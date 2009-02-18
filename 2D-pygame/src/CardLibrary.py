import glob, os
from cStringIO import StringIO
import pygame
from PIL import Image
from lrucache import LRUCache
import game

class _CardLibrary:
    card_cache = LRUCache(size=50)
    card_large_cache = LRUCache(size=50)
    back_cache = {}
    #datapath = "./data/cards/"
    cardlists = {}

    cardfile = game.CardLibrary.CardLibrary.cardfile

    def __init__(self):
        #cardsets = [s.strip() for s in file(self.datapath+"cardsets").readlines()]
        cardsets = [s.strip() for s in self.cardfile.read("cards/cardsets").splitlines()]
        self.back = pygame.image.load("./data/images/back.jpg")
        tokens = [("white", "W"), ("red", "R"), ("blue", "U"), ("black","B"), ("green","G"), ("white", "C")]
        self.token_image = dict([(color,pygame.image.load("./data/images/tokens/%s_token.png"%t).convert_alpha()) for t, color in tokens])
        total = 0
        for cs in cardsets:
            total += self.load_set(cs)

        self.numberCards = total
        self.load_card_properties()
        self.load_card_counters()
        cardsize = self.getCardSize()
        self.card_width, self.card_height = cardsize.w, cardsize.h
        self.overlay = pygame.Surface((cardsize.w, cardsize.h), pygame.SRCALPHA, 32)
        popup_rect = pygame.rect.Rect((2,52), (cardsize.w-4,39))
        self.popup = self.overlay.subsurface(popup_rect)

    def load_set(self, cardset):
        import string, operator
        #cardlist = file(self.datapath+cardset+"/checklist.txt").readlines()
        cardlist = self.cardfile.read("cards/"+cardset+"/checklist.txt").splitlines()
        cardlist = [map(string.strip, c.split("\t")) for c in cardlist if c[0] != "#"]
        numCards = len(cardlist)
        cardlist = [(int(c[0]), c[1]) for c in cardlist]
        cardlist.sort(key=operator.itemgetter(0))
        self.cardlists[cardset] = dict(cardlist) #map(operator.itemgetter(1), cardlist)

        # Load all the small ones, only load large on demand
        #numberCards = 0
        #for number, name in cardlist:
        #    name = name.strip().replace(" ", "_")
        #    cardimage = pygame.image.load(self.datapath+cardset+"/small/%d_%s.jpg" %(number,name))#.convert()
        #    w, h = cardimage.get_size()
        #    self.card_cache[(cardset,number)] = cardimage
        #    numberCards += 1
        return len(cardlist)

    def getCardSize(self, type="small"):
        #if type == "small": cardImage = self.card_cache.values()[0]
        #return cardImage.get_rect()
        if type == "small": return pygame.rect.Rect((0,0), (65,93))
        else: return pygame.rect.Rect((0,0), ())

    def getCard(self, key, type="small", size=None):
        if key:
            if len(key) == 3:
                cardset, number = key[1:]
                name = self.cardlists[cardset][number].replace(" ", "_")
                imagename = "cards/%s/%s/%d_%s.jpg"%(cardset,type,number,name)
                if type == "small": 
                    #cardImage = self.card_cache[(cardset,number)]
                    if key in self.card_cache: cardImage = self.card_cache[key]
                    else:
                        #cardImage = self.resizeCard(self.getCard(key, "large"), (65,93))
                        cardImage = pygame.image.load(StringIO(self.cardfile.read(imagename)), imagename).convert()
                        #cardImage = pygame.image.load(self.datapath+"%s/%s/%d_%s.jpg" %(cardset,type,number,name)).convert()
                        self.card_cache[key] = cardImage
                elif type == "large":
                    # Check the large image cache
                    if key in self.card_large_cache: cardImage = self.card_large_cache[key]
                    else:
                        cardImage = pygame.image.load(StringIO(self.cardfile.read(imagename)), imagename).convert()
                        #cardImage = pygame.image.load(self.datapath+"%s/%s/%d_%s.jpg" %(cardset,type,number,name)).convert()
                        if size and not size==cardImage.get_size(): cardImage = self.resizeCard(cardImage, size)
                        self.card_large_cache[key] = cardImage
                return cardImage
            else:
                return self.token_image[key[1]]
        else: return None

    def getCardTapped(self, key):
        if len(key) == 3:
            return pygame.transform.rotate(self.getCard(key), -90)
        else: return pygame.transform.rotate(self.token_image[key[1]], -90)

    def resizeCard(self, cardimage, size):
        #imgstr = pygame.image.tostring(cardimage, "RGBX")
        #temp = Image.fromstring("RGBX", cardimage.get_size(), imgstr)
        #temp = temp.resize(size, Image.BICUBIC) #Image.ANTIALIAS)
        #cardimage = pygame.image.fromstring(temp.tostring(), temp.size, temp.mode)
        cardimage = pygame.transform.scale(cardimage, size)
        return cardimage

    def getCardBack(self, size="default"):
        if size=="default": backImage = self.getCardBack(size=(self.card_width, self.card_height))
        else:
            # make sure we aren't asking for the original
            w, h = self.back.get_size()
            if w == size[0] and h == size[1]:
                backImage = self.back
            else:
                # check cache
                backImage = self.back_cache.get(tuple(size), None)
                if not backImage:
                    backImage = pygame.transform.scale(self.back, size)
                    self.back_cache[tuple(size)] = backImage
        return backImage
       
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
