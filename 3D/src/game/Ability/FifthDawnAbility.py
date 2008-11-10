

def scry(player, value):
    cards = player.library.top(value)
    bottom_cards = set(player.getCardSelection(cards, number=-1, prompt="Pick any number of cards to put on the bottom of your library."))
    for card in cards:
        if card in bottom_cards: position = 'bottom'
        else: position = 'top'
        card.move_to(player.library, position=position)
