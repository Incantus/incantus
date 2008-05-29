import bsddb
import cPickle as p
f = bsddb.hashopen("cards.db")
tested = [t.strip() for t in file("tested").readlines()]

for name in tested:
    str = "Setting %s"%name
    name = name.encode('rot13')
    if name in f:
        card = p.loads(f[name])
        f[name] = p.dumps((card[0], card[1], True, card[3]))
    else: str += " ...Error"
    print str
f.close()
