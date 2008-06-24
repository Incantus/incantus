import bsddb, sys
import cPickle as p

if not len(sys.argv) == 2:
    filename = "data/cards.db"
else: filename = sys.argv[1]

f = bsddb.hashopen(filename)
names = f.keys()
cards = []
for name in names:
    card = p.loads(f[name])
    cards.append((name.encode("rot13"), card[2], card[3]))

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
