from EffectsUtilities import keyword_action

@keyword_action
def scry(player, number):
    cards = player.library.top(number)
    bottom_cards = set(player.getCardSelection(cards, number=-1, prompt="Pick any number of cards to put on the bottom of your library."))
    for card in cards:
        if card in bottom_cards: position = 'bottom'
        else: position = 'top'
        card.move_to("library", position=position)
