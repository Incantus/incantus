#!/usr/bin/python

import bsddb
import os
import cPickle as pickle

db = bsddb.hashopen("data/cards.db", 'c')
for root, dirs, files in os.walk('cards', topdown=True):
    if ".svn" in dirs: dirs.remove(".svn")
    for fname in files:
        if fname[0] == '.': continue
        fullpath = os.path.join(root, fname)
        cardname = fname.replace("_", " ")
        text = open(fullpath).read()
        #db[cardname] = text
        card = (text, True, False)
        db[cardname] = pickle.dumps(card, protocol=2)
db.close()
