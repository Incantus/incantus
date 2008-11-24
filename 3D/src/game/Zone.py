import random
from GameObjects import MtGObject, GameObject
from GameEvent import CardEnteringZoneFrom, CardLeftZone, CardEnteredZone, CardCeasesToExist, TimestepEvent, ShuffleEvent

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
    def get(self, match=lambda c: True):
        # Retrieve all of a type of Card in current location
        return [card for card in iter(self._cards[::-1]) if match(card)]
    def cease_to_exist(self, card):
        self._remove_card(card, CardCeasesToExist())
        del GameObject._cardmap[card.key]
    def _remove_card(self, card, event=CardLeftZone()):
        self._cards.remove(card)
        card.zone = None
        self.send(event, card=card)
        self.after_card_removed(card)
    def _insert_card(self, oldcard, card, position):
        # Remove card from previous zone
        if oldcard.zone: oldcard.zone._remove_card(oldcard)
        self.before_card_added(card)
        if position == "top": self._cards.append(card)
        elif position == "bottom": self._cards.insert(0, card)
        else: self._cards.insert(position, card)
        card.zone = self
        self.send(CardEnteredZone(), card=card)
    def move_card(self, card, position):
        newcard = self.setup_new_role(card)
        if card.zone:
            self.send(CardEnteringZoneFrom(), from_zone=card.zone, oldcard=card, newcard=newcard)
        self._insert_card(card, newcard, position)
        return newcard
    # The next 2 are for zones to setup and takedown card roles
    def before_card_added(self, card):
        card.enteringZone(self.name)
    def after_card_removed(self, card):
        card.leavingZone(self.name)
    def setup_new_role(self, card):
        raise NotImplementedError()

class OrderedZone(Zone):
    def __init__(self):
        super(OrderedZone, self).__init__()
        self.pending = False
        self.pending_top = []
        self.pending_bottom = []
        self.register(self.commit, TimestepEvent())
    def _insert_card(self, oldcard, card, position):
        self.pending = True
        if position == "top": self.pending_top.append((oldcard, card))
        else: self.pending_bottom.append((oldcard, card))
    def get_card_order(self, cardlist, pos):
        if len(cardlist) > 1:
            player = cardlist[0].owner
            reorder = player.getCardSelection(cardlist, number=len(cardlist), zone=str(self), player=player, required=False, prompt="Order cards entering %s of %s"%(pos, self))
            if reorder: cardlist = reorder[::-1]
        return cardlist
    def pre_commit(self): pass
    def post_commit(self): pass
    def commit(self):
        if self.pending_top or self.pending_bottom:
            self.pre_commit()
            for oldcard, card in self.pending_top+self.pending_bottom:
                if oldcard.zone: oldcard.zone._remove_card(oldcard)
                self.before_card_added(card)
            toplist = self.get_card_order([c for o,c in self.pending_top], "top")
            bottomlist = self.get_card_order([c for o,c in self.pending_bottom], "bottom")
            self._cards = bottomlist + self._cards + toplist
            for card in toplist+bottomlist:
                card.zone = self
                self.send(CardEnteredZone(), card=card)
            self.pending_top[:] = []
            self.pending_bottom[:] = []
            self.post_commit()
            self.pending = False

class OutPlayMixin(object):
    def setup_new_role(self, card):
        cardtmpl = GameObject._cardmap[card.key]
        return cardtmpl.new_role(cardtmpl.out_play_role)

class Graveyard(OutPlayMixin, OrderedZone):
    name = "graveyard"

class Hand(OutPlayMixin, Zone):
    name = "hand"

class Removed(OutPlayMixin, Zone):
    name = "removed"

class Library(OutPlayMixin, OrderedZone):
    def __init__(self):
        super(Library, self).__init__()
        self.needs_shuffle = False
    def add_new_card(self, card, position="top"):
        newcard = self.setup_new_role(card)
        return self._insert_card(card, newcard, position)
    def get_card_order(self, cardlist, pos):
        # we're gonna shuffle anyway, no need to order the cards
        if self.needs_shuffle: return cardlist
        else: return super(Library, self).get_card_order(cardlist, pos)
    def shuffle(self):
        if not self.pending:
            random.shuffle(self._cards)
            self.send(ShuffleEvent())
        else: self.needs_shuffle = True
    def post_commit(self):
        if self.needs_shuffle:
            self.needs_shuffle = False
            random.shuffle(self._cards)
            self.send(ShuffleEvent())
    name = "library"

class PlayView(object):
    def __init__(self, player, play):
        self.player = player
        self.play = play
    def __iter__(self):
        # Top of the cards is the end of the list
        return iter(self.get())
    def get(self, match=lambda c: True, all=False):
        if all: return self.play.get(match)
        else:
            return [card for card in self.play if match(card) and card.controller == self.player]
    def __getattr__(self, attr):
        return getattr(self.play, attr)
    def move_card(self, card, position="top"):
        return self.play.move_card(card, position, self.player)
    def __str__(self): return "play"

class Play(OrderedZone):
    name = "play"
    def __init__(self, game):
        self.game = game
        self.controllers = {}
        super(Play, self).__init__()
    def get_view(self, player):
        return PlayView(player, self)
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
    def move_card(self, card, position, controller):
        card = super(Play, self).move_card(card, position)
        self.controllers[card] = controller
        return card
    def setup_new_role(self, card):
        cardtmpl = GameObject._cardmap[card.key]
        return cardtmpl.new_role(cardtmpl.in_play_role)
    def before_card_added(self, card):
        card.initialize_controller(self.controllers[card])
        super(Play, self).before_card_added(card)
    def post_commit(self):
        self.controllers = {}

class CardStack(Zone):
    name = "stack"
    def setup_new_role(self, card):
        cardtmpl = GameObject._cardmap[card.key]
        return cardtmpl.new_role(cardtmpl.stack_role)
