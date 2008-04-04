
import bsddb, urllib

f = bsddb.hashopen("cards.db", 'c')

cards = [l.split("\t")[1].strip() for l in file("checklist.txt").readlines()]

for name in set(cards):
    print "Downloading", name
    imagename = name.replace(" ", "_").replace("-", "_").replace("'","").replace(",","")
    img_file = urllib.urlopen("http://www.wizards.com/global/images/magic/general/%s.jpg"%imagename)
    data = img_file.read()
    img_file.close()
    f[name] = data
f.close()

