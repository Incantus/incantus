
import bsddb

elves = file("../decks/Elves.txt").readlines()
goblins = file("../decks/Goblins.txt").readlines()

cardnames = []
for group in [elves, goblins]:
    cardnames.extend([' '.join(c.strip().split()[1:]) for c in group])

carddb = bsddb.hashopen("../data/cards.db")
evg = bsddb.hashopen("../data/Elves_vs_Goblins.db")

for name in cardnames:
    key = name.encode("rot13")
    evg[key] = carddb[key]
evg.sync()
evg.close()
