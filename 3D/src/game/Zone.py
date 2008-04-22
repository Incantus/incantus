
import random
from GameObjects import MtGObject
from GameEvent import CardLeavingZone, CardEnteringZone, CardLeftZone, CardEnteredZone, TimestepEvent

class Zone(MtGObject):
    def __init__(self, cards=None):
        if not cards: cards = []
        self.cards = cards
        for card in self.cards: card.zone = self
    def __len__(self):
        return len(self.cards)
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
        self.add_card_pre(card, trigger)
        self.add_card_post(card, position, trigger)
    def add_card_pre(self, card, trigger=True):
        self.before_card_added(card)
        if trigger == True: self.send(CardEnteringZone(), card=card)
    def add_card_post(self, card, position=-1, trigger=True):
        if position == -1: self.cards.append(card)
        else: self.cards.insert(position, card)
        card.zone = self
        if trigger == True: self.send(CardEnteredZone(), card=card)
        self.after_card_added(card)
    def move_card(self, card, from_zone, position=-1):
        # This function always triggers entering and leaving events
        self.add_card_pre(card)
        # Remove card from previous zone
        from_zone.remove_card(card, trigger=True)
        self.add_card_post(card, position)
    # The next four are for subclasses to define for additional processing before sending an Event signal
    def before_card_added(self, card): pass
    def after_card_added(self, card): pass
    def before_card_removed(self, card): pass
    def after_card_removed(self, card): pass
    def __str__(self): return self.zone_name

# XXX One would think that when the card leaves play all it's triggered and static abilities cease
# to exist - but there is a brief time when they can exist. For example, whenever a card goes into a
# graveyard, Planar Chaos removes that card from the game. It also triggers on itself going to a graveyard
# The only way this works is that the current_role switches to the out play role after it's entered the
# other zone. So the out play role is set when the card is added to the other zone
# (4/22/08) this no longer applies
class Play(Zone):
    zone_name = "play"
    def before_card_added(self, card): card.current_role = card.in_play_role

class OutPlayZone(Zone):
    #def after_card_added(self, card):
    def before_card_added(self, card):
        # Maintain the in_play role as long as possible if it was added from play
        card.current_role = card.out_play_role

class OrderedOutPlayZone(OutPlayZone):
    def __init__(self, cards=[]):
        super(OrderedOutPlayZone, self).__init__(cards)
        self.pending = False
        self.pending_top = []
        self.pending_bottom = []
    def init(self):
        self.register(self.commit, TimestepEvent())
    def add_card_post(self, card, position=-1, trigger=True):
        self.pending = True
        if position == -1: self.pending_top.append((card, trigger))
        else: self.pending_bottom.append((card, trigger))
    def _get_order(self, cardlist, pos):
        if len(cardlist) > 1:
            player = cardlist[0].owner
            reorder = player.getCardSelection(cardlist, len(cardlist), from_zone=str(self), from_player=player, required=False, prompt="Order cards entering %s of %s"%(pos, self))
            if reorder: cardlist = reorder
        return cardlist
    def pre_commit(self): pass
    def post_commit(self): pass
    def commit(self):
        if self.pending_top or self.pending_bottom:
            self.pre_commit()
            toplist = self._get_order([c[0] for c in self.pending_top], "top")
            bottomlist = self._get_order([c[0] for c in self.pending_bottom], "bottom")
            self.cards = bottomlist[::-1] + self.cards + toplist[::-1]
            for card in toplist+bottomlist:
                trigger = True
                card.zone = self
                if trigger == True: self.send(CardEnteredZone(), card=card)
                self.after_card_added(card)
            self.pending_top[:] = []
            self.pending_bottom[:] = []
            self.post_commit()
            self.pending = False

class Library(OrderedOutPlayZone):
    def __init__(self, cards=[]):
        super(Library, self).__init__(cards)
        self.needs_shuffle = False
    def setup_card(self, card):
        self.before_card_added(card)
        self.send(CardEnteringZone(), card=card)
        self.cards.append(card)
        card.zone = self
        self.send(CardEnteredZone(), card=card)
        self.after_card_added(card)
    def shuffle(self):
        if not self.pending: random.shuffle(self.cards)
        else: self.needs_shuffle = True
    def post_commit(self):
        if self.needs_shuffle:
            self.needs_shuffle = False
            random.shuffle(self.cards)
    zone_name = "library"

class Graveyard(OrderedOutPlayZone):
    zone_name = "graveyard"

class Hand(OutPlayZone):
    zone_name = "hand"
class Removed(OutPlayZone):
    zone_name = "removed"
