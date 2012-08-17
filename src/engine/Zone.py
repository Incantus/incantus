import random
from MtGObject import MtGObject
from GameObjects import GameObject
from GameEvent import CardEnteringZoneFrom, CardLeftZone, CardEnteredZone, CardCeasesToExist, TimestepEvent, ShuffleEvent

__all__ = ["Zone", "GraveyardZone", "HandZone", "ExileZone", "LibraryZone",
           "BattlefieldZone", "CommandZone"]

all_cards = lambda card: True

class Zone(MtGObject):
    def __init__(self):
        self._cards = []
    def __str__(self):
        return self.name
    def __len__(self):
        return len(self._cards)
    def __iter__(self):
        # Top of the cards is the end of the list
        return iter(self.get())
    def top(self, number=None):
        if number:
            if number < 1 or len(self) == 0: return []
            else: return [c for c in self._cards[:-(number+1):-1]]
        else:
            if len(self) == 0: return None
            else: return self._cards[-1]
    def bottom(self, number=None):
        if number:
            if number < 1 or len(self) == 0: return []
            else: return [c for c in self._cards[:number]]
        else:
            if len(self) == 0: return None
            else: return self._cards[0]
    def get(self, match=all_cards):
        # Retrieve all of a type of Card in current location
        return [card for card in iter(self._cards[::-1]) if match(card)]
    def _remove_card(self, card, event=CardLeftZone()):
        self._cards.remove(card)
        self.send(event, card=card)
    def _insert_card(self, oldcard, card, position):
        # Remove card from previous zone
        oldcard.zone._remove_card(oldcard)
        oldcard.leavingZone()
        card.enteringZone(self)
        if position == "top": self._cards.append(card)
        elif position == "bottom": self._cards.insert(0, card)
        else: self._cards.insert(position, card)
        self.send(CardEnteredZone(), card=card)
    def move_card(self, card, position):
        newcard = self.setup_new_role(card)
        self.send(CardEnteringZoneFrom(), from_zone=card.zone, oldcard=card, newcard=newcard)
        # Give the old role a chance to modify the new role
        card.modifyNewRole(newcard, self)
        self._insert_card(card, newcard, position)
        return newcard
    def setup_new_role(self, card):
        raise NotImplementedError()

class OrderedZone(Zone):
    pending = property(fget=lambda self: self._pending)
    def __init__(self):
        super(OrderedZone, self).__init__()
        self._pending = False
        self._pending_top = []
        self._pending_bottom = []
        self.register(self.commit, TimestepEvent())
    def _insert_card(self, oldcard, card, position):
        self._pending = True
        if position == "top": self._pending_top.append((oldcard, card))
        else: self._pending_bottom.append((oldcard, card))
    def get_card_order(self, cardlist, pos):
        if len(cardlist) > 1:
            player = cardlist[0].owner
            reorder = player.getCardSelection(cardlist, number=len(cardlist), zone=str(self), player=player, required=False, prompt="Order cards entering %s of %s"%(pos, self))
            if reorder: cardlist = reorder[::-1]
        return cardlist
    def commit(self):
        if self._pending_top or self._pending_bottom:
            cards = self._pending_top+self._pending_bottom
            for oldcard, _ in cards:
                oldcard.zone._remove_card(oldcard)
            for oldcard, card in cards:
                oldcard.leavingZone()
                card.enteringZone(self)
            toplist = self.get_card_order([c for o,c in self._pending_top], "top")
            bottomlist = self.get_card_order([c for o,c in self._pending_bottom], "bottom")
            self._cards = bottomlist + self._cards + toplist
            for _, card in cards:
                self.send(CardEnteredZone(), card=card)
            self._pending_top[:] = []
            self._pending_bottom[:] = []
            self._pending = False

class NonBattlefieldMixin(object):
    def setup_new_role(self, card):
        cardtmpl = GameObject._cardmap[card.key]
        return cardtmpl.new_role(cardtmpl.out_battlefield_role)
    def cease_to_exist(self, card):
        self._remove_card(card, CardCeasesToExist())
        card.leavingZone()
        del GameObject._cardmap[card.key]

class AddCardsMixin(object):
    def add_new_card(self, card):
        card.enteringZone(self)
        self._cards.append(card)
        self.send(CardEnteredZone(), card=card)
        return card

class GraveyardZone(NonBattlefieldMixin, OrderedZone):
    name = "graveyard"

class HandZone(NonBattlefieldMixin, Zone):
    name = "hand"

class ExileZone(NonBattlefieldMixin, AddCardsMixin, Zone):
    name = "exile"

class LibraryZone(NonBattlefieldMixin, AddCardsMixin, OrderedZone):
    name = "library"
    def __init__(self):
        super(LibraryZone, self).__init__()
        self.skip_ordering = False
    def get_card_order(self, cardlist, pos):
        # we're gonna shuffle anyway, no need to order the cards
        if self.skip_ordering: return cardlist
        else: return super(LibraryZone, self).get_card_order(cardlist, pos)
    def shuffle(self):
        # If we have any pending insertions, move them to the library
        # before shuffling
        if self.pending:
            # don't need to order them
            self.skip_ordering = True
            self.commit()
            self.skip_ordering = False
        random.shuffle(self._cards)
        self.send(ShuffleEvent())

class BattlefieldZone(OrderedZone):
    name = "battlefield"
    def __init__(self, game):
        self.game = game
        super(BattlefieldZone, self).__init__()
    def get_view(self, player):
        return BattlefieldView(player, self)
    def get_card_order(self, cardlist, pos):
        if len(cardlist) > 1:
            # Sort the cards
            player_cards = dict([(player, []) for player in self.game.players])
            for card in cardlist:
                player_cards[card.controller].append(card)
            cardlist = []
            for player in self.game.players:
                cards = player_cards[player]
                if len(cards) > 1:
                    cards = player.getCardSelection(cards, number=len(cards), zone=str(self), player=player, prompt="Order cards entering %s"%(self))
                    cards.reverse()
                cardlist.extend(cards)
        return cardlist
    def setup_new_role(self, card):
        cardtmpl = GameObject._cardmap[card.key]
        return cardtmpl.new_role(cardtmpl.in_battlefield_role)

class BattlefieldView(object):
    def __init__(self, player, battlefield):
        self.player = player
        self.battlefield = battlefield
    def __iter__(self):
        # Top of the cards is the end of the list
        return iter(self.get())
    def __len__(self):
        return len(self.get())
    def get(self, match=all_cards, all=False):
        cards = self.battlefield.get(match)
        if not all: cards = [card for card in cards if card.controller == self.player]
        return cards
    #def __getattr__(self, attr):
    #    return getattr(self.battlefield, attr)
    def move_card(self, card, position="top"):
        card = self.battlefield.move_card(card, position)
        card.initialize_controller(self.player)
        return card
    def __str__(self): return "battlefield"

class CommandZone(NonBattlefieldMixin, AddCardsMixin, OrderedZone):
    name = "command"
