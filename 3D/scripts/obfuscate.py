import cPickle as p
import bsddb

old = bsddb.hashopen("cards.db")
new = bsddb.hashopen("newcards.db")
keys = old.keys()
for k in keys:
    text, impl, tested, error = p.loads(old[k])
    new[k.encode('rot13')] = p.dumps((text.encode('rot13'), impl, tested, error))

new.close()
