import random
from GameObjects import MtGObject
from GameEvent import CardLeavingZone, CardEnteringZone, CardLeftZone, CardEnteredZone, CardCeasesToExist, TimestepEvent, ShuffleEvent

class Zone(MtGObject):
    def __init__(self):
        self.cards = []
    def __str__(self):
        return self.name
    def __len__(self):
        return len(self.cards)
    def __iter__(self):
        # Top of the cards is the end of the list
        return iter(self.get())
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
    def cease_to_exist(self, card):
        self.cards.remove(card)
        card.zone = None
        self.send(CardCeasesToExist(), card=card)
    def _remove_card(self, card):
        self.cards.remove(card)
        card.zone = None
        self.send(CardLeftZone(), card=card)
    def _add_card(self, card, position=-1):
        if position == -1: self.cards.append(card)
        else: self.cards.insert(position, card)
        card.zone = self
        self.send(CardEnteredZone(), card=card)
    def move_card(self, card, position=-1):
        self.send(CardEnteringZone(), card=card)
        old_zone = card.zone
        old_zone.send(CardLeavingZone(), card=card)
        old_zone.before_card_removed(card)
        self.before_card_added(card)
        # Remove card from previous zone
        old_zone._remove_card(card)
        self._add_card(card, position)
    # The next 2 are for zones to setup and takedown card roles
    def before_card_added(self, card): pass
    def before_card_removed(self, card): pass

class OrderedZone(Zone):
    def __init__(self):
        super(OrderedZone, self).__init__()
        self.pending = False
        self.pending_top = []
        self.pending_bottom = []
        self.register(self.commit, TimestepEvent())
    def _add_card(self, card, position=-1):
        self.pending = True
        if position == -1: self.pending_top.append(card)
        else: self.pending_bottom.append(card)
    def get_card_order(self, cardlist, pos):
        if len(cardlist) > 1:
            player = cardlist[0].owner
            reorder = player.getCardSelection(cardlist, len(cardlist), from_zone=str(self), from_player=player, required=False, prompt="Order cards entering %s of %s"%(pos, self))
            if reorder: cardlist = reorder[::-1]
        return cardlist
    def pre_commit(self): pass
    def post_commit(self): pass
    def commit(self):
        if self.pending_top or self.pending_bottom:
            self.pre_commit()
            toplist = self.get_card_order([c for c in self.pending_top], "top")
            bottomlist = self.get_card_order([c for c in self.pending_bottom], "bottom")
            self.cards = bottomlist + self.cards + toplist
            for card in self.pending_top+self.pending_bottom:
                card.zone = self
                self.send(CardEnteredZone(), card=card)
            self.pending_top[:] = []
            self.pending_bottom[:] = []
            self.post_commit()
            self.pending = False

class Play(OrderedZone):
    name = "play"
    def before_card_added(self, card):
        card.current_role = card.in_play_role
        card.current_role.enteringPlay()
    def before_card_removed(self, card):
        card.save_lki()
        card.current_role.leavingPlay()

class OutPlayMixin(object):
    def before_card_added(self, card):
        card.current_role = card.out_play_role

class Library(OutPlayMixin, OrderedZone):
    def __init__(self):
        super(Library, self).__init__()
        self.needs_shuffle = False
        self.ordering = True
    def enable_ordering(self):
        self.ordering = True
    def disable_ordering(self):
        self.ordering = False
    def add_card(self, card, position=-1):
        self.send(CardEnteringZone(), card=card)
        self.before_card_added(card)
        self._add_card_unordered(card, position)
    def _add_card_unordered(self, card, position):
        # XXX Same as Zone._add_card
        if position == -1: self.cards.append(card)
        else: self.cards.insert(position, card)
        card.zone = self
        self.send(CardEnteredZone(), card=card)
    def _add_card(self, card, position=-1):
        if self.ordering:
            super(Library, self)._add_card(card, position)
        else:
            self._add_card_unordered(card, position)
    def shuffle(self):
        if not self.pending: random.shuffle(self.cards)
        else: self.needs_shuffle = True
    def pre_commit(self):
        if self.needs_shuffle:
            self.needs_shuffle = False
            random.shuffle(self.cards)
            self.send(ShuffleEvent())
    name = "library"

class Graveyard(OutPlayMixin, OrderedZone):
    name = "graveyard"
    def before_card_added(self, card):
        super(Graveyard, self).before_card_added(card)
        card.current_role.enteringGraveyard()
    def before_card_removed(self, card):
        card.current_role.leavingGraveyard()

class Hand(OutPlayMixin, Zone):
    name = "hand"
class Removed(OutPlayMixin, Zone):
    name = "removed"
