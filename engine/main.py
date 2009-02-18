"""
Sample game
"""

from Player import Player
from GameKeeper import Keeper

if __name__ == "__main__":

    player1 = Player("Bob")
    player2 = Player("Brian")

    player1.loadDeck("sample_deck.txt")
    player2.loadDeck("sample_deck.txt")
    player1.library.shuffle()
    player2.library.shuffle()
    player1.draw(7)
    player2.draw(7)

    Keeper.init(player1, player2)
    Keeper.run()
