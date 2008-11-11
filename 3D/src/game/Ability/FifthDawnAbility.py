from EffectsUtilities import keyword_action

@keyword_action
def scry(self, number):
    cards = self.library.top(number)
    bottom_cards = set(self.getCardSelection(cards, number=-1, prompt="Pick any number of cards to put on the bottom of your library."))
    for card in cards:
        if card in bottom_cards: position = 'bottom'
        else: position = 'top'
        card.move_to(self.library, position=position)

def keyword_action(func):
    setattr(Player, func.__name__, func)
