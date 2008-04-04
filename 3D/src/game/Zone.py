
import random
from GameObjects import MtGObject
from GameEvent import CardLeavingZone, CardEnteringZone, CardLeftZone, CardEnteredZone

class Zone(MtGObject):
    def __init__(self, cards=None, order=False):
        if not cards: cards = []
        self.cards = cards
        self.order = False
        for card in self.cards: card.zone = self
    def __len__(self):
        return len(self.cards)
    #def __getitem__(self, index):
    #    return self.cards[index]
    def __iter__(self):
        # Top of the cards is the end of the list
        return iter(self.get())
    def __str__(self): return str(self.__class__.__name__)
    def top(self, number=1):
        if len(self) == 0: return None
        else:
            if number == 1: return self.cards[-1]
            else: return self.cards[:-(number+1):-1]
    def bottom(self, number=1):
        if len(self) == 0: return None
        else: return self.cards[:number]
    def get(self, match=lambda c: True):
        # Retrieve all of a type of Card in current location
        return [card for card in iter(self.cards[::-1]) if match(card)]
    def remove_card(self, card, trigger=True):
        self.before_card_removed(card)
        # All zones do this the same
        if trigger == True: self.send(CardLeavingZone(), card=card)
        self.cards.remove(card)
        card.zone = None
        if trigger == True: self.send(CardLeftZone(), card=card)
        self.after_card_removed(card)
    def add_card(self, card, position=-1, trigger=True):
        self.before_card_added(card)
        if trigger == True: self.send(CardEnteringZone(), card=card)
        if position == -1: self.cards.append(card)
        else: self.cards.insert(position, card)
        card.zone = self
        if trigger == True: self.send(CardEnteredZone(), card=card)
        self.after_card_added(card)
    def move_card(self, card, from_zone, position=-1):
        # This function always triggers entering and leaving events
        self.before_card_added(card)
        self.send(CardEnteringZone(), card=card)
        # Remove card from previous zone
        from_zone.remove_card(card, trigger=True)
        if position == -1: self.cards.append(card)
        else: self.cards.insert(position, card)
        card.zone = self
        self.send(CardEnteredZone(), card=card)
        self.after_card_added(card)
    # The next four are for subclasses to define for additional processing before sending an Event signal
    def before_card_added(self, card): pass
    def after_card_added(self, card): pass
    def before_card_removed(self, card): pass
    def after_card_removed(self, card): pass

# XXX One would think that when the card leaves play all it's triggered and static abilities cease
# to exist - but there is a brief time when they can exist. For example, whenever a card goes into a
# graveyard, Planar Chaos removes that card from the game. It also triggers on itself going to a graveyard
# The only way this works is that the current_role switches to the out play role after it's entered the
# other zone. So the out play role is set when the card is added to the other zone
class Play(Zone):
    def before_card_added(self, card): card.current_role = card.in_play_role
    def __str__(self): return "play"

class OutPlayZone(Zone):
    def after_card_added(self, card):
        # Maintain the in_play role as long as possible if it was added from play
        card.current_role = card.out_play_role

class Library(OutPlayZone):
    def __init__(self, cards=None):
        super(Library,self).__init__(cards,order=True)
    def shuffle(self):
        random.shuffle(self.cards)
    def __str__(self): return "library"

class Graveyard(OutPlayZone):
    def __init__(self, cards=[]):
        super(Graveyard,self).__init__(cards, order=True)
    def __str__(self): return "graveyard"

class Hand(OutPlayZone):
    def __str__(self): return "hand"
class Removed(OutPlayZone):
    def __str__(self): return "removed"
