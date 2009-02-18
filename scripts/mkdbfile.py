#!/usr/bin/python

import bsddb
import sys, os
import cPickle as pickle

def combine(cardfile = "cards.db", carddir = "cards"):
    db = bsddb.hashopen(cardfile, 'c')
    for root, dirs, files in os.walk(carddir, topdown=True):
        if os.path.basename(root)[0] == '.':
            dirs[:] = []
            continue
        for fname in files:
            print fname
            if fname[0] == '.': continue
            fullpath = os.path.join(root, fname)
            cardname = fname.replace("_", " ")
            text = open(fullpath).read()
            if cardname in db: card = (text,)+pickle.loads(db[cardname])[1:]
            else: card = (text, True, False, False)
            db[cardname] = pickle.dumps(card, protocol=2)
    db.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Usage: python mkdbfile.py [cards.db] [card dir]"
        sys.exit(-1)

    cardfile = sys.argv[1]
    carddir = sys.argv[2]
    combine(cardfile, carddir)

