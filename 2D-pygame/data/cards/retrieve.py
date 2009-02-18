#! /usr/bin/env python

import urllib

def retrieveImage(edition, card_no, name):
    #request1 = "http://magiccards.info/scans/en/%s/%d.jpg"%(edition, card_no)
    request1 = "http://magiccards.info/scans/en/lw/%d.jpg"%(card_no)
    urllib.urlretrieve(request1, name)

if __name__ == '__main__':
    for ed in ['lrw']:
        cardlist = file("%s_checklist.txt"%ed).readlines()
        path = ed+'/'
        for line in cardlist:
            if line[0] == '#':
                continue

            fields = line.split("\t")
            import string
            fields = [l.strip() for l in fields]
            number = int(fields[0])
            name = fields[1].replace(" ", "_")
            #'_'.join(fields[1:2])

            print number, name
            name = '%s%03d_%s.jpg'%(path,number,name)
            name = '%s%s_%s.jpg'%(path,number,name)
            retrieveImage(ed, number, name)
