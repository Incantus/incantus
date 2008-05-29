import bsddb
import cPickle as p
f = bsddb.hashopen("data/cards.db")
names = f.keys()
cards = []
for name in names:
    card = p.loads(f[name])
    cards.append((name, card[2], card[3]))

cards.sort(key=lambda c: c[0])
f = file("cardlist.txt", 'w')
f.write("Name\tTested\tError\n")
f.write("---------------------------\n")
for name, tested, error in cards:
    #if tested: tested = 'x'
    #else: tested = ''
    #if error: error = 'x'
    #else: error = ''
    f.write("%s\t%s\t%s\n"%(name, tested, error))
f.close()
